import core
import core.error as error
import core.config as config
from core.context import Context
from core.load.base import Line
from core.profile.profile import AdressingMode, Profile
from core.save.formatter import as_values


def translate(program, profile: Profile):
    program = [Line(line, line_index_in_file=-1) for line in program]
    parser_pipeline = core.pipeline.make_parser_pipeline()
    
    partial_save_pipeline = [('fill addresses', core.save.fill.fill_empty_addresses),
                             ('format', core.save.formatter.format_output)]

    program, context = core.pipeline.exec_pipeline(parser_pipeline, program, Context(profile), progress_bar_name=None)
    config.override_from_dict({'save': 'bin'})
    program, context = core.pipeline.exec_pipeline(partial_save_pipeline, program, context, progress_bar_name=None)
    config.override_from_dict({'save': None})
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
    pass # do stuff
