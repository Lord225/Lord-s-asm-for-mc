import core.error as error
import core.loading as loading
import config
from enum import Enum

class TYPE(Enum):
    MOV         = 0
    ALU_ONE_ARG = 1 
    ALU_TWO_ARG = 2 
    JUMP        = 3 
    CALL        = 4 
    OTHER       = 5 
    DEBUG       = 6 

G_INFO_CONTAINER = {"Warnings": list(), "info": list(), "skip": False, "stop": False}

PROFILE = None

def load_profie(profile, emulator):
    global PROFILE
    PROFILE = loading.PROFILE_DATA(profile=profile, emulator=emulator)

def padhex(x, pad, prefix = True):
        return '{}{}{}'.format('0x' if prefix else '',"0"*(pad-len(hex(x)[2:])),hex(x)[2:])
def padbin(x, pad, prefix = True):
    return '{}{}{}'.format('0b' if prefix else '',"0"*(pad-len(bin(x)[2:])),bin(x)[2:])
def paddec(x, pad, fill = "0"):
    return '{}{}'.format(fill*(pad-len(str(x))), str(x))

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
        return get_value(raw_argument[1:]), PROFILE.ADRESS_MODE_REMAP["const"]
    elif "ram" in raw_argument:
        _reg_start = raw_argument.find("reg")
        if _reg_start != -1:
            if raw_argument.find("ram") > _reg_start:
                raise error.SynaxError("reg[ram[...]] is not supported (and doesn't make sense btw)")
            #ptr
            return extract_number_from_bracets(raw_argument[_reg_start:]), PROFILE.ADRESS_MODE_REMAP["ptr"]
        else:
            #const
            return extract_number_from_bracets(raw_argument), PROFILE.ADRESS_MODE_REMAP["ram"]
    elif "reg" in raw_argument:
        return extract_number_from_bracets(raw_argument), PROFILE.ADRESS_MODE_REMAP["reg"]
    else:
        if raw_raw_argument in JUMP_LIST:
            return get_jump_adress(raw_raw_argument),  PROFILE.ADRESS_MODE_REMAP["adress"]
        #probably custom arguments
        for key, val in PROFILE.ADRESS_MODE_REMAP.items():
            if key in raw_argument:
                return extract_number_from_bracets(raw_argument), val

def get_jump_adress(raw_argument: str, JUMP_LIST):
    """Returns true adress in ROM of raw_argument table"""
    if len(raw_argument)==0:
        raise error.SynaxError("expected jump identifier")
    if raw_argument not in JUMP_LIST:
        raise error.SynaxError("Jump identifier: '{}' is undefined.".format(raw_argument))
    return JUMP_LIST[raw_argument]

def get_value(strage_format:str):
    """Returns value of strage_format"""
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

def get_command_name(command:str):
    "Will return command type and name"
    if command[0] == "#":
        return command, "debug"
    try:
        cmd_splitted = command.split(" ")
        for i in PROFILE.COMMANDS_SUBTYPES:
            for j in PROFILE.COMMANDS_OREDERD_BY_SUBTYPES[i]:
                if j["name"] == cmd_splitted[0]:
                    return j["name"], i
    except KeyError as err:
        raise error.ProfileStructureError(err)
    except Exception as err:
        raise error.UndefinedCommand("Undefined error while searching for command: {}".format(err))
    raise error.UndefinedCommand(command)


def cliping_beheivior(arg, Max):
    """Way that solver will treat cliping"""
    if config.G_RISE_ERROR_ON_BAD_RANGES:
        raise error.ExpectedValue(Max, arg)
    G_INFO_CONTAINER["info"].append("Value has been cliped: {}".format(arg))

def get_command_hash(cmd, _type, args) -> str:
    """return hash of this command (accepted by) COMMAND_MAP"""
    if len(args) == 0:
        return cmd
    for command_pattern in PROFILE.COMMANDS_OREDERD_BY_SUBTYPES[_type]:
        if command_pattern["name"] == cmd:
            if "arguments pass" in command_pattern:
                raise error.DeprecatedFunction("arguments pass")
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
        raise error.UndefinedCommand("Can't match command: '{}' with arguments: {}".format(cmd, PROFILE.ADRESS_MODE_REMAP_REVERSED[args]))

