import core.config as config
from core.context import Context
import core.error as error
import core.emulate.debug_commands as debug
from core.profile.profile import AdressingMode, Profile
import inspect
import abc
import typing
import time
import enum
import pprint

from pybytes import Binary
from core.quick import gather_instructions, pack_adresses

from core.save.formatter import as_values

class DataTypes(enum.Enum):
    PROGRAM = 1,
    DATA = 2,

class EmulatorBase(abc.ABC):
    """
    # Overview
    Base class for CPU emulators with Python frontend.
    This class is disigned to support multiple threads/cores/devices so this class should
    represent whole machine. 
    chunk_name is an parameter that can be any of the KEYWORDS defined in model (or None if emulator doens't care)
    
    # Emulation Cycle
    Typical Emulation cycle looks like this
    
    ```
    machine: EmulatorBase = emulator.get_emulator() # Taking instance of an emulator
    machine.write_memory(..., DataTypes.PROGRAM, ...) # Loads program
    machine.write_memory(..., DataTypes.DATA, ...) # Loads data
    
    while machine.is_running():
        machine.get_current_pos(...)

        pre_debug(machine) # May call `exec_command`

        machine.next_tick()

        post_debug(machine) # May call `exec_command`

        machine.get_machine_cycles()

    ```
    """
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def get_current_pos(self, chunk_name: typing.Optional[str]) -> int:
        """
        Function should return `integer value` of current program counter adress for given `chunk_name`
        """

    @abc.abstractmethod
    def is_running(self) -> bool:
        """
        Function should return `True` if machine is still running
        """

    @abc.abstractmethod
    def get_machine_cycles(self,) -> int:
        """
        Function should return how many cycles was taken from last `next_tick` call. It is used for estimating runtime
        """

    @abc.abstractmethod
    def next_tick(self,) -> typing.Optional[str]:
        """
        Should evaluate next instruction/set of instructions. Beetwen calls of this function emulator will perform debug operations
        """

    @abc.abstractmethod
    def write_memory(self, chunk_name: typing.Optional[str], type: DataTypes, data: dict):
        """
        For givern `chunk_name`, `datatype` and `data`, function should initliaze machine memory with given values.
        * `chunk_name` is target core/thread/device.
        * `type` is type of the data possible values are:
           * PROGRAM (1) - Program binary
           * DATA (2) - Custom, external data included for debugging and emulating
        * `data` is an dict that consains adresses and coresponding values. You can copy and rearange this data any way you want. (Ss long as it will work fine.) 
        """

    @abc.abstractmethod
    def exec_command(self, chunk_name: typing.Optional[str], method_name: str, args: typing.List) -> typing.Any:
        """
        Function should call an arbitrary named function defined in emulator with given `arguments` and `chunk_name`
        Example implementation
        ```
        method = self.__getattribute__(method_name) # Ignoring chunk_name in this case.
        return method(*args)
        ```
        It is used for debugging pupruses if Debugger wants to know internal state of CPU like registers ect
        Debugger will expect definition for functions:
        * `get_ram_ref` -> returns reference to ram
        * `get_regs_ref` -> returns reference to regs
        """
        method = self.__getattribute__(method_name)
        return method(*args)

GLOBAL_CURR_ADRESS = 0
GLOBAL_CMD_HISTORY = list()

