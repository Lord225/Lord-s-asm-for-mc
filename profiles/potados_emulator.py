if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())

from ast import operator
import typing
from pybytes import Binary, u16, i16, ops
import core.config as config
import core.error as error
import core.emulate as emulate
import numpy as np
import queue
import unittest

class POTADOS_EMULATOR(emulate.EmulatorBase):
    DEBUG_IGNORE_JUMPS = False
    DEBUG_HALT_ON_NOP = False

    SP = 15
    PC = 7
    PT = 1
    FL = 8

    def __init__(self) -> None:
        self.regs = REGS()
        self.ram = RAM(self, None)
        self.rom = ROM(self, 4096)
        self.is_running_flag = True
        self.pc_modified = False


    def get_current_pos(self, chunk_name: typing.Optional[str]) -> int:
        return int(self.regs[self.PC])

    def is_running(self) -> bool:
        return self.is_running_flag

    def get_machine_cycles(self) -> int:
        return 1

    def next_tick(self,) -> typing.Optional[str]:
        command = self.rom[self.get_current_pos(None)]
        
        # nop
        if command == 0:
            self.nop()
            self.increment_pc()
            return

        # int 0 (early stop)
        if command == 1187584:
            self.halt()
            self.increment_pc()
            return

        # parse command
        pri_decoder = int(command[20:22])  # primary decoder 2 bit
        destination = int(command[0:4])    # dst register 4 bit

        if pri_decoder == 0:   # load imm
            constant = command[4:20] # const 16 bit

            if destination == self.PC:
                self.jump(constant)
            else:
                self.load_imm(constant, destination)

        elif pri_decoder == 3: # call
            constant = command[4:20] # const 16 bit
            self.call(constant)

        elif pri_decoder == 2: # jumps
            sec_decoder = int(command[17:20])
            r2_value = int(command[13:17])
            offsethi = command[8:13]
            r1_value = int(command[4:8])
            offsetlo = command[0:4]

            offset = Binary(bit_lenght=9)
            offset[0:4] = offsetlo
            offset[4:9] = offsethi
            offset = ops.sign_extend(offset, 16)

            if sec_decoder == 0:   # jge
                self.jge(r1_value, r2_value, offset)
            elif sec_decoder == 1: # jl
                self.jl(r1_value, r2_value, offset)
            elif sec_decoder == 2: # je
                self.je(r1_value, r2_value, offset)
            elif sec_decoder == 3: # jne
                self.jne(r1_value, r2_value, offset)
            elif sec_decoder == 4: # jae
                self.jae(r1_value, r2_value, offset)
            elif sec_decoder == 5: # jb 
                self.jb(r1_value, r2_value, offset)
            elif sec_decoder == 6: # jge imm
                self.jge_imm(r1_value, r2_value, offset)
            elif sec_decoder == 7: # je imm
                self.jge_imm(r1_value, r2_value, offset)
            else:
                raise error.EmulationError("Unreachable")
        else:                      # rest
            sec_decoder = int(command[17:20])
            flags = command[10:13]

            if sec_decoder in [0, 7, 6, 5, 4, 3]: # alu long
                self.alu_long(sec_decoder, destination, command)
            elif sec_decoder == 2:                # alu short / fpu
                self.alu_short(destination, flags, command)
            elif sec_decoder == 1:      # other        
                if flags == 0:
                    self.fpu(destination, command)
                elif flags == 1:        # load ptr lsh
                    print("load ptr lsh")
                elif flags == 2:        # load ptr imm
                    print("load ptr imm")
                elif flags == 3:        # store ptr lsh
                    print("store ptr lsh")
                elif flags == 4:        # store ptr imm
                    print("store ptr imm") 
                elif flags == 5:        # pop
                    print("pop")
                elif flags == 6:        # push
                    print("push")
                elif flags == 7:        # converts & interupt
                    print("converts")
                else:
                    raise error.EmulationError("Unrachable")
            else:
                raise error.EmulationError("Unrachable")
        
        self.increment_pc()
        self.pc_modified = False
        
    
    def increment_pc(self):
        if not self.pc_modified:
            self.regs[self.PC] += 1
            self.pc_modified = True
    def modify_pc(self, new_value):
        if self.DEBUG_IGNORE_JUMPS:
            print(f"Dummy jump: {new_value}")
            return
        self.regs[self.PC] = new_value
        self.pc_modified = True
        
    def alu_long(self, sec_decoder: int, destination: int, command: Binary):
        I = command[12]
        r1_value = command[4:12]       # 8 bit
        r2_value = int(command[13:17]) # 4 bit

        if I:
            imm = ops.sign_extend(r1_value, 16)
            if sec_decoder == 0:
                self.alu_add_imm(imm, r2_value, destination)
            elif sec_decoder == 7:
                self.alu_sub_imm(imm, r2_value, destination)
            elif sec_decoder == 6:
                self.alu_arsh_imm(imm, r2_value, destination)
            elif sec_decoder == 5:
                self.alu_rsh_imm(imm, r2_value, destination)
            elif sec_decoder == 4:
                self.alu_lsh_imm(imm, r2_value, destination)
            elif sec_decoder == 3:
                self.alu_mul_imm(imm, r2_value, destination)
        else:
            r1 = int(r1_value[:4])
            if sec_decoder == 0:
                self.alu_add_reg(r1, r2_value, destination)
            elif sec_decoder == 7:
                self.alu_sub_reg(r1, r2_value, destination)
            elif sec_decoder == 6:
                self.alu_arsh_reg(r1, r2_value, destination)
            elif sec_decoder == 5:
                self.alu_lsh_reg(r1, r2_value, destination)
            elif sec_decoder == 4:
                self.alu_rsh_reg(r1, r2_value, destination)
            elif sec_decoder == 3:
                self.alu_mul_reg(r1, r2_value, destination)
    def alu_short(self, destination: int, flags:Binary, command: Binary):
        tri_dec = int(command[8:10])
        r1 = int(command[4:8])
        r2 = int(command[13:16])

        if tri_dec == 0:    # adc
            self.alu_adc(r1, r2, destination)
        elif tri_dec == 1:  # sbc
            self.alu_adc(r1, r2, destination)
        elif tri_dec == 2:  # xor
            if flags[2]:
                self.alu_xnor(r1, r2, destination, "~" if flags[1] else "", "~" if flags[0] else "")
            else:
                self.alu_xor(r1, r2, destination, "~" if flags[1] else "", "~" if flags[0] else "")
        elif tri_dec == 3:  # or
            if flags[2]:
                self.alu_nor(r1, r2, destination, "~" if flags[1] else "", "~" if flags[0] else "")
            else:
                self.alu_or(r1, r2, destination, "~" if flags[1] else "", "~" if flags[0] else "")
        else:
            raise error.EmulationError("Unreachable")
    def fpu(self, destination: int, command: Binary):
        tri_dec = int(command[8:10])
        if tri_dec == 0:    # fadd
            print("fadd")
        elif tri_dec == 1:  # fsub
            print("fsub")
        elif tri_dec == 2:  # fmul
            print("fmul")
        elif tri_dec == 3:  # fdiv
            print("fdiv")
        else:
            raise error.EmulationError("Unreachable")
    ##################
    #    FL update   #
    ##################
    
    def update_flags_for_jump(self, r1, r2):
        eq = r1 == r2
        gr = r1 > r2
        le = r1 <= r2
        ge = r1 >= r2
        ls = r1 < r2
        self.regs[self.FL][0] = eq
        self.regs[self.FL][1] = gr
        self.regs[self.FL][2] = le
        self.regs[self.FL][3] = ge
        self.regs[self.FL][4] = ls
        self.regs[self.FL][4:16] = False

    def update_flags_for_add_sub(self, flags: ops.Flags):
        self.regs[self.FL][0] = flags.is_zero()
        self.regs[self.FL][1] = flags.is_overflow() #TODO check if it works fine for subtraction (tzn czy to jest borrow flag)
        self.regs[self.FL][2] = flags.is_sign()
        self.regs[self.FL][3] = flags.is_overflow()

    @emulate.log_disassembly(format='nop')
    def nop(self):
        if self.DEBUG_HALT_ON_NOP:
            self.halt()

    @emulate.log_disassembly(format='int 0')   
    def halt(self):
        self.is_running_flag = False

    ############
    # ALU LONG #
    ############
    ######################
    # add implementation #
    ######################
    def alu_add(self, imm_r1: Binary, imm_r2: Binary, dst: int):
        r1 = ops.cast(imm_r1.extended_low(), 'unsigned')
        r2 = ops.cast(imm_r2.extended_low(), 'unsigned')
        
        out, flags = ops.flaged_add(r1, r2)

        self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='add reg[{dst}], reg[{r2_reg}] {r1_imm}')
    def alu_add_imm(self, r1_imm: Binary, r2_reg: int, dst: int):
        r2_imm = self.regs[r2_reg]

        self.alu_add(r1_imm, r2_imm, dst)
    @emulate.log_disassembly(format='add reg[{dst}], reg[{r2_reg}], reg[{r1_reg}]')
    def alu_add_reg(self, r1_reg: int, r2_reg: int, dst: int):
        r1_imm = self.regs[r1_reg]
        r2_imm = self.regs[r2_reg]

        self.alu_add(r1_imm, r2_imm, dst)

    ######################
    # sub implementation #
    ######################
    def alu_sub(self, imm_r1: Binary, imm_r2: Binary, dst: int):
        r1 = ops.cast(imm_r1.extended_low(), 'unsigned')
        r2 = ops.cast(imm_r2.extended_low(), 'unsigned')
        
        out, flags = ops.flaged_sub(r1, r2)

        self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='sub reg[{dst}], reg[{r2_reg}] {r1_imm}')
    def alu_sub_imm(self, r1_imm: Binary, r2_reg: int, dst: int):
        r2_imm = self.regs[r2_reg]

        self.alu_sub(r1_imm, r2_imm, dst)
    @emulate.log_disassembly(format='sub reg[{dst}], reg[{r2_reg}], reg[{r1_reg}]')
    def alu_sub_reg(self, r1_reg: int, r2_reg: int, dst: int):
        r1_imm = self.regs[r1_reg]
        r2_imm = self.regs[r2_reg]

        self.alu_sub(r1_imm, r2_imm, dst)
        
    #######################
    # arsh implementation #
    #######################
    def alu_arsh(self, imm_r1: Binary, imm_r2: Binary, dst: int):
        r1 = ops.cast(imm_r1.extended_low(), 'unsigned')
        r2 = ops.cast(imm_r2.extended_low(), 'unsigned')
        
        out, _ = ops.arithmetic_flaged_rsh(r1, r2)

        #self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='arsh reg[{dst}], reg[{r2_reg}] {r1_imm}')
    def alu_arsh_imm(self, r1_imm: Binary, r2_reg: int, dst: int):
        r2_imm = self.regs[r2_reg]

        self.alu_arsh(r1_imm, r2_imm, dst)
    @emulate.log_disassembly(format='arsh reg[{dst}], reg[{r2_reg}], reg[{r1_reg}]')
    def alu_arsh_reg(self, r1_reg: int, r2_reg: int, dst: int):
        r1_imm = self.regs[r1_reg]
        r2_imm = self.regs[r2_reg]

        self.alu_arsh(r1_imm, r2_imm, dst)
    
    ######################
    # rsh implementation #
    ######################
    def alu_rsh(self, imm_r1: Binary, imm_r2: Binary, dst: int):
        r1 = ops.cast(imm_r1.extended_low(), 'unsigned')
        r2 = ops.cast(imm_r2.extended_low(), 'unsigned')
        
        out, _ = ops.flaged_rsh(r1, r2)

        #self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='rsh reg[{dst}], reg[{r2_reg}] {r1_imm}')
    def alu_rsh_imm(self, r1_imm: Binary, r2_reg: int, dst: int):
        r2_imm = self.regs[r2_reg]

        self.alu_rsh(r1_imm, r2_imm, dst)
    @emulate.log_disassembly(format='rsh reg[{dst}], reg[{r2_reg}], reg[{r1_reg}]')
    def alu_rsh_reg(self, r1_reg: int, r2_reg: int, dst: int):
        r1_imm = self.regs[r1_reg]
        r2_imm = self.regs[r2_reg]

        self.alu_rsh(r1_imm, r2_imm, dst)

    ######################
    # lsh implementation #
    ######################
    def alu_lsh(self, imm_r1: Binary, imm_r2: Binary, dst: int):
        r1 = ops.cast(imm_r1.extended_low(), 'unsigned')
        r2 = ops.cast(imm_r2.extended_low(), 'unsigned')
        
        out, _ = ops.flaged_lsh(r1, r2)

        #self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='lsh reg[{dst}], reg[{r2_reg}] {r1_imm}')
    def alu_lsh_imm(self, r1_imm: Binary, r2_reg: int, dst: int):
        r2_imm = self.regs[r2_reg]

        self.alu_lsh(r1_imm, r2_imm, dst)
    @emulate.log_disassembly(format='lsh reg[{dst}], reg[{r2_reg}], reg[{r1_reg}]')
    def alu_lsh_reg(self, r1_reg: int, r2_reg: int, dst: int):
        r1_imm = self.regs[r1_reg]
        r2_imm = self.regs[r2_reg]

        self.alu_lsh(r1_imm, r2_imm, dst)

    ######################
    # mul implementation #
    ######################
    def alu_mul(self, imm_r1: Binary, imm_r2: Binary, dst: int):
        r1 = ops.cast(imm_r1.extended_low(), 'unsigned')
        r2 = ops.cast(imm_r2.extended_low(), 'unsigned')
        
        out, _ = ops.flaged_mul(r1, r2)

        #self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='mul reg[{dst}], reg[{r2_reg}] {r1_imm}')
    def alu_mul_imm(self, r1_imm: Binary, r2_reg: int, dst: int):
        r2_imm = self.regs[r2_reg]

        self.alu_mul(r1_imm, r2_imm, dst)
    @emulate.log_disassembly(format='mul reg[{dst}], reg[{r2_reg}], reg[{r1_reg}]')
    def alu_mul_reg(self, r1_reg: int, r2_reg: int, dst: int):
        r1_imm = self.regs[r1_reg]
        r2_imm = self.regs[r2_reg]

        self.alu_mul(r1_imm, r2_imm, dst)
    
    #############
    # ALU SHORT #
    #############
    @emulate.log_disassembly(format='adc reg[{dst}], reg[{r2}], reg[{r1}]')
    def alu_adc(self, r1: int, r2: int, dst: int):
        r1_imm = self.regs[r1]
        r2_imm = self.regs[r2]
        carry = self.regs[self.FL][1]
        
        out, flags = ops.flaged_add(r1_imm, r2_imm + 1 if carry else 0)
        
        self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='sbc reg[{dst}], reg[{r2}], reg[{r1}]')
    def alu_sbc(self, r1: int, r2: int, dst: int):
        r1_imm = self.regs[r1]
        r2_imm = self.regs[r2]
        carry = self.regs[self.FL][1]
        
        out, flags = ops.flaged_sub(r1_imm, r2_imm + 1 if carry else 0)
        
        self.update_flags_for_add_sub(flags)

        self.regs[dst] = out
    @emulate.log_disassembly(format='xor reg[{dst}], {r1_neg}reg[{r2}], {r2_neg}reg[{r1}]')
    def alu_xor(self, r1: int, r2: int, dst: int, r1_neg: str, r2_neg: str):
        r1_imm = self.regs[r1] if r1_neg == "" else ops.bitwise_not(self.regs[r1])
        r2_imm = self.regs[r2] if r2_neg == "" else ops.bitwise_not(self.regs[r1])
        
        self.regs[dst] = ops.bitwise_xor(r1_imm, r2_imm)
    @emulate.log_disassembly(format='xnor reg[{dst}], {r1_neg}reg[{r2}], {r2_neg}reg[{r1}]')
    def alu_xnor(self, r1: int, r2: int, dst: int, r1_neg: str, r2_neg: str):
        r1_imm = self.regs[r1] if r1_neg == "" else ops.bitwise_not(self.regs[r1])
        r2_imm = self.regs[r2] if r2_neg == "" else ops.bitwise_not(self.regs[r1])
        
        self.regs[dst] = ops.bitwise_xnor(r1_imm, r2_imm)

    @emulate.log_disassembly(format='or reg[{dst}], {r1_neg}reg[{r2}], {r2_neg}reg[{r1}]')
    def alu_or(self, r1: int, r2: int, dst: int, r1_neg: str, r2_neg: str):
        r1_imm = self.regs[r1] if r1_neg == "" else ops.bitwise_not(self.regs[r1])
        r2_imm = self.regs[r2] if r2_neg == "" else ops.bitwise_not(self.regs[r1])
        
        self.regs[dst] = ops.bitwise_or(r1_imm, r2_imm)
    @emulate.log_disassembly(format='nor reg[{dst}], {r1_neg}reg[{r2}], {r2_neg}reg[{r1}]')
    def alu_nor(self, r1: int, r2: int, dst: int, r1_neg: str, r2_neg: str):
        r1_imm = self.regs[r1] if r1_neg == "" else ops.bitwise_not(self.regs[r1])
        r2_imm = self.regs[r2] if r2_neg == "" else ops.bitwise_not(self.regs[r1])
        
        self.regs[dst] = ops.bitwise_nor(r1_imm, r2_imm)
    
    
    ######################
    # mov implementation #
    ######################
    @emulate.log_disassembly(format='mov reg[{dst}], {const}')
    def load_imm(self, const: Binary, dst: int):
        if dst == self.PC:
            self.modify_pc(const)
        else:
            self.regs[dst] = const
    @emulate.log_disassembly(format='jmp {const}')
    def jump(self, const: Binary):
        self.modify_pc(const)
    @emulate.log_disassembly(format='call {const}')
    def call(self, const: Binary):
        self.ram[self.regs[self.SP]] = self.regs[self.PC]
        self.regs[self.SP] += 1
        self.modify_pc(const)
    

    ########################
    # cjmps implementation #
    ########################
    @emulate.log_disassembly(format='jge reg[{r1_value}], reg[{r2_value}], {offset}')
    def jge(self, r1_value, r2_value, offset):
        r1 = ops.cast(self.regs[r1_value], 'signed')
        r2 = ops.cast(self.regs[r2_value], 'signed')

        self.update_flags_for_jump(r1, r2)

        if r1 >= r2:
            self.modify_pc(self.regs[self.PC] + offset)
    @emulate.log_disassembly(format='jl reg[{r1_value}], reg[{r2_value}], {offset}')
    def jl(self, r1_value, r2_value, offset):
        r1 = ops.cast(self.regs[r1_value], 'signed')
        r2 = ops.cast(self.regs[r2_value], 'signed')

        self.update_flags_for_jump(r1, r2)

        if r1 < r2:
            self.modify_pc(self.regs[self.PC] + offset)
    @emulate.log_disassembly(format='je reg[{r1_value}], reg[{r2_value}], {offset}')
    def je(self, r1_value, r2_value, offset):
        r1 = self.regs[r1_value]
        r2 = self.regs[r2_value]

        self.update_flags_for_jump(r1, r2)

        if r1 == r2:
            self.modify_pc(self.regs[self.PC] + offset) 
    @emulate.log_disassembly(format='jne reg[{r1_value}], reg[{r2_value}], {offset}')
    def jne(self, r1_value, r2_value, offset):
        r1 = self.regs[r1_value]
        r2 = self.regs[r2_value]

        self.update_flags_for_jump(r1, r2)

        if r1 != r2:
            self.modify_pc(self.regs[self.PC] + offset) 
    @emulate.log_disassembly(format='jae reg[{r1_value}], reg[{r2_value}], {offset}')
    def jae(self, r1_value, r2_value, offset):
        r1 = self.regs[r1_value]
        r2 = self.regs[r2_value]

        self.update_flags_for_jump(r1, r2)

        if r1 >= r2:
            self.modify_pc(self.regs[self.PC] + offset) 
    @emulate.log_disassembly(format='jb reg[{r1_value}], reg[{r2_value}], {offset}')
    def jb(self, r1_value, r2_value, offset):
        r1 = self.regs[r1_value]
        r2 = self.regs[r2_value]

        self.update_flags_for_jump(r1, r2)

        if r1 < r2:
            self.modify_pc(self.regs[self.PC] + offset) 
    @emulate.log_disassembly(format='jge {r1_value}, reg[{r2_value}], {offset}')
    def jge_imm(self, r1_value, r2_value, offset):
        r1 = ops.cast(ops.sign_extend(r1_value, 16), 'signed')
        r2 = ops.cast(self.regs[r2_value], 'signed')

        self.update_flags_for_jump(r1, r2)

        if r1 >= r2:
            self.modify_pc(self.regs[self.PC] + offset)
    @emulate.log_disassembly(format='je {r1_value}, reg[{r2_value}], {offset}')
    def je_imm(self, r1_value, r2_value, offset):
        r1 = ops.cast(ops.sign_extend(r1_value, 16), 'signed')
        r2 = ops.cast(self.regs[r2_value], 'signed')

        self.update_flags_for_jump(r1, r2)

        if r1 == r2:
            self.modify_pc(self.regs[self.PC] + offset)
    



    def write_memory(self, chunk_name: typing.Optional[str], type: emulate.DataTypes, data: dict):
        if type == emulate.DataTypes.DATA:
            for address, value in data.items():
                self.ram[address] = value
        if type == emulate.DataTypes.PROGRAM:
            self.rom.program_rom(data)

    def exec_command(self, chunk_name: typing.Optional[str], method_name: str, args: typing.List) -> typing.Any:
        method = self.__getattribute__(method_name)
        return method(*args)

    ################## 
    # DEBUG COMMANDS #
    ##################

    def enable_dummy_jumps(self):
        self.DEBUG_IGNORE_JUMPS = True
    def disable_dummy_jumps(self):
        self.DEBUG_IGNORE_JUMPS = False
    def enable_dummy_reg_writes(self):
        self.regs.DEBUG_FREEZE_WRITES = True
    def disable_dummy_reg_writes(self):
        self.regs.DEBUG_FREEZE_WRITES = False
    def get_ram_ref(self):
        return self.ram.ram
    def get_regs_ref(self):
        return self.regs.regs


