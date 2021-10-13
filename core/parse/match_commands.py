from cv2 import line
import core.profile.profile as profile
import core.profile.patterns as patterns
import core.parse.match_expr as match_expr
import core.config as config
import core.error as error

def serach_for_command(line_obj, profile: profile.Profile, context):
    tokens = line_obj.tokenized

    for name, pattern in profile.commands_definitions.items():
        pattern: patterns.Pattern = pattern
        
        matched = match_expr.match_expr(pattern['pattern'], tokens, context)
        if matched is not None:
            return name, matched
    else:
        return None

def find_commands(program, context):
    cpu_profile: profile.Profile = context['profile']
    
    for line_obj in program:
        founded = serach_for_command(line_obj, cpu_profile, context)
        if founded is None and config.rise_on_unknown_command:
            raise error.ParserError(line_obj.line_index_in_file, f"Cannot parse command: '{line_obj.line}'")
        
        line_obj.mached_command = founded

    return program, context