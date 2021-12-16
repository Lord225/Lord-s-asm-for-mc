import chunk
from nbt import nbt
from typing import List, Iterable
import numpy as np
from core.profile.profile import Profile
from core.save.formatter import padbin
from core.emulate.emulator import gather_instructions 
import numpy as np

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
    if isinstance(layout, dict):
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
    else:
        raise


def generate_block_data(data, layout, blank):
    blocks = bytearray(blank["BlockData"].value)
    Width, Lenght, Height = get_dimensions(blank)
    high, low = 2, 0
    word_size = 8
    print(f'{Width, Lenght, Height}')
    for word_index, word in enumerate(data):
        str_byte = padbin(word, word_size, False)                                           #TODO VARIBLE SIZE
        for bit_index, bit in enumerate(str_byte):
            x, y, z = calculate_bit_cords(word_size*word_index+bit_index, layout)
            state = low if bit == "0" else high
            print(f"i: {word_size*word_index+bit_index}, [{x}, {y}, {z}], {state}")
            flat = x+y*Width+z*Width*Lenght
            try:
                blocks[flat] = state
            except:
                print("OUT OF MEMORY")
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
    
    context['outfiles'] = dict()
    
    for chunk_name, instructions_objs in program.items():
        output_name = chunk_name+".schem"                                             #TODO
        data, _ = gather_instructions(instructions_objs, context)
        data = flatten_instructions(data)
        generate_schematic(data, layout, blank_name, output_name)

        context['outfiles'][chunk_name] = output_name
        

def generate_schematic(data, layout, blank_name, name) -> None:
    blankschem = nbt.NBTFile(blank_name, "rb")

    nbtfile = nbt.NBTFile()
    nbtfile.name = "Schematic"

    nbtfile.tags.append(nbt.TAG_Int(name="PaletteMax", value=3))
    palette = nbt.TAG_Compound(name="Palette")
    palette.tags.append(nbt.TAG_Int(name="minecraft:air", value=1))
    palette.tags.append(nbt.TAG_Int(name="minecraft:lapis_block", value=2)) #TODO have to be dynamic, based on blank schematic.
    palette.tags.append(nbt.TAG_Int(name="minecraft:redstone_block", value=0))
    palette.name = "Palette"
    nbtfile.tags.append(palette)

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

    print(nbtfile)

    basedata = generate_block_data(data, layout, blankschem)
    nbtfile.tags.append(nbt.TAG_Byte_Array(name="BlockData"))
    nbtfile["BlockData"].value = basedata
    nbtfile.tags.append(nbt.TAG_List(name="BlockEntities", type=nbt.TAG_Compound))

    nbtfile.write_file(name)                  #TODO output in out dir
