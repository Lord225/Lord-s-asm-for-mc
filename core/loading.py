import core.error as error
import json
import re
import config
KEYWORDS = ["CORE0", "CORE1", "SHADER"]
CORE_ID_MAP = {word:i for i, word in enumerate(KEYWORDS)}


def update_keywords(new):
    global KEYWORDS, CORE_ID_MAP
    KEYWORDS = new
    CORE_ID_MAP = {word:i for i, word in enumerate(KEYWORDS)}

def smart_replace(line: str, From: str, To: str):
    line = re.sub("(?![^a-zA-Z0-9])({})(?![a-zA-Z0-9])".format(From), To, line)
    return line

def smart_find(line: str, From: str):
    finded = re.search("(?![^a-zA-Z0-9])({})(?![a-zA-Z0-9])".format(From),line)
    return finded

def load_preproces(path):
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
                    Program.append((i+1, lb.strip()))
    file.close()
    return Program, Settings

def split_sectors(Program):
    Programs = {a:[] for a in KEYWORDS}
    currentSector = ""
    for line in Program:
        if line[1][1:] in KEYWORDS:
            currentSector = line[1][1:]
        if len(currentSector) == 0:
            err = error.LoadError("'{}' is in undefined sector (valid sectors: {})".format(line[1], KEYWORDS))
            err.line = line[0]
            raise err
        Programs[currentSector].append(line)
    for Sector in KEYWORDS:
        Programs[Sector] = Programs[Sector][1:]
    return Programs

def jump_preprocesing(Programs):
    JUMPLIST = {a:dict() for a in KEYWORDS}
    for Device in KEYWORDS:
        rom_id = 0
        for cmd_i in range(len(Programs[Device])):
            if Programs[Device][cmd_i][1][0] == ":":
                name = Programs[Device][cmd_i][1]
                cmd_i += 1
                if cmd_i >= len(Programs[Device]):
                    if name[1:] in JUMPLIST[Device]:
                        raise error.LoadError("Jump identifier '{}' has appear multiple times.".format(name[1:]))
                    JUMPLIST[Device][name[1:]] = rom_id
                    continue
                while Programs[Device][cmd_i][1][0] == ":":
                        cmd_i += 1
                if name[1:] in JUMPLIST[Device]:
                    raise error.LoadError("Jump identifier '{}' has appear multiple times.".format(name[1:]))
                JUMPLIST[Device][name[1:]] = rom_id
            else:
                rom_id += 1
        
    for Device in KEYWORDS:
        Programs[Device] = [a for a in Programs[Device] if a[1][0] != ':']
    return Programs, JUMPLIST

def indices(Programs):
    line_indicator = dict()
    for Device in KEYWORDS:
        line_indicator[Device] = [x[0] for x in Programs[Device]]
        Programs[Device] = [x[1] for x in Programs[Device]]
    return line_indicator

def load_program(path : str, definitions: list = []):    
    Program, Settings = load_preproces(path)

    Program, data = const_evaluation(Program, definitions)

    Programs = split_sectors(Program)

    Programs, JUMPLIST = jump_preprocesing(Programs)
    
    line_indicator = indices(Programs)
    
    return Programs, line_indicator, JUMPLIST, Settings, data

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

def find_consts(program, definitions):
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
        if line[1].startswith("#define"):
            components = line[1].split(" ")
            if len(components) > 2:
                const_values[components[1]] = ''.join([x+" " for x in components[2:]]).strip()
            elif len(components) == 2:
                definition.append(components[1])
            else:
                raise error.LoadError("Can't inteprete const expression: {}".format(line[1]))
    return const_values, definition

