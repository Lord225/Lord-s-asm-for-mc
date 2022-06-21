import core.config as config
from core.context import Context
import core.error as error
from core.load.base import Line
from core.parse.match_commands import match_expr
from core.parse.generate import eval_space
from core.parse.tokenize import tokenize
from core.profile import patterns
from core.profile.profile import Profile


def serach_for_macros(line_obj, profile: Profile, context: Context):
    for name, pattern in profile.macro_definitions.items():
        pattern_instance: patterns.Pattern = pattern['pattern']
        
        matched = match_expr.match_expr(pattern_instance, line_obj, context)
        if matched is not None:
            return name, matched
    else:
        return None

def __process(process: dict, args: dict):
    for key, val in process.items():
        args[key] = eval_space(args, val)
    return args

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

def expand_macros_recurent(program, context: Context, limit):
    if limit == 0:
        raise error.ParserError(None, "Macro recursion limit exeeded.")

    profile: Profile = context.get_profile()

    new_program = list()

    modified = False

    for line in program:
        matched_macro = serach_for_macros(line, profile, context)
        
        if matched_macro is None:
            new_program.append(line)
            continue

        expanded = [wrap_line(exp, line) for exp in __subtitue(matched_macro, profile)]

        expanded, context = tokenize(expanded, context)

        expanded = [l for l in expanded if len(l.tokenized) != 0]

        new_program.extend(expanded)
        
        modified = True
    
    if modified:
        return expand_macros_recurent(new_program, context, limit-1)
    else:
        return new_program

def expand_procedural_macros(program, context: Context):
    profile: Profile = context.get_profile()
    if profile.macro_definitions is None:
        return program, context

    new_program = expand_macros_recurent(program, context, config.macro_recursion_limit)
    
    return new_program, context