import chunk
from nbt import nbt
from typing import List, Iterable
import numpy as np
from core.context import Context
from core.profile.profile import AdressingMode, Profile
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

def getbucket(cumsize, index):
    """Returns index of bucket that index would land in
    ```
    cumsum = [512, 1024, 1536]
    index = 0 => 0 
    index = 511 => 0
    index = 512 => 1
    index = 1024 => 2
    ```
    """
    for i, end in enumerate(cumsize):
        if index < end:
            return i
    return len(cumsize)

def calculate_bit_cords(index, layout):
    if isinstance(layout, dict): 
        offset = np.array(layout["offset"])
        stride = np.array(layout["stride"])
        next_level = layout["layout"] 

        if index > get_size(layout):
            raise error.CompilerError(None, f"Adress out of bounds, index: {index}, size: {get_size(layout)}")
        
        if next_level is None:
            return offset+stride*index

        total_size = get_size(next_level)
        next_index = index%total_size
        current_index = index//total_size
        
        next_level_cords = calculate_bit_cords(next_index, next_level)

        return next_level_cords+offset+stride*current_index
    elif isinstance(layout, list):
        sizes = [get_size(block) for block in layout]
        cumsize = np.cumsum(sizes) 

        i = getbucket(cumsize, index)

        actual_layout = layout[i]
        if i == 0:
            new_index = index
        elif i == len(cumsize):
            raise error.CompilerError(None, "Adress out of bounds")
        else:
            new_index = cumsize[i-1]-index

        return calculate_bit_cords(new_index, actual_layout)
    raise error.ProfileLoadError("Bad schematic layout")



def generate_block_data(data, layout, blank, high_id, low_id):
    blocks = bytearray(blank["BlockData"].value)

    Width, Lenght, Height = get_dimensions(blank)
    def flatten(x, y, z):
        return x+y*Width+z*Width*Lenght

    high, low = high_id, low_id
    def get_state(bit):
        return low if bit == "0" else high
    
    for i, bit in enumerate(data):                                   
        x, y, z = calculate_bit_cords(i, layout)
        
        try:
            blocks[flatten(x, y, z)] = get_state(bit)
        except IndexError:
            print(f"Error: Writing to cell outside rom volume. ([{x}, {y}, {z}])")
            return blocks
    return blocks

def flatten_instructions(instructions: dict):
    """Maps dict of adresses and word sequneses to flat array of words"""
    if not instructions:
        return []
    maximum_adress = max(instructions.keys())
    maximum_adress += len(instructions[maximum_adress])

    space = [0]*maximum_adress
    for adress, data in instructions.items():
        for offset, word in enumerate(data):
            space[adress+offset] = word

    return space 

def convert_to_bitstream(data: list, offset, adressing: AdressingMode):
    word_size = adressing.bin_len
    offseting_words = "0"*offset*word_size                            
    return offseting_words + ''.join((padbin(word, word_size) for word in data)) 

def generate_schematic_from_formatted(program: dict, context: Context):
    profile: Profile = context.get_profile()

    if profile.schematic is None:
        print("Schematic export is not suporrted. (Missing definition in profile) Skipping.")
        return
    
    #TODO
    offset = 0

    # Prepare output filenames
    outfile = config.output
    dirname = os.path.dirname(outfile)
    filename, _ = os.path.splitext(os.path.basename(outfile))

    filenames = generate_schematic_from(profile, program, 0, dirname, filename)

    context.outfiles.extend(filenames)

def generate_schematic_from(profile: Profile, program, offset, dirname, filename):
    schem_settings = profile.schematic
    filenames = list()

    if schem_settings is None:
        raise

    blank_name = schem_settings.blank_name
    layout = schem_settings.layout
    high_state = schem_settings.high_state
    low_state = schem_settings.low_state
    
    adressing: AdressingMode = profile.adressing
    
    new_filename = os.path.join(dirname, f"{filename}.schem")
    
    # Transform data
    data, _ = gather_instructions(program, adressing)
    data = flatten_instructions(data)
    data = convert_to_bitstream(data, offset, adressing)
    
    # Generate and save schematic
    nbt = generate_schematic(data, layout, blank_name, low_state, high_state)
    nbt.write_file(new_filename)

    filenames.append(new_filename)

    return filenames

def generate_palette(nbtfile: nbt.NBTFile, blankschem: nbt.NBTFile, low_state: str, high_state: str):
    blankpalette = {k:v.value for k, v in blankschem["Palette"].items()}

    palette = nbt.TAG_Compound(name="Palette")
    palette.name = "Palette"
    for name, id in blankpalette.items():
        palette.tags.append(nbt.TAG_Int(name=name, value=id))
    
    to_check = max(blankpalette.values())+2
    
    # Find id of low state (create new if it is not present in palette)
    if low_state not in blankpalette:
        low_id = min(x for x in range(to_check) if x not in blankpalette.values())
        palette.tags.append(nbt.TAG_Int(name=low_state, value=low_id))
    else:
        low_id = blankpalette[low_state]
    
    # Find id of high state (create new if it is not present in palette)
    if high_state not in blankpalette:
        high_id = min(x for x in range(to_check) if x not in blankpalette.values())
        palette.tags.append(nbt.TAG_Int(name=high_state, value=high_id))
    else:
        high_id = blankpalette[high_state]

    nbtfile.tags.append(palette)
    nbtfile.tags.append(nbt.TAG_Int(name="PaletteMax", value=len(palette)))
    return nbtfile, low_id, high_id

def generate_meta(nbtfile: nbt.NBTFile, blankschem: nbt.NBTFile):
    nbtfile["Offset"].value = blankschem["Offset"].value
    metadata = nbt.TAG_Compound()
    metadata.tags = blankschem["Metadata"].tags.copy()
    metadata.name = "Metadata"
    nbtfile.tags.append(metadata)
    return nbtfile

def generate_schematic(data, layout, blank_name, low_state, high_state):
    blankschem = nbt.NBTFile(blank_name, "rb")
    nbtfile = nbt.NBTFile()

    nbtfile.name = "Schematic"

    nbtfile, low_id, high_id = generate_palette(nbtfile, blankschem, low_state, high_state)

    Width, Lenght, Height = get_dimensions(blankschem)
    nbtfile.tags.extend([
        nbt.TAG_Int(name="DataVersion", value=blankschem["DataVersion"].value),       
        nbt.TAG_Int(name="Version", value=blankschem["Version"].value),
        nbt.TAG_Short(name="Length", value=Lenght),
        nbt.TAG_Short(name="Height", value=Height),
        nbt.TAG_Short(name="Width", value=Width),
        nbt.TAG_Int_Array(name="Offset"),
    ])
    
    nbtfile = generate_meta(nbtfile, blankschem)

    nbtfile.tags.append(nbt.TAG_Byte_Array(name="BlockData"))
    nbtfile["BlockData"].value = generate_block_data(data, layout, blankschem, high_id, low_id)

    return nbtfile