def generate_ram_display(RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "bin", ADD_ASCII_VIEW = True):
    """
    It just works.
    """
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
    OUTPUT = "\n"

    if config.RAM_DEBUG_MODE == "simple":
        return '\n'.format(RAM)
    elif config.RAM_DEBUG_MODE == "row":
        try:
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
    if config.DEBUG_MODE == "simple":
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
    MAP = dict()
    {
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
    if "parent" in PROFILE.COMMANDSETFULL[cmdhash]:
        try:
            parent = PROFILE.COMMANDSETFULL[PROFILE.COMMANDSETFULL[cmdhash]["parent"]]
        except KeyError as err:
            raise error.ProfileStructureError("command is parented to '{}', but it doesn't exist.".format(PROFILE.COMMANDSETFULL[cmdhash]["parent"]))
        cmd, _type = parent["name"], parent["type"]
        args_new = []
        for arg_patt, arg_old in zip(parent["args"], args):
            args_new.append((arg_old[0], arg_patt["type"]))
        args = args_new
    return cmd, _type, args

def check_argument_ranges(args):
    for arg, Type in args:
        try:
            cliping_beheivior(arg, PROFILE.PARAMETERS["arguments sizes"][Type])
        except KeyError as err:
            raise error.ProfileStructureError("Expected custom argument size definiton.", custom=True)

def solve(JUMP_MAP: dict, target_core: str, command:str):
    cmd, _type = get_command_name(command)
    if _type == "debug":
        return _type, cmd, []
    else:
        if ',' in command[len(cmd):]:
            args = [get_argument_type(arg.strip(), JUMP_MAP) for arg in command[len(cmd):].strip().split(",")]
        else:
            args = []
            
    check_argument_ranges(args)

    if config.USE_FANCY_SYNAX:
        cmd, _type, args = replace_fancy_commands(cmd, _type, args)

    cmd_hash = get_command_hash(cmd, _type, args)

    return _type, cmd_hash, args

def execute(_type, cmd_hash, device, target_core, args, thread):
    """Will execute builded commad on device"""
    reset_G_INFO_CONTAINER()
    if _type == "debug":
        execute_debug_command(device, target_core, cmd_hash)
        G_INFO_CONTAINER["skip"] = True
        return G_INFO_CONTAINER
    try:
        if len(args) == 0:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core])
        if len(args) == 1:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0])
        elif len(args) == 2:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0])
        elif len(args) == 3:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0], args[2][0])
        elif len(args) == 4:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0], args[2][0], args[4][0])
        else:
            raise error.Unsupported("Ouch. Ask author if you need more that 4 args...")
    except Exception as err:
        raise error.Unsupported("What just happen? You have to report this!, {}".format(err))   




    if config.LOG_COMMAND_MODE is not None:
        end = "\n" if thread is None or config.FORCE_COMMANDS_IN_SEPERATE_ROWS else "\t"

        if config.LOG_COMMAND_MODE == "short":
            print(target_core, cmd_hash, end=end)
        elif config.LOG_COMMAND_MODE == "long":
            print(form_full_log_command(_type, cmd_hash, device, target_core, args), end=end)
        else:
            raise error.UndefinedSetting("Possible settings for LOG_COMMAND_MODE are: ['short', 'long','raw', None] got: {}".format(config.LOG_COMMAND_MODE))
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

def form_full_log_command(_type, formed_command, device, target_core, args):
    """Will create standarised, redable command line with fancy synax and only with dec number representation"""
    if _type == "debug":
        return ""
    fancy_command = "Core[{}]: ".format(target_core)
    fancy_command = PROFILE.COMMANDSETFULL[formed_command]["name"]
    fancy_command += " "
    #* TODO FIX ram's moves (now thay are ugly)
    if len(args) != 0:
        for arg in args:
            if arg[1] == PROFILE.ADRESS_MODE_REMAP["const"]:
                arg = "{}".format(arg[0])
            elif arg[1] == PROFILE.ADRESS_MODE_REMAP["ram"]:
                arg = "ram[{}]".format(arg[0])
            elif arg[1] == PROFILE.ADRESS_MODE_REMAP["reg"]:
                arg = "reg[{}]".format(arg[0])
            elif arg[1] == PROFILE.ADRESS_MODE_REMAP["ptr"]:
                arg = "ram[reg[{}]]".format(arg[0])
            else:
                error.CurrentlyUnsupported("That shouldn't happen.")
            fancy_command += "{}, ".format(arg)
    return fancy_command[:-2]

def form_full_log_command_batch(batch, BUILD_OFFSET):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        for COMMAND in batch[core]:
            if type(COMMAND) is tuple:
                _type, formed_command, args, jump_adress = COMMAND 
                if _type != TYPE.DEBUG:
                    builded_program[core].append(form_full_log_command(_type, formed_command, None, loading.CORE_ID_MAP[core], args))
            else:
                MULTICOMMAND = "["
                for _type, formed_command, args, jump_adress in COMMAND:
                    if _type != TYPE.DEBUG:
                        MULTICOMMAND += "{}; ".format(form_full_log_command(_type, formed_command, None, loading.CORE_ID_MAP[core], args))
                MULTICOMMAND = MULTICOMMAND.strip()+"]"
                builded_program[core].append(MULTICOMMAND)
    return builded_program

def get_compiled_cmd(COMMAND):
    if type(COMMAND) is tuple:
        _type, formed_command, args = COMMAND
    else:
        raise error.Unsupported("Muli-lined commands")
        #call custom generate func from 'emul'
    def get_value_from_arg(name, CMD_PATTERN, args):
        for i, arg in enumerate(CMD_PATTERN["args"]):
            if arg["name"] == name:
                return args[i][0]
        else:
            raise error.ProfileStructureError("Can't find given name in args")
        

    CMD_PATTERN = PROFILE.COMMANDSETFULL[formed_command]
    ROM = {key:0 for key in PROFILE.COMMAND_LANE_PATTERN.keys()}
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
        builded_program[core].append(str().join(['{}{} \t'.format(key," "*(val["size"]+6-len(key))) for key, val in PROFILE.ROM_SIZES.items()]))
        for CMD in compiled[core]:
            line = ""
            for key, value in CMD.items():
                line += "{} ({}) \t".format(padbin(value,PROFILE.ROM_SIZES[key]["size"],False), paddec(value,3," "))
            builded_program[core].append(line)
    return builded_program
def get_bin(compiled):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        #builded_program[core].append(str().join(['{}{}'.format(key," "*(val["size"]+1-len(key))) for key, val in ROM_SIZES.items()]))
        for CMD in compiled[core]:
            line = ""
            for key, value in CMD.items():
                line += "{} ".format(padbin(value,PROFILE.ROM_SIZES[key]["size"],False))
            builded_program[core].append(line)
    return builded_program