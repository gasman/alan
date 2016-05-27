from functools import partial


def get_mem(mem, addr):
    return mem[addr & 0xffff]


class Instruction(object):
    is_routine_exit = False

    def __init__(self, mem, addr):
        self.addr = addr
        self.used_results = None

    @property
    def static_destination_addresses(self):
        return [(self.addr + self.length) & 0xffff]

    @property
    def jump_target(self):
        return None

    @property
    def call_target(self):
        return None

    def __str__(self):
        return "0x%04x: %s" % (self.addr, self.asm_repr())


class InstructionWithReg(Instruction):
    def __init__(self, reg, mem, addr):
        self.reg = reg
        super(InstructionWithReg, self).__init__(mem, addr)


class InstructionWithRegPair(Instruction):
    def __init__(self, reg_pair, mem, addr):
        self.reg_pair = reg_pair
        super(InstructionWithRegPair, self).__init__(mem, addr)


class InstructionWithTwoRegs(Instruction):
    def __init__(self, r1, r2, mem, addr):
        self.r1 = r1
        self.r2 = r2
        super(InstructionWithTwoRegs, self).__init__(mem, addr)


class InstructionWithRegAndRegPair(Instruction):
    def __init__(self, reg, reg_pair, mem, addr):
        self.reg = reg
        self.reg_pair = reg_pair
        super(InstructionWithRegAndRegPair, self).__init__(mem, addr)


class InstructionWithBit(Instruction):
    def __init__(self, bit, mem, addr):
        self.bit = bit
        super(InstructionWithBit, self).__init__(mem, addr)


class InstructionWithBitAndReg(Instruction):
    def __init__(self, bit, reg, mem, addr):
        self.bit = bit
        self.reg = reg
        super(InstructionWithBitAndReg, self).__init__(mem, addr)


class InstructionWithBitAndRegPair(Instruction):
    def __init__(self, bit, reg_pair, mem, addr):
        self.bit = bit
        self.reg_pair = reg_pair
        super(InstructionWithBitAndRegPair, self).__init__(mem, addr)


class InstructionWithTwoRegPairs(Instruction):
    # This is an instruction such as ADD IX,DE
    # Due to the way we apply partials, where ADD rr,DE is an instruction in the IX or IY list,
    # rp2 (DE) appears before rp1 (IX) in the param list
    def __init__(self, rp2, rp1, mem, addr):
        self.rp1 = rp1
        self.rp2 = rp2
        super(InstructionWithTwoRegPairs, self).__init__(mem, addr)


class InstructionWithCondition(Instruction):
    def __init__(self, condition, mem, addr):
        self.condition = condition
        super(InstructionWithCondition, self).__init__(mem, addr)


class InstructionWithNoParam(Instruction):
    length = 1


class ExtendedInstructionWithNoParam(Instruction):
    length = 2


class InstructionWithByteParam(Instruction):
    length = 2

    def __init__(self, mem, addr):
        super(InstructionWithByteParam, self).__init__(mem, addr)
        self.param = get_mem(mem, addr + 1)


class ExtendedInstructionWithByteParam(Instruction):
    length = 3

    def __init__(self, mem, addr):
        super(ExtendedInstructionWithByteParam, self).__init__(mem, addr)
        self.param = get_mem(mem, addr + 2)


class InstructionWithOffsetParam(Instruction):
    length = 2

    def __init__(self, mem, addr):
        super(InstructionWithOffsetParam, self).__init__(mem, addr)
        offset_param = get_mem(mem, addr + 1)

        if offset_param > 128:
            self.offset = offset_param - 256
        else:
            self.offset = offset_param


class ExtendedInstructionWithOffsetParam(Instruction):
    length = 3

    def __init__(self, mem, addr):
        super(ExtendedInstructionWithOffsetParam, self).__init__(mem, addr)
        offset_param = get_mem(mem, addr + 2)

        if offset_param > 128:
            self.offset = offset_param - 256
        else:
            self.offset = offset_param


class DoubleExtendedInstructionWithOffsetParam(Instruction):
    length = 4

    def __init__(self, mem, addr):
        super(DoubleExtendedInstructionWithOffsetParam, self).__init__(mem, addr)
        offset_param = get_mem(mem, addr + 2)

        if offset_param > 128:
            self.offset = offset_param - 256
        else:
            self.offset = offset_param


class ExtendedInstructionWithOffsetAndByteParams(Instruction):
    length = 4

    def __init__(self, mem, addr):
        super(ExtendedInstructionWithOffsetAndByteParams, self).__init__(mem, addr)
        offset_param = get_mem(mem, addr + 2)

        if offset_param > 128:
            self.offset = offset_param - 256
        else:
            self.offset = offset_param

        self.param = get_mem(mem, addr + 3)


class InstructionWithWordParam(Instruction):
    length = 3

    def __init__(self, mem, addr):
        super(InstructionWithWordParam, self).__init__(mem, addr)
        self.lo = get_mem(mem, addr + 1)
        self.hi = get_mem(mem, addr + 2)

    @property
    def param(self):
        return (self.hi << 8) | self.lo


class ExtendedInstructionWithWordParam(Instruction):
    length = 4

    def __init__(self, mem, addr):
        super(ExtendedInstructionWithWordParam, self).__init__(mem, addr)
        self.lo = get_mem(mem, addr + 2)
        self.hi = get_mem(mem, addr + 3)

    @property
    def param(self):
        return (self.hi << 8) | self.lo


REGS_FROM_PAIR = {
    'BC': ('B', 'C'),
    'DE': ('D', 'E'),
    'HL': ('H', 'L'),
    'IX': ('IXH', 'IXL'),
    'IY': ('IYH', 'IYL'),
}

FLAG_FROM_CONDITION = {
    'C': 'C-flag',
    'NC': 'C-flag',
    'Z': 'Z-flag',
    'NZ': 'Z-flag',
    'PO': 'PV-flag',
    'PE': 'PV-flag',
    'P': 'S-flag',
    'M': 'S-flag',
}


