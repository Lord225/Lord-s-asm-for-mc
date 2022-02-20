import typing
from pybytes import Binary, ops
import core.config as config
import core.error as error
import core.emulate as emulate
import numpy as np
import queue


class POTADOS_EMULATOR(emulate.EmulatorBase):
    def __init__(self) -> None:
        pass

    def get_current_pos(self, chunk_name: typing.Optional[str]) -> int:
        return 0

    def is_running(self) -> bool:
        return False

    def get_machine_cycles(self,) -> int:
        return 0

    def next_tick(self,) -> typing.Optional[str]:
        return None

    def write_memory(self, chunk_name: typing.Optional[str], type: emulate.DataTypes, data: dict):
        print(data)

    def exec_command(self, chunk_name: typing.Optional[str], method_name: str, args: typing.List) -> typing.Any:
        method = self.__getattribute__(method_name)
        return method(*args)

def get_emulator() -> POTADOS_EMULATOR:
    return POTADOS_EMULATOR()