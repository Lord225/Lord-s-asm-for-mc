import argparse
import os
import sys

import path
sys.path.append(str(path.Path(__file__).abspath().parent.parent))
import core
import requests
import hashlib
import random
import clipboard


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter, 
    description=
"""
Send schematics to redstonefun.pl! It can be piped with compile.py 
Example usage:
python compile.py -i ./src/examples/pm1.lor | python tools/send.py --nick YourNick --pass YourPassword123 --copy
"""
)

parser.add_argument("--nick", type=str, required=True,
help="""Your login for schematic upload""")

parser.add_argument("--pass", type=str, required=True,
help="""Your password for schematic upload""")

parser.add_argument("-c", "--copy", action='store_true',  dest='copy', 
help="""It will automaticly copy command to clipboard""")
parser.set_defaults(feature=False)

parserargs = vars(parser.parse_args())

def process_response(response: requests.Response):
    data = response.json()

    if 'error' in data:
        return data['error']
    else:
        print("Error: Got unexpected response from server")
        exit()

if __name__ == "__main__":
    import pipe_tools

    profile, program = pipe_tools.init()
    
    if len(program) == 0:
        exit()

    stream = ''.join(''.join(line["encoded"]) for line in program)
    schem = profile.schematic
    
    if schem is None:
        raise

    file = core.save.exporter.generate_schematic(stream, schem.layout, schem.blank_name, schem.low_state, schem.high_state)
    
    filename = f"{parserargs['nick']}_{hashlib.sha1(random.randbytes(10)).hexdigest()[:10]}.schem"
    full_path = os.path.join(f"{os.getcwd()}\\core\\cache\\{filename}")
    
    file.write_file(full_path)
    print(full_path)
    

    data = {
        'nick': parserargs["nick"],
        'pass': parserargs["pass"],
    }
    files = {
        'fileToUpload': open(full_path, "br")
    }

    response = requests.post('https://redstonefun.pl/schem-upload/index.php', data=data, files=files)

    error_code = process_response(response)

    if error_code == 0:
        print("Schematic has been uploaded!", end='\n\n')
        command = f"/schem load {filename}"
        if parserargs['copy']:
            print(f"Command has been copied! ({command})")
            clipboard.copy(command)
        else:
            print(command)
    elif error_code == 1:
        print("Invalid username or password")
        exit()
    elif error_code == 2:
        print("The schematic is too large")
        exit()
    elif error_code == 3:
        print("A schematic with this name already exists")
        exit()
    elif error_code == 4:
        print("You can only upload schematics")
        exit()
    elif error_code == 5:
        print("Server encountered an error during upload")
        exit()
    elif error_code == 6:
        print("Missing data. Make sure you have provided username, password and file to upload")
        exit()
    else:
        print(f"Other error: {error_code}")
        exit()
