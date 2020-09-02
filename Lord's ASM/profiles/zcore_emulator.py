import core.error as error
import numpy as np
import core.loading as error
import core.interpreter_synax_solver as iss
import time

np.warnings.filterwarnings('ignore')

REG_COUNT = 8
WORD_SIZE = 8
WORD_MAX = int(2**WORD_SIZE)


class Core:
    def __init__(self, ID, RAM):
        #TODO
        #numpy representation
        self.ID = ID
        self.Regs = np.zeros(shape=(REG_COUNT), dtype=np.uint8)                                 #rejestry                           #bufor rejestrów
        self.Stack = []                                                  #Stos rdzenia
        self.ROMStack = []                                               #Stos romu
        self.ALU_FLAGS = {"overflow":False,"sign":False,"zero":False,"partity":False}
        self.ROM_COUNTER = 0
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
    def write_const_pointer(self, _value, _to_pointer):
        _adress = self.Regs[_to_pointer]

        self.RAM_UPDATE_REQUEST = [_adress, _value] 
    def read_ram_reg(self, _adress, _to):
        self.Regs[_to] = self.RAM_REFRENCE[_adress]
    def write_reg_ram(self, _from, _adress):
        _value = self.Regs[_from]
        self.RAM_UPDATE_REQUEST = [_adress, _value]
    def write_const_ram(self, _value, _adress):
        self.RAM_UPDATE_REQUEST = [_adress, _value]
    #ALU OPERATIONS
    def alu_const_reg_or(self, _value, _from_b, _to):
        _value = _value | self.Regs[_from_b]
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_or(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_or(_value, _from_b, _to)
    def alu_const_reg_and(self, _value, _from_b, _to):
        _value = _value & self.Regs[_from_b]
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_and(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_and(_value, _from_b, _to)
    def alu_const_reg_xor(self, _value, _from_b, _to):
        _value = _value ^ self.Regs[_from_b]
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_xor(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_xor(_value, _from_b, _to)
    def alu_const_reg_rsh(self, _value, _from_b, _to):
        _value = _value*2
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_rsh(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_rsh(_value, _from_b, _to)
    def alu_const_reg_lsh(self, _value, _from_b, _to):
        if _value | 1 != 0:
            self.ALU_FLAGS["overflow"] = True
        _value = _value//2
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_lsh(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_lsh(_value, _from_b, _to)
    def alu_const_reg_add(self, _value, _from_b, _to):
        _value = _value + self.Regs[_from_b]
        if _value > 255:
            self.ALU_FLAGS["overflow"] = True
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_add(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_add(_value, _from_b, _to)
    def alu_const_reg_sub(self, _value_a, _from_b, _to):
        _value_b = self.Regs[_from_b]
        _value = _value_a-_value_b
        if _value < 0:
            _value = bin(-_value)[2:].replace("0","_").replace("1","0").replace("_","1")
            _value = "1"*(8-len(_value))+_value
            _value = int(_value,2)+1

        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_sub(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_sub(_value, _from_b, _to)
    def alu_const_reg_rsub(self, _value_a, _from_b, _to):
        _value_b = self.Regs[_from_b]
        _value = _value_b-_value_a
        if _value < 0:
            _value = bin(-_value)[2:].replace("0","_").replace("1","0").replace("_","1")
            _value = "1"*(8-len(_value))+_value
            _value = int(_value,2)+1

        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value
    def alu_reg_reg_rsub(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_sub(_value, _from_b, _to)
    def alu_const_reg_inc(self, _value, _from_b, _to):
        self.alu_const_reg_add(1, _value|_from_b, _to)
    def alu_reg_reg_inc(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_inc(_value, _from_b, _to)
    def alu_const_reg_dec(self, _value, _from_b, _to):
        self.alu_const_reg_rsub(1, _value|_from_b, _to)    
    def alu_reg_reg_dec(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_dec(_value, _from_b, _to)
    def alu_const_reg_just(self, _value, _from_b, _to):
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = (self.Regs[_from_b]|_value)      
    def alu_reg_reg_just(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_just(_value, _from_b, _to) 
    def alu_const_reg_not(self, _value, _from_b, _to):
        _value = bin(_value)[2:].replace("0","_").replace("1","0").replace("_","1")
        _value = int("1"*(8-len(_value))+_value,base=2)
        self.set_partiti_zero_flag(_value)
        self.Regs[_to] = _value     
    def alu_reg_reg_not(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_b]
        self.alu_const_reg_not(_value, 0, _to)
    def alu_const_reg_max(self, _value_a, _from_b, _to):
        _value_b = self.Regs[_from_b]
        if _value_a > _value_b:
            self.set_partiti_zero_flag(_value_a)
            self.Regs[_to] = _value_a
        else:
            self.set_partiti_zero_flag(_value_b)
            self.Regs[_to] = _value_b
    def alu_reg_reg_max(self, _from_a, _from_b, _to):
        _value = self.Regs[_from_a]
        self.alu_const_reg_max(_value, _from_b, _to)
    #JUMPS
    def jump(self, _target_true, _target_false):
        self.ROM_COUNTER = _target_true
    def call(self, _target_true, _target_false):
        if len(self.ROMStack) < 15:
            self.ROMStack.append(self.ROM_COUNTER)
        else:
            raise error.StackOverFlowError("ROM")
        self.jump(_target_true, 0)  

    def jump_equal_const_reg(self, _value_a, _from_b, _target_true, _target_false):
        if _value_a == self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_equal_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        self.jump_equal_const_reg(_value, _from_b, _target_true, _target_false) 
    
    def jump_not_equal_const_reg(self, _value_a, _from_b, _target_true, _target_false):
        if _value_a != self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    
        _value = self.Regs[_from_a]
        jump_equal_const_reg(_value, _from_b, _target_true, _target_false)
    def jump_not_equal_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        self.jump_not_equal_const_reg(_value, _from_b, _target_true, _target_false)
   
    def jump_less_const_reg(self, _value_a, _from_b, _target_true, _target_false):
        if _value_a < self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_less_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        self.jump_less_const_reg(_value, _from_b, _target_true, _target_false)
    
    def jump_greater_const_reg(self, _value_a, _from_b, _target_true, _target_false):
        if _value_a > self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_greater_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        self.jump_greater_const_reg(_value, _from_b, _target_true, _target_false)  
    
    def jump_greater_eq_const_reg(self, _value_a, _from_b, _target_true, _target_false):
        if _value_a >= self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_greater_eq_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        self.jump_greater_eq_const_reg(_value, _from_b, _target_true, _target_false)   
    
    def jump_less_eq_const_reg(self, _value_a, _from_b, _target_true, _target_false):
        if _value_a <= self.Regs[_from_b]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_less_eq_reg_reg(self, _from_a, _from_b, _target_true, _target_false):
        _value = self.Regs[_from_a]
        self.jump_less_eq_const_reg(_value, _from_b, _target_true, _target_false) 
    
    def jump_overflow_const_reg(self, _target_true, _target_false):
        if self.ALU_FLAGS["overflow"]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0) 
    def jump_sign_const_reg(self, _target_true, _target_false):
        if self.ALU_FLAGS["sign"]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_zero_const_reg(self, _target_true, _target_false):
        if self.ALU_FLAGS["zero"]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    def jump_partity_const_reg(self, _target_true, _target_false):
        if self.ALU_FLAGS["partity"]:
            self.jump(_target_true, 0)
        else:
            self.jump(_target_false, 0)
    
    def ret(self):
        if len(self.ROMStack) == 0:
            raise error.StackUnderFlowError("ROM")
        addres = self.ROMStack.pop()
        self.jump(addres, 0) 
    def interutp(self, _value_a, mode):
        if mode == 1:
            iss.G_INFO_CONTAINER["stop"] = True
        elif mode == 2:
            raise error.CurrentlyUnsupported("interupts")
        elif mode == 3:
            raise error.CurrentlyUnsupported("interupts")
            input()
        elif mode == 4:
            raise error.CurrentlyUnsupported("interupts")
            iss.G_INFO_CONTAINER["stop"] = True
        elif mode == 5:
            raise error.CurrentlyUnsupported("Cores syncs")
        elif mode == 6:
            raise error.CurrentlyUnsupported("Cores syncs")
        elif mode == 7:
            raise error.CurrentlyUnsupported("Cores syncs")
        elif mode == 8:
            raise error.CurrentlyUnsupported("Cores syncs")
        elif mode == 9:
            raise error.CurrentlyUnsupported("Cores syncs")
        else:
            raise error.UndefinedCommand("Interupt {} doesn't exist. ".format(mode))
    def push_const(self, _value_a):
        if len(self.Stack) < 15:
            self.Stack.append(_value_a)
        else:
            raise error.StackOverFlowError("CPU")
    def push_reg(self, _from_a):
        _value = self.Regs[_from_a]
        self.push_const(_value)
        
    def pop(self, _to):
        if len(self.ROMStack) == 0:
            raise error.StackUnderFlowError("CPU")
        value = self.Stack.pop()
        self.Regs[_to] = value
    def rom_stack_size(self, _to):
        self.Regs[_to] = len(self.ROMStack)
    def cpu_stack_size(self, _to):
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
        self.CORES = [Core(ID, self.RAM) for ID in range(2)]

    def end_cpu_tick(self):
        for core in self.CORES:
            cell, value = core.RAM_UPDATE_REQUEST
            if cell != -1:
                self.RAM[cell] = value


    def end_tick(self, core_id: int):
        self.CORES[core_id].Regs[0] = 0 
        self.CORES[core_id].ROM_COUNTER += 1
        self.CORES[core_id].reset_flags() #CPU characteristic, flag jumps only in same tick

    def get_rom_adress(self, core: int):
        return self.CORES[core].get_rom_adress()
