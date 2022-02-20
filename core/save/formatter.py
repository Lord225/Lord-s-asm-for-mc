import core.error as error
import core.config as config
from core.profile.profile import Profile

def padhex(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0x' if prefix else '', "0"*(pad-len(hex(x)[2:])), hex(x)[2:])

def padbin(x, pad, prefix = True):
    x = 0 if x is None else x
    value = bin(x if x>=0 else x+(1<<pad))[2:]
    return '{}{}{}'.format('0b' if prefix else '', "0"*(pad-len(value)), value)

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

def binary(x, size):
    output = padbin(x, size, False)
    if len(output) != size:
        raise error.ParserError(None, f"Argument of value: {x} ({len(output)} bits) cannot be parsed with {size} bits.")
    return output

def reversed_binary(x, size):
    return "".join((x for x in reversed(binary(x, size))))

def one_hot(x, size):
    return binary(2**x, size)

def reversed_one_hot(x, size):
    return reversed_binary(2**x, size)

def unsigned_binary(x, size):
    if x < 0:
        raise error.ParserError(None, f"Cannot parse value: {x} as unsigned.")
    output = padbin(x, size, False)
    if len(output) != size:
        raise error.ParserError(None, f"Argument of value: {x} ({len(output)} bits) cannot be parsed with {size} bits.")
    return output
def sign_module_binary(x, size):
    if size <= 1:
        raise error.ParserError(None, "Cannot use value of lenght 1 for sign module.")
    output = f"{'0' if x >= 0 else '1'}{padbin(abs(x), size-1, False)}"
    if len(output) != size:
        raise error.ParserError(None, f"Argument of value: {x} ({len(output)} bits) cannot be parsed with {size} bits.")
    return output

def u2_module_binary(x, size):
    output = padbin(x, size, False)
    if x > 2**size or x <= -(2**size):
        raise error.ParserError(None, f"Argument of value: {x} cannot be parsed as {size} bit u2 number")
    return output
def get_encoding(layout):
    if "encoding" not in layout:
        return binary
    transform_type = layout["encoding"]

    if transform_type == "bin":
        return binary
    elif transform_type == "rev":
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
        pass 
    
    print("WARNING LAYOUT ENCODING NOT FOUND")            #TODO Warnings in warnings context (modify pipeline execution)
    return binary

def encode_argument(layout, name, val):
    encoding = get_encoding(layout[name])
    try:
        return "{}".format(encoding(val, layout[name]["size"]))
    except error.ParserError as err:
        raise error.ParserError(None, f"{err.info}, Encoding: {encoding.__name__}, Argument: {name}")

def get_py(program, context):
    """Returns program line as dict"""
    parsed = program['parsed_command']
    meta = {'mached': program['mached_command']}
    profile: Profile = context['profile']
    layouts = profile.arguments

    if 'debug' in program:
        meta['debug'] = program['debug']
    encoded = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            encoded.append(encode_argument(layout, name, val))
    value = as_values(encoded, profile.adressing.bin_len)
    return {'data':parsed, 'meta':meta, 'adress':program['physical_adress'], 'encoded':encoded, 'value':value}


def get_bin(program, context):
    """Returns program written in binary (padded on arguments)"""
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append(encode_argument(layout, name, val))
    return line

def get_pad(program, context):
    """Returns program written in binary padded to byte"""
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append(encode_argument(layout, name, val))
    return wrap(''.join(line), 8)

def get_raw(program, context):
    """Returns program written in hex padded to bytes"""
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append(encode_argument(layout, name, val))
    values = wrap(''.join(line), 8)
    return [padhex(int(val, base=2), 2, False) for val in values]


def format_output(program, context):
    if config.save == 'py':
        formatter_function, req_tabulate = get_py, False
    elif config.save == 'bin':
        formatter_function, req_tabulate = get_bin, True
    elif config.save == 'pad' or config.save == "schem":
        formatter_function, req_tabulate = get_pad, True
    elif config.save == 'raw':
        formatter_function, req_tabulate = get_raw, True
    else: 
        raise 

    for _, program_lines in program.items():
        for line in program_lines:
            try:
                line.formatted = formatter_function(line, context)
            except error.ParserError as err:
                raise error.ParserError(line.line_index_in_file, err.info)

    context['tabulate'] = req_tabulate

    return program, context
    