class ADD_A_iHLi(InstructionWithNoParam):
    def asm_repr(self):
        return "ADD A,(HL)"

    uses = {'A', 'H', 'L'}
    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class ADD_A_N(InstructionWithByteParam):
    def asm_repr(self):
        return "ADD A,0x%02x" % self.param

    uses = {'A'}
    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class ADD_A_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "ADD A,%s" % self.reg

    @property
    def uses(self):
        return {'A', self.reg}

    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class ADD_HL_RR(InstructionWithRegPair, InstructionWithNoParam):
    def asm_repr(self):
        return "ADD HL,%s" % self.reg_pair

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {'H', 'L', h, l}

    overwrites = {'H', 'L', 'C-flag'}


class ADD_IXIY_RR(InstructionWithTwoRegPairs, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "ADD %s,%s" % (self.rp1, self.rp2)

    @property
    def uses(self):
        h1, l1 = REGS_FROM_PAIR[self.rp1]
        h2, l2 = REGS_FROM_PAIR[self.rp2]
        return {h1, l1, h2, l2}

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.rp1]
        return {h, l, 'C-flag'}


class AND_N(InstructionWithByteParam):
    def asm_repr(self):
        return "AND 0x%02x" % self.param

    uses = {'A'}
    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class AND_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "AND %s" % self.reg

    @property
    def uses(self):
        return {'A', self.reg}

    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class BIT_N_iIXIYpNi(InstructionWithBitAndRegPair, DoubleExtendedInstructionWithOffsetParam):
    def asm_repr(self):
        if self.offset < 0:
            return "BIT %d,(%s-0x%02x)" % (self.bit, self.reg_pair, -self.offset)
        else:
            return "BIT %d,(%s+0x%02x)" % (self.bit, self.reg_pair, self.offset)

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    overwrites = {'Z-flag', 'PV-flag', 'S-flag'}


class BIT_N_R(InstructionWithBitAndReg, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "BIT %d,%s" % (self.bit, self.reg)

    @property
    def uses(self):
        return {self.reg}

    overwrites = {'Z-flag', 'PV-flag', 'S-flag'}


class CALL_NN(InstructionWithWordParam):
    @property
    def static_destination_addresses(self):
        return [self.param]

    @property
    def call_target(self):
        return self.param

    @property
    def return_address(self):
        return (self.addr + self.length) & 0xffff

    def asm_repr(self):
        return "CALL 0x%04x" % self.param

    uses = set()
    overwrites = set()


class CALL_C_NN(InstructionWithCondition, InstructionWithWordParam):
    @property
    def static_destination_addresses(self):
        return [
            self.param,
            (self.addr + self.length) & 0xffff,
        ]

    @property
    def call_target(self):
        return self.param

    @property
    def return_address(self):
        return (self.addr + self.length) & 0xffff

    def asm_repr(self):
        return "CALL %s,0x%04x" % (self.condition, self.param)

    @property
    def uses(self):
        return {FLAG_FROM_CONDITION[self.condition]}

    overwrites = set()


class CP_iHLi(InstructionWithNoParam):
    def asm_repr(self):
        return "CP (HL)"

    uses = {'A', 'H', 'L'}
    overwrites = {'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class CP_N(InstructionWithByteParam):
    def asm_repr(self):
        return "CP 0x%02x" % self.param

    uses = {'A'}
    overwrites = {'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class DEC_iIXIYpNi(InstructionWithRegPair, ExtendedInstructionWithOffsetParam):
    def asm_repr(self):
        if self.offset < 0:
            return "DEC (%s-0x%02x)" % (self.reg_pair, -self.offset)
        else:
            return "DEC (%s+0x%02x)" % (self.reg_pair, self.offset)

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    overwrites = {'Z-flag', 'PV-flag', 'S-flag'}


class DEC_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "DEC %s" % self.reg

    @property
    def uses(self):
        return {self.reg}

    @property
    def overwrites(self):
        return {self.reg, 'Z-flag', 'PV-flag', 'S-flag'}


class DEC_RR(InstructionWithRegPair, InstructionWithNoParam):
    def asm_repr(self):
        return "DEC %s" % self.reg_pair

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}


class DI(InstructionWithNoParam):
    def asm_repr(self):
        return "DI"

    uses = set()
    overwrites = set()


class EI(InstructionWithNoParam):
    def asm_repr(self):
        return "EI"

    uses = set()
    overwrites = set()


class EX_DE_HL(InstructionWithNoParam):
    def asm_repr(self):
        return "EX DE,HL"

    uses = {'D', 'E', 'H', 'L'}
    overwrites = {'D', 'E', 'H', 'L'}


class INC_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "INC %s" % self.reg

    @property
    def uses(self):
        return {self.reg}

    @property
    def overwrites(self):
        return {self.reg, 'Z-flag', 'PV-flag', 'S-flag'}


class INC_RR(InstructionWithRegPair, InstructionWithNoParam):
    def asm_repr(self):
        return "INC %s" % self.reg_pair

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}


class JP_NN(InstructionWithWordParam):
    @property
    def jump_target(self):
        return self.param

    @property
    def static_destination_addresses(self):
        return [self.param]

    def asm_repr(self):
        return "JP 0x%04x" % self.param

    uses = set()
    overwrites = set()


class JP_C_NN(InstructionWithCondition, InstructionWithWordParam):
    @property
    def jump_target(self):
        return self.param

    @property
    def static_destination_addresses(self):
        return [
            self.param,
            (self.addr + self.length) & 0xffff,
        ]

    def asm_repr(self):
        return "JP %s,0x%04x" % (self.condition, self.param)

    @property
    def uses(self):
        return {FLAG_FROM_CONDITION[self.condition]}

    overwrites = set()


class JR_NN(InstructionWithOffsetParam):
    @property
    def jump_target(self):
        return (self.addr + 2 + self.offset) & 0xffff

    @property
    def static_destination_addresses(self):
        return [self.jump_target]

    def asm_repr(self):
        return "JR 0x%04x" % self.jump_target

    uses = set()
    overwrites = set()


class JR_C_NN(InstructionWithCondition, InstructionWithOffsetParam):
    @property
    def jump_target(self):
        return (self.addr + 2 + self.offset) & 0xffff

    @property
    def static_destination_addresses(self):
        return [
            self.jump_target,
            (self.addr + self.length) & 0xffff,
        ]

    def asm_repr(self):
        return "JR %s,0x%04x" % (self.condition, self.jump_target)

    @property
    def uses(self):
        return {FLAG_FROM_CONDITION[self.condition]}

    overwrites = set()


class LD_A_iNNi(InstructionWithWordParam):
    def asm_repr(self):
        return "LD A,(0x%04x)" % self.param

    uses = set()
    overwrites = {'A'}


class LD_A_iRRi(InstructionWithRegPair, InstructionWithNoParam):
    def asm_repr(self):
        return "LD A,(%s)" % self.reg_pair

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    overwrites = {'A'}


class LD_BCDE_iNNi(InstructionWithRegPair, ExtendedInstructionWithWordParam):
    def asm_repr(self):
        return "LD %s,(0x%04x)" % (self.reg_pair, self.param)

    uses = set()

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}


