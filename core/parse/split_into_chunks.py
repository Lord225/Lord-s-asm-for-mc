import core.config as config
import core.error as error
import math

from core.profile.profile import Profile

def get_next_chunk(entry, minimal_offset):
    minimal = (None, ('None', -1, math.inf))
    for key, val in entry.items():
        if val[2] > minimal_offset and val[2] < minimal[1][2]:
            minimal = (key, val)
    return minimal

def find_key_by_value(dict: dict, value):
    output = []
    for key, val in dict.items():
        if val == value:
            output.append(key)
    return output

def check_keywords_exists(entry, context):
    profile: Profile = context['profile']
    profilekeywords = set(profile.keywords)
    entrykeywords = set(entry.keys())
    
    missing_entrypoints = profilekeywords-entrykeywords
    missing_keywords = entrykeywords-profilekeywords

    if len(missing_keywords) != 0:
        msg = f"Keywords: {missing_keywords} are not defined in profile" if len(missing_entrypoints) != 1 else  f"Keyword: {missing_keywords} is not defined in profile"
        if config.rise_on_missing_keyword:
            raise error.ParserError(msg) # bad one
        else:
            context['warnings'].append(msg)
    if len(missing_entrypoints) != 0:
        msg = f"Keywords: {missing_entrypoints} are defined in profile but not used" if len(missing_entrypoints) != 1 else  f"Keyword: {missing_entrypoints} is defined in profile but never used"
        if config.rise_on_missing_entrypoint:
            raise error.ParserError(msg)
        else:
            context['warnings'].append(msg)

def get_adress_offset(current_line_obj, profile: Profile):
    if profile.adressing.mode == 'align':
        return max(profile.arguments_len.values())
    elif profile.adressing.mode == 'packed':
        return profile.arguments_len[list(current_line_obj.parsed_command.keys())[0]]

def split_into_chunks(program, context):
    entry: dict = context['entry']
    labels: dict = context['labels']
    profile: Profile = context['profile']
    physical_adresses = dict()
    chunk_labels = dict()
    namespace = dict()
    
    check_keywords_exists(entry, context)

    try:
        entry = {chunk_name:(label_name, offset, labels[label_name]) for chunk_name, (label_name, offset) in entry.items()}
    except KeyError as err:
        raise error.ParserError(None, f"Label marked as global: {err} cannot be founded in skope")
    chunks = {chunk_name: list() for chunk_name in entry.keys()}

    chunk_name, current_chunk = get_next_chunk(entry, 0)
    chunk_name_next, current_chunk_next = get_next_chunk(entry, current_chunk[2])

    current_chunk_physical_adress = current_chunk[1]
    current_chunk_adress = 1
    
    for i, program_line in enumerate(program):
        i += 1

        if i >= current_chunk_next[2]:
            if chunk_name_next is None:
                break
            chunk_name, current_chunk = get_next_chunk(entry, current_chunk[2])
            chunk_name_next, current_chunk_next = get_next_chunk(entry, current_chunk[2])
            current_chunk_physical_adress = current_chunk[1]
            current_chunk_adress = 1

        label = find_key_by_value(labels, i)
        if len(label) != 0:
            for lab in label:
                physical_adresses[lab] = current_chunk_physical_adress
                chunk_labels[lab] = current_chunk_adress
        
        program_line.physical_adress = current_chunk_physical_adress//profile.adressing.bin_len+profile.adressing.offset
        chunks[chunk_name].append(program_line)
        
        current_chunk_physical_adress += get_adress_offset(program_line, profile)
        current_chunk_adress += 1
    
    context['physical_adresses'] = {key:val//profile.adressing.bin_len+profile.adressing.offset for key, val in physical_adresses.items()}
    context['chunk_adreses'] = chunk_labels
    context['namespace'] = namespace
    context['use_phisical_adresses'] = True

    return chunks, context