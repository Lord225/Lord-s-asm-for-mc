import core.error as error
import core.loading as loading
import core.config as config
import core.analisers.base as base


def padhex(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0x' if prefix else '',"0"*(pad-len(hex(x)[2:])),hex(x)[2:])
def padbin(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0b' if prefix else '',"0"*(pad-len(bin(x)[2:])),bin(x)[2:])
def paddec(x, pad, fill = "0"):
    x = 0 if x is None else x
    return '{}{}'.format(fill*(pad-len(str(x))), str(x))

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
        for i in base.PROFILE.COMMANDS_TYPES:
            for j in base.PROFILE.COMMANDS_OREDERD_BY_TYPES[i]:
                if j["name"] == cmd_splitted[0]:
                    return j["name"], i
    except KeyError as err:
        raise error.ProfileStructureError(err)
    except Exception as err:
        raise error.UndefinedCommand("Undefined error while searching for command: {}".format(err))
    raise error.UndefinedCommand(command)