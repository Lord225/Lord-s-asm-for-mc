from typing import Dict, List, Tuple
import core.error as error
import core.config as config
import core.parse.base as parser_base



def get_metadata(program, context):
    context['entry'] = {}
    for program_line in program:
        line: str = program_line.line
        if line.startswith("#profile"):
            _, *args = line.split(' ')
            profile_name = ''.join(args)
            if profile_name:
                if 'profile_name' in context:
                    raise
                context["profile_name"] = profile_name
            else:
                raise
        elif line.startswith("#init"):
            _, *args = line.split(' ')
            settings = ''.join(args)
            if settings:
                if 'init' not in context:
                    context["init"] = [settings]
                else:
                    context["init"].append(settings)
            else:
                raise
        elif line.startswith("#global"):
            try:
                _, chunk_name, label_name, offset = line.split()
            except:
                raise error.PreprocesorError(program_line.line_index_in_file, f"Expected structure '#global <NAME> <LABEL NAME> <OFFSET>' got: '{line}'")
            context['entry'][chunk_name] = (label_name, offset)
    return program, context

KNOWON_PREPROCESOR_TOKENS = \
[ 
    "#profile",
    "#init",
    "#ifdef",
    "#else",
    "#endif",
    "#macro",
    "#endmacro",
    "#global",
]

DEBUG_TOKEN = "#debug"

def remove_known_preprocesor_instructions(program, context):
    output_program = list()
    context['debug'] = []
    for program_line in program:
        line : str = program_line.line
        if any((line.startswith(token) for token in KNOWON_PREPROCESOR_TOKENS)):
            continue
        
        if line.startswith(DEBUG_TOKEN):
            context['debug'].append(program_line)
            continue
        
        output_program.append(program_line)
    return output_program, context
    