from collections import defaultdict
import re
from io import StringIO

from instructions import get_instruction, TRACKED_VALUES


verbose = True

mem = bytearray(0x10000)

instructions_by_address = {}
origins_by_address = defaultdict(set)
destinations_by_address = defaultdict(set)
jump_targets = set()


def log(*args):
    if verbose:
        print(*args)


class Routine(object):
    def __init__(self, start_addr):
        self.start_addr = start_addr
        self.calls = []
        self.is_traced = False
        self.exit_points = set()
        self.instructions = []
        self.overwrites = None
        self.uses = None
        self.results = None

    def to_javascript(self):
        out = StringIO()
        print("function r%04x() {" % self.start_addr, file=out)

        print("\t/*\n\tInputs: %r\n\tOutputs: %r\n\tOverwrites: %r\n\t*/" % (
            list(self.uses), list(self.results), list(self.overwrites)
        ), file=out)

        has_jumps = any(
            instruction.addr in jump_targets for instruction in self.instructions
        )

        if has_jumps:
            print("\tvar pc = 0x%04x;" % self.start_addr, file=out)
            print("\twhile (true) {\n\t\tswitch (pc) {", file=out)

            for instruction in self.instructions:
                if instruction.addr in jump_targets or instruction.addr == self.start_addr:
                    print("\t\t\tcase 0x%04x:" % instruction.addr, file=out)

                code = instruction.to_javascript()
                print(re.sub(r'^', '\t\t\t\t', code, flags=re.MULTILINE), file=out)

            print('\t\t}\n\t}', file=out)
        else:
            for instruction in self.instructions:
                code = instruction.to_javascript()
                print(re.sub(r'^', '\t', code, flags=re.MULTILINE), file=out)

        print("}", file=out)

        result = out.getvalue()
        out.close()
        return result

routines = {}


def trace_routine(start_addr):
    addresses_to_trace = [start_addr]
    visited_addresses = set()
    log("Tracing from %04x..." % start_addr)

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
        log(instruction)

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
                log("Using previously-completed trace of routine from %04x." %
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
                log("Subroutine does not exit; not continuing to trace from its return address")

    routine.is_traced = True
    routine.instructions.sort(key=lambda inst:inst.addr)
    log("Completed trace from %04x." % start_addr)
    return routine


def value_is_used(var, addresses_to_trace, follow_routine_exits=True):
    addresses_to_trace = set(addresses_to_trace)
    visited_addresses = set()

    while addresses_to_trace:
        addr = addresses_to_trace.pop()
        visited_addresses.add(addr)
        instruction = instructions_by_address[addr]
        if var in instruction.uses:
            return True

        if var not in instruction.overwrites:
            # continue tracing past this instruction
            if (not follow_routine_exits) and instruction.is_routine_exit:
                # only follow the destinations of this instruction that are
                # not routine exits - i.e. the statically known ones
                for dest in instruction.static_destination_addresses:
                    if dest not in visited_addresses:
                        addresses_to_trace.add(dest)
            else:
                for dest in destinations_by_address[addr]:
                    if dest not in visited_addresses:
                        addresses_to_trace.add(dest)

    # exhausted all addresses without finding one that uses this result
    return False


def result_is_used(instruction, var):
    return value_is_used(var, destinations_by_address[instruction.addr])


def get_used_results(instruction):
    return set(
        var for var in instruction.overwrites
        if result_is_used(instruction, var)
    )


def get_values_written_by_routine(routine):
    values = set()
    for instruction in routine.instructions:
        values.update(instruction.overwrites)
    return values


def get_values_used_by_routine(routine):
    return set(
        value for value in TRACKED_VALUES
        if value_is_used(value, [routine.start_addr], follow_routine_exits=False)
    )


def get_results_from_routine(routine):
    # get the destinations of all exit points of this routine
    destinations = set()
    for instruction in routine.exit_points:
        for dest in destinations_by_address[instruction.addr]:
            if dest not in instruction.static_destination_addresses:
                destinations.add(addr)

    return set(
        value for value in routine.overwrites
        if value_is_used(value, destinations)
    )


def dump_javascript_with_dependencies(addrs):
    routines_output = set()
    routines_to_output = list(addrs)
    while routines_to_output:
        addr = routines_to_output.pop(0)
        routine = routines[addr]
        for call_addr in routine.calls:
            if call_addr not in routines_output and call_addr not in routines_to_output:
                routines_to_output.append(call_addr)

        print(routine.to_javascript())
        routines_output.add(addr)


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

log("Trace complete.")

for addr, instruction in sorted(instructions_by_address.items()):
    instruction.used_results = get_used_results(instruction)

    origins = ','.join(["%04x" % origin for origin in origins_by_address[addr]])
    destinations = ','.join(["%04x" % dest for dest in destinations_by_address[addr]])
    log("%s - reachable from: %s, goes to: %s" % (instruction, origins, destinations))
    log("Needs to evaluate", instruction.used_results, 'from', instruction.overwrites)


log("Routines:")

for addr, routine in sorted(routines.items()):
    routine.uses = get_values_used_by_routine(routine)
    routine.overwrites = get_values_written_by_routine(routine)
    routine.results = get_results_from_routine(routine)

    calls = ', '.join(["0x%04x" % dest for dest in routine.calls])
    log("0x%04x - %d instructions, calls %s, uses %r, overwrites %r, returns %r" % (
        addr, len(routine.instructions), calls, routine.uses, routine.overwrites, routine.results
    ))


# print("routine 0x4000 exits via: %r" % [exit.addr for exit in routines[0x4000].exit_points])
# print("routine 0x4006 exits via: %r" % [exit.addr for exit in routines[0x4006].exit_points])

dump_javascript_with_dependencies([0x4000])
dump_javascript_with_dependencies([0x4006])
