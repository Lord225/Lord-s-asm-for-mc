import core.error as error
import core.loading as loading
from enum import Enum

class TYPE(Enum):
    MOV         = 0
    ALU_ONE_ARG = 1 
    ALU_TWO_ARG = 2 
    JUMP        = 3 
    CALL        = 4 
    OTHER       = 5 
    DEBUG       = 6 

G_INFO_CONTAINER = {"Warnings": list(), "info": list(), "skip": False, "stop":False}
G_RISE_ERROR_ON_BAD_RANGES = True
LOG_COMMAND_MODE = "short" 
USE_FANCY_SYNAX = True
FORCE_COMMANDS_IN_SEPERATE_ROWS = False
RAISE_ERROR_ON_NOT_IMPLEMENTED_BIN_FORMATING = False
RAISE_ERROR_ON_NOT_IMPLEMENTED_EMULATOR = True
RAM_DEBUG_MODE = "simple"
DEBUG_MODE = "simple"

PROFILE_LOADED = False
COMMAND_MAP = dict() #ordered by hash, keeps emulator function pointers
COMMANDSETFULL = dict() #ordered by hash, keeps "COMMANDS":{}
COMMANDS_SUBTYPES = dict() #all subtypes
COMMANDS_OREDERD_BY_SUBTYPES = dict() #ordered by subtypes, keeps "COMMANDS":{}
COMMAND_LANE_PATTERN = dict()
ROM_SIZES = dict()
PARAMETERS = dict()
CUSTOM_ARGUMENTS = dict()
ADRESS_MODE_REMAP  = {x:i for i, x in enumerate(["const", "reg", "ptr", "ram", "adress"])}
ADRESS_MODE_REMAP_REVERSED = dict()

def padhex(x, pad, prefix = True):
        return '{}{}{}'.format('0x' if prefix else '',"0"*(pad-len(hex(x)[2:])),hex(x)[2:])
def padbin(x, pad, prefix = True):
    return '{}{}{}'.format('0b' if prefix else '',"0"*(pad-len(bin(x)[2:])),bin(x)[2:])
def paddec(x, pad, fill = "0"):
    return '{}{}'.format(fill*(pad-len(str(x))), str(x))
