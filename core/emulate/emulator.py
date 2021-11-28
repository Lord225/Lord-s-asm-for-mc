from glob import glob
import core.config as config
import core.error as error
import core.emulate.debug_commands as debug
from core.profile.profile import Profile
import inspect
import abc
import typing
import time
import enum

class DataTypes(enum.Enum):
    PROGRAM = 1,
    DATA = 2,

class EmulatorBase(abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def get_current_pos(self, chunk_name: typing.Optional[str]) -> int:
        """
        Function should return current program counter value for given chunk_name
        """

    @abc.abstractmethod
    def is_running(self) -> bool:
        """
        Function should return if machine is still running
        """

    @abc.abstractmethod
    def get_machine_cycles(self) -> int:
        """
        Function should return how many cycles was taken from last `next_tick` call
        """

    @abc.abstractmethod
    def next_tick(self,) -> typing.Optional[str]:
        """
        Should evaluate next instruction
        """

    @abc.abstractmethod
    def write_memory(self, chunk_name: typing.Optional[str], type: DataTypes, data: dict):
        """
        For givern chunk_name, datatype and data, function should initliaze machine memory with given values
        """

    @abc.abstractmethod
    def exec_command(self, chunk_name: typing.Optional[str], method_name: str, args: typing.List) -> typing.Any:
        """
        Function should call an arbitrary named function defined in emulator with given arguments and chunk_name
        Example implementation
        ```
        method = self.__getattribute__(method_name) # Ignoring chunk_name in this case.
        return method(*args)
        ```
        """
        method = self.__getattribute__(method_name)
        return method(*args)

GLOBAL_CURR_ADRESS = 0

def log_disassembly(**kwargs):
    global GLOBAL_CURR_ADRESS

    def params_ignore(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper


    def params_log_dissasembly(func):
            global GLOBAL_CURR_ADRESS
            format = str(kwargs['format']) if 'format' in kwargs else func.__name__ 
            spec = inspect.getfullargspec(func).args

            def wrapper(*args, **kwargs):
                global GLOBAL_CURR_ADRESS
                formated = format.format_map({name: value for name, value in zip(spec, args)})
                print(GLOBAL_CURR_ADRESS, formated)
                return func(*args, **kwargs)
            return wrapper
    if config.use_disassembly_as_logs and config.logmode:
        return params_log_dissasembly
    else:
        return params_ignore


def gather_instructions(program, context):
    output = dict()
    debug = dict()
    for line_obj in program:
        output[line_obj.physical_adress] = line_obj.formatted
        if 'debug' in line_obj:
            debug[line_obj.physical_adress] = line_obj.debug
    return output, debug
def pack_adresses(instructions):
    output = dict()
    for adress, data in instructions.items():
        for i, cell in enumerate(data):
            if (adress+i) in output:
                raise error.EmulationError(f"Output data is overlapping: adress: {adress+i} is arleady occuped by value: {output[adress+i]}")
            output[adress+i] = cell
    return output

def execute_debug_command(command: list, machine: EmulatorBase, profile: Profile):
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
            print(regs)
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

def emulate(program, context):
    global GLOBAL_CURR_ADRESS

    profile: Profile = context["profile"]
    emulator = profile.emul

    try:
        machine: EmulatorBase = emulator.get_emulator()
    except:
        raise error.EmulationError("File with emulator definition should define the 'get_emulator' function")

    if machine is None or not isinstance(machine, EmulatorBase):
        raise error.EmulationError(f"Function get_emulator returned unvalid instance of machine expected: 'EmulatorBase', got '{machine}'")
    
    print()
    print("Writing data to device")

    write_program(program, context, machine)
    write_data(program, context, machine)

    debug_instructions = context["debug_instructions"]

    print("Starting Emulation")
    
    emulate_start_time = time.thread_time_ns()
    emulation_cycles = 0
    machine_cycles = 0

    while machine.is_running():
        pos = machine.get_current_pos(None)
        GLOBAL_CURR_ADRESS = pos
        
        if pos in debug_instructions:
            for instruction in (i for i in debug_instructions[pos] if 'pre' in i): 
                execute_debug_command(instruction['pre'], machine, profile)

        machine.next_tick()
        
        if pos in debug_instructions:
            for instruction in (i for i in debug_instructions[pos] if 'post' in i): 
                execute_debug_command(instruction['post'], machine, profile)
        
        emulation_cycles += 1
        machine_cycles += machine.get_machine_cycles()
    emulate_end_time = time.thread_time_ns()
    
    print("Emulation finished")
    print(f"Took: {(emulate_end_time-emulate_start_time)/1000000.0}ms")
    try:
        print(f"Per command: {(emulate_end_time-emulate_start_time)/emulation_cycles/1000.0:0.2f}μs")
    except:
        print(f"Per command: {(emulate_end_time-emulate_start_time)/emulation_cycles/1000.0:0.2f}us")
    print(f"Machine took: {machine_cycles} steps, estimated execution time: {machine_cycles/profile.info.speed:0.1f}s")

def write_program(program, context, machine):
    debug_instructions = dict()

    for chunk, chunked_program in program.items():
        instructuons, debug = gather_instructions(chunked_program, context)
        packed_instructions = pack_adresses(instructuons)

        machine.write_memory(chunk, DataTypes.PROGRAM, packed_instructions)

        for adress, val in debug.items():
            debug_instructions[adress] = val
    context['debug_instructions'] = debug_instructions

def write_data(program, context, machine):
    data: dict = context['data']

    machine.write_memory(None, DataTypes.DATA, data)