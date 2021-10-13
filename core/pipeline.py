from . import load
from . import parse
from . import preprocesor
from . import save
from typing import *
import core.config as config
import core.error as error
from click import progressbar

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
            ('remove preprocesor cmds', preprocesor.meta.remove_known_preprocesor_instructions)
        ]
    return pipeline

def make_parser_pipeline() -> List[Tuple[str, Callable]]:
    pipeline = \
        [
            ('tokenize lines', parse.tokenize.tokenize),
            ('find labels', parse.jumps.find_labels),
            ('find commands', parse.match_commands.find_commands),
            ('add debug data', parse.debug_heades.add_debug_metadata),
            ('generate values', parse.generate.generate),
            ('assert argument sizes', parse.assert_arguments.assert_arguments)
        ]
    return pipeline

def make_save_pipeline()  -> List[Tuple[str, Callable]]:
    pipeline = \
        [
            ('split into chunks', parse.split_into_chunks.split_into_chunks),
            ('format', save.formatter.format_output),
            ('add comments', save.add_comments.add_comments),
            ('save', save.saver.save),
        ]
    return pipeline
def check_types(lines, stage):
    for line in lines:
        assert isinstance(line, load.Line), f"Stage {stage} returned wrong datatype."
def exec_pipeline(pipeline: List[Tuple[str, Callable]], start: Any, external = {}, progress_bar_name = None):
    data = start

    if 'warnings' not in external:
        external['warnings'] = list()

    def format_function(x):
        return str(x[1][0]) if x is not None else ''

    if config.show_pipeline_steges != 'bar':
        class PlaceHolder:
            def __init__(self, iter, **kwrgs):
                self.iter = iter
            def __enter__(self):
                return self.iter
            def __exit__(self, *args):
                pass
        bar = PlaceHolder
    else:
        bar = progressbar
    
    with bar(enumerate(pipeline), item_show_func=format_function, label=progress_bar_name) as pipeline_iterator:
        for i, (stage, func) in pipeline_iterator:
            try:
                output = func(data, external)
            except error.CompilerError as err:
                err.stage == stage
                raise err
            except Exception as other_error:
                raise other_error

            if isinstance(output, tuple):
                data, other = output
                external.update(other)
            else:
                data = output

            if config.pipeline_debug_asserts:
                if isinstance(data, list):
                    check_types(data, stage)
                elif isinstance(data, dict):
                    for _, lines in data.items():
                        check_types(lines, stage)
                else:
                    raise Exception(f"Stage {stage} returned wrong datatype.")
            if config.show_pipeline_steges == "simple":
                print(f'Stage {i+1}/{len(pipeline)}: {stage}')
        
        if config.show_pipeline_output:
            show_output(print, data)
            pprint.pprint(external)
        return data, external

def show_output(print, data, SPACE = ''):
    if isinstance(data, list):
        SPACEHERE = SPACE + ' '*2
        print(SPACE, '[')
        for line in data[:-1]:
            print(SPACEHERE, line)
        if len(data) != 0:
            print(SPACEHERE, data[-1],f'\n{SPACE}]')
        else:
            print(SPACEHERE,']')
    else:
        SPACEHERE = SPACE + ' '*2
        print(SPACE, "{")
        for key, val in data.items():
            print(SPACEHERE, key, ":")
            show_output(print, val, SPACEHERE)
        print(SPACE, "}")

