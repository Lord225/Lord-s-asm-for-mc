import core.config as config
import core.error as error
import math

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

def split_into_chunks(program, context):
    entry: dict = context['entry']
    labels: dict = context['labels']
    new_labels = dict()
    namespace = dict()
    try:
        entry = {chunk_name:(label_name, offset, labels[label_name]) for chunk_name, (label_name, offset) in entry.items()}
    except KeyError as err:
        raise error.ParserError(None, f"Label marked as global: {err} cannot be founded in skope")
    chunks = {chunk_name: list() for chunk_name in entry.keys()}

    chunk_name, current_chunk = get_next_chunk(entry, 0)
    chunk_name_next, current_chunk_next = get_next_chunk(entry, current_chunk[2])

    current_chunk_index = 0

    for i, program_line in enumerate(program):
        i += 1
        current_chunk_index += 1

        if i >= current_chunk_next[2]:
            if chunk_name_next is None:
                break
            chunk_name, current_chunk = get_next_chunk(entry, current_chunk[2])
            chunk_name_next, current_chunk_next = get_next_chunk(entry, current_chunk[2])
            current_chunk_index = 1

        label = find_key_by_value(labels, i)
        if len(label) != 0:
            for lab in label:
                new_labels[lab] = current_chunk_index
            
        chunks[chunk_name].append(program_line)

    context['chunked_labels'] = new_labels
    context['namespace'] = namespace

    return chunks, context