def log_disassembly(**kwargs):
    """
    Decorator that displays an message if function was called.
    Useful for logging disassembly. This decorator could be turned off with:
    * `config.use_disassembly_as_logs` equal `False`
    * `config.logmode` equal False
    It can take an 'format' as argument that can display custom message that includes parametres.
    
    ## Example

    ```
    # If write_const_reg(1,2) was called will display "mov reg[1], ram[2]"
    @log_disassembly(format='mov reg[{_from}], ram[{_adress}]')
    def write_const_reg(self, _from, _adress):
        pass
    ```
    """
    global GLOBAL_CURR_ADRESS

    def params_ignore(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    def format_value(value):
        if isinstance(value, Binary):
            return value.hex(prefix=True)
        return value

    def params_log_dissasembly(func):
            global GLOBAL_CURR_ADRESS
            format = str(kwargs['format']) if 'format' in kwargs else func.__name__ 
            spec = inspect.getfullargspec(func).args

            def wrapper(*args, **kwargs):
                global GLOBAL_CURR_ADRESS
                formated = format.format_map({name: format_value(value) for name, value in zip(spec, args)})
                print(GLOBAL_CURR_ADRESS, formated)
                if config.log_history:
                    GLOBAL_CMD_HISTORY.append(func.__name__)
                return func(*args, **kwargs)
            return wrapper
    if config.use_disassembly_as_logs and config.logmode:
        return params_log_dissasembly
    else:
        return params_ignore



def __execute_debug_command(command: list, machine: EmulatorBase, profile: Profile):
    if config.disable_debug:
        return
        
    if len(command) == 1:
        command_str: str = command[0]
        if command_str.lower() == 'break':
            debug.breakpoint()
        elif command_str.lower() == 'ram':
            ram = machine.exec_command(None, 'get_ram_ref', [])
            debug.ram_display(ram, profile.adressing.bin_len, 0, None)
        elif command_str.lower() == 'regs':
            regs = machine.exec_command(None, 'get_regs_ref', [])
            print('regs ----------------')
            for i, reg in enumerate(regs):
                if isinstance(reg, Binary):
                    print(i, '\t', reg.bin(), reg.hex(), reg.int())
                elif isinstance(reg, int):
                    print(i, '\t', bin(reg), hex(reg), reg)
                else:
                    print(i, '\t', reg)
            print('---- ----------------')
    elif command[0] == 'log':
        pos = machine.get_current_pos(None)
        debug.log(f"{pos}  {' '.join(command[1:])}")
    elif '(' in command and ')' in command:
        cmd: str = command[0]
        start = command.index('(')
        end = command.index(')')
        if start != 1:
            raise error.EmulationError(f"Bad debug cmd: {command}")
        args = [token for token in command[(start+1):end] if token != ',']

        if cmd.startswith("ram") and len(args) == 2:
            min_adress, max_adress = int(args[0]), int(args[1])
            ram = machine.exec_command(None, 'get_ram_ref', [])
            debug.ram_display(ram, profile.adressing.bin_len, min_adress, max_adress)
        else:
            machine.exec_command(None, cmd, args)

def telemetry_display(program, context: Context):
    print(f"Displaing collected telemetry data... ({len(GLOBAL_CMD_HISTORY)} points) You can turn this annying thing with log_history set to False in settings (default.ini file)")
    import matplotlib.pyplot as plt
    import pandas
    from collections import Counter
    from sklearn.preprocessing import OneHotEncoder
    from scipy.interpolate import interp1d
    import numpy as np

    df = pandas.DataFrame(GLOBAL_CMD_HISTORY, columns=['history'])
    hist = pandas.DataFrame.from_dict(Counter(GLOBAL_CMD_HISTORY), orient='index')
    
    encoder = OneHotEncoder(handle_unknown='ignore')
    
    encoder_df = pandas.DataFrame(encoder.fit_transform(df[['history']]).toarray(), columns=encoder.categories_)

    rolling = encoder_df.rolling(int(config.telemetry_window_size), min_periods=1).mean().interpolate(method='cubic', limit_direction='both')
    rollinginterp = interp1d(rolling.index, rolling.T, kind='cubic')

    hist.plot(kind='bar')
    plt.xticks(rotation=45)
    plt.ylabel("Count")
    plt.xlabel("Ops")
    plt.title("Command Usage Histogram")
    plt.show()

    if config.telemetry_interpolate:
        freqs = rollinginterp(np.linspace(0, len(rolling.index)-1, int(config.telemetry_interpolate_points))).T
    else:
        freqs = rolling

    plt.plot(freqs, label=rolling.columns)
    plt.legend()
    plt.show()

def emulate(program, context: Context):
    global GLOBAL_CURR_ADRESS

    profile: Profile = context.get_profile()
    get_emulator = profile.emul

    if isinstance(get_emulator, dict):
        raise error.EmulationError(f"Emulator is callable that returns EmulatorBase class: {get_emulator}")

    machine = get_emulator()

    if machine is None or not isinstance(machine, EmulatorBase):
        raise error.EmulationError(f"Function get_emulator returned invalid instance of machine expected: 'EmulatorBase', got '{machine}'")
    
    print()
    print("Writing data to device")

    debug_instructions = __write_program(program, context, machine)
    __write_data(program, context, machine)


    print("Starting Emulation")
    
    emulate_start_time = time.thread_time_ns()
    emulation_cycles = 1
    machine_cycles = 0

    while machine.is_running():
        pos = machine.get_current_pos(None)
        GLOBAL_CURR_ADRESS = pos
        
        if pos in debug_instructions:
            for instruction in (i for i in debug_instructions[pos] if 'pre' in i): 
                __execute_debug_command(instruction['pre'], machine, profile)

        machine.next_tick()
        
        if pos in debug_instructions:
            for instruction in (i for i in debug_instructions[pos] if 'post' in i): 
                __execute_debug_command(instruction['post'], machine, profile)
        
        emulation_cycles += 1
        machine_cycles += machine.get_machine_cycles()
    emulate_end_time = time.thread_time_ns()
    
    print("Emulation finished")
    print(f"Took: {(emulate_end_time-emulate_start_time)/1000000.0}ms")
    try:
        print(f"Per command: {(emulate_end_time-emulate_start_time)/emulation_cycles/1000.0:0.2f}μs")
    except:
        print(f"Per command: {(emulate_end_time-emulate_start_time)/emulation_cycles/1000.0:0.2f}us")
    print(f"Machine took: {machine_cycles} steps, estimated execution time: {machine_cycles/float(profile.info.speed):0.1f}s")
    
    if config.log_history:
        telemetry_display(program, context)

def __write_program(program, context: Context, machine: EmulatorBase):
    debug_instructions = dict()
    adressing: AdressingMode = context.get_profile().adressing

    instructuons, debug = gather_instructions(program, adressing)
    packed_instructions = pack_adresses(instructuons)

    machine.write_memory('default', DataTypes.PROGRAM, packed_instructions)

    for adress, val in debug.items():
        debug_instructions[adress] = val
    
    return debug_instructions

def __write_data(program, context: Context, machine: EmulatorBase):
    data: dict = context.data

    machine.write_memory(None, DataTypes.DATA, data)