def extract_basic_data(profile):
    global COMMAND_MAP
    global COMMANDSETFULL
    global COMMANDS_SUBTYPES
    global ROM_SIZES
    global PARAMETERS
    global CUSTOM_ARGUMENTS
    global ADRESS_MODE_REMAP
    global ADRESS_MODE_REMAP_REVERSED
    
    #TODO CHECK IT BETTER
    #Check ROM_SIZES with "bin"
    #Check COMMANDS with name, type, subtype, emulator, description, example, args, bin
    #Check parametrs with word len, num of regs, ram adress space, rom adress space, cores, arguments sizesSUPPORTED TECHNOLOGIES
    #Check if any of the COMMAND_MAP key is pointing to None

    def checkstructure():
        __NAMESPACE__ = ["Name", "Architecture", "ARGUMENTS", "Author", "emulator", "DEFINES", "parametrs", "COMMANDS", "CUSTOM ARGUMENTS"]
        try:
            for name in __NAMESPACE__:
                try:
                    profile["CPU"][name]
                except KeyError as err:
                    raise error.ProfileStructureError("Expected key in master branch: {}".format(name))
            #DEFINES
            if type(profile["CPU"]["DEFINES"]) is not list:
                raise error.ProfileStructureError("Expected 'DEFINES' to be list of definitions: {}".format(name))
            if any((type(x) is not str for x in profile["CPU"]["DEFINES"])):
                raise error.ProfileStructureError("Expected 'DEFINES' to be list of strings.".format())
            
            #parametrs
            parametrs__NAMESPACE__ = ["clock_speed", "word len", "num of regs", "ram adress space", "rom adress space", "cores", "arguments sizes"]

            for name in parametrs__NAMESPACE__:
                try:
                    profile["CPU"]["parametrs"]
                except KeyError as err:
                    raise error.ProfileStructureError("Expected '{}' in 'parametrs'".format(name))
            #custom arguments
            cmd__NAMESPACE__ = ["name", "type", "subtype", "args"]
            cmd__NAMESPACE__WARNING = ["description", "example"]

            if RAISE_ERROR_ON_NOT_IMPLEMENTED_BIN_FORMATING:
                cmd__NAMESPACE__.append("bin")
            else:
                cmd__NAMESPACE__WARNING.append("bin")

            if RAISE_ERROR_ON_NOT_IMPLEMENTED_EMULATOR:
                cmd__NAMESPACE__.append("emulator")
            else:
                cmd__NAMESPACE__WARNING.append("emulator")
            #COMMANDS
            for name, cmd in profile["CPU"]["COMMANDS"].items():
                for cmd_must in cmd__NAMESPACE__:
                    try:
                        cmd[cmd_must]
                    except KeyError as err:
                        raise error.ProfileStructureError("Expected '{}' in 'COMMANDS'->'{}'".format(cmd_must, name))
                for cmd_should in cmd__NAMESPACE__WARNING:
                    try:
                        cmd[cmd_should]
                    except KeyError as err:
                        print("WARNING: Expected '{}' key in 'COMMANDS'->'{}'".format(cmd_should, name)) 
        except KeyError as err:
            raise err
            
    def get_full_command_set():
        return {value["HASH"]:value for key, value in profile["CPU"]["COMMANDS"].items()}
    def get_unified_commands_types():
        return list({i["subtype"] for i in profile["CPU"]["COMMANDS"].values()})
    def build_command_map():
        for i, (key, value) in enumerate(profile["CPU"]["COMMANDS"].items()):
            profile["CPU"]["COMMANDS"][key]["HASH"] = i
            exec("COMMAND_MAP[{}] = emul.Core.{}".format(i, value["emulator"]))
            if COMMAND_MAP[i] == None:
                raise error.LoadError("Can't link '{}' operation with emulator (emulator doesn't implement this function)".format(value["emulator"]))
        for i, (key, value) in enumerate(profile["CPU"]["COMMANDS"].items()):
            if "parent" in value:
                profile["CPU"]["COMMANDS"][key]["parent"] = profile["CPU"]["COMMANDS"][value["parent"]]["HASH"]
    def order_commands_by_subtypes():
        global COMMANDSETFULL
        global COMMANDS_SUBTYPES
        for i in COMMANDS_SUBTYPES:
            COMMANDS_OREDERD_BY_SUBTYPES[i] = []
            for j in profile["CPU"]["COMMANDS"].values():
                if j["subtype"] == i:
                    COMMANDS_OREDERD_BY_SUBTYPES[i].append(j)
    def remap_adress_mode():
        global COMMANDSETFULL
        for cmd_pattern in COMMANDSETFULL.values():
            for arg_id in range(len(cmd_pattern["args"])):
                cmd_pattern["args"][arg_id]["type"] = ADRESS_MODE_REMAP[cmd_pattern["args"][arg_id]["type"]]
    def get_command_lane():
        global COMMAND_LANE_PATTERN
        COMMAND_LANE_PATTERN = profile["CPU"]["ARGUMENTS"]
    def get_custom_arguments():
        global CUSTOM_ARGUMENTS
        CUSTOM_ARGUMENTS = profile["CPU"]["CUSTOM ARGUMENTS"]        
    def get_rom_arg_sizes():
        global ROM_SIZES
        ROM_SIZES = profile["CPU"]["ARGUMENTS"]
    def get_custom_arguments_types():
        global ADRESS_MODE_REMAP
        global ADRESS_MODE_REMAP_REVERSED
        last = max(ADRESS_MODE_REMAP.values())
        i = 1
        for key, val in profile["CPU"]["CUSTOM ARGUMENTS"].items():
            if key in ADRESS_MODE_REMAP:
                raise error.ProfileStructureError()
            ADRESS_MODE_REMAP[key] = last+i
            i += 1
        ADRESS_MODE_REMAP_REVERSED = {b:a for a,b in ADRESS_MODE_REMAP.items()}
   
    try:
        checkstructure()
    except Exception as err:
        raise err

    try:
        COMMANDS_SUBTYPES = get_unified_commands_types()

        order_commands_by_subtypes()

        build_command_map()

        COMMANDSETFULL = get_full_command_set()
        
        get_custom_arguments_types()
        
        remap_adress_mode()

        get_command_lane()

        get_rom_arg_sizes()
        
   
        PARAMETERS = profile["CPU"]["parametrs"]

        NEW_ARGUMENT_SIZES = dict()
        for key, value in PARAMETERS["arguments sizes"].items():
            NEW_ARGUMENT_SIZES[ADRESS_MODE_REMAP[key]] = value
        PARAMETERS["arguments sizes"] = NEW_ARGUMENT_SIZES
    
    except Exception as err:
        raise error.ProfileStructureError(err)
    PROFILE_LOADED = True

