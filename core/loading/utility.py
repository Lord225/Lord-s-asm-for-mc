import re

def smart_replace(line: str, From: str, To: str):
    line = re.sub("(?<![a-zA-Z0-9])({})(?![a-zA-Z0-9])".format(From), To, line)
    return line

def smart_find(line: str, From: str):
    finded = re.search("(?<![a-zA-Z0-9])({})(?![a-zA-Z0-9])".format(From),line)
    return finded