class REGS:
    DEBUG_FREEZE_WRITES = False

    def __init__(self):
        self.regs = [u16(0) for _ in range(0, 16)]
    def __getitem__(self, key: int) -> Binary: 
        if key == 0:
            return u16(0)
        return self.regs[key]
    def __setitem__(self, key: int, val: Binary):
        if self.DEBUG_FREEZE_WRITES:
            return
        if key == 0:
            return

        if len(val) != 16:
            val = val.extended_low()
        val = ops.cast(val, 'unsigned')
        self.regs[key] = val
    def __str__(self) -> str:
        return str(self.regs)

class RAM:
    DEBUG_LOG_RAM_MOVMENT = False 
    DEBUG_FREEZE_RAM_WRITES = False
    DEBUG_RISE_ON_OUT_OF_BOUNDS = False

    def __init__(self, potados: typing.Optional[POTADOS_EMULATOR], ram: typing.Optional[np.ndarray]) -> None:
        self.cpu = potados
        if ram is None:
            self.ram: np.ndarray = np.zeros((256), dtype='uint16')
        else:
            self.ram: np.ndarray = ram.astype('uint16')
        self.ram = self.ram[:256]

    
    def __getitem__(self, key: int) -> Binary:
        key = int(key)

        bus = u16(0)
        if key < 0x0100:
            bus = self.io_get(key)
        if key >= 0x0200:
            if self.DEBUG_RISE_ON_OUT_OF_BOUNDS:
                raise error.EmulationError(f"Ram address out of bounds: {key}")
            bus = u16(0)
        else:
            bus = u16(int(self.ram[key-0x0100]))
        if self.DEBUG_LOG_RAM_MOVMENT:
            print(f"RAM READ ADDRES: {key} (BUS: {key})")
        return bus
        
    def __setitem__(self, key: int, val: Binary):
        key = int(key)
        if not isinstance(val, Binary):
            val = Binary(val, bit_lenght=16)
        if key < 0x0100:
            if self.DEBUG_LOG_RAM_MOVMENT:
                print(f"RAM WRITE ADDRES: {key} (BUS: {val})")
            self.io_set(key, val)
        if key >= 0x0200:
            if self.DEBUG_RISE_ON_OUT_OF_BOUNDS:
                raise error.EmulationError(f"Ram address out of bounds: {key}, trying write value: {val}")
            return
        if self.DEBUG_FREEZE_RAM_WRITES:
            return
        if self.DEBUG_LOG_RAM_MOVMENT:
                print(f"RAM WRITE ADDRES: {key} (BUS: {val.extended_low()})")
        self.ram[key-0x0100] = int(val.extended_low())


    def io_set(self, index: int, val: Binary):
        if index > 0x0100:
            raise
        
        
    def io_get(self, index: int) -> Binary:
        if index > 0x0100:
            raise
        
        return u16()