def reset_G_INFO_CONTAINER():
    global G_INFO_CONTAINER
    if len(G_INFO_CONTAINER["Warnings"]) != 0:
        G_INFO_CONTAINER["Warnings"] = list()
    if len(G_INFO_CONTAINER["info"]) != 0:
        G_INFO_CONTAINER["info"] = list()
    if G_INFO_CONTAINER["skip"] != False:
        G_INFO_CONTAINER["skip"] = False
    if G_INFO_CONTAINER["stop"] != False:
        G_INFO_CONTAINER["stop"] = False

def extract_number_from_bracets(unformed):
    """wqerfewfw[return_this_value]wefwefwe"""

    start_bracket = unformed.find("[")
    end_bracket = unformed.find("]")
    if start_bracket == -1:
        raise error.SynaxError("Expected '[' in argument")
    if end_bracket == -1:
        raise error.SynaxError("Expected ']' in argument")
    return get_value(unformed[start_bracket+1:end_bracket])

#TODO ADD jumps adress support
def get_argument_type(raw_raw_argument: str, JUMP_LIST):
    """
    Accepts:
    reg[_value] -> reg    (reg access, fancy)
    _value      -> reg    (reg access, simple)
    $_value     -> _value (const)

    Any selector in ADRESS_MODE_REMAP dict. 

    types:
    0xFFFF -> hex
    0b0011 -> bin
    123456 -> dec

    fancy acces:
    
    ram[_value] -> ram adress
    ram[reg[_value]] -> ram pointer

    custom:

    NAME[value]
    """
    
    raw_argument = raw_raw_argument.lower()
    if len(raw_argument)==0:
        raise error.Expected("Argument", raw_argument)
    if raw_argument[0] == "$":
        return get_value(raw_argument[1:]), ADRESS_MODE_REMAP["const"]
    elif "ram" in raw_argument:
        _reg_start = raw_argument.find("reg")
        if _reg_start != -1:
            if raw_argument.find("ram") > _reg_start:
                raise error.SynaxError("reg[ram[...]] is not supported (and doesn't make sense btw)")
            #ptr
            return extract_number_from_bracets(raw_argument[_reg_start:]), ADRESS_MODE_REMAP["ptr"]
        else:
            #const
            return extract_number_from_bracets(raw_argument), ADRESS_MODE_REMAP["ram"]
    elif "reg" in raw_argument:
        return extract_number_from_bracets(raw_argument), ADRESS_MODE_REMAP["reg"]
    else:
        if raw_raw_argument in JUMP_LIST:
            return get_jump_adress(raw_raw_argument), ADRESS_MODE_REMAP["adress"]
        #probably custom arguments
        for key, val in ADRESS_MODE_REMAP.items():
            if key in raw_argument:
                return extract_number_from_bracets(raw_argument), val

def get_jump_adress(raw_argument: str, JUMP_LIST):
    if len(raw_argument)==0:
        raise error.SynaxError("expected jump identifier")
    if raw_argument not in JUMP_LIST:
        raise error.SynaxError("Jump identifier: '{}' is undefined.".format(raw_argument))
    return JUMP_LIST[raw_argument]

def get_value(strage_format:str):
    if strage_format.isdecimal():
        return int(strage_format)
    elif len(strage_format[2:]) == 0:
        raise error.UndefinedValue(strage_format)
    elif strage_format[:2] == "0x":
        return int(strage_format[2:],base=16)
    elif strage_format[:2] == "0b":
        return int(strage_format[2:],base=2)
    else:
        raise error.UndefinedValue(strage_format)

