import core.error as error
import core.config as config
from core.profile.profile import Profile

def generate(program, context):
    profile: Profile = context['profile']
    layouts = profile.arguments
    cmds = profile.commands_definitions
    
    for line_obj in program:
        output_line = dict()
        name, args = line_obj.mached_command
        cmd = cmds[name]
        bin_map = cmd['bin']
        layout = layouts[cmd['command_layout']]
        for arg_name in layout.keys():
            if arg_name not in bin_map:
                output_line[arg_name] = 0
            else:
                process_request = bin_map[arg_name]
                if isinstance(process_request, int):
                    output_line[arg_name] = process_request
                elif isinstance(process_request, str):
                    output_line[arg_name] = args[process_request]
                elif isinstance(process_request, dict):
                    if 'eval' in process_request:
                        output_line[arg_name] = eval(process_request['eval'])
                    else:
                        raise error.ProfileLoadError(f"Binary map in '{name}'' cannot be resolved becouse of token: '{process_request}' with name '{arg_name}'") 
        line_obj.parsed_command = {cmd['command_layout']: output_line}
    return program, context

def generate_chunked(program, context):
    for _, program_chunk in program.items():
        program_chunk, _ = generate(program_chunk, context)
    return program, context