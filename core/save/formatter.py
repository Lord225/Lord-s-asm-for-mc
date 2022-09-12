from core.context import Context
import core.error as error
import core.config as config
from core.profile.profile import Profile
import pybytes

def into_binary(x, pad):
    return pybytes.Binary(x, lenght=pad)

def padhex(x, pad):
    val = pybytes.Binary(x, lenght=pad)
    return val.hex(prefix=False)

def padbin(x, pad):
    val = pybytes.Binary(x, lenght=pad)
    return val.bin(prefix=False)

def paddec(x, pad, fill = "0"):
    x = 0 if x is None else x
    return '{}{}'.format(fill*(pad-len(str(x))), str(x))

def split_by_n(seq, n):
    while len(seq) != 0:
        yield seq[-n:]
        seq = seq[:-n]
def wrap(seq, n):
    """
    Chunks sequence into chunks with size n, starting from end:

    `wrap("12345", n=2)` => `["1", "23", "45"]`
    """
    return list(split_by_n(seq, n))[::-1]
def as_values(seq, n: int):
    """Returns sequence of integers, where every integer is up to n bits long, based on binary value seq"""
    if not isinstance(seq, list):
        seq = [seq]
    return [int(chunk, base = 2) for chunk in wrap(''.join(seq), n)]

def binary(x, size) -> pybytes.Binary:
    try:
        return into_binary(x, size)
    except:
        raise error.ParserError(None, f"Argument of value: {x} ({len(into_binary(x, None))} bits) cannot be parsed to {size} bits.")
    
def reversed_binary(x, size):
    return pybytes.Binary([v for v in binary(x, size)]) # Reverse value

def one_hot(x, size):
    return binary(2**x, size)

def reversed_one_hot(x, size):
    return pybytes.Binary([v for v in one_hot(x, size)])

def unsigned_binary(x, size) -> pybytes.Binary:
    return pybytes.Binary(x, lenght=size, sign_behavior='unsigned')

def sign_module_binary(x, size):
    if x >= 0:
        return pybytes.Binary(x, lenght=size, sign_behavior='unsigned')
    else:
        return pybytes.Binary(x, lenght=size-1, sign_behavior='unsigned').append(True)

def u2_module_binary(x, size):
    return pybytes.Binary(x, lenght=size, sign_behavior='signed')
    
def get_encoding(layout):
    if "encoding" not in layout:
        return binary
    transform_type = layout["encoding"]

    if transform_type == "bin":
        return binary
    elif transform_type == "binrev":
        return reversed_binary
    elif transform_type == "onehot":
        return one_hot
    elif transform_type == "onehotrev":
        return reversed_one_hot
    elif transform_type == "unsignedbin":
        return unsigned_binary
    elif transform_type == "signmodulebin":
        return sign_module_binary
    elif transform_type == "u2bin":
        return u2_module_binary
    else:
        raise error.ProfileLoadError("Unknown encoding type: {}".format(transform_type))

def encode_argument(layout, name, val):
    encoding = get_encoding(layout[name])
    try:
        encoded = encoding(val, layout[name]["size"]).bin(prefix=False)
        if len(encoded) != layout[name]["size"]:
            raise error.ParserError(None, f"Cannot encode {val}, encoder returned invalid value.")
        return encoded
    except error.ParserError as err:
        raise error.ParserError(None, f"{err.info}, Encoding: {encoding.__name__}, Argument: {name}")

def get_py(program, context: Context):
    """Returns program line as dict"""
    parsed = program['parsed_command']
    meta = {'mached': program['mached_command']}
    profile: Profile = context.get_profile()
    layouts = profile.arguments

    if 'debug' in program:
        meta['debug'] = program['debug']
    encoded = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            encoded.append(encode_argument(layout, name, val))
    value = as_values(encoded, profile.adressing.bin_len)
    return {'data':parsed, 'meta':meta, 'adress': program['physical_adress'], 'encoded': encoded, 'value':value}


def get_bin(program, context: Context):
    """Returns program written in binary (padded on arguments)"""
    profile: Profile = context.get_profile()
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append(encode_argument(layout, name, val))
    return line

def get_pad(program, context: Context):
    """Returns program written in binary padded to byte"""
    line = get_bin(program, context)
    
    return wrap(''.join(line), 8)

def get_raw(program, context: Context):
    """Returns program written in hex padded to bytes"""
    values = get_pad(program, context)

    return [padhex(int(val, base=2), 8) for val in values]


def format_output(program, context: Context):
    
    if config.save == 'pip':
        formatter_function = get_py
    elif config.save == 'bin':
        formatter_function = get_bin
    elif config.save == 'pad' or config.save == "schem":
        formatter_function = get_pad
    elif config.save == 'hex':
        formatter_function = get_raw
    else: 
        raise error.CompilerError(None, "Unknown save format")

    for line in program:
        try:
            line.formatted = formatter_function(line, context)
        except error.ParserError as err:
            raise error.ParserError(line.line_index_in_file, err.info)
                
    return program, context
    