def find_macros(program, definitions):
    line_iter = iter(program)
    macros = dict()
    new_program = []
    try:
        while line_iter:
                line = next(line_iter)
                if line[1].startswith("#endmacro"):
                    raise error.LoadError("The macro definition hasn't been started (found '#endmacro' without '#macro')")
                if line[1].startswith("#macro"):
                    components = line[1].split(" ")
                    if components[1].find("(") != -1 and components[-1].find(")") != -1:
                        DATA = []
                        conact = ''.join(components[1:])
                        start = conact.find("(")
                        end = conact.find(")")
                        if start == -1:
                            raise error.LoadError("Expected '(' in macro definition")
                        if end == -1:
                            raise error.LoadError("Expected ')' in macro definition")
                        name = components[1][:components[1].find("(")]
                        if len(name) == 0:
                            raise error.LoadError("Expected name for the macro")
                        parametres = conact[start+1:end].split(',')
                        line = next(line_iter)
                        while not line[1].startswith("#endmacro"):
                            if line[1].startswith("#macro"):
                                raise error.LoadError("Canno't define macros in macro")
                            line_id, line = line
                            for i, param in enumerate(parametres):
                                line = smart_replace(line, param, "{arg_"+str(i)+"}") #sorry
                            DATA.append((line_id, line))
                            try:
                                line = next(line_iter)
                            except StopIteration:
                                raise error.LoadError("he macro definition hasn't been ended (found '#macro' without '#endmacro')")
                        macros[name] = (len(parametres), DATA)
                else:
                    new_program.append(line)
    except StopIteration:
        return macros, new_program

def definition_solver(program, definition):
    recursion = [True]
    else_watchman = [0]
    new_program = []
    if config.DEFINITION_DEBUG:
        print("line", "app", "depth",sep="\t; ")
    for i in range(len(program)):
        if program[i][1].startswith("#ifdef"):
            SPLITED = program[i][1].split(" ")[1]
            recursion.append(True if SPLITED in definition else False)
            else_watchman.append(0)
        elif program[i][1].startswith("#ifndef"):
            SPLITED = program[i][1].split(" ")[1]
            recursion.append(True if SPLITED not in definition else False)
            else_watchman.append(0)
        elif program[i][1] == "#endif":
            if len(recursion) == 1:
                raise error.LoadError("#endif expression without #ifdef or #ifndef")
            recursion.pop()
        elif program[i][1] == "#else":
            if else_watchman[len(recursion)-1] == 0:
                recursion[len(recursion)-1] = not recursion[len(recursion)-1]
                else_watchman[len(recursion)-1] += 1
            else:
                raise error.LoadError("multiple #else expression in same #ifdef/#endif statment")
        else:
            if config.DEFINITION_DEBUG:
                print(program[i][1][:6],  all(recursion), len(recursion), sep="\t; ")
            if all(recursion):
                new_program.append(program[i])
    if len(recursion) != 1:
        raise error.LoadError("Expected #endif expression")
    return new_program

def apply_macro(program, name, macro):
    new_program = list()
    for line in program:
        if line[1].startswith(name):
            start = line[1].find("(")
            end = line[1].find(")")
            if start == -1:
                raise error.LoadError("Expected '(' in macro call")
            if end == -1:
                raise error.LoadError("Expected ')' in macro call")
            args = {"arg_{}".format(i):x.strip() for i, x in enumerate(line[1][start+1:end].split(","))}
            if len(args) != macro[0]:
                raise error.LoadError("Expected {} arguments in macro, but got: {}".format(macro[0], len(args)))
            for macro_line in macro[1]:
                formated = macro_line[1].format_map(args)
                new_program.append((macro_line[0], formated))
        else:
            new_program.append(line)
    return new_program

def datablocks(program):
    DATA = dict()
    for line in program:
        if line[1].startswith("#data"):
            splited = line[1].split(" ")
            ADRESS_START = -1
            try:
                ADRESS_START = int(splited[1], base=0)
            except ValueError:
                raise error.LoadError("Canno't interpretate datablock: {}".format(line))
            start = line[1].find('"')
            end = line[1].rfind('"')
            if start != -1 or end != -1:
                if start == -1 or end == -1:
                    raise error.LoadError("String hasn't been close or open")
                if start != end:
                    data = [ord(x) for x in line[1][start+1:end]]
                else:
                    raise error.LoadError("String hasn't been close or open")
            else:
                data_raw = ''.join(splited[2:])
                if len(data_raw) == 0:
                    raise error.LoadError("Datablock doesn't provide data.")
                data = [int(x, base=0) for x in data_raw.split(',')]
            for index, value in enumerate(data):
                DATA[index+ADRESS_START] = value
    return DATA

