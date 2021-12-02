import core.error as error
import core.config as config
from core.profile.profile import Profile

def find_key_by_value(dict: dict, value):
    output = []
    for key, val in dict.items():
        if val == value:
            output.append(key)
    return output

def within_bounds(bit_size, value):
    if value >= 0:
        max_val = 2**bit_size - 1
        return value <= max_val
    else:
        min_val = -(2**bit_size)
        return value >= min_val

def assert_arguments_chunked(program, context):
    for _, program_chunk in program.items():
        program_chunk, _ = assert_arguments(program_chunk, context)
    return program, context

def assert_arguments(program, context):
    if not config.assert_argument_size:
        return program, context

    profile: Profile = context['profile']
    layouts = profile.arguments
    cmds = profile.commands_definitions
    
    for line_obj in program:
        name, args = line_obj.mached_command
        cmd = cmds[name]
        bin_map = cmd['bin']
        layout = layouts[cmd['command_layout']]
        for (args_name, value) in args.items():
            x = find_key_by_value(bin_map, args_name)
            if len(x) != 0:
                x = x[0]
            else:
                continue
            
            if not within_bounds(layout[x]['size'], value):
                raise error.ParserError(line_obj.line_index_in_file, f"Value '{value}' is not within bounds for argument: '{x}' in command: '{name}' (argument is {layout[x]['size']} bit long)")
    return program, context


