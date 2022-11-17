from typing import Any, List, Optional
from bitvec import Binary, arithm as ops
import core.config as config
import core.error as error
import core.emulate as emulate
import numpy as np

class EXAMPLE_EMULATOR(emulate.EmulatorBase):
    def __init__(self):
        self.RAM = np.zeros(shape=(256,), dtype=np.uint8)
        self.ROM = np.zeros(shape=(256,), dtype=np.uint16)
        self.Regs = np.zeros(shape=(4,), dtype=np.uint8)

        self.ROM_COUNTER = Binary(0, lenght=8)
        self.is_running_flag = True

        self.DEBUG_SHOW_RAM_FLOW = False

    def next_tick(self,) -> Optional[str]:
        # Execute next CPU cycle

        instruction = Binary(self.ROM[self.ROM_COUNTER], lenght=16) # You can use this module to work with binary numbers
        # 0000 00 00 00000000

        cu = instruction[12:16]
        r1 = instruction[10:12]
        r2 = instruction[8:10]
        imm = instruction[0:8]

        if cu == 0:
            pass
        elif cu == 1:
            self.mov_reg_imm(r1, imm)
        else:
            raise error.EmulationError("Unknown instruction")
        # TODO add more instructions

        self.ROM_COUNTER, of = ops.overflowing_add(self.ROM_COUNTER, 1)

        # stop emulation if ROM counter overflows
        if of:
            self.is_running_flag = False

    # Helper methods

    #
    # Instructions If function is decorated with `log_disassembly` it will be shown in disassembly when called 
    #
    @emulate.log_disassembly(format='mov reg[{arg1}], {const}')
    def mov_reg_imm(self, arg1: Binary, const: Binary):
        self.Regs[arg1.int()] = const.int()
    #
    # RAM IO
    #
    def read_ram(self, adress: int) -> Binary:
        if adress >= len(self.RAM):
            raise error.EmulationError("Out of RAM bounds")
        if self.DEBUG_SHOW_RAM_FLOW:
            print(f"RAM: {adress} -> {self.RAM[adress]}")
        return Binary(self.RAM[adress], lenght=8)
    def write_ram(self, adress: int, value: Binary):
        if adress >= len(self.RAM):
            raise error.EmulationError("Out of RAM bounds")
        if self.DEBUG_SHOW_RAM_FLOW:
            print(f"RAM: {adress} <- {value}")
        self.RAM[adress] = value.int()
    #
    # Functions can be called via #debug command so you can add some debug functions 
    # You can invoke this with #debug toggle_show_ram()
    #
    def toggle_show_ram(self):
        self.DEBUG_SHOW_RAM_FLOW = not self.DEBUG_SHOW_RAM_FLOW

    # 
    # Boilerplate for emulator. You should be mostly interested in `write_memory` and `next_tick` methods
    #
    def write_memory(self, chunk_name: str, type: emulate.DataTypes, data: dict):
        if type ==  emulate.DataTypes.DATA:
            for adress, value in data.items():
                self.RAM[adress] = value
        elif type == emulate.DataTypes.PROGRAM:
            for adress, value in data.items():
                self.ROM[adress] = value
    def get_current_pos(self, chunk_name) -> int:
        return self.ROM_COUNTER.int() # what is the current position in ROM?
    def get_machine_cycles(self) -> int:
        return 1 # how long this command took?
    def exec_command(self, chunk_name: str, method_name: str, args: List) -> Any:
        method = self.__getattribute__(method_name)
        return method(*args) # just call an instruction, used in #debug METHOD_TO_CALL(args...)
    def is_running(self) -> bool:
        return self.is_running_flag # should we stop emulation?
    def get_ram_ref(self):
        return self.RAM # return RAM reference (it will be used to show RAM in #debug it should be indexable and have `__len__` method defined, preferable numpy array)) 
    def get_regs_ref(self):
        return self.Regs # return REG reference (it should return an iterator over registers, registers can be Binary, int or any other type, preferable List[Binary])

def get_emulator() -> EXAMPLE_EMULATOR:
    return EXAMPLE_EMULATOR()