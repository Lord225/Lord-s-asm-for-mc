import logging
from .patterns import Pattern
import json
from typing import Any, Callable, Literal, Union
from jsmin import jsmin
import core.config as config
import core.error as error
import runpy

from path import Path 
import os

REQUIRED_FIELDS = ["pattern", "command_layout", "bin"]
OPTIONAL_FIELDS = []

def load_json(file):
    try:
        file = jsmin(file.read())
        return json.loads(file)
    except Exception as err:
        raise error.ProfileLoadError(f"Cannot Load json: {err}") 

def load_json_profile(profile_path):
    def load(path):
        path = Path(path)
        if os.path.isfile(path):
            with open(path, "r") as file:
                base_folder = path.parent
                return load_json(file), base_folder
        if os.path.isdir(path):
            path_to_profile = path/f'{path.basename()}.jsonc'
            if path_to_profile.exists():
                with open(path_to_profile, "r") as file:
                    base_folder = path_to_profile.parent
                    return load_json(file), base_folder
    loaded = load(profile_path)
    if loaded is not None:
        return loaded
    
    # check if profile is in default profiles folder
    loaded = load(os.path.join(config.HOME_DIR, profile_path))
    if loaded is not None:
        return loaded
    raise error.ProfileLoadError(f"Cannot find Profile under {profile_path}")

def get_emulator(DEFAULT_PROFILES_PATH: Path, CPU_PROFILE: dict):
    emul = CPU_PROFILE["CPU"]["emulator"]
    if isinstance(emul, str):
        emulator_path = DEFAULT_PROFILES_PATH/f'{emul}.py'
        try:
            emul = runpy.run_path(str(emulator_path), run_name="__package__")
        except Exception as err:
            raise error.ProfileLoadError(f"Cannot load emulator: {emulator_path}, Trying to run this script resulted in this error: {err}")
        if 'get_emulator' in emul:
            return emul['get_emulator']
        else:
            raise error.ProfileLoadError(f"Emulator should define `get_emulator` function that returns instance of EmulatorBase class. But function is not even present in the file {emulator_path}")
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
            logging.warning(f"Command: {cmd_id} does not have one of these fields: {missing}")
    
        cmd['pattern'] = Pattern(cmd['pattern'])
    return commands

def process_macros(macros: dict):
    for cmd_id, cmd in macros.items():
        try:
            cmd['pattern'] = Pattern(cmd['pattern'])
        except Exception as err:
            raise error.ProfileLoadError(f"Cannot load macro: {cmd_id} because of error: {err}")
    return macros

class ProfileInfo:
    def __init__(self, kwargs: dict):
        self.name: str = kwargs.get("Name", "Unknown")
        self.arch: str = kwargs.get("Arch", "Unknown")
        self.author: str = kwargs.get("Author", "Unknown")
        self.speed: str = kwargs.get("Speed", 1)
    def __str__(self) -> str:
        return f"Name: '{self.name}', Arch: '{self.arch}', Author: '{self.author}', Speed: '{self.speed}'"
        
class AdressingMode:
    def __init__(self, kwargs: dict, profile):
        self.mode: Literal["align", "packed"] = kwargs["ADRESSING"]["mode"] if "mode" in kwargs["ADRESSING"] else "align"
        self.bin_len: int = kwargs["ADRESSING"]["bin_len"] if "bin_len" in kwargs["ADRESSING"] else 1 if self.mode == "packed" else max(profile.arguments_len.values())
        self.offset: int = kwargs["ADRESSING"]["offset"] if "offset" in kwargs["ADRESSING"] else 0

class SchematicInfo:
    def __init__(self, kwargs: dict, base_folder: Path):
        schem_settings = kwargs["SCHEMATIC"]
        self.blank_name = str(base_folder/schem_settings['blank'])
        self.layout = schem_settings["layout"]
        self.high_state = schem_settings["high"]
        self.low_state = schem_settings["low"]

