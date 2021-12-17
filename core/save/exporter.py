import chunk
from nbt import nbt
from typing import List, Iterable
import numpy as np
from core.profile.profile import Profile
from core.save.formatter import padbin
from core.emulate.emulator import gather_instructions 
import numpy as np
import core.config as config
import core.error as error
import os

def get_dimensions(schem):
    Width, Lenght, Height = schem["Width"].value, schem["Length"].value, schem["Height"].value
    return Width, Lenght, Height

def get_size(layout):
    size = layout["size"]
    next_level = layout["layout"]
    if next_level is None:
        return size
    
    return get_size(next_level)*size

def calculate_bit_cords(index, layout):
    offset = np.array(layout["offset"])
    stride = np.array(layout["stride"])
    size = layout["size"]
    next_level = layout["layout"] 
    
    if next_level is None:
        return offset+stride*index

    total_size = get_size(next_level)
    next_index = index%total_size
    current_index = index//total_size
    
    next_level_cords = calculate_bit_cords(next_index, next_level)

    return next_level_cords+offset+stride*current_index


def generate_block_data(data, layout, blank, high_id, low_id, word_size):
    blocks = bytearray(blank["BlockData"].value)
    Width, Lenght, Height = get_dimensions(blank)
    high, low = high_id, low_id
    if config.debug_show_schematic_updates:
        print(f'{Width, Lenght, Height}')
    for word_index, word in enumerate(data):
        str_byte = padbin(word, word_size, False)                                           
        for bit_index, bit in enumerate(str_byte):
            x, y, z = calculate_bit_cords(word_size*word_index+bit_index, layout)
            state = low if bit == "0" else high
            if config.debug_show_schematic_updates:
                print(f"i: {word_size*word_index+bit_index} \t [{x}, {y}, {z}] \t {bit == '0'}")
            flat = x+y*Width+z*Width*Lenght
            try:
                blocks[flat] = state
            except:
                print(f"Error: Writing to cell outside rom volume. ([{x}, {y}, {z}])")
                return blocks
    return blocks

def flatten_instructions(instructions: dict):
    if not instructions:
        return []
    maximum_adress = max(instructions.keys())
    maximum_adress += len(instructions[maximum_adress])

    space = [0]*maximum_adress
    for adress, data in instructions.items():
        for offset, word in enumerate(data):
            space[adress+offset] = word

    return space 


def generate_schematic_from_formatted(program, context):
    profile: Profile = context["profile"]
    schem_settings = profile.schematic
    blank_name = f"profiles/{schem_settings['blank']}"
    layout = schem_settings["layout"]
    high_state = schem_settings["high"]
    low_state = schem_settings["low"]
    
    context['outfiles'] = dict()

    outfile = config.output
    dirname = os.path.dirname(outfile)
    filename, _ = os.path.splitext(os.path.basename(outfile))
    filenames = {}

    for chunk_name, instructions_objs in program.items():
        new_filename = os.path.join(dirname, f"{filename}_{chunk_name}.schem")
        data, _ = gather_instructions(instructions_objs, context)
        data = flatten_instructions(data)
        generate_schematic(data, layout, blank_name, new_filename, context, low_state, high_state)

        filenames[chunk_name] = new_filename

    context['outfiles'] = filenames

def auto_generate_palette(nbtfile: nbt.NBTFile, blankschem: nbt.NBTFile, low_state, high_state):
    blankpalette = {k:v.value for k, v in blankschem["Palette"].items()}

    palette = nbt.TAG_Compound(name="Palette")
    palette.name = "Palette"
    for name, id in blankpalette.items():
        palette.tags.append(nbt.TAG_Int(name=name, value=id))
    
    to_check = max(blankpalette.values())+2
    if low_state not in blankpalette:
        low_id = min(x for x in range(to_check) if x not in blankpalette.values())
        palette.tags.append(nbt.TAG_Int(name=low_state, value=low_id))
    else:
        low_id = blankpalette[low_state]
    if high_state not in blankpalette:
        high_id = min(x for x in range(to_check) if x not in blankpalette.values())
        palette.tags.append(nbt.TAG_Int(name=high_state, value=high_id))
    else:
        high_id = blankpalette[high_state]

    nbtfile.tags.append(palette)
    nbtfile.tags.append(nbt.TAG_Int(name="PaletteMax", value=len(palette)))
    return nbtfile, low_id, high_id

def generate_schematic(data, layout, blank_name, name, context, low_state, high_state) -> None:
    blankschem = nbt.NBTFile(blank_name, "rb")
    
    word_size = context["profile"].adressing.bin_len

    nbtfile = nbt.NBTFile()
    nbtfile.name = "Schematic"

    nbtfile, low_id, high_id = auto_generate_palette(nbtfile, blankschem, low_state, high_state)

    Width, Lenght, Height = get_dimensions(blankschem)

    nbtfile.tags.extend([
        nbt.TAG_Int(name="DataVersion", value=blankschem["DataVersion"].value),       
        nbt.TAG_Int(name="Version", value=blankschem["Version"].value),
        nbt.TAG_Short(name="Length", value=Lenght),
        nbt.TAG_Short(name="Height", value=Height),
        nbt.TAG_Short(name="Width", value=Width),
        nbt.TAG_Int_Array(name="Offset"),
    ])
    nbtfile["Offset"].value = blankschem["Offset"].value
    metadata = nbt.TAG_Compound()
    metadata.tags = blankschem["Metadata"].tags.copy()
    metadata.name = "Metadata"
    nbtfile.tags.append(metadata)

    basedata = generate_block_data(data, layout, blankschem, high_id, low_id, word_size)
    nbtfile.tags.append(nbt.TAG_Byte_Array(name="BlockData"))
    nbtfile["BlockData"].value = basedata
    nbtfile.tags.append(nbt.TAG_List(name="BlockEntities", type=nbt.TAG_Compound))

    nbtfile.write_file(name)                  #TODO output in out dir
