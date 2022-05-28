from typing import Dict, List
import core.config as config
import core.error as error
from core.parse.jumps import SectionMeta

from core.profile.profile import Profile


def check_keywords_exists(entry, context):
    profile: Profile = context['profile']
    profilekeywords = set(profile.keywords)
    entrykeywords = set(entry.keys())
    
    missing_entrypoints = profilekeywords-entrykeywords
    missing_keywords = entrykeywords-profilekeywords

    if len(missing_keywords) != 0:
        msg = f"Keywords: {missing_keywords} are not defined in profile" if len(missing_entrypoints) != 1 else  f"Keyword: {missing_keywords} is not defined in profile"
        if config.rise_on_missing_keyword:
            raise error.ParserError(None, msg) # bad one
        else:
            context['warnings'].append(msg)
    if len(missing_entrypoints) != 0:
        msg = f"Keywords: {missing_entrypoints} are defined in profile but not used" if len(missing_entrypoints) != 1 else  f"Keyword: {missing_entrypoints} is defined in profile but never used"
        if config.rise_on_missing_entrypoint:
            raise error.ParserError(None, msg)
        else:
            context['warnings'].append(msg)

def gather_instructions_by_section(program, sections: Dict[str, SectionMeta]):
    chunks = {x:list() for x in sections.keys()}

    for line_obj in program:
        chunks[line_obj.section.name].append(line_obj)
    return chunks

def get_adress_offset(current_line_obj, profile: Profile):
    if profile.adressing.mode == 'align':
        return max(profile.arguments_len.values())
    elif profile.adressing.mode == 'packed':
        return int(profile.arguments_len[list(current_line_obj.parsed_command.keys())[0]])
    raise RuntimeError("Logic Error")

def get_address(current_chunk_physical_adress, profile: Profile):
    return current_chunk_physical_adress//profile.adressing.bin_len+profile.adressing.offset

def find_key_by_value(dict: dict, value):
    output = []
    for key, val in dict.items():
        if val == value:
            output.append(key)
    return output

def calculate_addresses(chunks: dict, sections: Dict[str, SectionMeta], profile: Profile, labels: dict):
    used_addresses = dict()
    chunk_labels_physical_adresses = dict()
    chunk_labels = dict()

    def handle_labels(i, chunk_physical_adress):
        label = find_key_by_value(labels, i)
        if len(label) != 0:
            for lab in label:
                chunk_labels_physical_adresses[lab] = chunk_physical_adress
                chunk_labels[lab] = i
    def find_last_used_address(section_name):
        if len(used_addresses) == 0:
            return 0
        return max(address for address, section in used_addresses.items() if section == section_name)
    
    def add_address(chunk_physical_adress, section):
        if chunk_physical_adress in used_addresses:
            raise error.CompilerError(None, f"Cannot solve sections addresses: {section} overlaps with {last_section}")
        used_addresses[chunk_physical_adress] = section

    last_section = 'default'
    
    i = 1
    for section_name, chunk in chunks.items():
        section = sections[section_name]
        offset = section.offset
        write = section.write

        if offset == None:
            offset = find_last_used_address(last_section)+1

        current_chunk_physical_adress = 0
        
        # Calculate physical address for each command (relative to section)
        for line_obj in chunk:

            chunk_physical_adress = get_address(current_chunk_physical_adress, profile)+offset
            
            handle_labels(i, chunk_physical_adress)
            add_address(chunk_physical_adress, section.name)

            line_obj.physical_adress = chunk_physical_adress
            current_chunk_physical_adress += get_adress_offset(line_obj, profile)
            
            i += 1
        last_section = section_name
    return used_addresses, chunk_labels_physical_adresses, chunk_labels
        
def stick_chunks(chunks, used_addresses, chunk_labels):
    output = list()
    
    for val in chunks.values():
        output.extend(val)
    
    program = sorted(output, key = lambda x: x.physical_adress)

    return program

def solve_sections(program, context):
    labels: dict = context['labels']
    profile: Profile = context['profile']
    sections: Dict[str,SectionMeta] = context["sections"]

    chunks = gather_instructions_by_section(program, sections)

    used_addresses, chunk_labels_physical_adresses, chunk_labels = calculate_addresses(chunks, sections, profile, labels)
    
    context['physical_adresses'] = {key:val for key, val in chunk_labels_physical_adresses.items()}
    context['chunk_adreses'] = chunk_labels
    context['used_addresses'] = used_addresses
    context['namespace'] = None
    context['use_phisical_adresses'] = True

    program = stick_chunks(chunks, used_addresses, chunk_labels)

    return program, context
