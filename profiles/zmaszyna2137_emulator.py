import core.error as error
import core.loading as loading
import core.interpreter_synax_solver as iss
import numpy as np
import time

np.warnings.filterwarnings('ignore')

REG_COUNT = 7
WORD_SIZE = 16
WORD_MAX = int(2**WORD_SIZE)

class Core:
    def __init__(self, ID, RAM):
        #TODO
        #numpy representation
        self.ID = ID
        self.Regs = np.zeros(shape=(REG_COUNT), dtype=np.uint16)                                 #rejestry
        self.ALU_FLAGS = {"overflow":False,"sign":False,"zero":False}
        self.ROM_COUNTER = 0
        self.ROMStack = []
        self.RAM_UPDATE_REQUEST = [-1,-1]
        self.RAM_REFRENCE = RAM
    
    def stop(self):
        print("stop")
    
    def break_cmd (self, n1, dst):
        print("breaking", n1, dst)

    def load_a(self, adress):
        print("load_a",adress)
    def store_a(self, adress):
        print("load_a",adress)

    def load_b(self, adress):
        print("load_b",adress)
    def store_b(self, adress):
        print("load_b",adress)

    def load_c(self, adress):
        print("load_c",adress)
    def store_c(self, adress):
        print("load_c",adress)

    def jump(self, adress):
        print("jmp", adress)
    def jump_zero(self, adress):
        print("jump_zero", adress)
    def jump_neg(self, adress):
        print("jump_neg", adress)
    def jump_overflow(self, adress):
        print("jump_overflow", adress)
    def load_indirect(self, dst, src):
        print("load_indirect", dst, src)
    def store_indirect(self, dst, src):
        print("store_indirect", dst, src)
    def mov_reg_reg(self, dst, src):
        print("mov_reg_reg", dst, src)
    def add_reg_reg(self, dst, srca, srcb):
        print("add_reg_reg",dst, srca, srcb)

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
        self.RAM = np.zeros((2048), dtype=np.uint16)
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
