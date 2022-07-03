import core
from core.context import Context
import core.error as error
import core.config as config
from core.load.base import Line
from core.profile.profile import Profile

def fill_empty_addresses(program, context: Context):
    profile: Profile = context.get_profile()    
    addresing = profile.adressing

    if config.use_fill == False:
        return program, context
    if profile.fill is None:
        context.warnings.append("Fill command is not defined in profile. Skipping.")
        return program, context

    fill_command = Line(profile.fill, line_index_in_file=-1)

    parser_pipeline = core.pipeline.make_parser_pipeline()

    fill_prog, _ = core.pipeline.exec_pipeline(parser_pipeline, [fill_command], Context(context.get_profile()), progress_bar_name=None)

    fill = fill_prog[0]

    lines_by_addresses = {line.physical_adress:line for line in program}
    last_address = max(lines_by_addresses.keys())
    first_address = min(lines_by_addresses.keys())
    

    new_program = list()
    for address in range(first_address, last_address+1):
        if address not in context.used_addresses:
            fill_cp = Line(**fill.copy())
            fill_cp.physical_adress = address
            new_program.append(fill_cp)
        else:
            if address in lines_by_addresses:
                new_program.append(lines_by_addresses[address])

    return new_program, context