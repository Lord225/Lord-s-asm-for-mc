import core.config as config
import core.error as error
from core.load.base import Line
from core.parse import match_expr
from core.parse.generate import eval_space
from core.profile import patterns
from core.profile.profile import Profile


def serach_for_macros(line_obj, profile: Profile, context):
    for name, pattern in profile.macro_definitions.items():
        pattern_instance: patterns.Pattern = pattern['pattern']
        
        matched = match_expr.match_expr(pattern_instance, line_obj, context)
        if matched is not None:
            return name, matched
    else:
        return None

def __process(process: dict, args: dict):
    output = dict()
    for key, val in process.items():
        output[key] = eval_space(args, val)
    return output

def __subtitue(match, profile: Profile):
    name: str = match[0]
    arg_map: dict = match[1]

    macro = profile.macro_definitions[name]

    expansion = macro['expansion']
    process = macro['process']

    arg_map.update(__process(process, arg_map))

    expansion_list = list()

    for cmd in expansion:
        cmd: str = cmd

        expansion_list.append(cmd.format_map(arg_map))

    return expansion_list

def wrap_line(newline, line):
    return Line(newline, line_index_in_file=line.line_index_in_file, is_macro_expanded=True)

def expand_macros(program, context):
    profile: Profile = context['profile']

    new_program = list()

    for line in program:
        matched_macro = serach_for_macros(line, profile, context)
        
        if matched_macro is None:
            new_program.append(line)
            continue

        expanded = __subtitue(matched_macro, profile)

        new_program.extend([wrap_line(exp, line) for exp in expanded])
    
    return new_program, context