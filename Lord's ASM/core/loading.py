import core.error as error
import json
import re

KEYWORDS = ["CORE0", "CORE1", "SHADER"]
CORE_ID_MAP = {"CORE0":0, "CORE1":1, "CORE2":2, "CORE3":3, "SHADER":4}

DEFINITION_DEBUG = False

def load_program(path : str, definitions: list = []):
    Program = []
    Settings = []
    with open(path,"r") as file:
        for i, line in enumerate(file):
            if line[0] == '[' and line[-2] == ']':
                Settings = {a:b for a,b in [x.strip(" ").split(" ") for x in line[1:-2].split(",")]}
            else:
                lb = line.replace("\t",' ').replace("\n",'')
                if "//" in lb:
                    lb = lb[:lb.find("//")]
                if lb.strip():
                    Program.append(lb.strip())
    file.close()
    
    Program = const_evaluation(Program, definitions)

    Programs = {a:[] for a in KEYWORDS}
    currentSector = ""
    for line in Program:
        if line[1:] in KEYWORDS:
            currentSector = line[1:]
        Programs[currentSector].append(line)
    for Sector in KEYWORDS:
        Programs[Sector] = Programs[Sector][1:]
    JUMPLIST = {a:dict() for a in KEYWORDS}
    for Device in KEYWORDS:
        rom_id = 0
        for cmd_i in range(len(Programs[Device])):
            if Programs[Device][cmd_i][0][0] == ":":
                name = Programs[Device][cmd_i]
                cmd_i += 1
                if cmd_i >= len(Programs[Device]):
                    JUMPLIST[Device][name[1:]] = rom_id
                    continue
                while Programs[Device][cmd_i][0][0] == ":":
                        cmd_i += 1
                JUMPLIST[Device][name[1:]] = rom_id
            else:
                rom_id += 1
        
    for Device in KEYWORDS:
        Programs[Device] = [a for a in Programs[Device] if a[0] != ':']
    return Programs, JUMPLIST, Settings

def load_commands(path: str):
    COMMANDS = list()
    with open(path) as file:
        for line in file:
            COMMANDS.append(line.strip().split(" "))

    return COMMANDS

def find_executable_cores(Program: dict) -> list:
    ACTIVES = list()
    for device, program in Program.items():
        if len(program) != 0:
            ACTIVES.append(device)
    return ACTIVES

def const_evaluation(program, definitions):
    const_values = dict()
    definition = list()
    
    for item in definitions:
        components = item.split(" ")
        if len(components) > 1:
            const_values[components[0]] = ''.join([x+" " for x in components[1:]]).strip()
        elif len(components) == 1:
            definition.append(components[0])
        else:
            raise error.LoadError("Can't inteprete const expression: {}".format(item))


    for line in program:
        if line.startswith("const"):
            components = line.split(" ")
            if len(components) > 2:
                const_values[components[1]] = ''.join([x+" " for x in components[2:]]).strip()
            elif len(components) == 2:
                definition.append(components[1])
            else:
                raise error.LoadError("Can't inteprete const expression: {}".format(line))
    program = [x for x in program if not x.startswith("const")]

    recursion = [True]
    else_watchman = [0]
    new_program = []
    if DEFINITION_DEBUG:
        print("line", "app", "depth",sep="\t; ")
    for i in range(len(program)):
        if program[i].startswith("#ifdef"):
            SPLITED = program[i].split(" ")[1]
            recursion.append(True if SPLITED in definition else False)
            else_watchman.append(0)
        elif program[i].startswith("#ifndef"):
            SPLITED = program[i].split(" ")[1]
            recursion.append(True if SPLITED not in definition else False)
            else_watchman.append(0)
        elif program[i] == "#endif":
            if len(recursion) == 1:
                raise error.LoadError("#endif expression without #ifdef or #ifndef")
            recursion.pop()
        elif program[i] == "#else":
            if else_watchman[len(recursion)-1] == 0:
                recursion[len(recursion)-1] = not recursion[len(recursion)-1]
                else_watchman[len(recursion)-1] += 1
            else:
                raise error.LoadError("multiple #else expression in same #ifdef/#endif statment")
        else:
            if DEFINITION_DEBUG:
                print(program[i][:6],  all(recursion), len(recursion), sep="\t; ")
            if all(recursion):
                new_program.append(program[i])
    if len(recursion) != 1:
        raise error.LoadError("Expected #endif expression")

    #swap const's
    def smart_replace(line: str, From: str, To: str):
        line = re.sub("(?![^a-zA-Z0-9])({})(?![a-zA-Z0-9])".format(From), To, line)
        return line

    for i, _ in enumerate(new_program):
        for const, value in const_values.items():
            new_program[i] = smart_replace(new_program[i], const, value)
    
    return new_program

def save(filename, binary):
    with open(filename,"w") as file:
        for key in KEYWORDS:
            file.write(":{}\n".format(key))
            for line in binary[key]:
                file.write('\t{}\n'.format(line))
            file.write("\n")
        file.close()
    
def load_json_profile(path):
    with open(path, "r") as file:
        profile = json.load(file)
    return profile