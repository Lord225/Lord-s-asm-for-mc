from threading import local
import core.error as error
import core.config as config
from core.profile.profile import Profile

def eval_space(args, evaluation):
    locals().update(args)

    return eval(evaluation)

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
                    output_line[arg_name] = eval_space(args, process_request)
                else:
                    raise error.ProfileLoadError(f"Binary map in '{name}'' cannot be resolved becouse of token: '{process_request}' with name '{arg_name}'")
                
                if output_line[arg_name] is None:
                    raise error.CompilerError(line_obj.line_index_in_file, f"Cannot evalate value: `{process_request}` with args: {args}")
                if not isinstance(output_line[arg_name], int):
                    raise error.ProfileLoadError(f"Evaluator: `{process_request}` returned None-integer value: {output_line[arg_name]} for args: {args}")
        line_obj.parsed_command = {cmd['command_layout']: output_line}
    return program, context

def generate_chunked(program, context):
    for _, program_chunk in program.items():
        program_chunk, _ = generate(program_chunk, context)
    return program, context