class Profile:
    def __init__(self, profile, base_folder, emulator):
        from core.emulate.emulator import EmulatorBase
        self.builded = False
        self.base_folder = base_folder

        self.profile: dict[str, Any] = profile["CPU"]
        self.emul: 'Union[Callable[[], EmulatorBase], dict[Any, Any]]' = emulator

        self.build_profile()
        self.__selfcheck()

        self.builded = True
    

    def build_profile(self):
        try:
            self.__build_commands()
        except Exception as err:
            raise error.ProfileLoadError(f"Faild to load commands: {err}")

        try:
            self.__build_macros()
        except Exception as err:
            raise error.ProfileLoadError(f"Faild to load macros: {err}")
        
        try:
            self.__build_arguments()
        except Exception as err:
            raise error.ProfileLoadError(f"Faild to load layouts variants: {err}")

        try:
            self.__build_info()
        except Exception as err:
            raise error.ProfileLoadError(f"Faild to load mata data of the profile: {err}")
        
        try:
            self.__get_schematics()
        except Exception as err:
            raise error.ProfileLoadError(f"Faild to load schematic definitions: {err}")
    
    def __build_commands(self):
        raw_commandset = self.profile["COMMANDS"]
        self.commands_definitions = process_commands(raw_commandset)
    def __build_macros(self):
        raw_macros = self.profile["MACROS"] if "MACROS" in self.profile else None

        if raw_macros is None:
            self.macro_definitions = dict()
        else:
            self.macro_definitions = process_macros(raw_macros)
    def __build_info(self):
        self.info = ProfileInfo(self.profile)
        self.adressing = AdressingMode(self.profile, self)
    def __build_arguments(self):
        def load_raw_arguments():
            try:
                args = self.profile["ARGUMENTS"]
                if "variants" in args:
                    logging.warning("'variants' field is deprecated in 'ARGUMENTS' section. Use 'ARGUMENTS' instead.")
                    return args["variants"]
            
                return args
            except KeyError:
                raise error.ProfileLoadError(f"Profile does not defined `ARGUMENTS` section")
        def load_defs():
            try:
                return [definiton for definiton in self.profile["DEFINES"] if isinstance(definiton, str)]
            except KeyError:
                raise error.ProfileLoadError(f"Profile does not have `DEFINES` section")
        def load_consts():
            try:
                return {definiton[0]: str(definiton[1]) for definiton in self.profile["DEFINES"] if isinstance(definiton, list)}
            except KeyError:
                raise error.ProfileLoadError(f"Profile does not have `CONSTANTS` section")
        def load_entrypoint():
            try:
                return self.profile["KEYWORDS"]
            except KeyError:
                raise error.ProfileLoadError(f"Profile does not have `KEYWORDS` section")
            
        def load_arguments_len():
            try:
                return {name: sum((int(arg['size']) for arg in val.values())) for name, val in load_raw_arguments().items()}
            except KeyError:
                raise error.ProfileLoadError(f"Profile does not have `ARGUMENTSs` section")
        def load_fill():
            try:
                return self.profile["FILL"] if 'FILL' in self.profile else None
            except KeyError:
                raise error.ProfileLoadError(f"Profile does not have `ARGUMENTS/fill` section")

        self.arguments: dict[str, dict[str, Any]] = load_raw_arguments()
        self.defs: list[str]                      = load_defs()
        self.consts: dict[str, str]               = load_consts()
        self.entrypoints: dict[str, Any]          = load_entrypoint()
        self.arguments_len                        = load_arguments_len()
        self.fill                                 = load_fill()
        
    def __get_schematics(self):
        if "SCHEMATIC" in self.profile and self.profile["SCHEMATIC"] is not None:
            self.schematic = SchematicInfo(self.profile, self.base_folder)
        else:
            logging.warning("Profile does not have SCHEMATIC section, schematic export will be disabled.")
            self.schematic = None

    def __selfcheck(self):
        assert self.info is not None
        assert self.commands_definitions is not None
        assert self.arguments is not None
        assert self.arguments_len is not None
        assert self.defs is not None
        assert self.entrypoints is not None
        assert self.adressing is not None


    
def load_profile_from_file(path, load_emulator = True) -> Profile:
    path = path.strip('"')
    if path.startswith("http"):
        import core.install_profiles as install_profiles
        path = install_profiles.download_and_install_profile(path, quiter=True)

    path = os.path.join(str(config.default_json_profile_path), str(path))
    profile, base_folder = load_json_profile(path)
    emulator = get_emulator(base_folder, profile) if load_emulator else None

    try:
        return Profile(profile, base_folder, emulator)
    except KeyError as err:
        raise error.ProfileLoadError(f"Cannot find field: {err} in profile '{path}'")


