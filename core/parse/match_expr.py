from typing import List

from tables import UnImplemented
import core.profile.profile as profile
import core.profile.patterns as patterns
import core.parse as parse
import core.error as error


def match_expr(pattern:profile.patterns.Pattern, expr: List, context: dict):
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
                parsed_token = parse.parse_label(expr_token, context)
            elif pattern_token[2] == patterns.ArgumentTypes.ANY_STR:
                parsed_token = expr_token
            elif pattern_token[2] == patterns.ArgumentTypes.OFFSET_LABEL:
                raise UnImplemented("ArgumentTypes.OFFSET_LABEL")
            elif pattern_token[2] == patterns.ArgumentTypes.HEX_NUM:
                raise UnImplemented("ArgumentTypes.HEX_NUM")
            elif pattern_token[2] == patterns.ArgumentTypes.BIN_NUM:
                raise UnImplemented("ArgumentTypes.BIN_NUM")
            elif pattern_token[2] == patterns.ArgumentTypes.DEC_NUM:
                raise UnImplemented("ArgumentTypes.DEC_NUM")
            else:
                raise

            if parsed_token is None:
                return None
            args[pattern_token[1]] = parsed_token
    return args