def get_command_name(command:str) -> (str,str):
    if command[0] == "#":
        return command, "debug"
    try:
        cmd_splitted = command.split(" ")
        for i in COMMANDS_SUBTYPES:
            for j in COMMANDS_OREDERD_BY_SUBTYPES[i]:
                if j["name"] == cmd_splitted[0]:
                    return j["name"], i
    except KeyError as err:
        raise error.ProfileStructureError(err)
    except Exception as err:
        raise error.UndefinedCommand("Undefined error while searching for command: {}".format(err))
    raise error.UndefinedCommand(command)

#* DOTO replace emulator.WORD_SIZE with profile value
def cliping_beheivior(arg, Max):
    """Way that solver will treat cliping"""
    if G_RISE_ERROR_ON_BAD_RANGES:
        raise error.ExpectedValue(Max, arg)
    G_INFO_CONTAINER["info"].append("Value has been cliped: {}".format(arg))

def get_command_hash(cmd, _type, args) -> str:
    """return hash of this command (accepted by) COMMAND_MAP"""
    if len(args) == 0:
        return cmd
    for command_pattern in COMMANDS_OREDERD_BY_SUBTYPES[_type]:
        if command_pattern["name"] == cmd:
            if "arguments pass" in command_pattern:
                raise error.DeprecatedFunction("arguments pass")
                return command_pattern["HASH"]
            if len(command_pattern["args"]) != len(args):
                if _type in ["jump_cond", "jump_uncond", "call_cond", "call_uncond"]:
                    if len(command_pattern["args"]) != len(args)+1:
                        continue
                else:
                    continue
            for args_pattern, args_current in zip(command_pattern["args"], args):
                if args_pattern["type"] != args_current[1]:
                    break
            else:
                #print("mached: {}".format(command_pattern["emulator"]))
                return command_pattern["HASH"]        
    else:
        raise error.UndefinedCommand("Can't match command: '{}' with arguments: {}".format(cmd, ADRESS_MODE_REMAP_REVERSED[args]))

