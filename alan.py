from collections import defaultdict

from instructions import get_instruction


mem = bytearray(0x10000)

instructions_by_address = {}
origins_by_address = defaultdict(set)
destinations_by_address = defaultdict(set)


class Routine(object):
    def __init__(self, start_addr):
        self.start_addr = start_addr
        self.calls = []
        self.is_traced = False
        self.exit_points = set()

routines = {}


def trace_routine(start_addr):
    addresses_to_trace = [start_addr]
    visited_addresses = set()
    print("Tracing from %04x..." % start_addr)

    routine = Routine(start_addr)
    routines[start_addr] = routine

    while addresses_to_trace:
        addr = addresses_to_trace.pop()
        visited_addresses.add(addr)

        instruction = get_instruction(mem, addr)
        print(instruction)

        is_previously_traced = addr in instructions_by_address

        if not is_previously_traced:
            instructions_by_address[addr] = instruction

        if instruction.is_routine_exit:
            # TODO: check that stack is balanced
            routine.exit_points.add(instruction)

        for dest in instruction.static_destination_addresses:
            if not is_previously_traced:
                destinations_by_address[addr].add(dest)
                origins_by_address[dest].add(addr)

            if dest in visited_addresses:
                # already traced
                pass
            elif dest in addresses_to_trace:
                # already scheduled to be traced
                pass
            elif dest == instruction.call_target:
                # special case - follow calls recursively
                pass
            else:
                addresses_to_trace.append(dest)

        if instruction.call_target is not None:
            if instruction.call_target in routines:
                subroutine = routines[instruction.call_target]
                if not subroutine.is_traced:
                    raise Exception("Recursive call detected!")
                print("Using previously-completed trace of routine from %04x." %
                    instruction.call_target)
            else:
                subroutine = trace_routine(instruction.call_target)

            if subroutine.exit_points:
                for exit_point in subroutine.exit_points:
                    # mark each exit instruction as having this call's return address
                    # as a destination
                    destinations_by_address[exit_point.addr].add(instruction.return_address)
                    # mark the return address as being arrivable from each exit point
                    origins_by_address[instruction.return_address].add(exit_point.addr)

                # continue tracing from the return address
                addresses_to_trace.append(instruction.return_address)
            else:
                print("Subroutine does not exit; not continuing to trace from its return address")

    routine.is_traced = True
    print("Completed trace from %04x." % start_addr)
    return routine


i = 0x4000
with open('stc_player.bin', 'rb') as f:
    for byte in bytearray(f.read()):
        mem[i] = byte
        i += 1

with open('shatners_bassoon.stc', 'rb') as f:
    for byte in bytearray(f.read()):
        mem[i] = byte
        i += 1

trace_routine(0x4000)
trace_routine(0x4006)

print("Trace complete:")

for addr, instruction in sorted(instructions_by_address.items()):
    origins = ','.join(["%04x" % origin for origin in origins_by_address[addr]])
    destinations = ','.join(["%04x" % dest for dest in destinations_by_address[addr]])
    print("%s - reachable from: %s, goes to: %s" % (instruction, origins, destinations))


print("routine 0x4000 exits via: %r" % [exit.addr for exit in routines[0x4000].exit_points])
print("routine 0x4006 exits via: %r" % [exit.addr for exit in routines[0x4006].exit_points])