def const_evaluation(program, definitions):
    #find consts and definitions (#define X or #define X value)
    const_values, definition = find_consts(program, definitions)
    
    #remove these definitions
    program = [x for x in program if not x[1].startswith("#define")]

    #evalueate definitions
    new_program = definition_solver(program, definition)

    data = datablocks(new_program)
    new_program = [x for x in new_program if not x[1].startswith("#data")]

    #apply definitions
    for i, _ in enumerate(new_program):
        for const, value in const_values.items():
            new_program[i] = (new_program[i][0], smart_replace(new_program[i][1], const, value))

    #find macros
    macros, new_program = find_macros(new_program, definitions)

    #apply macros
    for name, macro in macros.items():
        new_program = apply_macro(new_program, name, macro)

    return new_program, data

def save(filename, binary, with_decorators = True):
    if config.SAVE_IN_ONE_FILE:
        with open(filename,"w") as file:
            for key in KEYWORDS:
                if with_decorators:
                    file.write(":{}\n".format(key))
                    for line in binary[key]:
                        file.write('\t{}\n'.format(line))
                else:
                    for line in binary[key]:
                        file.write('{}\n'.format(line))
                file.write("\n")
            file.close()
    else:
        for key in KEYWORDS:
            FILE_NAME = "{}_{}.{}".format(filename.split(".")[0], key, filename.split(".")[1])
            if config.IGNORE_EMPTY_PROGRAMS and len(binary[key]) == 1:
                print("INFO: File {} hasn't been saved because is empty".format(FILE_NAME))
                continue
            with open(FILE_NAME,"w") as file:
                if with_decorators:
                    file.write(":{}\n".format(key))
                    for line in binary[key]:
                        file.write('\t{}\n'.format(line))
                else:
                    for line in binary[key]:
                        file.write('{}\n'.format(line))
                file.close()

def load_json_profile(path):
    with open(path, "r") as file:
        profile = json.load(file)
    return profile

def get_profile(DEFAULT_PROFILES_PATH, NAME, CONSTS):
    CPU_PROFILE = load_json_profile('{}/{}'.format(DEFAULT_PROFILES_PATH, NAME))
    #emulator = None
    exec("import {}.{} as emulator".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]),globals())
    
    if emulator is None:
        raise error.LoadError("Canno't load emulator {}.{}".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]))

    try:
        print("Loaded profile for: '{}' by {}".format(CPU_PROFILE["CPU"]["Name"], CPU_PROFILE["CPU"]["Author"]))
        CONSTS.extend(CPU_PROFILE["CPU"]["DEFINES"])
    except KeyError as key:
        print("Can't find key in profile: {}".format(key))
        return
    except:
        print("Error: module {} doesn't exists.".format(CPU_PROFILE["CPU"]["emulator"]))
        return

    COMMAND_COUNTER = [0 for _ in range(4)]
    DEVICE = emulator.CPU()
    try:
        KEYWORDS = CPU_PROFILE["CPU"]["KEYWORDS"]
    except KeyError as error:
        raise error.ProfileStructureError("Expected key '{}' in 'CPU'".format("KEYWORDS"))
    return CPU_PROFILE, COMMAND_COUNTER, DEVICE, emulator, CONSTS, KEYWORDS

