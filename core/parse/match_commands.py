from core.context import Context
import core.profile.profile as profile
import core.profile.patterns as patterns
import core.parse.match_expr as match_expr
import core.config as config
import core.error as error

def serach_for_command(line_obj, profile: profile.Profile, context: Context):
    for name, pattern in profile.commands_definitions.items():
        pattern_instance: patterns.Pattern = pattern['pattern']
        
        matched = match_expr.match_expr(pattern_instance, line_obj, context)
        if matched is not None:
            return name, matched
    else:
        return None


def find_commands(program, context: Context):
    cpu_profile: profile.Profile = context.get_profile()
    
    for line_obj in program:
        founded = serach_for_command(line_obj, cpu_profile, context)
        
        if founded is None and config.why_error:
            output = serach_harder_for_command(line_obj, cpu_profile, context)
            print(line_obj)
            raise error.ParserError(line_obj.line_index_in_file, f"Cannot parse command: '{line_obj.line}', Maybe you meant: {summarise_best_fit(output, context)}", line_object=line_obj)
        if founded is None and config.rise_on_unknown_command:
            raise error.ParserError(line_obj.line_index_in_file, f"Cannot parse command: '{line_obj.line}', Use --why to use fuzzy search to get more info", line_object=line_obj)
        
        line_obj.mached_command = founded

    return program, context


def summarise_best_fit(best_fit, context: Context):
    cpu_profile: profile.Profile = context.get_profile()
    best_cmd = cpu_profile.commands_definitions[best_fit[0]]
    new_line = "\n *  "
    missmaches = best_fit[1]['missmaches'][:1]
    message = f"'{best_cmd['pattern'].summarize()}'\nCommand differs with: {new_line}{new_line.join(missmaches)}"
    return message


def serach_harder_for_command(line_obj, profile: profile.Profile, context: Context):
    output = dict()
    for name, pattern in profile.commands_definitions.items():
        pattern_instance: patterns.Pattern = pattern['pattern']
        output[name] = match_expr.soft_match_expr(pattern_instance, line_obj, context)
    

    best_offsets = {key:min(val, key=lambda x: x['cost']) for key, val in output.items()}
    
    #pp(best_offsets)
    
    best_fit = min(best_offsets.items(), key = lambda x: x[1]['cost'])
    return best_fit