class ROM:
    def __init__(self, potados: POTADOS_EMULATOR, ROM_SIZE) -> None: 
        self.cpu = potados
        self.rom = np.zeros((ROM_SIZE), dtype='uint32')

    def program_rom(self, data: dict):
        for address, value in data.items():
            self.rom[address] = value
    
    def __getitem__(self, address: int) -> Binary:
        return Binary(int(self.rom[address]), bit_lenght=22)
    
def get_emulator() -> POTADOS_EMULATOR:
    return POTADOS_EMULATOR()


# To pulloff tests just run 
# python -m unittest profiles\potados_emulator.py from \Lord-s-asm-for-mc\ 
# (or debug this file inside vs code)

class RAM_TESTS(unittest.TestCase):
    def test_get_ram_default(self):
        ram = RAM(None, None)

        self.assertEqual(ram[0x0100], u16(0))
        self.assertEqual(ram[0x0101], u16(0))
        self.assertEqual(ram[0x01FF], u16(0))
        self.assertEqual(ram[0x0200], u16(0))
        self.assertEqual(ram.ram.shape, (256,))

    def test_get_ram_ones(self):
        ram = RAM(None, np.ones((256)))

        self.assertEqual(ram[0x0100], u16(1))
        self.assertEqual(ram[0x0101], u16(1))
        self.assertEqual(ram[0x01FF], u16(1))
        self.assertEqual(ram[0x0200], u16(0))
        self.assertEqual(ram.ram.shape, (256,))

    def test_get_ram_ones_from_bigger_array(self):
        ram = RAM(None, np.ones((1024)))

        self.assertEqual(ram[0x0100], u16(1))
        self.assertEqual(ram[0x0101], u16(1))
        self.assertEqual(ram[0x01FF], u16(1))
        self.assertEqual(ram[0x0200], u16(0))
        self.assertEqual(ram.ram.shape, (256,))
    
    def test_set_ram(self):
        ram = RAM(None, np.ones((256)))

        ram[0x0100] = 255
        self.assertEqual(ram[0x0100], u16(255))
        ram[0x0100] = -1
        self.assertEqual(ram[0x0100], u16(2**16-1)) #u16 max 
        ram[0x01FF] = 255
        self.assertEqual(ram[0x01FF], u16(255))
        ram[0x0200] = 255
        self.assertEqual(ram[0x0200], u16(0))

    def test_get_io(self):
        pass
    def test_set_io(self):
        pass

