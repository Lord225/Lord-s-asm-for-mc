import core.config as config
from core.context import Context
import core.error as error
from core.load.base import Line
from core.parse.match_commands import match_expr
from core.parse.generate import eval_space
from core.parse.tokenize import tokenize
from core.profile import patterns
from core.profile.profile import Profile
from copy import deepcopy

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
        try:
            args[key] = eval_space(args, val)
        except Exception as e:
            raise error.ParserError(None, f"Expression '{val}' rised an exeption: '{e}' with args: '{args}'")
    return args

def __subtitue(match, profile: Profile):
    name: str = match[0]
    arg_map: dict = match[1]

    macro = profile.macro_definitions[name]

    expansion = macro['expansion'] if 'expansion' in macro else list()
    process = macro['process'] if 'process' in macro else dict()

    arg_map.update(__process(process, arg_map))

    expansion_list = list()

    for cmd in expansion:
        cmd: str = cmd

        expansion_list.append(cmd.format_map(arg_map))

    return expansion_list

def wrap_line(newline, line: Line, expanded_command):
    expanstion = line.expanded_command if 'expanded_command' in line else list()
    expanstion = deepcopy(expanstion)
    expanstion.append(expanded_command)
    return Line(newline, line_index_in_file=line.line_index_in_file, is_macro_expanded=True, expanded_command=expanstion)

def expand_macros_recurent(program, context: Context, limit, expanded_indexes, macro_stack=None):
    if limit == 0:
        raise error.ParserError(None, "Macro recursion limit exceeded.")

    if macro_stack is None:
        macro_stack = []

    profile: Profile = context.get_profile()

    new_program = list()
    new_expanded_indexes = set()

    modified = False
    
    for i, line in enumerate(program):
        if i not in expanded_indexes:
            new_program.append(line)
            continue

        matched_macro = serach_for_macros(line, profile, context)
        
        if matched_macro is None:
            new_program.append(line)
            continue

        macro_stack.append((line.line_index_in_file, line.line, matched_macro[0]))

        try:
            expanded_command =  __subtitue(matched_macro, profile)
            expanded = [wrap_line(exp, line, line.line) for exp in expanded_command]
        except error.ParserError as e:
            macro_traceback = " -> ".join([f"line {idx}: {line}" for idx, line, macro in macro_stack])
            raise error.ParserError(line.line_index_in_file, f"Error while expanding macro: {e}\nThis error originates from:\n{macro_traceback}\nOriginal Line: '{line.line}'")

        expanded, context = tokenize(expanded, context)

        expanded = [l for l in expanded if len(l.tokenized) != 0]

        new_expanded_indexes.update(range(len(new_program), len(new_program)+len(expanded)))
        new_program.extend(expanded)

        modified = True

        macro_stack.pop()
    
    if modified:
        return expand_macros_recurent(new_program, context, limit-1, new_expanded_indexes, macro_stack)
    else:
        return new_program

def expand_procedural_macros(program, context: Context):
    profile: Profile = context.get_profile()
    if profile.macro_definitions is None:
        return program, context
    
    new_program = expand_macros_recurent(program, context, config.macro_recursion_limit, set(range(len(program))))

    return new_program, context