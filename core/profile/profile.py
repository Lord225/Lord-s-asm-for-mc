from enum import Enum, auto
import json
from typing import Any, List, Literal, Optional
from jsmin import jsmin
import core.config as config
import core.error as error
import importlib
import core.parse as parser
import core.profile.patterns as patterns

REQUIRED_FIELDS = ["pattern", "command_layout", "bin"]
OPTIONAL_FIELDS = []

def load_json_profile(path):
    with open(path, "r") as file:
        try:
            file = jsmin(file.read())
            profile = json.loads(file)
        except Exception as err:
            raise error.ProfileLoadError(f"Cannot Load json: {err}")
    return profile

def get_emulator(DEFAULT_PROFILES_PATH: str, CPU_PROFILE: dict):
    emul: dict = CPU_PROFILE["CPU"]["emulator"]
    if emul is str:
        return importlib.import_module("{}.{}".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]))
    else:
        return emul

def check_raw_command_integrity(id: str, cmd: dict):
    required = [required for required in REQUIRED_FIELDS if required not in cmd]
    if len(required) != 0:
        raise error.ProfileLoadError(f"Command: {id} does not have one of these fields: {REQUIRED_FIELDS}")
    optional = [optional for optional in OPTIONAL_FIELDS if optional not in cmd]
    return optional


def process_commands(commands: dict):
    warnings = dict()
    for cmd_id, cmd in commands.items():
        missing = check_raw_command_integrity(cmd_id, cmd)

        if len(missing) != 0:
            warnings[cmd_id] = missing
    
        cmd['pattern'] = patterns.Pattern(cmd['pattern'])
    return commands

class ProfileInfo:
    def __init__(self, kwargs: dict):
        self.name: str = kwargs["Name"]
        self.arch: str = kwargs["Arch"]
        self.author: str = kwargs["Author"]
        self.speed: str = kwargs["time_per_cycle"]
        
class AdressingMode:
    def __init__(self, kwargs: dict, profile):
        self.mode: Literal["align", "packed"] = kwargs["ADRESSING"]["mode"] if "mode" in kwargs["ADRESSING"] else "align"
        self.bin_len: int = kwargs["ADRESSING"]["bin_len"] if "bin_len" in kwargs["ADRESSING"] else 1 if self.mode == "packed" else max(profile.arguments_len.values())
        self.offset: int = kwargs["ADRESSING"]["offset"] if "offset" in kwargs["ADRESSING"] else 0

class Profile:
    def __init__(self, profile, emulator):
        self.builded = False

        self.profile: dict[str, Any] = profile["CPU"]
        self.emul = emulator

        self.build_profile()
        self.__selfcheck()

        self.builded = True
    
    def build_profile(self):
        self.__build_commands()
        self.__build_arguments()
        self.__build_info()
    
    def __build_commands(self):
        raw_commandset = self.profile["COMMANDS"]
        self.commands_definitions = process_commands(raw_commandset)
    def __build_info(self):
        self.info = ProfileInfo(self.profile)
        self.adressing = AdressingMode(self.profile, self)
    def __build_arguments(self):
        self.arguments: dict[str, dict[str, Any]] = self.profile["ARGUMENTS"]["variants"]
        self.defs: dict[str, Any] = self.profile["DEFINES"]
        self.keywords: dict[str, Any] = self.profile["KEYWORDS"]
        self.arguments_len = {name: sum((int(arg['size']) for arg in val.values())) for name, val in self.profile["ARGUMENTS"]["variants"].items()}

    def __selfcheck(self):
        assert self.info is not None
        assert self.commands_definitions is not None
        assert self.arguments is not None
        assert self.arguments_len is not None
        assert self.defs is not None
        assert self.keywords is not None
        assert self.adressing is not None


    
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


