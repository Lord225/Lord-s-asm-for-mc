from typing import Dict, List, Tuple
from core.context import Context
import core.error as error
import core.config as config
import core.parse.base as parser_base

def definition_solver(program, context: Context):
    recursion = [True]
    else_watchman = [0]
    new_program = []

    definition = context.defs
    consts = context.const
    
    if config.DEFINITION_DEBUG:
        print("line", "app", "depth",sep="\t; ")
    for i in range(len(program)):
        if program[i].line.startswith("#ifdef"):
            SPLITED = program[i].line.split(" ")[1]
            recursion.append(True if SPLITED in definition else False)
            else_watchman.append(0)
        elif program[i].line.startswith("#ifndef"):
            SPLITED = program[i].line.split(" ")[1]
            recursion.append(True if SPLITED not in definition else False)
            else_watchman.append(0)
        elif program[i].line == "#endif":
            if len(recursion) == 1:
                raise error.PreprocesorError(i, "#endif expression without #ifdef or #ifndef")
            recursion.pop()
        elif program[i].line.startswith("#else"):
            if else_watchman[len(recursion)-1] == 0:
                recursion[len(recursion)-1] = not recursion[len(recursion)-1]
                else_watchman[len(recursion)-1] += 1
            else:
                raise error.PreprocesorError(i, "multiple #else expression in same #ifdef/#endif statment")
        else:
            if config.DEFINITION_DEBUG:
                print(program[i].line[:6],  all(recursion), len(recursion), sep="\t; ")
            if all(recursion):
                new_program.append(program[i])
                if program[i].line.startswith("#define"):
                    new_defs, new_consts = add_definition(program[i].line, i)
                    consts.update(new_consts)
                    definition.extend(new_defs)
    if len(recursion) != 1:
        raise error.PreprocesorError(None, "Expected #endif")
    return new_program, context
def add_definition(line: str, i) -> Tuple[List[str], Dict[str, str]]:
    components = line.split(" ")
    if len(components) > 2:
        return list(), {str(components[1]): ''.join([x + " " for x in components[2:]]).strip()}
    elif len(components) == 2:
        if not components[1].isupper():
            raise error.PreprocesorError(i, f"Definitions should have UPPER CASE NAMES. got: {components[1]}")
        return [components[1]], {}
    else:
        raise error.PreprocesorError(i, "Can't inteprete #define expression: '{}'".format(line))
def apply_consts(program, context: Context):
    for i, _ in enumerate(program):
        for const, value in context.const.items():
            program[i].line = parser_base.smart_replace(program[i].line, const, value)
    return program, context
def remove_definitions(program, context: Context):
    return [x for x in program if not x.line.startswith("#define")], context

