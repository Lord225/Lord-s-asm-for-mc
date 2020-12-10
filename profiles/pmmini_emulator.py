import core.error as error
import core.loading as loading
import core.interpreter_synax_solver as iss
import numpy as np
import time

np.warnings.filterwarnings('ignore')

REG_COUNT = 4
WORD_SIZE = 8
WORD_MAX = int(2**WORD_SIZE)

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

    def set_partiti_zero_flag(self, _value):
        self.ALU_FLAGS["partity"] = _value&1 == 0
        self.ALU_FLAGS["zero"] = _value == 0
    def mov_reg_reg(self, _from, _to):
        self.Regs[_to] = self.Regs[_from]
    def mov_const_reg(self, _value, _to):
        self.Regs[_to] = _value
    def write_pointer_reg(self, _from, _to_pointer):
        _value = self.Regs[_from]
        _adress = self.Regs[_to_pointer]
        
        self.RAM_UPDATE_REQUEST = [_adress, _value]
    def read_reg_pointer(self, _from, _to):
        _adress = self.Regs[_from]
        self.Regs[_to] = self.RAM_REFRENCE[_adress]    
    def read_ram_reg(self, _adress, _to):
        self.Regs[_to] = self.RAM_REFRENCE[_adress]
    def write_reg_ram(self, _from, _adress):
        _value = self.Regs[_from]
        self.RAM_UPDATE_REQUEST = [_adress, _value]

    #ALU OPERATIONS
    def alu_reg_reg_or(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value | self.Regs[_from_a]
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    def alu_reg_reg_and(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value & self.Regs[_from_a]
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    def alu_reg_reg_xor(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value ^ self.Regs[_from_a]
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value   
    def alu_reg_reg_rsh(self, _from_a, _from_b):
        _value = self.Regs[_from_a]
        if _value | 1 != 0:
            self.ALU_FLAGS["overflow"] = True
        _value = _value//2
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    def alu_reg_reg_lsh(self, _from_a, _from_b):
        _value = self.Regs[_from_a]
        _value = _value + self.Regs[_from_b]
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    def alu_reg_reg_add(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value + self.Regs[_from_a]
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_from_b] = _value
    def alu_reg_reg_sub(self, _from_a, _from_b):
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
    def jump(self, _target_true, _target_false):
        self.ROM_COUNTER = _target_true
    def call(self, _target_true, _target_false):
        if len(self.ROMStack) < 15:
            self.ROMStack.append(self.ROM_COUNTER)
        else:
            raise error.StackOverFlowError("ROM")
        self.jump(_target_true, 0)
    
    def shut(self, ):
        pass

    def jump_equal_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        if _value == self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_greater_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        if _value > self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    
    def jump_overflow_const_reg(self, _target_true, _target_false):
        if self.ALU_FLAGS["overflow"]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_zero_const_reg(self, _target_true, _target_false):
        if self.ALU_FLAGS["zero"]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def ret(self):
        if len(self.ROMStack) == 0:
            raise error.StackUnderFlowError("ROM")
        addres = self.ROMStack.pop()
        self.jump(addres, 0)      
    def interutp(self, _value_a, mode):
        pass
    
        _value = _value_a
        self.push_const(_value)        
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
    
class CPU:
    def __init__(self):
        self.RAM = np.zeros((256), dtype=np.uint8)
        self.CORES = [Core(0, self.RAM)]

    def end_cpu_tick(self):
        for core in self.CORES:
            cell, value = core.RAM_UPDATE_REQUEST
            if cell != -1:
                self.RAM[cell] = value

    def end_tick(self, core_id: int):
        self.CORES[core_id].ROM_COUNTER += 1

    def get_rom_adress(self, core: int):
        return self.CORES[core].get_rom_adress()
