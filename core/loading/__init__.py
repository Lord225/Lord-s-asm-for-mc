import core.error as error
import json
import core.config as config
import importlib

import core.loading.macros as macros
import core.loading.base as base
import core.loading.jumps as jumps

KEYWORDS = ["CORE0", "CORE1", "SHADER"]
CORE_ID_MAP = {word:i for i, word in enumerate(KEYWORDS)}


def update_keywords(new):
    global KEYWORDS, CORE_ID_MAP
    KEYWORDS = new
    CORE_ID_MAP = {word:i for i, word in enumerate(KEYWORDS)}

def load_program(path : str, definitions: list = []):    
    Program, Settings = base.load_preproces(path)

    Program, data = macros.const_evaluation(Program, [] if definitions is None else definitions)

    Programs = jumps.split_sectors(Program, KEYWORDS)

    Programs, JUMPLIST = jumps.jump_preprocesing(Programs, KEYWORDS)
    
    line_indicator = jumps.indices(Programs, KEYWORDS)
    
    return Programs, line_indicator, JUMPLIST, Settings, data


def find_executable_cores(Program: dict) -> list:
    ACTIVES = list()
    for device, program in Program.items():
        if len(program) != 0:
            ACTIVES.append(device)
    return ACTIVES


def load_commands(path: str):
    COMMANDS = list()
    with open(path) as file:
        for line in file:
            COMMANDS.append(line.strip().split(" "))
    return COMMANDS

def save(filename, binary, with_decorators = True):
    if config.SAVE_IN_ONE_FILE:
        with open(filename,"w") as file:
            for key in KEYWORDS:
                file.write(key+":\n")
                for line in binary[key]:
                    file.write(line)
    else:
        for key in KEYWORDS:
            FILE_NAME = "{}_{}.{}".format(filename.split(".")[0], key, filename.split(".")[1])
            if config.IGNORE_EMPTY_PROGRAMS and len(binary[key]) == 1:
                print("INFO: File '{}' hasn't been saved because is empty".format(FILE_NAME))
                continue
            with open(FILE_NAME,"w") as file:
                file.write(key+":\n")
                file.write(binary[key])

def load_json_profile(path):
    with open(path, "r") as file:
        profile = json.load(file)
    return profile

def get_emulator(DEFAULT_PROFILES_PATH: str, CPU_PROFILE: dict):
    try:
        emulator = importlib.import_module("{}.{}".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]))
    except Exception as err:
        raise error.LoadError("Cannot import {}.{}: {}".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"], err))
    return emulator

def get_profile(DEFAULT_PROFILES_PATH, NAME, CONSTS):
    CPU_PROFILE = load_json_profile('{}/{}'.format(DEFAULT_PROFILES_PATH, NAME))

    emulator = get_emulator(DEFAULT_PROFILES_PATH, CPU_PROFILE)
    if emulator is None:
        raise error.LoadError("Canno't load emulator {}.{}".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]))

    try:
        print("Loading profile for: '{}' by {}".format(CPU_PROFILE["CPU"]["Name"], CPU_PROFILE["CPU"]["Author"]))
        if CONSTS is None:
            CONSTS = list()
        CONSTS.extend(CPU_PROFILE["CPU"]["DEFINES"])
    except KeyError as key:
        print("Can't find key in profile: {}".format(key))
        return
    except Exception as err:
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
        self.COMMANDS_TYPES = dict() #all types
        self.COMMANDS_OREDERD_BY_TYPES = dict() #ordered by type, keeps "COMMANDS":{}
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
                cmd__NAMESPACE__ = ["name", "args"]
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
                        if cmd_must not in cmd: 
                            if "parent" not in cmd:
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
                        #TODO
                        # for key, val in cmd["bin"].items():
                        #     if key.lower() not in [k.lower() for k in self.profile["CPU"]["ARGUMENTS"].keys()]:
                        #         raise error.ProfileStructureError("Undeclared bin's key: '{}'. Delcared ones: {}".format(key, list(cmd["bin"].keys())))
                        #     if type(val) is not int and val not in ARG_NAMES:
                        #         raise error.ProfileStructureError("Undeclared bin's key. '{}', delcared ones: {}".format(key, cmd["bin"]))
                        pass
                    
            except KeyError as err:
                raise err
    def get_full_command_set(self,):
            return {value["HASH"]:value for key, value in self.profile["CPU"]["COMMANDS"].items()}
    def get_unified_commands_types(self,):
        return list({i.get("type", "DEF") for i in self.profile["CPU"]["COMMANDS"].values()})
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
    def order_commands_by_types(self,):
        for i in self.COMMANDS_TYPES:
            self.COMMANDS_OREDERD_BY_TYPES[i] = []
            for j in self.profile["CPU"]["COMMANDS"].values():
                if j.get("type", "DEF") == i:
                    j["type"] = j.get("type", "DEF")
                    self.COMMANDS_OREDERD_BY_TYPES[i].append(j)
    def remap_adress_mode(self,):
        for key, cmd_pattern in self.COMMANDSETFULL.items():
            for arg_id in range(len(cmd_pattern["args"])):
                self.COMMANDSETFULL[key]["args"][arg_id]["type"] = self.ADRESS_MODE_REMAP[cmd_pattern["args"][arg_id].get("type", "DEF")] #! WFY CO TY KURWA TU ZROBIŁEŚ CHŁOPIE PIJANY KURWA.
    def get_command_lane(self,):
        self.COMMAND_LANE_PATTERN = self.profile["CPU"]["ARGUMENTS"]
    def get_custom_arguments(self,):
        self.CUSTOM_ARGUMENTS = self.profile["CPU"]["CUSTOM ARGUMENTS"]        
    def get_rom_arg_sizes(self,):
        self.ROM_SIZES = self.profile["CPU"]["ARGUMENTS"]
    def get_custom_arguments_types(self,):
        last = max(self.ADRESS_MODE_REMAP.values())
        i = 1
        for key, _ in self.profile["CPU"]["CUSTOM ARGUMENTS"].items():
            if key in self.ADRESS_MODE_REMAP:
                raise error.ProfileStructureError()
            self.ADRESS_MODE_REMAP[key] = last+i
            i += 1
        self.ADRESS_MODE_REMAP_REVERSED = {b:a for a,b in self.ADRESS_MODE_REMAP.items()}
    def extract_data_from_profile(self):
        #TODO CHECK IT BETTER
        #Check ROM_SIZES with "bin"
        #Check COMMANDS with name, type, emulator, description, example, args, bin
        #Check parametrs with word len, num of regs, ram adress space, rom adress space, cores, arguments sizesSUPPORTED TECHNOLOGIES
        #Check if any of the COMMAND_MAP key is pointing to None

        try:
            self.COMMANDS_TYPES = self.get_unified_commands_types()

            self.order_commands_by_types()

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