class ROM_TESTS(unittest.TestCase):
    pass

class REGS_TESTS(unittest.TestCase):
    pass

class POTADOS_TESTS(unittest.TestCase):
    def test_mov(self):
        potados = POTADOS_EMULATOR()

        potados.load_imm(u16(1), 1)

        self.assertEqual(potados.regs[1], u16(1))

        potados.load_imm(u16(1), 0)

        self.assertEqual(potados.regs[0], u16(0))
        
    def jump_test(self): 
        potados = POTADOS_EMULATOR()

        potados.jump(u16(2))

        self.assertEqual(potados.regs[potados.PC], u16(2))

        potados.next_tick()

        self.assertEqual(potados.regs[potados.PC], u16(3))
        
    def call_test(self):
        potados = POTADOS_EMULATOR()

        potados.regs[potados.SP] = 0x0100

        potados.jump(u16(1))

        potados.call(u16(32))

        self.assertEqual(potados.regs[potados.SP], u16(1))
        self.assertEqual(potados.regs[potados.PC], u16(32))
        self.assertEqual(potados.ram[0x0100], u16(1))
    def jumps_test(self):
        potados = POTADOS_EMULATOR()

        potados.regs[1] = u16(1)
        potados.regs[2] = u16(3)
        potados.regs[potados.PC] = u16(10)

        potados.jge(1, 2, u16(10))
        self.assertEqual(potados.regs[potados.PC], 20)
        self.assertEqual(operator.regs[potados.FL], u16('01010'))
        
        potados.jge(2, 1, u16(10))
        self.assertEqual(potados.regs[potados.PC], 20)
        self.assertEqual(operator.regs[potados.FL], u16('10100'))

        potados.regs[3] = u16(-1)
        potados.regs[4] = u16(1)

        potados.jge(3, 4, i16(-10))
        self.assertEqual(potados.regs[potados.PC], 10)
        self.assertEqual(operator.regs[potados.FL], u16('01010'))

        potados.jl(3, 4, u16(10))
        self.assertEqual(potados.regs[potados.PC], 10)
        
        potados.je(3, 3, u16(10))
        self.assertEqual(potados.regs[potados.PC], 20)
        self.assertEqual(operator.regs[potados.FL], u16('01101'))

        # -1 casted to unsigned (all ones) >= 1 casted to unsigned 
        potados.jae(3, 4)
        self.assertEqual(potados.regs[potados.PC], 30)


if __name__ == "__main__":
    unittest.main()
    