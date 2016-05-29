from collections import defaultdict
import re

from instructions import get_instruction


mem = bytearray(0x10000)

instructions_by_address = {}
origins_by_address = defaultdict(set)
destinations_by_address = defaultdict(set)
jump_targets = set()


class Routine(object):
    def __init__(self, start_addr):
        self.start_addr = start_addr
        self.calls = []
        self.is_traced = False
        self.exit_points = set()
        self.instructions = []

    def to_javascript(self):
        print("function r%04x() {" % self.start_addr)

        has_jumps = any(
            instruction.addr in jump_targets for instruction in self.instructions
        )

        if has_jumps:
            print("\tvar pc = 0x%04x;" % self.start_addr)
            print("\twhile (true) {\n\t\tswitch (pc) {")

            for instruction in self.instructions:
                if instruction.addr in jump_targets or instruction.addr == self.start_addr:
                    print("\t\t\tcase 0x%04x:" % instruction.addr)

                code = instruction.to_javascript()
                print(re.sub(r'^', '\t\t\t\t', code, flags=re.MULTILINE))

            print('\t\t}\n\t}')
        else:
            for instruction in self.instructions:
                code = instruction.to_javascript()
                print(re.sub(r'^', '\t', code, flags=re.MULTILINE))

        print("}")

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

        is_previously_traced = addr in instructions_by_address
        if is_previously_traced:
            instruction = instructions_by_address[addr]
        else:
            instruction = get_instruction(mem, addr)
            instructions_by_address[addr] = instruction

        routine.instructions.append(instruction)
        print(instruction)

        if instruction.is_routine_exit:
            # TODO: check that stack is balanced
            routine.exit_points.add(instruction)

        if instruction.jump_target is not None:
            jump_targets.add(instruction.jump_target)

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
            routine.calls.append(instruction.call_target)

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
    routine.instructions.sort(key=lambda inst:inst.addr)
    print("Completed trace from %04x." % start_addr)
    return routine


def result_is_used(instruction, var):
    addresses_to_trace = set(destinations_by_address[instruction.addr])
    visited_addresses = set()

    while addresses_to_trace:
        addr = addresses_to_trace.pop()
        visited_addresses.add(addr)
        instruction = instructions_by_address[addr]
        if var in instruction.uses:
            return True

        if var not in instruction.overwrites:
            # continue tracing past this instruction
            for dest in destinations_by_address[addr]:
                if dest not in visited_addresses:
                    addresses_to_trace.add(dest)

    # exhausted all addresses without finding one that uses this result
    return False


def get_used_results(instruction):
    return set(
        var for var in instruction.overwrites
        if result_is_used(instruction, var)
    )

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

print("Trace complete.")

for addr, instruction in sorted(instructions_by_address.items()):
    instruction.used_results = get_used_results(instruction)

    origins = ','.join(["%04x" % origin for origin in origins_by_address[addr]])
    destinations = ','.join(["%04x" % dest for dest in destinations_by_address[addr]])
    print("%s - reachable from: %s, goes to: %s" % (instruction, origins, destinations))
    print("Needs to evaluate", instruction.used_results, 'from', instruction.overwrites)


print("Routines:")

for addr, routine in sorted(routines.items()):
    calls = ', '.join(["0x%04x" % dest for dest in routine.calls])
    print("0x%04x - %d instructions, calls %s" % (addr, len(routine.instructions), calls))


# print("routine 0x4000 exits via: %r" % [exit.addr for exit in routines[0x4000].exit_points])
# print("routine 0x4006 exits via: %r" % [exit.addr for exit in routines[0x4006].exit_points])

print(routines[0x40af].to_javascript())
print(routines[0x40b5].to_javascript())
print(routines[0x40ba].to_javascript())
print(routines[0x441f].to_javascript())
print(routines[0x4000].to_javascript())
