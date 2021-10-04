from typing import List, Dict
from .base import *

def remove_comments(lines: List[List[Line]], context: Dict):
    for line in lines:
        if "//" in line.line:
            line.line = line.line[:line.line.find("//")]
    return lines