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
                raise
        elif line.startswith("#init"):
            _, *args = line.split(' ')
            settings = ''.join(args)
            if settings:
                context.init.append(settings)
            else:
                raise
        elif line.startswith("#global"):
            context.warnings.append('#global keyword is deprased. Use Section system instead.')
            try:
                _, chunk_name, label_name, *other = line.split()
                if len(other) == 1:
                    offset = other[0]
                elif len(other) == 2:
                    offset, schemoffset = other
                    context.schematic_offset = int(schemoffset, base = 0)
                else:
                    raise
            except:
                raise error.PreprocesorError(program_line.line_index_in_file, f"Expected structure '#global <NAME> <LABEL NAME> <OFFSET> [<OFFSET>]' got: '{line}'")

            context.entry[chunk_name] = (label_name, int(offset))
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
    "#init",
    "#ifdef",
    "#else",
    "#endif",
    "#macro",
    "#endmacro",
    "#global",
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
    