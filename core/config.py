import configparser
from ast import literal_eval
import os

DEFAULT_SECTION = "lor"
SHOW_UNKNOWNS = True
HOME_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

config = configparser.ConfigParser()

config.read(f"{HOME_DIR}\\settings\\default.ini")

def __getattr__(name):
    if name not in config[DEFAULT_SECTION] and SHOW_UNKNOWNS:
        print(f"Unknown configuration token: {name}")
    value = config.get(DEFAULT_SECTION, name, fallback='None')
    try:
        return literal_eval(value)
    except:
        return value

def __setattr__(name, val):
    override_from_dict({name:val})

def override_from_file(paths):
    config.read(paths)

def override_from_dict(args={}, **kwargs):
    config.read_dict({DEFAULT_SECTION:{key: str(val) for key, val in {**args, **kwargs}.items() if val is not None}})
