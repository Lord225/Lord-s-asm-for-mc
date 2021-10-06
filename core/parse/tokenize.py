import core.error as error
import core.config as config
import core.parse.base as parser_base
import re

TOKENIZE_PATTERN = re.compile("(\W|\s)")
USELSESS = ' '

def tokienize_line(line: str):
    return re.split(TOKENIZE_PATTERN, line)

def remove_meaningless_tokens(tokens):
    return [token for token in tokens if token not in USELSESS]

def tokenize(program, context):
    for line_obj in program:
        line: str = line_obj.line
        line_obj.tokenized = remove_meaningless_tokens(tokienize_line(line))
    return program, context
