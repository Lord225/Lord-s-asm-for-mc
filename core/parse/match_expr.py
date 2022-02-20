from dis import dis
from typing import List, Optional
import Levenshtein
import core.profile.profile as profile
import core.profile.patterns as patterns
import core.parse as parse
import core.error as error

def match_word(pattern_token, expr_token):
    return pattern_token[1] != expr_token


def parse_argument_token(context, pattern_token, expr_token, line):
    parsed_token = None
    if pattern_token[2] == patterns.ArgumentTypes.NUM:
        parsed_token = parse.parse_number(expr_token)
    elif pattern_token[2] == patterns.ArgumentTypes.LABEL:
        parsed_token = parse.parse_label(expr_token, context)
    elif pattern_token[2] == patterns.ArgumentTypes.ANY_STR:
        parsed_token = expr_token
    elif pattern_token[2] == patterns.ArgumentTypes.OFFSET_LABEL:
        parsed_token = parse.parse_offset_label(expr_token, context, line)
    elif pattern_token[2] == patterns.ArgumentTypes.HEX_NUM:
        parsed_token = parse.parse_hex(expr_token)
    elif pattern_token[2] == patterns.ArgumentTypes.BIN_NUM:
        parsed_token = parse.parse_bin(expr_token)
    elif pattern_token[2] == patterns.ArgumentTypes.DEC_NUM:
        parsed_token = parse.parse_dec(expr_token)
    elif pattern_token[2] == patterns.ArgumentTypes.QUOTE_STR:
        parsed_token = parse.parse_quote_str(expr_token, context)
    else:
        raise
    return parsed_token


def match_expr(pattern: profile.patterns.Pattern, line, context: Optional[dict]):
    args = dict()
    expr = line.tokenized

    if len(pattern.tokens) != len(expr):
        return None
    for pattern_token, expr_token in zip(pattern.tokens, expr):
        if pattern_token[0] == patterns.TokenTypes.LITERAL_WORD:
            if match_word(pattern_token, expr_token):
                return None
        elif pattern_token[0] == patterns.TokenTypes.ARGUMENT:
            parsed_token = parse_argument_token(context, pattern_token, expr_token, line)
            if parsed_token is None:
                return None
            args[pattern_token[1]] = parsed_token
    return args


def soft_word_match(token, expr_token, context):
    distance = Levenshtein.distance(token, expr_token)
    return distance

    
def soft_match_expr(pattern:profile.patterns.Pattern, line, context: dict):
    expr = line.tokenized

    output = list()
    len_diff = abs(len(pattern.tokens)-len(expr))
    if len_diff == 0:
        lenght_bias = 0
    elif len_diff == 1:
        lenght_bias = 0
    elif len_diff == 2:
        lenght_bias = 2
    else:
        lenght_bias = len_diff        

    for offset in range(max(len(pattern.tokens), len(expr))):
        command_cost = lenght_bias
        misses = []
        if offset != 0:
            command_cost += 0.2*offset if offset > 2 else 0
        
        for i in range(min(len(pattern.tokens), len(expr))):
            
            if offset == 0:
                pattern_token = pattern.tokens[i]
                expr_token = expr[i]
            elif offset > 0:
                if i+offset < len(pattern.tokens):
                    pattern_token = pattern.tokens[i+offset]
                    expr_token = expr[i]
                else:
                    break
            else:
                offset = -offset
                if i+offset < len(expr):
                    pattern_token = pattern.tokens[i]
                    expr_token = expr[i+offset]
                else:
                    break
        
            if pattern_token[0] == patterns.TokenTypes.LITERAL_WORD:
                dis = soft_word_match(pattern_token[1], expr_token, context)
                if dis != 0:
                    if expr_token in pattern_token[1] or pattern_token[1] in expr_token:
                        command_cost += 0.2
                    else:
                        command_cost += 0.5     
                    misses.append(f"'{pattern_token[1]}' != '{expr_token}'")
                else:
                    command_cost -= 0.1
            elif pattern_token[0] == patterns.TokenTypes.ARGUMENT:
                parsed_token = parse_argument_token(context, pattern_token, expr_token, line)
                if parsed_token is None:
                    misses.append(f"'{expr_token}' cannot be parsed as {pattern_token[2]}")
                    command_cost += 0.5
                else:
                    command_cost -= 0.1
        if len_diff != 0:
            misses.append(f"Missing token")
        output.append({'offset': offset, 'cost': float(command_cost+abs(1.5*offset))/max(len(pattern.tokens), len(expr)), 'missmaches': misses})
    return output