class LD_iIXIYpNi_N(InstructionWithRegPair, ExtendedInstructionWithOffsetAndByteParams):
    def asm_repr(self):
        if self.offset < 0:
            return "LD (%s-0x%02x),0x%02x" % (self.reg_pair, -self.offset, self.param)
        else:
            return "LD (%s+0x%02x),0x%02x" % (self.reg_pair, self.offset, self.param)

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    overwrites = set()


class LD_iIXIYpNi_R(InstructionWithRegAndRegPair, ExtendedInstructionWithOffsetParam):
    def asm_repr(self):
        if self.offset < 0:
            return "LD (%s-0x%02x),%s" % (self.reg_pair, -self.offset, self.reg)
        else:
            return "LD (%s+0x%02x),%s" % (self.reg_pair, self.offset, self.reg)

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l, self.reg}

    overwrites = set()


class LD_HL_iNNi(InstructionWithWordParam):
    def asm_repr(self):
        return "LD HL,(0x%04x)" % self.param

    uses = set()
    overwrites = {'H', 'L'}


class LD_iHLi_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "LD (HL),%s" % self.reg

    @property
    def uses(self):
        return {'H', 'L', self.reg}

    overwrites = set()


class LD_iNNi_A(InstructionWithWordParam):
    def asm_repr(self):
        return "LD (0x%04x),A" % self.param

    uses = {'A'}
    overwrites = set()


class LD_iNNi_BCDE(InstructionWithRegPair, ExtendedInstructionWithWordParam):
    def asm_repr(self):
        return "LD (0x%04x),%s" % (self.param, self.reg_pair)

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    overwrites = set()


class LD_iNNi_HL(InstructionWithWordParam):
    def asm_repr(self):
        return "LD (0x%04x),HL" % self.param

    uses = {'H', 'L'}
    overwrites = set()


class LD_IXIY_iNNi(InstructionWithRegPair, ExtendedInstructionWithWordParam):
    def asm_repr(self):
        return "LD %s,(0x%04x)" % (self.reg_pair, self.param)

    uses = set()

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}


class LD_IXIY_NN(InstructionWithRegPair, ExtendedInstructionWithWordParam):
    def asm_repr(self):
        return "LD %s,0x%04x" % (self.reg_pair, self.param)

    uses = set()

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}


class LD_R_iIXIYpNi(InstructionWithRegAndRegPair, ExtendedInstructionWithOffsetParam):
    def asm_repr(self):
        if self.offset < 0:
            return "LD %s,(%s-0x%02x)" % (self.reg, self.reg_pair, -self.offset)
        else:
            return "LD %s,(%s+0x%02x)" % (self.reg, self.reg_pair, self.offset)

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}

    @property
    def overwrites(self):
        return {self.reg}


