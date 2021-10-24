import core.error as error
import core.config as config
from core.load.base import Line
import core.parse.base as parser_base

def find_macros(program, context):
    line_iter = iter(program)
    macros = dict()
    new_program = []
    try:
        while line_iter:
                line = next(line_iter)
                line_str = line.line
                if line_str.startswith("#endmacro"):
                    raise error.PreprocesorError("The macro definition hasn't been started (found '#endmacro' without '#macro')")
                if line_str.startswith("#macro"):
                    components = line_str.split(" ")
                    if components[1].find("(") != -1 and components[-1].find(")") != -1:
                        DATA = []
                        conact = ''.join(components[1:])
                        start = conact.find("(")
                        end = conact.find(")")
                        if start == -1:
                            raise error.PreprocesorError("Expected '(' in macro definition")
                        if end == -1:
                            raise error.PreprocesorError("Expected ')' in macro definition")
                        name = components[1][:components[1].find("(")]
                        if len(name) == 0:
                            raise error.PreprocesorError("Expected name for the macro")
                        parametres = conact[start+1:end].split(',')
                        line = next(line_iter)
                        while not line.line.startswith("#endmacro"):
                            if line.line.startswith("#macro"):
                                raise error.PreprocesorError("Canno't define macros in macro")
                            for i, param in enumerate(parametres):
                                line.line = parser_base.smart_replace(line.line, param, "{arg_"+str(i)+"}") #sorry
                            DATA.append(line)
                            try:
                                line = next(line_iter)
                            except StopIteration:
                                raise error.PreprocesorError("he macro definition hasn't been ended (found '#macro' without '#endmacro')")
                        macros[name] = (len(parametres), DATA)
                else:
                    new_program.append(line)
    except StopIteration:
        context['macros'] = macros
        return new_program, context

def apply_all_macros(program, context):
    macros =  context["macros"] if "macros" in context else dict()
    
    new_program = program
    for name, macro in macros.items():
        new_program = apply_macro(new_program, name, macro)
    return new_program, context

def apply_macro(program, name, macro):
    new_program = list()
    for line_obj in program:
        line = line_obj.line
        if line.startswith(name):
            start = line.find("(")
            end = line.find(")")
            if start == -1:
                raise error.LoadError("Expected '(' in macro call")
            if end == -1:
                raise error.LoadError("Expected ')' in macro call")
            args = {"arg_{}".format(i):x.strip() for i, x in enumerate(line[start+1:end].split(","))}
            if len(args) != macro[0]:
                raise error.LoadError("Expected {} arguments in macro, but got: {}".format(macro[0], len(args)))
            for macro_line in macro[1]:
                as_dict = dict(macro_line).copy()
                macro_line = Line(**as_dict)
                macro_line.line = macro_line.line.format_map(args)
                macro_line.macro_instruction_index_in_file=macro_line.line_index_in_file
                macro_line.line_index_in_file=line_obj.line_index_in_file
                macro_line.is_macro_expanded=True
                
                new_program.append(macro_line)
        else:
            new_program.append(line_obj)
    return new_program