def generate_ram_display(RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "bin", ADD_ASCII_VIEW = True):
    if rows%subrows != 0:
        raise error.UndefinedSetting("Row number should be dividable by subrow count.")
    def generate_value(PAD = -1, MODE = "dec"):
        ADRESS = ""
        try:
            val = RAM[adress + i]
        except IndexError:
            raise "END"
        if MODE == "dec":
            PAD = 4 if PAD == -1 else PAD
            ADRESS = str(val)
        elif MODE == "hex":
            PAD = 3 if PAD == -1 else PAD
            ADRESS = str(padhex(val, 2, False))
        elif MODE == "bin":
            PAD = 9 if PAD == -1 else PAD
            ADRESS = padbin(val, 8, False)
        return '{}{}'.format(" "*(PAD-len(ADRESS)), ADRESS)
    totalrows = rows
    rows //= subrows
    LINE_START = 0
    subrow_cunter = 0
    if RAM_DEBUG_MODE == "simple":
        return '\n'.format(RAM)
    elif RAM_DEBUG_MODE == "row":
        try:
            OUTPUT = "\n"
            for adress in range(0, 255, rows):
                if subrow_cunter == 0:
                    LINE_START = adress
                rows_data = ""
                for i in range(rows):
                    rows_data += generate_value(-1, VALUE_AS)
                if ADD_ASCII_VIEW:
                    if subrow_cunter == (subrows-1):
                        asciirep = ""
                        for i in range(totalrows):
                            char_id = RAM[LINE_START+i]
                            asciirep += chr(char_id) if char_id >= 32 else "."

                        rows_data += "\t{}".format(asciirep)
                if ADRESS_AS_HEX:
                    OUTPUT += " {}:{}{}".format(padhex(adress, 2), rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                else:
                    OUTPUT += " {}:{}{}".format(adress, rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                subrow_cunter = (subrow_cunter+1)%subrows
        except:
            pass
            
        return OUTPUT

def execute_debug_command(device, target_core:int, debug_cmd:str):
    debug_cmd = debug_cmd.lower()[1:]
    if DEBUG_MODE == "simple":
        if debug_cmd == "regs":
            print("Core{} regs =".format(target_core),device.CORES[target_core].get_regs_status())
        elif debug_cmd == "break":
            print("CPU hit breakpoint")
            input()
        elif debug_cmd == "ram":
            print("Ram =", generate_ram_display(device.RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "dec", ADD_ASCII_VIEW = True))
        elif debug_cmd == "ramslice":
            raise error.CurrentlyUnsupported("ramslice")
            print("Ram =",device.RAM)
        elif debug_cmd[:4] == "log ":
            print(solve_log_command(debug_cmd[4:], device, target_core))

def solve_log_command(cmd: str, device, target_core: int):
    MAP = {
        "regs":device.CORES[target_core].Regs,
        "rom_stack":device.CORES[target_core].ROMStack,
        "rom_stack_len":len(device.CORES[target_core].ROMStack),
        "stack":device.CORES[target_core].Stack,
        "stack_len":len(device.CORES[target_core].Stack),
        "flags":device.CORES[target_core].ALU_FLAGS,
        "rom":device.CORES[target_core].ROM_COUNTER,
        "overflow":device.CORES[target_core].ALU_FLAGS["overflow"],
        "sign":device.CORES[target_core].ALU_FLAGS["sign"],
        "zero":device.CORES[target_core].ALU_FLAGS["zero"],
        "partity":device.CORES[target_core].ALU_FLAGS["partity"]
        }
        
    return cmd.format_map(MAP)

def replace_fancy_commands(cmd, _type, args):
    cmdhash = get_command_hash(cmd, _type, args)
    if "parent" in COMMANDSETFULL[cmdhash]:
        try:
            parent = COMMANDSETFULL[COMMANDSETFULL[cmdhash]["parent"]]
        except KeyError as err:
            raise error.ProfileStructureError("command is parented to '{}', but it doesn't exist.".format(COMMANDSETFULL[cmdhash]["parent"]))
        cmd, _type = parent["name"], parent["type"]
        args_new = []
        for arg_patt, arg_old in zip(parent["args"], args):
            args_new.append((arg_old[0], arg_patt["type"]))
        args = args_new
    return cmd, _type, args

def check_custom_argument_pass(cmd, _type, args):
    return cmd, _type, args
    raise error.DeprecatedFunction("argument passes")

    for command_pattern in COMMANDS_OREDERD_BY_SUBTYPES[_type]:
        if command_pattern["name"] == cmd:
            if "arguments pass" in command_pattern:
                new_args = []
                for arg in command_pattern["arguments pass"]:
                    if "const" in arg:
                        new_args.append((arg["const"], ADRESS_MODE_REMAP["const"]))
                    elif "arg" in arg:
                        new_args.append(args[arg["arg"]])
                    else:
                        raise error.ProfileStructureError("Argument pass is fucked up.")
                return cmd, _type, new_args
    else:
        return cmd, _type, args

def check_argument_ranges(args):
    for arg, Type in args:
        try:
            cliping_beheivior(arg, PARAMETERS["arguments sizes"][Type])
        except KeyError as err:
            raise error.ProfileStructureError("Expected custom argument size definiton.",custom=True)

def solve(JUMP_MAP: dict, target_core: str, command:str):
    cmd, _type = get_command_name(command)
    if _type == "debug":
        return _type, cmd, None, -1
    else:
        if ',' in command[len(cmd):]:
            args = [get_argument_type(arg.strip(), JUMP_MAP) for arg in command[len(cmd):].strip().split(",")]
        else:
            args = []
            
    check_argument_ranges(args)

    if USE_FANCY_SYNAX:
        cmd, _type, args = replace_fancy_commands(cmd, _type, args)
        cmd, _type, args = check_custom_argument_pass(cmd, _type, args)

    cmd_hash = get_command_hash(cmd, _type, args)

    return _type, cmd_hash, args

def read_and_execute(device, JUMP_MAP: dict, target_core:str, command:str):
    """Will interprate and execute raw command"""
    _type, cmd_hash, args = solve(JUMP_MAP, target_core, command)
    
    # Comand has been computed: 
    # formed_commad - command accepted by COMMAND_MAP
    # args          - arguments in format [(value, ADRESS_MODE), (value, ADRESS_MODE),...] 
    # _type         - cmd generalized command type _TYPE

    execute(_type, cmd_hash, device, target_core, args, 0)
    
    return G_INFO_CONTAINER

def execute(_type, cmd_hash, device, target_core, args, thread):
    """Will execute builded commad on device"""
    reset_G_INFO_CONTAINER()
    if _type == "debug":
        execute_debug_command(device, target_core, cmd_hash)
        G_INFO_CONTAINER["skip"] = True
        return G_INFO_CONTAINER
    try:
        if len(args) == 0:
            COMMAND_MAP[cmd_hash](device.CORES[target_core])
        if len(args) == 1:
            COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0])
        elif len(args) == 2:
            COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0])
        elif len(args) == 3:
            COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0], args[2][0])
        elif len(args) == 4:
            COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0], args[2][0], args[4][0])
        else:
            raise error.Unsupported("Ouch. Ask author if you need more that 4 args...")
    except Exception as err:
        raise error.Unsupported("What just happen? You have to report this!, {}".format(err))   
    if LOG_COMMAND_MODE is not None:
        end = "\n" if thread is None or FORCE_COMMANDS_IN_SEPERATE_ROWS else "\t"

        if LOG_COMMAND_MODE == "short":
            print(target_core, cmd_hash, end=end)
        elif LOG_COMMAND_MODE == "long":
            print(form_full_log_command(_type, cmd_hash, device, target_core, args, jump_adress), end=end)
        else:
            raise error.UndefinedSetting("Possible settings for LOG_COMMAND_MODE are: ['short', 'long','raw', None] got: {}".format(LOG_COMMAND_MODE))
    return G_INFO_CONTAINER

