from typing import List, Dict
from .base import *
import core.error as error
import core.config as config

def remove_comments(lines: List[Line], context: Dict):
    for line in lines:
        if "//" in line.line:
            line.line = line.line[:line.line.find("//")]
            if config.save_comments_after_lines:
                if line.line.find("//") != 0:
                    line.comment =  line.line[line.line.find("//"):]
    return lines