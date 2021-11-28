import core.error as error
import core.config as config
from textwrap import wrap
from core.profile.profile import Profile

def padhex(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0x' if prefix else '',"0"*(pad-len(hex(x)[2:])),hex(x)[2:])
def padbin(x, pad, prefix = True):
    x = 0 if x is None else x
    return '{}{}{}'.format('0b' if prefix else '',"0"*(pad-len(bin(x)[2:])),bin(x)[2:])
def paddec(x, pad, fill = "0"):
    x = 0 if x is None else x
    return '{}{}'.format(fill*(pad-len(str(x))), str(x))

def get_py(program, context):
    parsed = program['parsed_command']
    meta = {'mached': program['mached_command']}
    if 'debug' in program:
        meta['debug'] = program['debug']
    return {'data':parsed, 'meta':meta, 'adress':program['physical_adress']}


def get_bin(program, context):
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append("{}".format(padbin(val,layout[name]["size"],prefix=False)))
        return line


def get_dec(program, context):
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append("{}".format(padbin(val, layout[name]["size"],prefix=False)))
            line.append("({})".format(paddec(val, 3," ")))
        return line


def get_pad(program, context):
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append("{}".format(padbin(val, layout[name]["size"],prefix=False)))
        return wrap(''.join(line), 8)


def get_raw(program, context):
    profile: Profile = context['profile']
    layouts = profile.arguments

    parsed = program['parsed_command']
    line = list()
    for layout, args in parsed.items():
        layout = layouts[layout]
        for name, val in args.items():
            line.append("{}".format(padbin(val, int(layout[name]["size"]) ,prefix=False)))
        values = wrap(''.join(line), 8)
        return [f'{int(val, base=2):02x}' for val in values]


def format_output(program, context):
    if config.save == 'py':
        formatter_function, req_tabulate = get_py, False
    elif config.save == 'bin':
        formatter_function, req_tabulate = get_bin, True
    elif config.save == 'dec':
        formatter_function, req_tabulate = get_dec, True
    elif config.save == 'pad':
        formatter_function, req_tabulate = get_pad, True
    elif config.save == 'raw':
        formatter_function, req_tabulate = get_raw, True
    else: 
        raise 

    for _, program_lines in program.items():
        for line in program_lines:
            line.formatted = formatter_function(line, context)
    context['tabulate'] = req_tabulate

    return program, context


