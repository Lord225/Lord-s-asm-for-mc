from tempfile import TemporaryFile
from .base import *
from . import tokenize as tokenize
from . import match_commands as match_commands
from . import jumps as jumps
from . import debug_heades as debug_heades
from . import split_into_chunks as split_into_chunks
from . import generate as generate
from . import assert_arguments as assert_arguments

def parse_number(token):
    try:
        return get_value(token)
    except:
        return None

def parse_label(token, labels):
    return labels[token]