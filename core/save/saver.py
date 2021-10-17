import core.error as error
import core.config as config
import os
from tabulate import tabulate
import json

def collect_data(data):
    return [line.formatted for line in data]

def save(program, context):
    outfile = config.output
    dirname = os.path.dirname(outfile)
    filename, ext = os.path.splitext(os.path.basename(outfile))
    filenames = {}
    json_encode = json.JSONEncoder()
    for chunk, data in program.items():
        new_filename = os.path.join(dirname, f"{filename}_{chunk}{ext}")
        filenames[chunk] = new_filename
        with open(new_filename, 'w') as file:
            if context['tabulate']:
                collected = [line.formatted for line in data]
                file.write(tabulate(collected))
            else:
                output_structure = {'entry': chunk, 'program': collect_data(data)}
                json.dump(output_structure, file, indent=config.json_output_indent)
    context['outfiles'] = filenames

    return program, context