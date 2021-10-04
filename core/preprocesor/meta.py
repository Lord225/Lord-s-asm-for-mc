from typing import Dict, List, Tuple
import core.error as error
import core.config as config
import core.parse.base as parser_base



def get_metadata(program, context):
    for program_line in program:
        line: str = program_line.line
        if line.startswith("#profile"):
            _, *args = line.split(' ')
            profile_name = ''.join(args)
            if profile_name:
                if 'profile' in context:
                    raise
                context["profile"] = profile_name
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
    return program, context