class PROFILE_DATA:
    def __init__(self, profile, emulator) -> None:
        self.PROFILE_LOADED = False
        self.COMMAND_MAP = dict() #ordered by hash, keeps emulator function pointers
        self.COMMANDSETFULL = dict() #ordered by hash, keeps "COMMANDS":{}
        self.COMMANDS_SUBTYPES = dict() #all subtypes
        self.COMMANDS_OREDERD_BY_SUBTYPES = dict() #ordered by subtypes, keeps "COMMANDS":{}
        self.COMMAND_LANE_PATTERN = dict()
        self.ROM_SIZES = dict()
        self.PARAMETERS = dict()
        self.CUSTOM_ARGUMENTS = dict()
        self.ADRESS_MODE_REMAP  = {x:i for i, x in enumerate(["const", "reg", "ptr", "ram", "adress"])}
        self.ADRESS_MODE_REMAP_REVERSED = dict()
        self.profile = profile
        self.emul = emulator

        try:
            self.checkstructure()
        except Exception as err:
            raise err

        self.extract_data_from_profile()
    def checkstructure(self):
            __NAMESPACE__ = ["Name", "Architecture", "ARGUMENTS", "Author", "emulator", "DEFINES", "parametrs", "COMMANDS", "CUSTOM ARGUMENTS"]
            try:
                for name in __NAMESPACE__:
                    try:
                        self.profile["CPU"][name]
                    except KeyError as err:
                        raise error.ProfileStructureError("Expected key in master branch: {}".format(name))

                #DEFINES
                if type(self.profile["CPU"]["DEFINES"]) is not list:
                    raise error.ProfileStructureError("Expected 'DEFINES' to be list of definitions: {}".format(name))
                if any((type(x) is not str for x in self.profile["CPU"]["DEFINES"])):
                    raise error.ProfileStructureError("Expected 'DEFINES' to be list of strings.".format())
                
                #parametrs
                parametrs__NAMESPACE__ = ["clock_speed", "word len", "num of regs", "ram adress space", "rom adress space", "cores", "arguments sizes"]

                for name in parametrs__NAMESPACE__:
                    try:
                        self.profile["CPU"]["parametrs"]
                    except KeyError as err:
                        raise error.ProfileStructureError("Expected '{}' in 'parametrs'".format(name))
                #custom arguments
                cmd__NAMESPACE__ = ["name", "type", "subtype", "args"]
                cmd__NAMESPACE__WARNING = ["description", "example"]

                if config.RAISE_ERROR_ON_NOT_IMPLEMENTED_BIN_FORMATING:
                    cmd__NAMESPACE__.append("bin")
                else:
                    cmd__NAMESPACE__WARNING.append("bin")

                if config.RAISE_ERROR_ON_NOT_IMPLEMENTED_EMULATOR:
                    cmd__NAMESPACE__.append("emulator")
                else:
                    cmd__NAMESPACE__WARNING.append("emulator")

                #COMMANDS
                for name, cmd in self.profile["CPU"]["COMMANDS"].items():
                    for cmd_must in cmd__NAMESPACE__:
                        try:
                            cmd[cmd_must]
                        except KeyError as err:
                            raise error.ProfileStructureError("Expected '{}' in 'COMMANDS'->'{}'".format(cmd_must, name))
                    for cmd_should in cmd__NAMESPACE__WARNING:
                        try:
                            cmd[cmd_should]
                        except KeyError as err:
                            print("WARNING: Expected '{}' key in 'COMMANDS'->'{}'".format(cmd_should, name)) 
                    ARG_NAMES = []
                    for arg in cmd["args"]:
                        try:
                            ARG_NAMES.append(arg["name"])
                        except KeyError as err:
                            raise error.ProfileStructureError("Expected '{}' key in CPU->COMMANDS['{}']->args".format("name", name))
                        try:
                            arg["type"]
                        except KeyError as err:
                            raise error.ProfileStructureError("Expected '{}' key in CPU->COMMANDS[{}]->args".format("type", name))
                        if not (arg["type"] in self.profile["CPU"]["parametrs"]["arguments sizes"].keys() or arg["type"] in self.profile["CPU"]["CUSTOM ARGUMENTS"].keys()):
                            raise error.ProfileStructureError("Undefined argument type: '{}'".format(arg["type"]))
                    try:
                        cmd["bin"]
                    except:
                        pass
                    else:
                        for key, val in cmd["bin"].items():
                            if key.lower() not in [k.lower() for k in self.profile["CPU"]["ARGUMENTS"].keys()]:
                                raise error.ProfileStructureError("Undeclared bin's key: '{}'. Delcared ones: {}".format(key, list(cmd["bin"].keys())))
                            if type(val) is not int and val not in ARG_NAMES:
                                raise error.ProfileStructureError("Undeclared bin's key. '{}', delcared ones: {}".format(key, cmd["bin"]))
                    
            except KeyError as err:
                raise err
    def get_full_command_set(self,):
            return {value["HASH"]:value for key, value in self.profile["CPU"]["COMMANDS"].items()}
    def get_unified_commands_types(self,):
        return list({i["subtype"] for i in self.profile["CPU"]["COMMANDS"].values()})
    def build_command_map(self,):
        for i, (key, value) in enumerate(self.profile["CPU"]["COMMANDS"].items()):
            self.profile["CPU"]["COMMANDS"][key]["HASH"] = i
            try:
                exec("self.COMMAND_MAP[{}] = self.emul.Core.{}".format(i, value["emulator"]))
            except:
                raise error.LoadError("Cannot find function in emulator.Core: {}".format(value["emulator"]))
            if self.COMMAND_MAP[i] == None:
                raise error.LoadError("Can't link '{}' operation with emulator (emulator doesn't implement this function)".format(value["emulator"]))
        for i, (key, value) in enumerate(self.profile["CPU"]["COMMANDS"].items()):
            if "parent" in value:
                self.profile["CPU"]["COMMANDS"][key]["parent"] = self.profile["CPU"]["COMMANDS"][value["parent"]]["HASH"]
    def order_commands_by_subtypes(self,):
        for i in self.COMMANDS_SUBTYPES:
            self.COMMANDS_OREDERD_BY_SUBTYPES[i] = []
            for j in self.profile["CPU"]["COMMANDS"].values():
                if j["subtype"] == i:
                    self.COMMANDS_OREDERD_BY_SUBTYPES[i].append(j)
    def remap_adress_mode(self,):
        for cmd_pattern in self.COMMANDSETFULL.values():
            for arg_id in range(len(cmd_pattern["args"])):
                cmd_pattern["args"][arg_id]["type"] = self.ADRESS_MODE_REMAP[cmd_pattern["args"][arg_id]["type"]]
    def get_command_lane(self,):
        self.COMMAND_LANE_PATTERN = self.profile["CPU"]["ARGUMENTS"]
    def get_custom_arguments(self,):
        self.CUSTOM_ARGUMENTS = self.profile["CPU"]["CUSTOM ARGUMENTS"]        
    def get_rom_arg_sizes(self,):
        self.ROM_SIZES = self.profile["CPU"]["ARGUMENTS"]
    def get_custom_arguments_types(self,):

        last = max(self.ADRESS_MODE_REMAP.values())
        i = 1
        for key, val in self.profile["CPU"]["CUSTOM ARGUMENTS"].items():
            if key in self.ADRESS_MODE_REMAP:
                raise error.ProfileStructureError()
            self.ADRESS_MODE_REMAP[key] = last+i
            i += 1
        self.ADRESS_MODE_REMAP_REVERSED = {b:a for a,b in self.ADRESS_MODE_REMAP.items()}
    def extract_data_from_profile(self):
        #TODO CHECK IT BETTER
        #Check ROM_SIZES with "bin"
        #Check COMMANDS with name, type, subtype, emulator, description, example, args, bin
        #Check parametrs with word len, num of regs, ram adress space, rom adress space, cores, arguments sizesSUPPORTED TECHNOLOGIES
        #Check if any of the COMMAND_MAP key is pointing to None

        try:
            self.COMMANDS_SUBTYPES = self.get_unified_commands_types()

            self.order_commands_by_subtypes()

            self.build_command_map()

            self.COMMANDSETFULL = self.get_full_command_set()
            
            self.get_custom_arguments_types()
            
            self.remap_adress_mode()

            self.get_command_lane()

            self.get_rom_arg_sizes()
            
    
            self.PARAMETERS = self.profile["CPU"]["parametrs"]

            self.NEW_ARGUMENT_SIZES = dict()
            for key, value in self.PARAMETERS["arguments sizes"].items():
                self.NEW_ARGUMENT_SIZES[self.ADRESS_MODE_REMAP[key]] = value
            self.PARAMETERS["arguments sizes"] = self.NEW_ARGUMENT_SIZES
        
        except Exception as err:
            raise error.ProfileStructureError(err)