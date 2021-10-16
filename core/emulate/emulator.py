import core.config as config
import core.error as error
import core.emulate.debug_commands as debug
from core.profile.profile import Profile
import inspect
import abc
import typing
import enum

class DataTypes(enum.Enum):
    PROGRAM = 1,
    DATA = 2,

class EmulatorBase(abc.ABC):
    def __init__(self) -> None:
        super().__init__()

    @abc.abstractmethod
    def get_current_pos(self, chunk_name: str) -> int:
        pass

    @abc.abstractmethod
    def is_running(self) -> bool:
        pass

    @abc.abstractmethod
    def next_tick(self,) -> typing.Optional[str]:
        pass

    @abc.abstractmethod
    def write_memory(self, chunk_name: str, type: DataTypes, data: dict):
        pass

    @abc.abstractmethod
    def exec_command(self, chunk_name: str, method_name: str, args: typing.List) -> typing.Any:
        pass


def log_disassembly(**kwargs):
    if config.use_disassembly_as_logs:
        def params(func):
            format = str(kwargs['format']) if 'format' in kwargs else func.__name__ 
            spec = inspect.getfullargspec(func).args

            def wrapper(*args, **kwargs):
                formated = format.format_map({name: value for name, value in zip(spec, args)})
                print(formated)
                return func(*args, **kwargs)
            return wrapper
    else:
        def params(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
    return params


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
    if len(command) == 1:
        command = command[0]
        if command.lower() == 'break':
            debug.breakpoint()
        elif command.lower() == 'ram':
            ram = machine.exec_command(None, 'get_ram_ref', [])
            debug.ram_display(ram, profile.adressing.bin_len, 0, None)
        elif command.lower() == 'regs':
            regs = machine.exec_command(None, 'get_regs_ref', [])
            print(regs)
    elif command[0] == 'log':
        debug.log(f"{machine.get_current_pos()}  {' '.join(command[1:])}")
    elif '(' in command and ')' in command:
        cmd = command[0]
        start = command.index('(')
        end = command.index(')')
        if start != 1:
            raise error.EmulationError(f"Bad debug cmd: {command}")
        args = [token for token in command[(start+1):end] if token != ',']
        machine.exec_command(None, cmd, args)

def emulate(program, context):
    profile: Profile = context["profile"]
    emulator: EmulatorBase = profile.emul

    try:
        machine = emulator.get_emulator()
    except:
        raise error.EmulationError("File with emulator definition should define the 'get_emulator' function")

    if machine is None or not isinstance(machine, EmulatorBase):
        raise error.EmulationError(f"Function get_emulator returned unvalid instance of machine expected: 'EmulatorBase', got '{machine}'")
    
    print()
    print("Writing data to device")

    debug_instructions = write_program(program, context, machine)
    write_data(program, context, machine)

    print("Starting Emulation")
    # Load data from #data
    while machine.is_running():
        pos = machine.get_current_pos()
        
        if pos in debug_instructions:
            for instruction in (i for i in debug_instructions[pos] if 'pre' in i): 
                execute_debug_command(instruction['pre'], machine, profile)

        machine.next_tick()
        
        if pos in debug_instructions:
            for instruction in (i for i in debug_instructions[pos] if 'post' in i): 
                execute_debug_command(instruction['post'], machine, profile)

    print("Emulation finished")

def write_program(program, context, machine):
    debug_instructions = dict()

    for chunk, chunked_program in program.items():
        instructuons, debug = gather_instructions(chunked_program, context)
        packed_instructions = pack_adresses(instructuons)

        machine.write_memory(chunk, DataTypes.PROGRAM, packed_instructions)
        for adress, val in debug.items():
            debug_instructions[adress] = val
    return debug_instructions

def write_data(program, context, machine):
    data: dict = context['data']

    machine.write_memory(None, DataTypes.DATA, data)

        
        
        






