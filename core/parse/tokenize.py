import core.error as error
import core.config as config
import core.parse.base as parser_base
import re

TOKENIZE_PATTERN = re.compile(r"(\W|\s)")
USELSESS = ' '

def tokienize_line(line: str):
    return re.split(TOKENIZE_PATTERN, line)

def remove_meaningless_tokens(tokens):
    return [str(token) for token in tokens if token not in USELSESS]

def join_quote_str(tokens):
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
    return output
    
def tokenize(program, context):
    for line_obj in program:
        line: str = line_obj.line
        line_obj.tokenized = remove_meaningless_tokens(join_quote_str(tokienize_line(line)))
    return program, context
