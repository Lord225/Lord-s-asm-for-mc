from core.context import Context
import core.error as error
import core.config as config

def get_metadata(program, context: Context):
    for program_line in program:
        line: str = program_line.line
        if line.startswith("#profile"):
            _, *args = line.split(' ')
            profile_name = ''.join(args)
            if profile_name:
                if context.profile_name:
                    raise error.PreprocesorError(None, "Multiple profiles defitions")
                context.profile_name = profile_name
            else:
                raise error.PreprocesorError(program_line.line_index_in_file, "Profile name is empty")
        elif line.startswith("#data"):
            splited = line.split(" ")
            ADRESS_START = -1

            try:
                ADRESS_START = int(splited[1], base=0)
            except ValueError:
                raise error.PreprocesorError(program_line.line_index_in_file, "Canno't interpretate datablock: {}".format(line))
            
            start = line.find('"')
            end = line.rfind('"')
            if start != -1 or end != -1:
                if start == -1 or end == -1:
                    raise error.PreprocesorError(program_line.line_index_in_file, "String hasn't been close or open")
                if start != end:
                    data = [ord(x) for x in line[start+1:end]]
                else:
                    raise error.PreprocesorError(program_line.line_index_in_file, "String hasn't been close or open")
            else:
                data_raw = ''.join(splited[2:])
                if len(data_raw) == 0:
                    raise error.PreprocesorError(program_line.line_index_in_file, "Datablock doesn't provide data.")
                data = [int(x, base=0) for x in data_raw.split(',')]
            for index, value in enumerate(data):
                context.data[index+ADRESS_START] = value

    return program, context

KNOWON_PREPROCESOR_TOKENS = \
[ 
    "#profile",
    "#ifdef",
    "#else",
    "#endif",
    "#macro",
    "#endmacro",
    "#data",
]

DEBUG_TOKEN = "#debug"

def remove_known_preprocesor_instructions(program, context: Context):
    output_program = list()
    for program_line in program:
        line: str = program_line.line
        if any((line.startswith(token) for token in KNOWON_PREPROCESOR_TOKENS)):
            continue
        
        if line.startswith(DEBUG_TOKEN):
            context.debug.append(program_line)
            continue
        
        output_program.append(program_line)
    return output_program, context
    