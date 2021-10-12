import core.error as error
import core.config as config
import tabulate

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
    meta = dict()
    return str({'data':parsed, 'meta':meta})

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
def format_output(program, context):
    if config.save == 'py':
        formatter_function, req_tabulate = get_py, False
    elif config.save == 'bin':
        formatter_function, req_tabulate = get_bin, True
    elif config.save == 'dec':
        formatter_function, req_tabulate = get_dec, True
    else:
        pass

    for chunk, program_lines in program.items():
        for line in program_lines:
            line.formatted = formatter_function(line, context)
    context['tabulate'] = req_tabulate

    return program, context


