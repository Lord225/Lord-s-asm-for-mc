import core.error as error
import core.loading as loading
import core.config as config
from tabulate import tabulate
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
    print("Profile Loaded")

def padhex(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0x' if prefix else '',"0"*(pad-len(hex(x)[2:])),hex(x)[2:])
def padbin(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0b' if prefix else '',"0"*(pad-len(bin(x)[2:])),bin(x)[2:])
def paddec(x, pad, fill = "0"):
    x = 0 if x is None else x
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

def extract_from_brackets(raw, bracket_in = '[', bracked_out = ']'):
    """wqerfewfw[return_this_value, _THIS TOOO]wefwefwe"""
    start_bracket = raw.find(bracket_in)
    end_bracket = raw.find(bracked_out)
    if start_bracket == -1:
        raise error.SynaxError("Expected '{}' in argument".format(bracket_in))
    if end_bracket == -1:
        raise error.SynaxError("Expected '{}' in argument".format(bracked_out))
    return raw[start_bracket+1:end_bracket]

def extract_number_from_bracets(unformed):
    """wqerfewfw[return_this_value]wefwefwe"""

    return get_value(extract_from_brackets(unformed))

def get_argument_type(raw_raw_argument: str, JUMP_LIST):
    """
    Accepts:
    reg[_value] -> reg    (reg access, fancy)
    _value      -> reg    (reg access, simple)
    _value     -> _value  (const)

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

    try:
        return get_value(raw_argument), PROFILE.ADRESS_MODE_REMAP["const"]
    except error.UndefinedValue as err:
        pass
    except:
        raise error.UndefinedValue("'{}'".format(raw_argument))

    if "ram" in raw_argument:
        _reg_start = raw_argument.find("reg")
        if _reg_start != -1:
            if raw_argument.find("ram") > _reg_start:
                raise error.SynaxError("reg[ram[...]] is not supported (and doesn't make sense idiot!)")
            #ptr
            return extract_number_from_bracets(raw_argument[_reg_start:]), PROFILE.ADRESS_MODE_REMAP["ptr"]
        else:
            #const
            return extract_number_from_bracets(raw_argument), PROFILE.ADRESS_MODE_REMAP["ram"]
    elif "reg" in raw_argument:
        return extract_number_from_bracets(raw_argument), PROFILE.ADRESS_MODE_REMAP["reg"]
    else:
        if raw_raw_argument in JUMP_LIST:
            return get_jump_adress(raw_raw_argument, JUMP_LIST),  PROFILE.ADRESS_MODE_REMAP["adress"]
        #probably custom arguments
        for key, val in PROFILE.ADRESS_MODE_REMAP.items():
            if key in raw_argument:
                return extract_number_from_bracets(raw_argument), val
        raise error.SynaxError("Cannot interpretate value: {}".format(raw_argument))

def get_jump_adress(raw_argument: str, JUMP_LIST):
    """Returns true adress in ROM of raw_argument table"""
    if len(raw_argument)==0:
        raise error.SynaxError("expected jump identifier")
    if raw_argument not in JUMP_LIST:
        raise error.SynaxError("Jump identifier: '{}' is undefined.".format(raw_argument))
    return JUMP_LIST[raw_argument]
def get_mark_from_jump_adress(raw_argument, JUMP_LIST):
    if type(raw_argument) is list:
        raw_argument = raw_argument[0]
    for key, val in JUMP_LIST.items():
        if val == raw_argument:
            return key
    raise error.SynaxError("Unresolved adress: {}", raw_argument)
def get_value(strage_format:str):
    """Returns value of strage_format"""
    strage_format = strage_format.strip()
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
        for i in PROFILE.COMMANDS_TYPES:
            for j in PROFILE.COMMANDS_OREDERD_BY_TYPES[i]:
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

    for command_pattern in PROFILE.COMMANDS_OREDERD_BY_TYPES[_type]:
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
        raise error.UndefinedCommand("Can't match command: '{}' with arguments: {}".format(cmd, [PROFILE.ADRESS_MODE_REMAP_REVERSED[arg[1]] for arg in args]))

def generate_ram_display(RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "bin", ADD_ASCII_VIEW = True, start = 0, end = None):
    """
    It just works.
    """
    if start != 0:
        start = start + (rows - start % rows)-rows
    else:
        start = 0
    if end is not None:
        end = end + (rows - end % rows)
    else:
        end = len(RAM)
    WORD_SIZE = PROFILE.profile["CPU"]["parametrs"]["word len"]

    if rows%subrows != 0:
        raise error.UndefinedSetting("Row number should be dividable by subrow count.")
    def generate_value(PAD = -1, MODE = "dec"):
        ADRESS = ""
        try:
            val = RAM[adress + i]
        except IndexError:
            raise "END"
        if MODE == "dec":
            PAD = len(str(int(2**WORD_SIZE)-1))+1
            ADRESS = str(val)
        elif MODE == "hex":
            PAD = len(str(hex(2**WORD_SIZE-1)[2:]))+1
            ADRESS = str(padhex(val, 2, False))
        elif MODE == "bin":
            PAD = len(str(bin(2**WORD_SIZE-1)[2:]))+1
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
            for adress in range(0, len(RAM), rows):
                if not (adress in range(start, end)):
                    continue

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
                            asciirep += chr(char_id) if char_id >= 32 and char_id < 127 else "."

                        rows_data += "\t{}".format(asciirep)
                
                if ADRESS_AS_HEX:
                    OUTPUT += " {}:{}{}".format(padhex(adress, len(hex(len(RAM))[2:])), rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                else:
                    OUTPUT += " {}:{}{}".format(adress, rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                subrow_cunter = (subrow_cunter+1)%subrows
        except Exception as err:
            pass
            
        return OUTPUT

def execute_debug_command(device, target_core:int, debug_cmd:str):
    debug_cmd = debug_cmd[1:]
    if config.DEBUG_MODE == "simple":
        if debug_cmd == "regs":
            print("Core{} regs =".format(target_core),device.CORES[target_core].get_regs_status())
        elif debug_cmd == "break":
            print("CPU hit breakpoint")
            input()
        elif debug_cmd == "ram":
            print(generate_ram_display(device.RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "dec", ADD_ASCII_VIEW = True))
        elif debug_cmd.startswith("ramslice"):
            values = extract_from_brackets(debug_cmd,'(',')')
            start, end = [get_value(val) for val in values.split(',')]
            print(generate_ram_display(device.RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "dec", ADD_ASCII_VIEW = True, start = start, end = end))
        elif debug_cmd[:4] == "log ":
            print(solve_log_command(debug_cmd[4:], device, target_core))

def solve_log_command(cmd: str, device, target_core: int):
    MAP = device.CORES[target_core].__dict__
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

def solve(JUMP_MAP: dict, command:str):
    cmd, _type = get_command_name(command)
    if _type == "debug":
        return _type, cmd, []
    else:
        if len(command[len(cmd):]) != 0:
            args = [get_argument_type(arg.strip(), JUMP_MAP) for arg in command[len(cmd):].strip().split(",")]
        else:
            args = []
            
    check_argument_ranges(args)

    if config.USE_FANCY_SYNAX:
        cmd, _type, args = replace_fancy_commands(cmd, _type, args)

    cmd_hash = get_command_hash(cmd, _type, args)

    return _type, cmd_hash, args

def execute(_type, cmd_hash, device, target_core, args, thread, jump_list):
    """Will execute builded commad on device"""
    reset_G_INFO_CONTAINER()
    if _type == "debug":
        execute_debug_command(device, target_core, cmd_hash)
        G_INFO_CONTAINER["skip"] = True
        return G_INFO_CONTAINER
    try:
        if len(args) == 0:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core])
        elif len(args) == 1:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0])
        elif len(args) == 2:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0])
        elif len(args) == 3:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0], args[2][0])
        elif len(args) == 4:
            PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], args[0][0], args[1][0], args[2][0], args[4][0])
        else:
            raise error.Unsupported("Ouch. Ask if you need more that 4 args...")
    except Exception as err:
        raise error.Unsupported("You broke emulator. Congratulations...  '{}'".format(err))   

    if config.LOG_COMMAND_MODE:
        end = "\n" if thread is None or config.FORCE_COMMANDS_IN_SEPERATE_ROWS else "\t"

        print(form_full_log_command(_type, cmd_hash, device, target_core, args, jump_list), end=end)

    return G_INFO_CONTAINER

def build_program(Program, line_indicator, JUMPLIST, Settings) -> list:
    """Returns builded instructions by solve function (will change raw command in to solved ones)"""
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        if core != "SHADER":
            for i, line in enumerate(Program[core]):
                try:
                    builded_program[core].append(solve(JUMPLIST[core], line))
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


def find_if_line_is_marked(line: int, JUMP_LIST: dict()):
        for key, val in JUMP_LIST.items():
            if val == line:
                return str(key)
        return None

def form_full_log_command(_type, formed_command, device, target_core, args, JUMP_LIST):
    """Will create standarised, redable command line with fancy synax and only with dec number representation"""
    if _type == "debug":
        return ""
    fancy_command = "Core[{}]: ".format(target_core)
    fancy_command = PROFILE.COMMANDSETFULL[formed_command]["name"]
    fancy_command += " "
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
            elif arg[1] == PROFILE.ADRESS_MODE_REMAP["adress"]:
                arg = get_mark_from_jump_adress(arg[0], JUMP_LIST)
            else:
                error.Unsupported("That shouldn't happen.")
            fancy_command += "{}, ".format(arg)
    return fancy_command[:-2]

def add_commands_to_end(builded_program: dict(), to_save: dict(), JUMP_LIST: dict()):
    for core in loading.KEYWORDS:
        program = builded_program[core].split('\n')
        longest = max(len(x) for x in program)
        program = [line+' '*(longest-len(line)) for line in program]

        RAW_CMD_ITER = iter(to_save[core])
        all_lines = ""
        for i, line in enumerate(program[1:-1]):
            RAW_CMD = next(RAW_CMD_ITER)
            while RAW_CMD[0] == 'debug':
                RAW_CMD = next(RAW_CMD_ITER)

            _type, formed_command, args = RAW_CMD
            line += " |  {}".format(form_full_log_command(_type, formed_command, None, loading.CORE_ID_MAP[core], args, JUMP_LIST[core]))
            marked_line = find_if_line_is_marked(i, JUMP_LIST[core])
            if marked_line is not None:
                line += "\t({})".format(marked_line)
            all_lines += line+'\n'
        builded_program[core] = all_lines
    return builded_program

def add_comments(builded_program: dict(), to_save: dict(), JUMP_LIST: dict()):
    return add_commands_to_end(builded_program, to_save, JUMP_LIST)


def extract_command_layout_data(CMD):
    command_layout, CMD, meta = list(CMD["command"].keys())[0], list(CMD["command"].values())[0], CMD["meta"]
    command_layout_sizes = PROFILE.ROM_SIZES["variants"][command_layout] if 'variants' in PROFILE.ROM_SIZES else PROFILE.ROM_SIZES
    return CMD, command_layout_sizes, meta

def get_compiled_cmd(COMMAND):
    #TODO MUCH WORK HERE
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
    def get_rom(PROFILE, CMD_PATTERN):
        if "variants" in PROFILE.COMMAND_LANE_PATTERN and len(PROFILE.COMMAND_LANE_PATTERN) == 1:
            try:
                bin_type = CMD_PATTERN["command_layout"]
            except KeyError:
                bin_type = 'default'
            rom_pattern = PROFILE.COMMAND_LANE_PATTERN["variants"][bin_type]
            return {"command":{bin_type:{key:None for key, val in rom_pattern.items()}},"meta":dict()}, bin_type
        raise error.ProfileStructureError("Sth is wrong")

    def get_bin_definition(ROM, CMD_PATTERN):
        for i in ROM.keys():
            if i in CMD_PATTERN["bin"]:
                return CMD_PATTERN["bin"][i]
        return CMD_PATTERN["bin"]
    CMD_PATTERN = PROFILE.COMMANDSETFULL[formed_command]
    ROM, rom_type = get_rom(PROFILE, CMD_PATTERN)

    try:
        layout = get_bin_definition(ROM, CMD_PATTERN)
        for key, value in layout.items():
            if type(value) is not str:
                ROM["command"][rom_type][key] = value
            else:
                ROM["command"][rom_type][key] = get_value_from_arg(value, CMD_PATTERN, args)
    except KeyError as err:
        raise error.ProfileStructureError("Can't find command profile ({}) in '{}' command.".format(err, CMD_PATTERN["name"]))
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
    #print(frame)
    pass

def get_raw(compiled):
    builded_program = {x:"" for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        for CMD in compiled[core]:
            CMD, command_layout_sizes, meta = extract_command_layout_data(CMD)
            line = ""
            for key, value in CMD.items():
                line += "{}".format(padbin(value,command_layout_sizes[key]["size"],prefix=False))
            SPACEING = 4
            line = ' '.join([line[i:i+SPACEING] for i in range(0, len(line), SPACEING)])
            builded_program[core] += line+'\n'
    return builded_program
def get_dec(compiled):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        #builded_program[core].append(str().join(['{}{}'.format(key," "*(val["size"]+6-len(key))) for key, val in PROFILE.ROM_SIZES.items()]))
        for CMD in compiled[core]:
            line = list()
            CMD, command_layout_sizes, meta = extract_command_layout_data(CMD)
            for key, value in CMD.items():
                line.append("{}".format(padbin(value,command_layout_sizes[key]["size"], prefix=False)))
                line.append("({})".format(paddec(value,3," ")))
            builded_program[core].append(line)
        builded_program[core] = tabulate(builded_program[core])
    return builded_program
def get_bin(compiled):
    builded_program = {x:[] for x in loading.KEYWORDS}
    for core in loading.KEYWORDS:
        for CMD in compiled[core]:
            CMD, command_layout_sizes, meta = extract_command_layout_data(CMD)
            line = list()
            for key, value in CMD.items():
                line.append("{}".format(padbin(value,command_layout_sizes[key]["size"],prefix=False)))
            builded_program[core].append(line)
        builded_program[core] = tabulate(builded_program[core])
    return builded_program