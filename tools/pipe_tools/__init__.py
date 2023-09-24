import sys 
import json
import path
import core
import core.config as config

sys.path.append(str(config.HOME_DIR))

def init():
    """
    Loads json from stdin and restores profile_name and parsed instructions
    """
    
    data = ''.join(list(sys.stdin))
    decoder = json.JSONDecoder()

    try:
        raw = decoder.decode(data)
        profile = core.profile.profile.load_profile_from_file(f"{raw['profile_name']}", False)

        data = list(raw['data'])
    
        return profile, data
    except json.JSONDecodeError as err:
        print("Cannot parse input. Check if you didn't add --save to compile.py")
        raise
    