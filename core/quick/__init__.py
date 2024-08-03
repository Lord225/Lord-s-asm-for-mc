from nbt import nbt
import core
import core.error as error
import core.config as config
from core.context import Context
from core.load.base import Line
from core.profile.profile import AdressingMode, Profile
from core.save.formatter import as_values

import io

def translate(program, profile: Profile):
    # check if program is list of strings or list of Line objects
    if isinstance(program[0], str):
        program = [Line(line, line_index_in_file=-1) for line in program]
    
    parser_pipeline = core.pipeline.make_parser_pipeline()
    
    partial_save_pipeline = [('fill addresses', core.save.fill.fill_empty_addresses),
                             ('format', core.save.formatter.format_output),
                             ('add comments', core.save.add_comments.add_comments)]

    program, context = core.pipeline.exec_pipeline(parser_pipeline, program, Context(profile), progress_bar_name=None)
    program, context = core.pipeline.exec_pipeline(partial_save_pipeline, program, context, progress_bar_name=None)
    return program, context

def gather_instructions(program, adressing: AdressingMode):
    output = dict()
    debug = dict()
    for line_obj in program:
        output[line_obj.physical_adress] = as_values(line_obj.formatted, adressing.bin_len)
        if 'debug' in line_obj:
            debug[line_obj.physical_adress] = line_obj.debug
    return output, debug

def pack_adresses(instructions):
    output = dict()
    for adress, data in instructions.items():
        for i, cell in enumerate(data):
            if (adress+i) in output:
                raise error.EmulationError(f"Output data is overlapping: adress: {adress+i} is arleady occuped by value: {output[adress+i]}")
            output[adress+i] = cell
    return output

def preproces(program, profile: Profile):
    pipeline = core.pipeline.make_preproces_pipeline_for_reditor()

    program, context = core.pipeline.exec_pipeline(pipeline, program, Context(profile), progress_bar_name=None)

    return program, context

def language_server(program, context: Context, profile: Profile):
    pass

def build_schematic(program, profile: Profile):
    schematic = profile.schematic

    data = ''.join(''.join(line["encoded"]) for line in program)

    if schematic is None:
        raise error.ProfileLoadError("Schematic definition is required for building one")

    blank = nbt.NBTFile(profile.schematic.blank_name)
    file = core.save.exporter.generate_schematic(data, schematic.layout, blank, schematic.low_state, schematic.high_state)

    return file

import hashlib
import random
import requests


def process_response(response: requests.Response):
    data = response.json()

    if 'error' in data:
        return data['error']
    else:
        print("Error: Got unexpected response from server")
        exit()

def send_schematic(schematic: nbt.NBTFile, nick=None, passwd=None, phpsessid=None):
    filename = f"{hashlib.sha1(random.randbytes(10)).hexdigest()[:10]}.schem"

    data = {
        'nick': nick,
        'pass': passwd,
    }
    files = {
        'fileToUpload': schematic
    }
    cookies = {
        'PHPSESSID': phpsessid
    }
    
    if nick is not None and passwd is not None:
        response = requests.post('https://redstonefun.pl/uploadapi.php', data=data, files=files)
    elif phpsessid is not None:
        response = requests.post('https://redstonefun.pl/uploadapi.php', files=files, cookies=cookies)
    else:
        raise error.CompilerError("You need to pass either nick and passwd or sessionId")
    error_code = process_response(response)

    if error_code == 0:
        return f"/load {filename}"
    elif error_code == 1:
        raise error.CompilerError("Invalid username or password")
    elif error_code == 2:
        raise error.CompilerError("The schematic is too large")
    elif error_code == 3:
        raise error.CompilerError("A schematic with this name already exists")
    elif error_code == 4:
        raise error.CompilerError("You can only upload schematics")
    elif error_code == 5:
        raise error.CompilerError("Server encountered an error during upload")
    elif error_code == 6:
        raise error.CompilerError("Missing data. Make sure you have provided username, password and file to upload")
    else:
        raise error.CompilerError(f"Other error: {error_code}")

def build_and_upload(program, profile: Profile, nick, passwd):
    schematic = build_schematic(program, profile)

    return send_schematic(schematic, nick, passwd)