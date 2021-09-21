import core.error as error
import core.loading as loading
import core.interpreter_synax_solver as iss
import numpy as np
import time
import pybytes

from profiles.emulator_base import *

np.warnings.filterwarnings('ignore')

REG_COUNT = 4
WORD_SIZE = 8
WORD_MAX = int(2**WORD_SIZE)

RANGE_256 = Annotated[int, ValueRange(0, 255)]
RANGE_4 = Annotated[int, ValueRange(0, 3)]

class Core:

    def __init__(self, ID, RAM):
        #TODO
        #numpy representation
        self.ID = ID
        self.Regs = np.zeros(shape=(REG_COUNT), dtype=np.uint8)                                 #rejestry
        self.ALU_FLAGS = {"overflow":False,"sign":False,"zero":False,"partity":False}
        self.ROM_COUNTER = 0
        self.ROMStack = []
        self.RAM_UPDATE_REQUEST = [-1,-1]
        self.RAM_REFRENCE = RAM
        self.FPU_CONV = pybytes.floats.CustomFloat(preset='fp16')

    def nop(self):
        pass

    def set_partiti_zero_flag(self, _value):
        self.ALU_FLAGS["partity"] = _value&1 == 0
        self.ALU_FLAGS["zero"] = _value == 0

    @check_arguments
    def mov_reg_reg(self, _from: RANGE_4, _to: RANGE_4):
        self.Regs[_to] = self.Regs[_from]
    
    @check_arguments
    def mov_const_reg(self, _value: RANGE_256, _to: RANGE_4):
        self.Regs[_to] = _value
    @check_arguments
    def write_pointer_reg(self, _from: RANGE_4, _to_pointer: RANGE_4):
        _value = self.Regs[_from]
        _adress = self.Regs[_to_pointer]
        
        self.RAM_UPDATE_REQUEST = [_adress, _value]
    @check_arguments
    def read_reg_pointer(self, _from: RANGE_4, _to: RANGE_4):
        _adress = self.Regs[_from]
        self.Regs[_to] = self.RAM_REFRENCE[_adress]   
    @check_arguments 
    def read_ram_reg(self, _adress: RANGE_256, _to: RANGE_4):
        self.Regs[_to] = self.RAM_REFRENCE[_adress]
    @check_arguments
    def write_reg_ram(self, _from: RANGE_4, _adress: RANGE_256):
        _value = self.Regs[_from]
        self.RAM_UPDATE_REQUEST = [_adress, _value]

    #ALU OPERATIONS
    @check_arguments
    def alu_reg_reg_or(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_b]
        _value = _value | self.Regs[_from_a]
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    @check_arguments
    def alu_reg_reg_and(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_b]
        _value = _value & self.Regs[_from_a]
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    @check_arguments
    def alu_reg_reg_xor(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_b]
        _value = _value ^ self.Regs[_from_a]
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    @check_arguments
    def alu_reg_reg_rsh(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_a]
        if _value | 1 != 0:
            self.ALU_FLAGS["overflow"] = True
        _value = _value//2
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    @check_arguments
    def alu_reg_reg_lsh(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_a]
        _value = _value + self.Regs[_from_b]
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    @check_arguments
    def alu_reg_reg_add(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_b] + self.Regs[_from_a]
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    @check_arguments
    def alu_reg_inc(self, _from_a: RANGE_4):
        _value = self.Regs[_from_a]+1
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_a] = _value
    @check_arguments
    def alu_reg_dec(self, _from_a: RANGE_4):
        _value = self.Regs[_from_a]-1
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_a] = _value
    @check_arguments
    def alu_reg_reg_sub(self, _from_a: RANGE_4, _from_b: RANGE_4):
        _value = self.Regs[_from_b]
        _value_b = self.Regs[_from_a]
        _value = _value-_value_b
        if _value < 0:
            _value = bin(-_value)[2:].replace("0","_").replace("1","0").replace("_","1")
            _value = "1"*(8-len(_value))+_value
            _value = int(_value,2)+1

        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
        
    #JUMPS
    @check_arguments
    def jump(self, _target_true):
        self.ROM_COUNTER = _target_true
    @check_arguments
    def call(self, _target_true):
        if len(self.ROMStack) < 15:
            self.ROMStack.append(self.ROM_COUNTER)
        else:
            raise error.StackOverFlowError("ROM")
        self.jump(_target_true)
    @check_arguments
    def shut(self, ):
        pass
    @check_arguments    
    def jump_rednet(self, _target_true):
        pass
    @check_arguments 
    def jump_equal_reg_reg(self, _from_a: RANGE_4, _from_b: RANGE_4, _target_true):
        _value = self.Regs[_from_a]
        if _value == self.Regs[_from_b]:
            self.jump(_target_true)
    @check_arguments 
    def jump_greater_reg_reg(self, _from_a: RANGE_4, _from_b: RANGE_4, _target_true):
        _value = self.Regs[_from_a]
        if _value > self.Regs[_from_b]:
            self.jump(_target_true)
    @check_arguments 
    def jump_overflow_const_reg(self, _target_true):
        if self.ALU_FLAGS["overflow"]:
            self.jump(_target_true)
    @check_arguments
    def jump_zero_const_reg(self, _target_true):
        if self.ALU_FLAGS["zero"]:
            self.jump(_target_true)
    @check_arguments 
    def jump_flag(self, _target_true):
        FLAG = self.RAM[233]
        if FLAG&128 != 0:
            self.jump_overflow_const_reg(_target_true)
        elif FLAG&64 != 0:
            pass
    @check_arguments 
    def ret(self):
        if len(self.ROMStack) == 0:
            raise error.StackUnderFlowError("ROM")
        addres = self.ROMStack.pop()
        self.jump(addres)      
    @check_arguments 
    def interutp(self, _value_a: RANGE_256, mode):
        pass
    
        _value = _value_a
        self.push_const(_value)

    def fpu_load(self):
        arg_a = np.array([self.RAM_REFRENCE[229], self.RAM_REFRENCE[228]])
        arg_b = np.array([self.RAM_REFRENCE[231], self.RAM_REFRENCE[230]])
        
        a = self.FPU_CONV.get(pybytes.Binary(arg_a, bit_lenght=16))
        b = self.FPU_CONV.get(pybytes.Binary(arg_b, bit_lenght=16))
        return a, b
    def fpu_save(self, val):
        as_bytes = self.FPU_CONV.get(val)
        self.RAM_UPDATE_REQUEST = [233, int(as_bytes.low_byte())]
        self.RAM_UPDATE_REQUEST = [232, int(as_bytes.high_byte())]
    def fadd(self):
        a, b = self.fpu_load()
        out = a+b
        self.fpu_save(out)
    def fmul(self):
        a, b = self.fpu_load()
        out = a*b
        self.fpu_save(out)
    
    def clear(self):
        print("CLEARING SCREEN (REMOVE THIS LINE)")
    def rom_stack_size(self, _to):
        self.Regs[_to] = len(self.ROMStack)
        self.Regs[_to] = len(self.Stack)
    def get_rom_adress(self)->int:
        return self.ROM_COUNTER
    def reset_flags(self):
        self.ALU_FLAGS = {"overflow":False,"sign":False,"zero":False,"partity":False}
    def reset_regs(self):
        self.Regs = np.zeros(shape=(16), dtype=np.uint8)                        
    def get_regs_status(self) -> str:
        return str(self.Regs)

    def show_ascii(self,):
        vals = self.RAM_REFRENCE[0xF0:0xFF]
        vals = [chr(x if x > 32 and x < 127 else 0) for x in vals]
        print('ASCII: ', ''.join(vals))
    def debug_get_fpu_values(self):
        a, b = self.fpu_load()
        out = self.FPU_CONV.get(pybytes.Binary(np.array([self.RAM_REFRENCE[233], self.RAM_REFRENCE[232]]),  bit_lenght=16))
        print(f'a {a}, b: {b}, out: {out}')
class CPU:
    def __init__(self):
        self.RAM    = np.zeros((256), dtype=np.uint8)
        self.CORES  = [Core(0, self.RAM)]

    def end_cpu_tick(self):
        for core in self.CORES:
            cell, value = core.RAM_UPDATE_REQUEST
            if cell != -1:
                self.RAM[cell] = value

    def end_tick(self, core_id: int):
        self.CORES[core_id].ROM_COUNTER += 1

    def get_rom_adress(self, core: int):
        return self.CORES[core].get_rom_adress()