def build_program(Program, line_indicator, JUMPLIST, Settings) -> list:
    """Returns builded instructions by solve function (will change raw command in to solved)"""
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        if core != "SHADER":
            for i, line in enumerate(Program[core]):
                try:
                    builded_program[core].append(solve(JUMPLIST[core], loading.CORE_ID_MAP[core], line))
                except Exception as err:
                    err.line = "{} ('{}')".format(line_indicator[core][i], line)
                    raise err

    return builded_program

def args_equal(args1, args2, TypesOnly = False):
    """Will compare all passed arguments
    if TypesOnly == True -> will compare only types of arguments (not values)"""
    if type(args1) is not list:
        args1 = [args1]
    if type(args2) is not list:
        args2 = [args2]    
    if TypesOnly:
        return all(arg1[1] == arg2[1] for arg1, arg2 in zip(args1, args2))
    else:
        return all(arg1[1] == arg2[1] and arg1[0] == arg2[0] for arg1, arg2 in zip(args1, args2))

def form_full_log_command(_type, formed_command, device, target_core, args, jump_adress):
    """Will create standarised, redable command line with fancy synax and only with dec number representation"""
    if _type == "debug":
        return ""
    fancy_command = "Core[{}]: ".format(target_core)
    fancy_command = COMMANDSETFULL[formed_command]["name"]
    fancy_command += " "
    #* TODO FIX ram's moves (now thay are ugly)
    if len(args) != 0:
        for arg in args:
            if arg[1] == ADRESS_MODE_REMAP["const"]:
                arg = "{}".format(arg[0])
            elif arg[1] == ADRESS_MODE_REMAP["ram"]:
                arg = "ram[{}]".format(arg[0])
            elif arg[1] == ADRESS_MODE_REMAP["reg"]:
                arg = "reg[{}]".format(arg[0])
            elif arg[1] == ADRESS_MODE_REMAP["ptr"]:
                arg = "ram[reg[{}]]".format(arg[0])
            else:
                error.CurrentlyUnsupported("That shouldn't happen.")
            fancy_command += "{}, ".format(arg)
    if jump_adress is not None:
        fancy_command += "{}".format(jump_adress)
        return fancy_command
    else:
        return fancy_command[:-2]

def form_full_log_command_batch(batch, BUILD_OFFSET):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        for COMMAND in batch[core]:
            if type(COMMAND) is tuple:
                _type, formed_command, args, jump_adress = COMMAND 
                if _type != TYPE.DEBUG:
                    builded_program[core].append(form_full_log_command(_type, formed_command, None, loading.CORE_ID_MAP[core], args, jump_adress+BUILD_OFFSET if jump_adress is not None else None))
            else:
                MULTICOMMAND = "["
                for _type, formed_command, args, jump_adress in COMMAND:
                    if _type != TYPE.DEBUG:
                        MULTICOMMAND += "{}; ".format(form_full_log_command(_type, formed_command, None, loading.CORE_ID_MAP[core], args, jump_adress+BUILD_OFFSET if jump_adress is not None else None))
                MULTICOMMAND = MULTICOMMAND.strip()+"]"
                builded_program[core].append(MULTICOMMAND)
    return builded_program