class LD_R_iHLi(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "LD %s,(HL)" % self.reg

    uses = {'H', 'L'}

    @property
    def overwrites(self):
        return {self.reg}


class LD_R_N(InstructionWithReg, InstructionWithByteParam):
    def asm_repr(self):
        return "LD %s,0x%02x" % (self.reg, self.param)

    uses = set()

    @property
    def overwrites(self):
        return {self.reg}


class LD_R_R(InstructionWithTwoRegs, InstructionWithNoParam):
    def asm_repr(self):
        return "LD %s,%s" % (self.r1, self.r2)

    @property
    def uses(self):
        return {self.r2}

    @property
    def overwrites(self):
        return {self.r1}


class LD_RR_NN(InstructionWithRegPair, InstructionWithWordParam):
    def asm_repr(self):
        return "LD %s,0x%04x" % (self.reg_pair, self.param)

    uses = set()

    @property
    def overwrites(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {h, l}


class LDIR(ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "LDIR"

    uses = {'B', 'C', 'D', 'E', 'H', 'L'}
    overwrites = {'B', 'C', 'D', 'E', 'H', 'L', 'PV-flag'}


class OR_iHLi(InstructionWithNoParam):
    def asm_repr(self):
        return "OR (HL)"

    uses = {'A', 'H', 'L'}
    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class OR_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "OR %s" % self.reg

    @property
    def uses(self):
        return {'A', self.reg}

    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class OUT_iCi_R(InstructionWithReg, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "OUT (C),%s" % self.reg

    @property
    def uses(self):
        return {'B', 'C', self.reg}

    overwrites = set()


class OUTD(ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "OUTD"

    uses = {'B', 'C', 'H', 'L'}
    overwrites = {'B', 'H', 'L', 'Z-flag', 'PV-flag', 'S-flag'}


class POP_RR(InstructionWithRegPair, InstructionWithNoParam):
    def asm_repr(self):
        return "POP %s" % self.reg_pair

    uses = set()

    @property
    def overwrites(self):
        if self.reg_pair == 'AF':
            return {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}
        else:
            h, l = REGS_FROM_PAIR[self.reg_pair]
            return {h, l}


class PUSH_RR(InstructionWithRegPair, InstructionWithNoParam):
    def asm_repr(self):
        return "PUSH %s" % self.reg_pair

    @property
    def uses(self):
        if self.reg_pair == 'AF':
            return {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}
        else:
            h, l = REGS_FROM_PAIR[self.reg_pair]
            return {h, l}

    overwrites = set()


class RES_N_R(InstructionWithBitAndReg, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "RES %d,%s" % (self.bit, self.reg)

    @property
    def uses(self):
        return {self.reg}

    @property
    def overwrites(self):
        return {self.reg}


class RET(InstructionWithNoParam):
    is_routine_exit = True

    @property
    def static_destination_addresses(self):
        return []

    def asm_repr(self):
        return "RET"

    uses = set()
    overwrites = set()


class RET_C(InstructionWithCondition, InstructionWithNoParam):
    is_routine_exit = True

    def asm_repr(self):
        return "RET %s" % self.condition

    @property
    def uses(self):
        return {FLAG_FROM_CONDITION[self.condition]}

    overwrites = set()


class RLC_R(InstructionWithReg, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "RLC %s" % self.reg

    @property
    def uses(self):
        return {self.reg}

    @property
    def overwrites(self):
        return {self.reg, 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class RRCA(InstructionWithNoParam):
    def asm_repr(self):
        return "RRCA"

    uses = {'A'}
    overwrites = {'A', 'C-flag'}


class SBC_HL_RR(InstructionWithRegPair, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "SBC HL,%s" % self.reg_pair

    @property
    def uses(self):
        h, l = REGS_FROM_PAIR[self.reg_pair]
        return {'H', 'L', h, l, 'C-flag'}

    overwrites = {'H', 'L', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class SET_N_iHLi(InstructionWithBit, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "SET %d,(HL)" % self.bit

    uses = {'H', 'L'}
    overwrites = set()


class SET_N_R(InstructionWithBitAndReg, ExtendedInstructionWithNoParam):
    def asm_repr(self):
        return "SET %d,%s" % (self.bit, self.reg)

    @property
    def uses(self):
        return {self.reg}

    @property
    def overwrites(self):
        return {self.reg}


class SUB_N(InstructionWithByteParam):
    def asm_repr(self):
        return "SUB 0x%02x" % self.param

    uses = {'A'}
    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


class XOR_R(InstructionWithReg, InstructionWithNoParam):
    def asm_repr(self):
        return "XOR %s" % self.reg

    @property
    def uses(self):
        return {'A', self.reg}

    overwrites = {'A', 'C-flag', 'Z-flag', 'PV-flag', 'S-flag'}


INSTRUCTIONS_BY_CB_OPCODE = {
    0x00: partial(RLC_R, 'B'),
    0x01: partial(RLC_R, 'C'),
    0x02: partial(RLC_R, 'D'),
    0x03: partial(RLC_R, 'E'),
    0x04: partial(RLC_R, 'H'),
    0x05: partial(RLC_R, 'L'),

    0x07: partial(RLC_R, 'A'),

    0x40: partial(BIT_N_R, 0, 'B'),
    0x41: partial(BIT_N_R, 0, 'C'),
    0x42: partial(BIT_N_R, 0, 'D'),
    0x43: partial(BIT_N_R, 0, 'E'),
    0x44: partial(BIT_N_R, 0, 'H'),
    0x45: partial(BIT_N_R, 0, 'L'),

    0x47: partial(BIT_N_R, 0, 'A'),
    0x48: partial(BIT_N_R, 1, 'B'),
    0x49: partial(BIT_N_R, 1, 'C'),
    0x4a: partial(BIT_N_R, 1, 'D'),
    0x4b: partial(BIT_N_R, 1, 'E'),
    0x4c: partial(BIT_N_R, 1, 'H'),
    0x4d: partial(BIT_N_R, 1, 'L'),

    0x4f: partial(BIT_N_R, 1, 'A'),
    0x50: partial(BIT_N_R, 2, 'B'),
    0x51: partial(BIT_N_R, 2, 'C'),
    0x52: partial(BIT_N_R, 2, 'D'),
    0x53: partial(BIT_N_R, 2, 'E'),
    0x54: partial(BIT_N_R, 2, 'H'),
    0x55: partial(BIT_N_R, 2, 'L'),

    0x57: partial(BIT_N_R, 2, 'A'),
    0x58: partial(BIT_N_R, 3, 'B'),
    0x59: partial(BIT_N_R, 3, 'C'),
    0x5a: partial(BIT_N_R, 3, 'D'),
    0x5b: partial(BIT_N_R, 3, 'E'),
    0x5c: partial(BIT_N_R, 3, 'H'),
    0x5d: partial(BIT_N_R, 3, 'L'),

    0x5f: partial(BIT_N_R, 3, 'A'),
    0x60: partial(BIT_N_R, 4, 'B'),
    0x61: partial(BIT_N_R, 4, 'C'),
    0x62: partial(BIT_N_R, 4, 'D'),
    0x63: partial(BIT_N_R, 4, 'E'),
    0x64: partial(BIT_N_R, 4, 'H'),
    0x65: partial(BIT_N_R, 4, 'L'),

    0x67: partial(BIT_N_R, 4, 'A'),
    0x68: partial(BIT_N_R, 5, 'B'),
    0x69: partial(BIT_N_R, 5, 'C'),
    0x6a: partial(BIT_N_R, 5, 'D'),
    0x6b: partial(BIT_N_R, 5, 'E'),
    0x6c: partial(BIT_N_R, 5, 'H'),
    0x6d: partial(BIT_N_R, 5, 'L'),

    0x6f: partial(BIT_N_R, 5, 'A'),
    0x70: partial(BIT_N_R, 6, 'B'),
    0x71: partial(BIT_N_R, 6, 'C'),
    0x72: partial(BIT_N_R, 6, 'D'),
    0x73: partial(BIT_N_R, 6, 'E'),
    0x74: partial(BIT_N_R, 6, 'H'),
    0x75: partial(BIT_N_R, 6, 'L'),

    0x77: partial(BIT_N_R, 6, 'A'),
    0x78: partial(BIT_N_R, 7, 'B'),
    0x79: partial(BIT_N_R, 7, 'C'),
    0x7a: partial(BIT_N_R, 7, 'D'),
    0x7b: partial(BIT_N_R, 7, 'E'),
    0x7c: partial(BIT_N_R, 7, 'H'),
    0x7d: partial(BIT_N_R, 7, 'L'),

    0x7f: partial(BIT_N_R, 7, 'A'),
    0x80: partial(RES_N_R, 0, 'B'),
    0x81: partial(RES_N_R, 0, 'C'),
    0x82: partial(RES_N_R, 0, 'D'),
    0x83: partial(RES_N_R, 0, 'E'),
    0x84: partial(RES_N_R, 0, 'H'),
    0x85: partial(RES_N_R, 0, 'L'),

    0x87: partial(RES_N_R, 0, 'A'),
    0x88: partial(RES_N_R, 1, 'B'),
    0x89: partial(RES_N_R, 1, 'C'),
    0x8a: partial(RES_N_R, 1, 'D'),
    0x8b: partial(RES_N_R, 1, 'E'),
    0x8c: partial(RES_N_R, 1, 'H'),
    0x8d: partial(RES_N_R, 1, 'L'),

    0x8f: partial(RES_N_R, 1, 'A'),
    0x90: partial(RES_N_R, 2, 'B'),
    0x91: partial(RES_N_R, 2, 'C'),
    0x92: partial(RES_N_R, 2, 'D'),
    0x93: partial(RES_N_R, 2, 'E'),
    0x94: partial(RES_N_R, 2, 'H'),
    0x95: partial(RES_N_R, 2, 'L'),

    0x97: partial(RES_N_R, 2, 'A'),
    0x98: partial(RES_N_R, 3, 'B'),
    0x99: partial(RES_N_R, 3, 'C'),
    0x9a: partial(RES_N_R, 3, 'D'),
    0x9b: partial(RES_N_R, 3, 'E'),
    0x9c: partial(RES_N_R, 3, 'H'),
    0x9d: partial(RES_N_R, 3, 'L'),

    0x9f: partial(RES_N_R, 3, 'A'),
    0xa0: partial(RES_N_R, 4, 'B'),
    0xa1: partial(RES_N_R, 4, 'C'),
    0xa2: partial(RES_N_R, 4, 'D'),
    0xa3: partial(RES_N_R, 4, 'E'),
    0xa4: partial(RES_N_R, 4, 'H'),
    0xa5: partial(RES_N_R, 4, 'L'),

    0xa7: partial(RES_N_R, 4, 'A'),
    0xa8: partial(RES_N_R, 5, 'B'),
    0xa9: partial(RES_N_R, 5, 'C'),
    0xaa: partial(RES_N_R, 5, 'D'),
    0xab: partial(RES_N_R, 5, 'E'),
    0xac: partial(RES_N_R, 5, 'H'),
    0xad: partial(RES_N_R, 5, 'L'),

    0xaf: partial(RES_N_R, 5, 'A'),
    0xb0: partial(RES_N_R, 6, 'B'),
    0xb1: partial(RES_N_R, 6, 'C'),
    0xb2: partial(RES_N_R, 6, 'D'),
    0xb3: partial(RES_N_R, 6, 'E'),
    0xb4: partial(RES_N_R, 6, 'H'),
    0xb5: partial(RES_N_R, 6, 'L'),

    0xb7: partial(RES_N_R, 6, 'A'),
    0xb8: partial(RES_N_R, 7, 'B'),
    0xb9: partial(RES_N_R, 7, 'C'),
    0xba: partial(RES_N_R, 7, 'D'),
    0xbb: partial(RES_N_R, 7, 'E'),
    0xbc: partial(RES_N_R, 7, 'H'),
    0xbd: partial(RES_N_R, 7, 'L'),

    0xbf: partial(RES_N_R, 7, 'A'),
    0xc0: partial(SET_N_R, 0, 'B'),
    0xc1: partial(SET_N_R, 0, 'C'),
    0xc2: partial(SET_N_R, 0, 'D'),
    0xc3: partial(SET_N_R, 0, 'E'),
    0xc4: partial(SET_N_R, 0, 'H'),
    0xc5: partial(SET_N_R, 0, 'L'),
    0xc6: partial(SET_N_iHLi, 0),
    0xc7: partial(SET_N_R, 0, 'A'),
    0xc8: partial(SET_N_R, 1, 'B'),
    0xc9: partial(SET_N_R, 1, 'C'),
    0xca: partial(SET_N_R, 1, 'D'),
    0xcb: partial(SET_N_R, 1, 'E'),
    0xcc: partial(SET_N_R, 1, 'H'),
    0xcd: partial(SET_N_R, 1, 'L'),
    0xce: partial(SET_N_iHLi, 1),
    0xcf: partial(SET_N_R, 1, 'A'),
    0xd0: partial(SET_N_R, 2, 'B'),
    0xd1: partial(SET_N_R, 2, 'C'),
    0xd2: partial(SET_N_R, 2, 'D'),
    0xd3: partial(SET_N_R, 2, 'E'),
    0xd4: partial(SET_N_R, 2, 'H'),
    0xd5: partial(SET_N_R, 2, 'L'),
    0xd6: partial(SET_N_iHLi, 2),
    0xd7: partial(SET_N_R, 2, 'A'),
    0xd8: partial(SET_N_R, 3, 'B'),
    0xd9: partial(SET_N_R, 3, 'C'),
    0xda: partial(SET_N_R, 3, 'D'),
    0xdb: partial(SET_N_R, 3, 'E'),
    0xdc: partial(SET_N_R, 3, 'H'),
    0xdd: partial(SET_N_R, 3, 'L'),
    0xde: partial(SET_N_iHLi, 3),
    0xdf: partial(SET_N_R, 3, 'A'),
    0xe0: partial(SET_N_R, 4, 'B'),
    0xe1: partial(SET_N_R, 4, 'C'),
    0xe2: partial(SET_N_R, 4, 'D'),
    0xe3: partial(SET_N_R, 4, 'E'),
    0xe4: partial(SET_N_R, 4, 'H'),
    0xe5: partial(SET_N_R, 4, 'L'),
    0xe6: partial(SET_N_iHLi, 4),
    0xe7: partial(SET_N_R, 4, 'A'),
    0xe8: partial(SET_N_R, 5, 'B'),
    0xe9: partial(SET_N_R, 5, 'C'),
    0xea: partial(SET_N_R, 5, 'D'),
    0xeb: partial(SET_N_R, 5, 'E'),
    0xec: partial(SET_N_R, 5, 'H'),
    0xed: partial(SET_N_R, 5, 'L'),
    0xee: partial(SET_N_iHLi, 5),
    0xef: partial(SET_N_R, 5, 'A'),
    0xf0: partial(SET_N_R, 6, 'B'),
    0xf1: partial(SET_N_R, 6, 'C'),
    0xf2: partial(SET_N_R, 6, 'D'),
    0xf3: partial(SET_N_R, 6, 'E'),
    0xf4: partial(SET_N_R, 6, 'H'),
    0xf5: partial(SET_N_R, 6, 'L'),
    0xf6: partial(SET_N_iHLi, 6),
    0xf7: partial(SET_N_R, 6, 'A'),
    0xf8: partial(SET_N_R, 7, 'B'),
    0xf9: partial(SET_N_R, 7, 'C'),
    0xfa: partial(SET_N_R, 7, 'D'),
    0xfb: partial(SET_N_R, 7, 'E'),
    0xfc: partial(SET_N_R, 7, 'H'),
    0xfd: partial(SET_N_R, 7, 'L'),
    0xfe: partial(SET_N_iHLi, 7),
    0xff: partial(SET_N_R, 7, 'A'),
}


def get_cb_instruction(mem, addr):
    sub_opcode = get_mem(mem, addr + 1)
    try:
        instruction = INSTRUCTIONS_BY_CB_OPCODE[sub_opcode]
    except KeyError:
        raise Exception("Unrecognised CB sub-opcode at 0x%04x: 0xcb 0x%02x" % (addr, sub_opcode))

    return instruction(mem, addr)


INSTRUCTIONS_BY_DDFDCB_OPCODE = {
    0x46: partial(BIT_N_iIXIYpNi, 0),

    0x4e: partial(BIT_N_iIXIYpNi, 1),

    0x56: partial(BIT_N_iIXIYpNi, 2),

    0x5e: partial(BIT_N_iIXIYpNi, 3),

    0x66: partial(BIT_N_iIXIYpNi, 4),

    0x6e: partial(BIT_N_iIXIYpNi, 5),

    0x76: partial(BIT_N_iIXIYpNi, 6),

    0x7e: partial(BIT_N_iIXIYpNi, 7),
}


def get_ddfdcb_instruction(reg_pair, mem, addr):
    root_opcode = mem[addr]
    offset = get_mem(mem, addr + 2)
    sub_opcode = get_mem(mem, addr + 3)
    try:
        instruction = INSTRUCTIONS_BY_DDFDCB_OPCODE[sub_opcode]
    except KeyError:
        raise Exception(
            "Unrecognised DD/FD CB sub-opcode at 0x%04x: 0x%02x 0xcb 0x%02x 0x%02x" % (addr, root_opcode, offset, sub_opcode)
        )

    return instruction(reg_pair, mem, addr)


INSTRUCTIONS_BY_DDFD_OPCODE = {
    0x09: partial(ADD_IXIY_RR, 'BC'),

    0x19: partial(ADD_IXIY_RR, 'DE'),

    0x21: LD_IXIY_NN,

    0x2a: LD_IXIY_iNNi,

    0x35: DEC_iIXIYpNi,
    0x36: LD_iIXIYpNi_N,

    0x46: partial(LD_R_iIXIYpNi, 'B'),

    0x4e: partial(LD_R_iIXIYpNi, 'C'),

    0x56: partial(LD_R_iIXIYpNi, 'D'),

    0x5e: partial(LD_R_iIXIYpNi, 'E'),

    0x66: partial(LD_R_iIXIYpNi, 'H'),

    0x6e: partial(LD_R_iIXIYpNi, 'L'),

    0x70: partial(LD_iIXIYpNi_R, 'B'),
    0x71: partial(LD_iIXIYpNi_R, 'C'),
    0x72: partial(LD_iIXIYpNi_R, 'D'),
    0x73: partial(LD_iIXIYpNi_R, 'E'),
    0x74: partial(LD_iIXIYpNi_R, 'H'),
    0x75: partial(LD_iIXIYpNi_R, 'L'),
    0x77: partial(LD_iIXIYpNi_R, 'A'),

    0x7e: partial(LD_R_iIXIYpNi, 'A'),

    0xcb: get_ddfdcb_instruction,
}


def get_dd_instruction(mem, addr):
    sub_opcode = get_mem(mem, addr + 1)
    try:
        instruction = INSTRUCTIONS_BY_DDFD_OPCODE[sub_opcode]
    except KeyError:
        raise Exception("Unrecognised DD sub-opcode at 0x%04x: 0xdd 0x%02x" % (addr, sub_opcode))

    return instruction('IX', mem, addr)


INSTRUCTIONS_BY_ED_OPCODE = {
    0x41: partial(OUT_iCi_R, 'B'),
    0x42: partial(SBC_HL_RR, 'BC'),
    0x43: partial(LD_iNNi_BCDE, 'BC'),

    0x49: partial(OUT_iCi_R, 'C'),

    0x4b: partial(LD_BCDE_iNNi, 'BC'),

    0x51: partial(OUT_iCi_R, 'D'),
    0x52: partial(SBC_HL_RR, 'DE'),
    0x53: partial(LD_iNNi_BCDE, 'DE'),

    0x59: partial(OUT_iCi_R, 'E'),

    0x5b: partial(LD_BCDE_iNNi, 'DE'),

    0x61: partial(OUT_iCi_R, 'H'),
    0x62: partial(SBC_HL_RR, 'HL'),

    0x69: partial(OUT_iCi_R, 'L'),

    0x79: partial(OUT_iCi_R, 'A'),

    0xab: OUTD,

    0xb0: LDIR,
}


def get_ed_instruction(mem, addr):
    sub_opcode = get_mem(mem, addr + 1)
    try:
        instruction = INSTRUCTIONS_BY_ED_OPCODE[sub_opcode]
    except KeyError:
        raise Exception("Unrecognised ED sub-opcode at 0x%04x: 0xed 0x%02x" % (addr, sub_opcode))

    return instruction(mem, addr)


INSTRUCTIONS_BY_OPCODE = {
    0x01: partial(LD_RR_NN, 'BC'),

    0x03: partial(INC_RR, 'BC'),
    0x04: partial(INC_R, 'B'),
    0x05: partial(DEC_R, 'B'),
    0x06: partial(LD_R_N, 'B'),

    0x09: partial(ADD_HL_RR, 'BC'),
    0x0a: partial(LD_A_iRRi, 'BC'),
    0x0b: partial(DEC_RR, 'BC'),
    0x0c: partial(INC_R, 'C'),
    0x0d: partial(DEC_R, 'C'),
    0x0e: partial(LD_R_N, 'C'),
    0x0f: RRCA,

    0x11: partial(LD_RR_NN, 'DE'),

    0x13: partial(INC_RR, 'DE'),
    0x14: partial(INC_R, 'D'),
    0x15: partial(DEC_R, 'D'),
    0x16: partial(LD_R_N, 'D'),

    0x18: JR_NN,
    0x19: partial(ADD_HL_RR, 'DE'),
    0x1a: partial(LD_A_iRRi, 'DE'),
    0x1b: partial(DEC_RR, 'DE'),
    0x1c: partial(INC_R, 'E'),
    0x1d: partial(DEC_R, 'E'),
    0x1e: partial(LD_R_N, 'E'),

    0x20: partial(JR_C_NN, 'NZ'),
    0x21: partial(LD_RR_NN, 'HL'),
    0x22: LD_iNNi_HL,
    0x23: partial(INC_RR, 'HL'),
    0x24: partial(INC_R, 'H'),
    0x25: partial(DEC_R, 'H'),
    0x26: partial(LD_R_N, 'H'),

    0x28: partial(JR_C_NN, 'Z'),
    0x29: partial(ADD_HL_RR, 'HL'),
    0x2a: LD_HL_iNNi,
    0x2b: partial(DEC_RR, 'HL'),
    0x2c: partial(INC_R, 'L'),
    0x2d: partial(DEC_R, 'L'),
    0x2e: partial(LD_R_N, 'L'),

    0x30: partial(JR_C_NN, 'NC'),

    0x32: LD_iNNi_A,

    0x38: partial(JR_C_NN, 'C'),

    0x3a: LD_A_iNNi,

    0x3c: partial(INC_R, 'A'),
    0x3d: partial(DEC_R, 'A'),
    0x3e: partial(LD_R_N, 'A'),

    0x40: partial(LD_R_R, 'B', 'B'),
    0x41: partial(LD_R_R, 'B', 'C'),
    0x42: partial(LD_R_R, 'B', 'D'),
    0x43: partial(LD_R_R, 'B', 'E'),
    0x44: partial(LD_R_R, 'B', 'H'),
    0x45: partial(LD_R_R, 'B', 'L'),
    0x46: partial(LD_R_iHLi, 'B'),
    0x47: partial(LD_R_R, 'B', 'A'),
    0x48: partial(LD_R_R, 'C', 'B'),
    0x49: partial(LD_R_R, 'C', 'C'),
    0x4a: partial(LD_R_R, 'C', 'D'),
    0x4b: partial(LD_R_R, 'C', 'E'),
    0x4c: partial(LD_R_R, 'C', 'H'),
    0x4d: partial(LD_R_R, 'C', 'L'),
    0x4e: partial(LD_R_iHLi, 'C'),
    0x4f: partial(LD_R_R, 'C', 'A'),
    0x50: partial(LD_R_R, 'D', 'B'),
    0x51: partial(LD_R_R, 'D', 'C'),
    0x52: partial(LD_R_R, 'D', 'D'),
    0x53: partial(LD_R_R, 'D', 'E'),
    0x54: partial(LD_R_R, 'D', 'H'),
    0x55: partial(LD_R_R, 'D', 'L'),
    0x56: partial(LD_R_iHLi, 'D'),
    0x57: partial(LD_R_R, 'D', 'A'),
    0x58: partial(LD_R_R, 'E', 'B'),
    0x59: partial(LD_R_R, 'E', 'C'),
    0x5a: partial(LD_R_R, 'E', 'D'),
    0x5b: partial(LD_R_R, 'E', 'E'),
    0x5c: partial(LD_R_R, 'E', 'H'),
    0x5d: partial(LD_R_R, 'E', 'L'),
    0x5e: partial(LD_R_iHLi, 'E'),
    0x5f: partial(LD_R_R, 'E', 'A'),
    0x60: partial(LD_R_R, 'H', 'B'),
    0x61: partial(LD_R_R, 'H', 'C'),
    0x62: partial(LD_R_R, 'H', 'D'),
    0x63: partial(LD_R_R, 'H', 'E'),
    0x64: partial(LD_R_R, 'H', 'H'),
    0x65: partial(LD_R_R, 'H', 'L'),
    0x66: partial(LD_R_iHLi, 'H'),
    0x67: partial(LD_R_R, 'H', 'A'),
    0x68: partial(LD_R_R, 'L', 'B'),
    0x69: partial(LD_R_R, 'L', 'C'),
    0x6a: partial(LD_R_R, 'L', 'D'),
    0x6b: partial(LD_R_R, 'L', 'E'),
    0x6c: partial(LD_R_R, 'L', 'H'),
    0x6d: partial(LD_R_R, 'L', 'L'),
    0x6e: partial(LD_R_iHLi, 'L'),
    0x6f: partial(LD_R_R, 'L', 'A'),
    0x70: partial(LD_iHLi_R, 'B'),
    0x71: partial(LD_iHLi_R, 'C'),
    0x72: partial(LD_iHLi_R, 'D'),
    0x73: partial(LD_iHLi_R, 'E'),
    0x74: partial(LD_iHLi_R, 'H'),
    0x75: partial(LD_iHLi_R, 'L'),
    0x77: partial(LD_iHLi_R, 'A'),
    0x78: partial(LD_R_R, 'A', 'B'),
    0x79: partial(LD_R_R, 'A', 'C'),
    0x7a: partial(LD_R_R, 'A', 'D'),
    0x7b: partial(LD_R_R, 'A', 'E'),
    0x7c: partial(LD_R_R, 'A', 'H'),
    0x7d: partial(LD_R_R, 'A', 'L'),
    0x7e: partial(LD_R_iHLi, 'A'),
    0x7f: partial(LD_R_R, 'A', 'A'),
    0x80: partial(ADD_A_R, 'B'),
    0x81: partial(ADD_A_R, 'C'),
    0x82: partial(ADD_A_R, 'D'),
    0x83: partial(ADD_A_R, 'E'),
    0x84: partial(ADD_A_R, 'H'),
    0x85: partial(ADD_A_R, 'L'),
    0x86: ADD_A_iHLi,
    0x87: partial(ADD_A_R, 'A'),

    0xa0: partial(AND_R, 'B'),
    0xa1: partial(AND_R, 'C'),
    0xa2: partial(AND_R, 'D'),
    0xa3: partial(AND_R, 'E'),
    0xa4: partial(AND_R, 'H'),
    0xa5: partial(AND_R, 'L'),

    0xa7: partial(AND_R, 'A'),
    0xa8: partial(XOR_R, 'B'),
    0xa9: partial(XOR_R, 'C'),
    0xaa: partial(XOR_R, 'D'),
    0xab: partial(XOR_R, 'E'),
    0xac: partial(XOR_R, 'H'),
    0xad: partial(XOR_R, 'L'),

    0xaf: partial(XOR_R, 'A'),
    0xb0: partial(OR_R, 'B'),
    0xb1: partial(OR_R, 'C'),
    0xb2: partial(OR_R, 'D'),
    0xb3: partial(OR_R, 'E'),
    0xb4: partial(OR_R, 'H'),
    0xb5: partial(OR_R, 'L'),
    0xb6: OR_iHLi,
    0xb7: partial(OR_R, 'A'),

    0xbe: CP_iHLi,

    0xc0: partial(RET_C, 'NZ'),
    0xc1: partial(POP_RR, 'BC'),
    0xc2: partial(JP_C_NN, 'NZ'),
    0xc3: JP_NN,
    0xc4: partial(CALL_C_NN, 'NZ'),
    0xc5: partial(PUSH_RR, 'BC'),
    0xc6: ADD_A_N,

    0xc8: partial(RET_C, 'Z'),
    0xc9: RET,
    0xca: partial(JP_C_NN, 'Z'),
    0xcb: get_cb_instruction,
    0xcc: partial(CALL_C_NN, 'Z'),
    0xcd: CALL_NN,

    0xd0: partial(RET_C, 'NC'),
    0xd1: partial(POP_RR, 'DE'),
    0xd2: partial(JP_C_NN, 'NC'),

    0xd4: partial(CALL_C_NN, 'NC'),
    0xd5: partial(PUSH_RR, 'DE'),
    0xd6: SUB_N,

    0xd8: partial(RET_C, 'C'),

    0xda: partial(JP_C_NN, 'C'),

    0xdc: partial(CALL_C_NN, 'C'),
    0xdd: get_dd_instruction,

    0xe0: partial(RET_C, 'PO'),
    0xe1: partial(POP_RR, 'HL'),
    0xe2: partial(JP_C_NN, 'PO'),

    0xe4: partial(CALL_C_NN, 'PO'),
    0xe5: partial(PUSH_RR, 'HL'),
    0xe6: AND_N,

    0xe8: partial(RET_C, 'PE'),

    0xea: partial(JP_C_NN, 'PE'),
    0xeb: EX_DE_HL,
    0xec: partial(CALL_C_NN, 'PE'),
    0xed: get_ed_instruction,

    0xf0: partial(RET_C, 'P'),
    0xf1: partial(POP_RR, 'AF'),
    0xf2: partial(JP_C_NN, 'P'),
    0xf3: DI,
    0xf4: partial(CALL_C_NN, 'P'),
    0xf5: partial(PUSH_RR, 'AF'),

    0xf8: partial(RET_C, 'M'),

    0xfa: partial(JP_C_NN, 'M'),
    0xfb: EI,
    0xfc: partial(CALL_C_NN, 'M'),

    0xfe: CP_N,
}


def get_instruction(mem, addr):
    opcode = mem[addr]
    try:
        instruction = INSTRUCTIONS_BY_OPCODE[opcode]
    except KeyError:
        raise Exception("Unrecognised opcode at 0x%04x: 0x%02x" % (addr, opcode))

    return instruction(mem, addr)
