from typing import Any, List, Optional, Union
from pybytes import Binary, ops
import core.config as config
import core.error as error
import core.emulate as emulate
import numpy as np

class PM1_EMULATOR(emulate.EmulatorBase):
    def __init__(self):
        self.RAM = np.zeros(shape=(256,), dtype=np.uint8)
        self.Regs = np.zeros(shape=(4,), dtype=np.uint8)
        self.ROM_COUNTER = 0
        self.ROMStack = []
        self.is_running_flag = True
        self.cycles = 0

    def get_current_pos(self, chunk_name) -> int:
        return self.ROM_COUNTER
    
    def inc_counter(self, value=1):
        self.cycles += 1
        self.ROM_COUNTER = (self.ROM_COUNTER+value)%255
    
    def get_machine_cycles(self) -> int:
        return self.cycles

    def next_tick(self,) -> Optional[str]:
        self.cycles = 0
        self.parse_command()

    def write_memory(self, chunk_name: str, type: emulate.DataTypes, data: dict):
        for adress, value in data.items():
            self.RAM[adress] = value
    
    def exec_command(self, chunk_name: str, method_name: str, args: List) -> Any:
        method = self.__getattribute__(method_name)
        return method(*args)

    def is_running(self) -> bool:
        return self.is_running_flag
    

    def parse_command(self):
        low = Binary(int(self.RAM[self.ROM_COUNTER]), bit_lenght=8)
        cu = int(low[4:])
        r1 = int(low[:2])
        r2 = int(low[2:4])

        if cu == 0:
            r1r2 = int(low[:4])
            if r1r2 == 0:
                print("Shuting with error")
                self.is_running_flag = False
            elif r1r2 == 1:
                self.is_running_flag = False
            elif r1r2 == 2:
                self.inc_counter()
                n1 = int(self.RAM[self.ROM_COUNTER])
                self.jump(n1)
                return
            elif r1r2 == 3:
                self.inc_counter()
                n1 = int(self.RAM[self.ROM_COUNTER])
                self.jump_flag(n1)
                return
            elif r1r2 == 4:
                self.interutp(None, None)
            elif r1r2 == 5:
                self.clear_screen()
            else:
                raise error.EmulationError("Command is not implemented")

        elif cu == 1:
            if r2 == 0:
                self.inc_counter()
                n1 = int(self.RAM[self.ROM_COUNTER])
                self.mov_const_reg(n1, r1)
            elif r2 == 1:
                self.alu_reg_inc(r1)
            elif r2 == 2:
                self.alu_reg_dec(r1)
            elif r2 == 3:
                raise
        elif cu == 2:
            self.mov_reg_reg(r2, r1)
        elif cu == 3:
            self.alu_reg_reg_add(r2, r1)
        elif cu == 4:
            self.alu_reg_reg_sub(r2, r1)
        elif cu == 5:
            self.alu_reg_reg_rsh(r2, r1)
        elif cu == 6:
            self.alu_reg_reg_lsh(r2, r1)
        elif cu == 7:
            self.alu_reg_reg_and(r2, r1)
        elif cu == 8:
            self.alu_reg_reg_or(r2, r1)
        elif cu == 9:
            self.alu_reg_reg_xor(r2, r1)
        elif cu == 10:                 #JUMP EQUAL
            zf, _ = self.alu_reg_reg_cmp(r2, r1)
            if zf == True:
                self.inc_counter()
                n1 = self.RAM[self.ROM_COUNTER]
                self.jump(n1)
                return
            else:
                self.inc_counter()
        elif cu == 11:                #JUMP GREATER
            zf, of = self.alu_reg_reg_cmp(r2, r1)
            if zf == False and of == True:
                self.inc_counter()
                n1 = self.RAM[self.ROM_COUNTER]
                self.jump(n1)
                return
            else:
                self.inc_counter()
        elif cu == 12:
            self.read_reg_pointer(r2, r1)
        elif cu == 13:
            self.inc_counter()
            n1 = self.RAM[self.ROM_COUNTER]
            self.read_ram_reg(n1, r1)
        elif cu == 14:
            self.write_pointer_reg(r1, r2)
        elif cu == 15:
            self.inc_counter()
            n1 = self.RAM[self.ROM_COUNTER]
            self.write_const_reg(r1, n1)
        else:
            raise error.EmulationError("Unreachable")
        
        self.inc_counter()
    
    @emulate.log_disassembly(format='mov reg[{_from}], reg[{_to}]')
    def mov_reg_reg(self, _from, _to):
        self.Regs[_to] = self.Regs[_from]

    @emulate.log_disassembly(format='mov {_value}, reg[{_to}]')
    def mov_const_reg(self, _value, _to):
        self.Regs[_to] = _value

    @emulate.log_disassembly(format='mov reg[{_from}], ram[reg[{_to_pointer}]]')
    def write_pointer_reg(self, _from, _to_pointer):
        _value = self.Regs[_from]
        _adress = self.Regs[_to_pointer]
        
        self.RAM[_adress] =  _value

    @emulate.log_disassembly(format='mov reg[{_from}], ram[{_adress}]')
    def write_const_reg(self, _from, _adress):
        _value = self.Regs[_from]
        self.RAM[_adress] =  _value

    @emulate.log_disassembly(format='mov ram[reg[{_from}]], reg[{_to}]')
    def read_reg_pointer(self, _from, _to):
        _adress = self.Regs[_from]
        self.Regs[_to] = self.RAM[_adress]   

    @emulate.log_disassembly(format='mov ram[{_adress}], reg[{_to}]')
    def read_ram_reg(self, _adress, _to):
        self.Regs[_to] = self.RAM[_adress]
    
    @emulate.log_disassembly(format='mov reg[{_from}], ram[{_adress}]')
    def write_reg_ram(self, _from, _adress):
        _value = self.Regs[_from]
        self.RAM[_adress] =  _value

    #ALU OPERATIONS
    @emulate.log_disassembly(format='or reg[{_from_a}], reg[{_from_b}]')
    def alu_reg_reg_or(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value | self.Regs[_from_a]

        self.Regs[_from_b] = _value

    @emulate.log_disassembly(format='and reg[{_from_a}], reg[{_from_b}]')
    def alu_reg_reg_and(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value & self.Regs[_from_a]

        self.Regs[_from_b] = _value

    @emulate.log_disassembly(format='xor reg[{_from_a}], reg[{_from_b}]')
    def alu_reg_reg_xor(self, _from_a, _from_b):
        _value = self.Regs[_from_b]
        _value = _value ^ self.Regs[_from_a]

        self.Regs[_from_b] = _value

    @emulate.log_disassembly(format='rsh reg[{_from_a}], reg[{_to_b}]')
    def alu_reg_reg_rsh(self, _from_a, _to_b):
        _value = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned') 
        _value, of = ops.underflowing_rsh(_value, 1)  #TODO

        self.Regs[_to_b] = _value

    @emulate.log_disassembly(format='lsh reg[{_from_a}], reg[{_to_b}]')
    def alu_reg_reg_lsh(self, _from_a, _to_b):
        _value = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned') 
        _value, of = ops.overflowing_lsh(_value, 1)  #TODO
        
        self.Regs[_to_b] = int(_value)

    @emulate.log_disassembly(format='add reg[{_from_a}], reg[{_from_b}]')
    def alu_reg_reg_add(self, _from_a, _from_b):
        _value_a = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned') 
        _value_b = Binary(int(self.Regs[_from_b]), bit_lenght=8, sign_behavior='unsigned') 
        
        _value, of = ops.overflowing_add(_value_a, _value_b)

        self.Regs[_from_b] = int(_value)

    @emulate.log_disassembly(format='inc reg[{_from_a}]')
    def alu_reg_inc(self, _from_a):
        _value = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned') 

        _value, of = ops.overflowing_add(_value, 1)

        self.Regs[_from_a] = _value

    @emulate.log_disassembly(format='dec reg[{_from_a}]')
    def alu_reg_dec(self, _from_a):
        _value = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned') 

        _value, of = ops.overflowing_sub(_value, 1)

        self.Regs[_from_a] = _value

    @emulate.log_disassembly(format='sub reg[{_from_a}], reg[{_from_b}]')
    def alu_reg_reg_sub(self, _from_a, _from_b):
        _value_a = Binary(int(self.Regs[_from_b]), bit_lenght=8, sign_behavior='unsigned')
        _value_b = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned')
        _value, of = ops.overflowing_sub(_value_a, _value_b)

        self.Regs[_from_b] = _value
    
    @emulate.log_disassembly(format='cmp reg[{_from_a}], reg[{_from_b}]')
    def alu_reg_reg_cmp(self, _from_a, _from_b):
        _value_a = Binary(int(self.Regs[_from_b]), bit_lenght=8, sign_behavior='unsigned')
        _value_b = Binary(int(self.Regs[_from_a]), bit_lenght=8, sign_behavior='unsigned')
        _value, of = ops.overflowing_sub(_value_b, _value_a)
        zf = int(_value) == 0
        return zf, of

    #JUMPS
    @emulate.log_disassembly(format='jump {_target_true}')
    def jump(self, _target_true):
        self.ROM_COUNTER = _target_true

    @emulate.log_disassembly(format='call {_target_true}')
    def call(self, _target_true):
        if len(self.ROMStack) < 15:
            self.ROMStack.append(self.ROM_COUNTER)
        else:
            raise error.EmulationError("rom stack overflow")
        self.jump(_target_true)

    @emulate.log_disassembly(format='shut')
    def shut(self):
        pass
    
    def jump_rednet(self, _target_true):
        pass

    @emulate.log_disassembly(format='jf {_target_true}')
    def jump_flag(self, _target_true):
        FLAG = self.RAM[233]
        if FLAG & 128 != 0:
            self.jump(_target_true)
        elif FLAG & 64 != 0:
            pass

    @emulate.log_disassembly(format='ret')
    def ret(self):
        if len(self.ROMStack) == 0:
            raise error.EmulationError("ROM")
        addres = self.ROMStack.pop()
        self.jump(addres)
    
    @emulate.log_disassembly(format='int {_value_a}')
    def interutp(self, _value_a, mode):
        pass

    @emulate.log_disassembly(format='cls')
    def clear_screen(self):
        pass
    
    def show_ascii(self):
        vals = self.RAM[0xF0:0xFF]
        vals = [chr(x if x > 32 and x < 127 else 0) for x in vals]
        print('ASCII: ', ''.join(vals))

    def get_keyboard(self):
        keyboard_input = input("Czekam na interakcje... ")
        if keyboard_input == 'enter':
            keyboard_input = '\n'
        if len(keyboard_input) == 0:
            return
        self.RAM[0xE0] = ord(keyboard_input[0])

    def insert_keyboard(self, val):
        keyboard_input = val
        if keyboard_input == 'enter':
            keyboard_input = '\n'
        if len(keyboard_input) == 0:
            return
        self.RAM[0xE0] = ord(keyboard_input[0])

    def get_ram_ref(self):
        return self.RAM

    def get_regs_ref(self):
        return self.Regs

def get_emulator() -> PM1_EMULATOR:
    return PM1_EMULATOR()