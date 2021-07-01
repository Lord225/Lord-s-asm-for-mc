import core.error as error
import core.loading as loading
import core.config as config
from enum import Enum
from core.analisers.debuger import *
from core.analisers.semantic import *
from core.analisers.generate import *


class TYPE(Enum):
    MOV         = 0
    ALU_ONE_ARG = 1 
    ALU_TWO_ARG = 2 
    JUMP        = 3 
    CALL        = 4 
    OTHER       = 5 
    DEBUG       = 6 


def replace_fancy_commands(cmd, _type, args):
    cmdhash = get_command_hash(cmd, _type, args)
    if "parent" in base.PROFILE.COMMANDSETFULL[cmdhash]:
        try:
            parent = base.PROFILE.COMMANDSETFULL[base.PROFILE.COMMANDSETFULL[cmdhash]["parent"]]
        except KeyError as err:
            raise error.ProfileStructureError("command is parented to '{}', but it doesn't exist.".format(base.PROFILE.COMMANDSETFULL[cmdhash]["parent"]))
        cmd, _type = parent["name"], parent["type"]
        args_new = []
        for arg_patt, arg_old in zip(parent["args"], args):
            args_new.append((arg_old[0], arg_patt["type"]))
        args = args_new
    return cmd, _type, args



def solve(JUMP_MAP: dict, command:str):
    cmd, _type = get_command_name(command)
    if _type == "debug":
        return _type, cmd, []
    else:
        if len(command[len(cmd):]) != 0:
            args = [get_argument_type(arg.strip(), JUMP_MAP) for arg in command[len(cmd):].strip().split(",")]
        else:
            args = []
            
    base.check_argument_ranges(args)

    if config.USE_FANCY_SYNAX:
        cmd, _type, args = replace_fancy_commands(cmd, _type, args)

    cmd_hash = get_command_hash(cmd, _type, args)

    return _type, cmd_hash, args

def execute(_type, cmd_hash, device, target_core, args, thread, jump_list):
    """Will execute builded commad on device"""
    base.reset_G_INFO_CONTAINER()
    if _type == "debug":
        execute_debug_command(device, target_core, cmd_hash)
        base.G_INFO_CONTAINER["skip"] = True
        return base.G_INFO_CONTAINER
        
    try:
        unpacked_args = [arg[0] for arg in args]
        base.PROFILE.COMMAND_MAP[cmd_hash](device.CORES[target_core], *unpacked_args)
    except error.EmulatorError as err:
        raise error.EmulatorError("Emulator throws an exeption: '{}'".format(err))
    except Exception as err:
        raise error.Unsupported("Unknown Emulator error: '{}'".format(err))   

    if config.LOG_COMMAND_MODE:
        end = "\n" if thread is None or config.FORCE_COMMANDS_IN_SEPERATE_ROWS else "\t"

        print(form_full_log_command(_type, cmd_hash, device, target_core, args, jump_list), end=end)

    return base.G_INFO_CONTAINER

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


def form_full_log_command(_type, formed_command, device, target_core, args, JUMP_LIST):
    """Will create standarised, redable command line with fancy synax and only with dec number representation"""
    if _type == "debug":
        return ""
    
    fancy_command = base.PROFILE.COMMANDSETFULL[formed_command]["name"]
    fancy_command += " "
    if len(args) != 0:
        for arg in args:
            if arg[1] == base.PROFILE.ADRESS_MODE_REMAP["const"]:
                arg = "{}".format(arg[0])
            elif arg[1] == base.PROFILE.ADRESS_MODE_REMAP["ram"]:
                arg = "ram[{}]".format(arg[0])
            elif arg[1] == base.PROFILE.ADRESS_MODE_REMAP["reg"]:
                arg = "reg[{}]".format(arg[0])
            elif arg[1] == base.PROFILE.ADRESS_MODE_REMAP["ptr"]:
                arg = "ram[reg[{}]]".format(arg[0])
            elif arg[1] == base.PROFILE.ADRESS_MODE_REMAP["adress"]:
                arg = get_mark_from_jump_adress(arg[0], JUMP_LIST)
            else:
                error.Unsupported("That shouldn't happen.")
            fancy_command += "{}, ".format(arg)
        fancy_command = fancy_command[:-2]
    return fancy_command

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