def get_compiled_cmd(COMMAND):
    if type(COMMAND) is tuple:
        _type, formed_command, args, jump_adress = COMMAND
    else:
        raise error.Unsupported("Muli-lined commands")
        #call custom generate func from 'emul'
    def get_value_from_arg(name, CMD_PATTERN, args):
        for i, arg in enumerate(CMD_PATTERN["args"]):
            if arg["name"] == name:
                return args[i][0]
        else:
            raise error.ProfileStructureError("Can't find given name in args")
        

    CMD_PATTERN = COMMANDSETFULL[formed_command]
    ROM = {key:0 for key in COMMAND_LANE_PATTERN.keys()}
    try:
        for key, value in CMD_PATTERN["bin"].items():
            if type(value) is not str:
                ROM[key] = value
            else:
                ROM[key] = get_value_from_arg(value, CMD_PATTERN, args)
    except KeyError as err:
        raise error.ProfileStructureError("Can't find binary command profile ({})".format(err))
    except Exception as err:
        raise error.ProfileStructureError("Undefined error while compiling: {}".format(err))
    return ROM

def get_compiled(builded_commands, offset: int):
    """Converts builded instructions into binary"""
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        for COMMAND in builded_commands[core]:
            if COMMAND[0] == "debug":
                continue
            builded_program[core].append(get_compiled_cmd(COMMAND))
    return builded_program

def generate_debug_frame():
    frame = """
    Core0: =================================================================

    0           | 1           | 2              
    mov 0, 5, 7 | sub 5, 7, 9 | jmp 12 
    ========================================================================
    Regs: [0, 0, 0, 0, 0, 0, 0, 0] S: 0 OF: 1 Z:
    ROMSTACK: [0, 2, 3]
    CPUSTACK: [0, 2, 3]

    Core1: =================================================================
    0           | 1           | 2              
    mov 0, 1, 3 | add 4, 6, 7 | jmp 10 
    ========================================================================
    Regs: [0, 0, 0, 0, 0, 0, 0, 0] S: 0 OF: 1 Z:
    ROMSTACK: [0, 2, 3]
    CPUSTACK: [0, 2, 3]

    0x00: cc 80 7f cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x10: cc cc cc cc cc cc cc cc cc cc cc cc cc cc 48 65  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x20: 6c 6c 6f 20 57 6f 72 6c 64 cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌHe
    0x30: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  llo WorldÌÌÌÌÌÌÌ
    0x40: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x50: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x60: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x70: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x80: 7e 80 cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0x90: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ~ÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0xa0: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0xb0: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0xc0: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0xd0: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0xe0: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ
    0xf0: cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc cc  ÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌÌ

    Errors, Warinings ect
    """
    print(frame)

def get_csv(compiled):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        builded_program[core].append(str().join(['{},'.format(key," "*(val["size"]+6-len(key))) for key, val in ROM_SIZES.items()])[:-1])
        for CMD in compiled[core]:
            line = ""
            for key, value in CMD.items():
                line += "{},".format(value)
            builded_program[core].append(line[:-2])
    return builded_program
def get_dec(compiled):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        builded_program[core].append(str().join(['{}{} \t'.format(key," "*(val["size"]+6-len(key))) for key, val in ROM_SIZES.items()]))
        for CMD in compiled[core]:
            line = ""
            for key, value in CMD.items():
                line += "{} ({}) \t".format(padbin(value,ROM_SIZES[key]["size"],False), paddec(value,3,"_"))
            builded_program[core].append(line)
    return builded_program
def get_bin(compiled):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        #builded_program[core].append(str().join(['{}{}'.format(key," "*(val["size"]+1-len(key))) for key, val in ROM_SIZES.items()]))
        for CMD in compiled[core]:
            line = ""
            for key, value in CMD.items():
                line += "{} ".format(padbin(value,ROM_SIZES[key]["size"],False))
            builded_program[core].append(line)
    return builded_program