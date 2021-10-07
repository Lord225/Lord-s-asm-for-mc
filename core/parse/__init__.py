from .base import *
from . import tokenize as tokenize
from . import match_commands as match_commands

def parse_number(token):
    try:
        return get_value(token)
    except:
        return None

def parse_label(token, labels):
    pass