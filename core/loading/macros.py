import core.error as error
from core.loading.utility import *
import core.config as config

def find_consts(program, definitions):
    const_values = dict()
    definition = list()

    for item in definitions:
        components = item.split(" ")
        if len(components) > 1:
            const_values[components[0]] = ''.join([x+" " for x in components[1:]]).strip()
        elif len(components) == 1:
            definition.append(components[0])
        else:
            raise error.LoadError("Can't inteprete const expression: {}".format(item))
    for line in program:
        if line[1].startswith("#define"):
            components = line[1].split(" ")
            if len(components) > 2:
                const_values[components[1]] = ''.join([x+" " for x in components[2:]]).strip()
            elif len(components) == 2:
                definition.append(components[1])
            else:
                raise error.LoadError("Can't inteprete const expression: {}".format(line[1]))
    return const_values, definition

def find_macros(program, definitions):
    line_iter = iter(program)
    macros = dict()
    new_program = []
    try:
        while line_iter:
                line = next(line_iter)
                if line[1].startswith("#endmacro"):
                    raise error.LoadError("The macro definition hasn't been started (found '#endmacro' without '#macro')")
                if line[1].startswith("#macro"):
                    components = line[1].split(" ")
                    if components[1].find("(") != -1 and components[-1].find(")") != -1:
                        DATA = []
                        conact = ''.join(components[1:])
                        start = conact.find("(")
                        end = conact.find(")")
                        if start == -1:
                            raise error.LoadError("Expected '(' in macro definition")
                        if end == -1:
                            raise error.LoadError("Expected ')' in macro definition")
                        name = components[1][:components[1].find("(")]
                        if len(name) == 0:
                            raise error.LoadError("Expected name for the macro")
                        parametres = conact[start+1:end].split(',')
                        line = next(line_iter)
                        while not line[1].startswith("#endmacro"):
                            if line[1].startswith("#macro"):
                                raise error.LoadError("Canno't define macros in macro")
                            line_id, line = line
                            for i, param in enumerate(parametres):
                                line = smart_replace(line, param, "{arg_"+str(i)+"}") #sorry
                            DATA.append((line_id, line))
                            try:
                                line = next(line_iter)
                            except StopIteration:
                                raise error.LoadError("he macro definition hasn't been ended (found '#macro' without '#endmacro')")
                        macros[name] = (len(parametres), DATA)
                else:
                    new_program.append(line)
    except StopIteration:
        return macros, new_program

def definition_solver(program, definition):
    recursion = [True]
    else_watchman = [0]
    new_program = []
    if config.DEFINITION_DEBUG:
        print("line", "app", "depth",sep="\t; ")
    for i in range(len(program)):
        if program[i][1].startswith("#ifdef"):
            SPLITED = program[i][1].split(" ")[1]
            recursion.append(True if SPLITED in definition else False)
            else_watchman.append(0)
        elif program[i][1].startswith("#ifndef"):
            SPLITED = program[i][1].split(" ")[1]
            recursion.append(True if SPLITED not in definition else False)
            else_watchman.append(0)
        elif program[i][1] == "#endif":
            if len(recursion) == 1:
                raise error.LoadError("#endif expression without #ifdef or #ifndef")
            recursion.pop()
        elif program[i][1] == "#else":
            if else_watchman[len(recursion)-1] == 0:
                recursion[len(recursion)-1] = not recursion[len(recursion)-1]
                else_watchman[len(recursion)-1] += 1
            else:
                raise error.LoadError("multiple #else expression in same #ifdef/#endif statment")
        else:
            if config.DEFINITION_DEBUG:
                print(program[i][1][:6],  all(recursion), len(recursion), sep="\t; ")
            if all(recursion):
                new_program.append(program[i])
    if len(recursion) != 1:
        raise error.LoadError("Expected #endif expression")
    return new_program

def apply_macro(program, name, macro):
    new_program = list()
    for line in program:
        if line[1].startswith(name):
            start = line[1].find("(")
            end = line[1].find(")")
            if start == -1:
                raise error.LoadError("Expected '(' in macro call")
            if end == -1:
                raise error.LoadError("Expected ')' in macro call")
            args = {"arg_{}".format(i):x.strip() for i, x in enumerate(line[1][start+1:end].split(","))}
            if len(args) != macro[0]:
                raise error.LoadError("Expected {} arguments in macro, but got: {}".format(macro[0], len(args)))
            for macro_line in macro[1]:
                formated = macro_line[1].format_map(args)
                new_program.append((macro_line[0], formated))
        else:
            new_program.append(line)
    return new_program

def datablocks(program):
    DATA = dict()
    for line in program:
        if line[1].startswith("#data"):
            splited = line[1].split(" ")
            ADRESS_START = -1
            try:
                ADRESS_START = int(splited[1], base=0)
            except ValueError:
                raise error.LoadError("Canno't interpretate datablock: {}".format(line))
            start = line[1].find('"')
            end = line[1].rfind('"')
            if start != -1 or end != -1:
                if start == -1 or end == -1:
                    raise error.LoadError("String hasn't been close or open")
                if start != end:
                    data = [ord(x) for x in line[1][start+1:end]]
                else:
                    raise error.LoadError("String hasn't been close or open")
            else:
                data_raw = ''.join(splited[2:])
                if len(data_raw) == 0:
                    raise error.LoadError("Datablock doesn't provide data.")
                data = [int(x, base=0) for x in data_raw.split(',')]
            for index, value in enumerate(data):
                DATA[index+ADRESS_START] = value
    return DATA

def const_evaluation(program, definitions):
    #find consts and definitions (#define X or #define X value)
    const_values, definition = find_consts(program, definitions)
    
    #remove these definitions
    program = [x for x in program if not x[1].startswith("#define")]

    #evalueate definitions
    new_program = definition_solver(program, definition)

    data = datablocks(new_program)
    new_program = [x for x in new_program if not x[1].startswith("#data")]

    #apply definitions
    for i, _ in enumerate(new_program):
        for const, value in const_values.items():
            new_program[i] = (new_program[i][0], smart_replace(new_program[i][1], const, value))

    #find macros
    macros, new_program = find_macros(new_program, definitions)

    #apply macros
    for name, macro in macros.items():
        new_program = apply_macro(new_program, name, macro)

    return new_program, data
