import core.error as error
import core.loading as loading
import core.config as config
import core.analisers.parser as parse
import core.analisers.base as base


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
        return parse.get_value(raw_argument), base.PROFILE.ADRESS_MODE_REMAP["const"]
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
            return parse.extract_number_from_bracets(raw_argument[_reg_start:]), base.PROFILE.ADRESS_MODE_REMAP["ptr"]
        else:
            #const
            return parse.extract_number_from_bracets(raw_argument), base.PROFILE.ADRESS_MODE_REMAP["ram"]
    elif "reg" in raw_argument:
        return parse.extract_number_from_bracets(raw_argument), base.PROFILE.ADRESS_MODE_REMAP["reg"]
    else:
        if raw_raw_argument in JUMP_LIST:
            return get_jump_adress(raw_raw_argument, JUMP_LIST),  base.PROFILE.ADRESS_MODE_REMAP["adress"]
        #probably custom arguments
        for key, val in base.PROFILE.ADRESS_MODE_REMAP.items():
            if key in raw_argument:
                return parse.extract_number_from_bracets(raw_argument), val
        raise error.SynaxError("Cannot interpretate value: {}".format(raw_argument))

def get_command_hash(cmd, _type, args) -> str:
    """return hash of this command (accepted by) COMMAND_MAP"""

    for command_pattern in base.PROFILE.COMMANDS_OREDERD_BY_TYPES[_type]:
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
        raise error.UndefinedCommand("Can't match command: '{}' with arguments: {}".format(cmd, [base.PROFILE.ADRESS_MODE_REMAP_REVERSED[arg[1]] for arg in args]))

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