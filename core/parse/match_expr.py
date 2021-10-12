from typing import List
import core.profile.profile as profile
import core.profile.patterns as patterns
import core.parse as parse


def match_expr(pattern:profile.patterns.Pattern, expr: List, cmds_profile: profile.Profile):
    args = dict()
    if len(pattern.tokens) != len(expr):
        return None
    for pattern_token, expr_token in zip(pattern.tokens, expr):
        if pattern_token[0] == patterns.TokenTypes.LITERAL_WORD:
            if pattern_token[1] != expr_token:
                return None
        elif pattern_token[0] == patterns.TokenTypes.ARGUMENT:
            parsed_token = None
            if pattern_token[2] == patterns.ArgumentTypes.NUM:
                parsed_token = parse.parse_number(expr_token)
            elif pattern_token[2] == patterns.ArgumentTypes.LABEL:
                parsed_token = parse.parse_label(expr_token, cmds_profile.labels)
            elif pattern_token[2] == patterns.ArgumentTypes.ANY_STR:
                parsed_token = expr_token
            
            if parsed_token == None:
                return None
            args[pattern_token[1]] = parsed_token
    return args

def format_expr(pattern: profile.patterns.Pattern, args: dict):
    pass