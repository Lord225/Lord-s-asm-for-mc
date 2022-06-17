import core.error as error
import core.config as config
import core.parse.base as parser_base
import re

TOKENIZE_PATTERN = re.compile(r"(\W|\s)")
USELSESS = ' '

def tokienize_str(string):
    return re.split(TOKENIZE_PATTERN, string)

def tokienize_line(line):
    line.tokenized = tokienize_str(line.line)
    return line

def remove_meaningless_tokens_list(tokens_list):
    return [str(token) for token in tokens_list if token not in USELSESS]

def remove_meaningless_tokens(line):
    line.tokenized = remove_meaningless_tokens_list(line.tokenized)
    return line

def join_sign_expressions(line):
    tokens = line.tokenized
    output = list()
    i = 0
    while i < len(tokens):
        if tokens[i] == '-':
            try:
                parser_base.get_value(tokens[i+1])
                output.append(f"-{tokens[i+1]}")
                i += 2
                continue
            except:
                pass
        output.append(tokens[i])
        i += 1
    line.tokenized = output
    return line

def join_string(line):
    """
    Joins tokens between euotes:
    `['a', 'b', '"', ' ', "c". '"'] => ['a', 'b', '" c"']
    """
    tokens = line.tokenized
    state = False
    output = list()
    joined = ""
    for i in range(len(tokens)):
        if tokens[i] == '"':
            if state:
                output.append(f'"{joined}"')
                joined = ""
            state = not state 
            continue
        if state:
            joined += tokens[i]
        else:
            output.append(tokens[i])
    if state:
        raise error.ParserError(line.line_index_in_file, 'Expected \'"\'')
    line.tokenized = output
    return line
    
def tokenize(program, context):
    for line_obj in program:
        line_obj = remove_meaningless_tokens(join_sign_expressions(join_string(tokienize_line(line_obj))))
    return program, context
