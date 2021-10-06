from . import load
from . import parse
from . import  preprocesor
from typing import *
import core.config as config
import core.error as error

import pprint

def make_preproces_pipeline() -> List[Tuple[str, Callable]]:
    pipeline = \
        [
            ('load', load.loading.load_raw),
            ('strip data', load.loading.strip),
            ('remove comments', load.comments.remove_comments),
            ('remove empty lines', load.loading.remove_empty_lines),
            ('solve defs', preprocesor.definitions.definition_solver),
            ('remove defs', preprocesor.definitions.remove_definitions),
            ('apply consts', preprocesor.definitions.apply_consts),
            ('find macros', preprocesor.macros.find_macros),
            ('apply macros', preprocesor.macros.apply_all_macros),
            ('find meta', preprocesor.meta.get_metadata),
            ('remove preprocesor cmds', preprocesor.meta.remove_known_preprocesor_instructions),
            ('tokenize lines', parse.tokenize.tokenize)
        ]
    return pipeline

def make_parser_pipeline() -> List[Tuple[str, Callable]]:
    pass

def exec_pipeline(pipeline: List[Tuple[str, Callable]], start: Any):
    data = start
    external = dict()
    
    for i, (stage, func) in enumerate(pipeline):
        try:
            output = func(data, external)
        except error.CompilerError as err:
            raise err
        except Exception as other_error:
            print(f"Unhealty error: {other_error}")
            raise other_error

        if isinstance(output, tuple):
            data, other = output
            external.update(other)
        else:
            data = output

        if config.show_pipeline_steges:
            print(f'Stage {i+1}/{len(pipeline)}: {stage}')
    
    if config.show_pipeline_output:
        show_output(print, data)
        pprint.pprint(external)
    return data, external

def example_exec_pipeline():
    pipeline = make_preproces_pipeline()

    compile(pipeline, "H:\scripts\Lord's asm redux\src\program.lor")

def show_output(print, data):
    SPACE = ' '*2
    print('[')
    for line in data[:-1]:
        print(SPACE, line)
    print(SPACE, data[-1],'\n]')
    