import core.error as error
import core.loading as loading
import core.config as config
from tabulate import tabulate
from core.analisers.parser import *


def calculate_phisical_adresses_of_commands(builded_commands, offset: int):
    counter = offset
    offsets = []
    for cmd in builded_commands:
        cost = 0 if cmd[0] == 'debug' else base.PROFILE.COMMANDSETFULL[cmd[1]]["command_cost"]
        offsets.append(counter)
        counter += cost
    return offsets
def get_compiled_cmd(COMMAND, offsets):
    #TODO MUCH WORK HERE
    if type(COMMAND) is tuple:
        _type, formed_command, args = COMMAND
    else:
        raise error.Unsupported("Muli-lined commands")
        #call custom generate func from 'emul'
    def get_value_from_arg(name, CMD_PATTERN, args, adresses):
        for i, arg in enumerate(CMD_PATTERN["args"]):
            if arg["name"] == name:
                if arg["type"] != 4:
                    return args[i][0] #none adress
                else:
                    return adresses[args[i][0]+1]
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
    CMD_PATTERN = base.PROFILE.COMMANDSETFULL[formed_command]
    ROM, rom_type = get_rom(base.PROFILE, CMD_PATTERN)

    try:
        layout = get_bin_definition(ROM, CMD_PATTERN)
        for key, value in layout.items():
            if type(value) is not str:
                ROM["command"][rom_type][key] = value
            else:
                ROM["command"][rom_type][key] = get_value_from_arg(value, CMD_PATTERN, args, offsets)
    except KeyError as err:
        raise error.ProfileStructureError("Can't find command profile ({}) in '{}' command.".format(err, CMD_PATTERN["name"]))
    except Exception as err:
        raise error.ProfileStructureError("Undefined error while compiling: {}".format(err))
    return ROM
def get_compiled(builded_commands, offset: int):
    """Converts builded instructions into binary"""
    builded_program = {x:[] for x in loading.KEYWORDS}

    for core in loading.KEYWORDS:
        offsets = calculate_phisical_adresses_of_commands(builded_commands[core], offset)
        for COMMAND in builded_commands[core]:
            if COMMAND[0] == "debug":
                continue
            builded_program[core].append(get_compiled_cmd(COMMAND, offsets))
    return builded_program

def extract_command_layout_data(CMD):
    command_layout, CMD, meta = list(CMD["command"].keys())[0], list(CMD["command"].values())[0], CMD["meta"]
    command_layout_sizes = base.PROFILE.ROM_SIZES["variants"][command_layout] if 'variants' in base.PROFILE.ROM_SIZES else base.PROFILE.ROM_SIZES
    return CMD, command_layout_sizes, meta


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