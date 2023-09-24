from core.context import Context
import core.error as error
import core.config as config
import core.save.exporter as exporter
import os
from tabulate import tabulate
import json
import sys

def collect_data(data):
    return [line.formatted for line in data]

def save(program, context: Context):
    dirname = config.output
    filename, ext = os.path.splitext(os.path.basename(dirname))
    filenames = {}

    # check if directory exists
    if not os.path.exists(dirname):
        os.makedirs(os.path.dirname(dirname), exist_ok=True)

    if config.save == 'schem':
        exporter.generate_schematic_from_formatted(program, context)
        return program, context
        
    if config.save == "pip":        
        data_to_dump = { 'profile_name': context.profile_name, "data": dict() }

        data_to_dump["data"] = collect_data(program)
        
        json.dump(data_to_dump, sys.__stdout__)
        
    else:
        filenames['default'] = filename
        with open(dirname, 'w') as file:
            collected = [line.formatted for line in program]
            file.write(tabulate(collected, tablefmt = config.tablefmt))
        context.outfiles.append(filenames)

    return program, context