from enum import Enum, auto
import json
import core.config as config
import core.error as error
import importlib
import core.parse as parser
import core.profile.patterns as patterns

def load_json_profile(path):
    with open(path, "r") as file:
        profile = json.load(file)
    return profile

def get_emulator(DEFAULT_PROFILES_PATH: str, CPU_PROFILE: dict):
    return importlib.import_module("{}.{}".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]))

def check_raw_command_integrity(id: str, cmd: dict):
    REQ_FIELDS = ["pattern", 'command_cost']
    OPT_FIELDS = ["command_cost", "command_layout", 'bin']
    required = [required for required in REQ_FIELDS if required not in cmd]
    if len(required) != 0:
        raise error.ProfileLoadError(f"Command: {id} does not have one of these fields: {REQ_FIELDS}")
    optional = [optional for optional in OPT_FIELDS if optional not in cmd]
    return optional


def process_commands(commands: dict):
    warnings = dict()
    for cmd_id, cmd in commands.items():
        missing = check_raw_command_integrity(cmd_id, cmd)
        if len(missing) != 0:
            warnings[cmd_id] = missing
        
        cmd['args'] = {key: patterns.ArgumentTypes[val.upper()] for key, val in cmd['args'].items()}
        cmd['pattern'] = patterns.Pattern(cmd['pattern'], cmd['args'])
    return commands

class ProfileInfo:
    def __init__(self, kwargs: dict):
        self.name = kwargs["Name"]
        self.arch = kwargs["Arch"]
        self.author = kwargs["Author"]



class Profile:
    def __init__(self, profile, emulator):
        self.builded = False

        self.profile = profile["CPU"]
        self.emul = emulator

        self.info = None
        self.commands_definitions = None
        self.arguments = None
        self.defs = None
        self.keywords = None

        
        self.build_profile()
        self.__selfcheck()

        self.builded = True
    
    def build_profile(self):
        self.__build_commands()
        self.__build_arguments()
        self.__build_info()

        self.__selfcheck()
        self.builded = True

    
    def __build_commands(self):
        raw_commandset = self.profile["COMMANDS"]
        self.commands_definitions = process_commands(raw_commandset)
    def __build_info(self):
        self.info = ProfileInfo(self.profile)
    def __build_arguments(self):
        self.arguments = self.profile["ARGUMENTS"]["variants"]
        self.defs = self.profile["DEFINES"]
        self.keywords = self.profile["KEYWORDS"]

    def __selfcheck(self):
        pass
    
def load_profile_from_file(NAME, ignore_emulator_on_fail = False) -> Profile:
    profile = load_json_profile('{}/{}'.format(config.default_json_profile_path, NAME))
    try:
        emulator = get_emulator(config.default_emuletor_path, profile)
    except ModuleNotFoundError as err:
        if ignore_emulator_on_fail:
            emulator = None
        else:
            raise err
    try:
        return Profile(profile, emulator)
    except KeyError as err:
        raise error.ProfileLoadError(f"Cannot find field: {err} in profile '{NAME}'")


