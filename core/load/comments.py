from typing import List
from core.context import Context
from .base import *
import core.error as error
import core.config as config

def remove_comments(lines: List[Line], context: Context):
    for line in lines:
        if "//" in line.line:
            if config.save_comments_after_lines:
                pos = line.line.find("//%")
                if pos > 0:
                    line.comment = line.line[pos+3:].strip()
            line.line = line.line[:line.line.find("//")]
    return lines