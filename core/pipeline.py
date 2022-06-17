from . import load
from . import parse
from . import preprocesor
from . import save
from typing import List, Tuple, Callable, Any
import core.config as config
import core.error as error
from click import progressbar

import pprint

def make_preproces_pipeline() -> List[Tuple[str, Callable]]:
    """
    Pipieline that is responsible for loading and preprocesing data.
    Input:
    * Path to file
    Output:
    * List of line obj
       - `line_index_in_file` - line inside the file
       - `line` - str of preprocessed lines of code without comments or preprocesing instructions
    * Context dict
       - `const` - dict of consts and its values
       - `data` - dict of adresses and its values
       - `debug` - list of debug lines obj's (these objs contains `line_index_in_file` field and `line` field)
       - `defs` - list of definitions (`#define` without values)
       - `entry` - dict of entrypoints with coresponding labels and offsets
       - `macros` - dict of macros
       - `profile_name` - name of profile
       - `warnigns` - warnings that occure in this pipeline.
    """
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
            
            #('tokenize lines', parse.tokenize.tokenize)

        ]
    return pipeline

def make_parser_pipeline() -> List[Tuple[str, Callable]]:
    """
    Pipieline that is responsible for parsing the lines from preprocesing pipeline
    Input:
    * Output from preprocesing pipeline
    Output:
    * Dict of Lists that associates chunk of entrypoint with data
    * Every Chunk contains list of line objs with fields:
       - Everything from previous pipeline
       - `debug` - debug meta-data for this line.
       - `mached_command` - mached command in cmd defs in profile and argument values
       - `parsed_command` - ROM arguments with parsed values
       - `physical_adress` - adress of command in device space
       - `tokenized` - tokenized line
    * Context dict
       - Everything from previous pipeline
       - `profile` - profile object
       - `warnigns` - warnings that occure in this pipeline.
       - `labels` - founed labels with corresponding lines
       - `physical_adress` - founded labels but with adresses in device space
       - `namespace` - idk
    """
    pipeline = \
        [
            ('tokenize lines', parse.tokenize.tokenize),
            ('expand macros', parse.macros.expand_macros),
            ('tokenize lines', parse.tokenize.tokenize),
            ('find sections', parse.jumps.find_sections),
            ('find labels', parse.jumps.find_labels),
            ('find commands', parse.match_commands.find_commands),
            ('add debug data', parse.debug_heades.add_debug_metadata),
            ('generate values', parse.generate.generate),
            ('add debug logs', parse.debug_heades.add_debug_command_logging),
            ('test', parse.solve_sections.solve_sections),
            ('find commands with physical addresses', parse.match_commands.find_commands),
            ('generate values', parse.generate.generate),
        ]
    return pipeline

def make_save_pipeline()  -> List[Tuple[str, Callable]]:
    """
    Pipieline that is responsible for formatting and saveing files
    Input:
    * Output from parsing pipeline
    Output:
       - Everything from previous pipeline
       - `formatted` - list of formated tokens (cound be merged to get formated and padded line)
    * Context dict
        - Everything from previous pipeline
        - `chunk adresses` - adresses of the lines but relative to chunk start adress
        - `outfiles` - outputed files with formatted output
    """
    pipeline = \
        [
            ('fill addresses', save.fill.fill_empty_addresses),
            ('format', save.formatter.format_output),
            ('add comments', save.add_comments.add_comments),
            ('save', save.saver.save),
        ]
    return pipeline
def make_format_pipeline()  -> List[Tuple[str, Callable]]:
    """
    Pipieline that is responsible for formatting lines
    Input:
    * Output from parsing pipeline
    Output:
       - Everything from previous pipeline
       - `formatted` - list of formated tokens without comments
    * Context dict
        - Everything from previous pipeline
        - `chunk adresses` - adresses of the lines but relative to chunk start adress
    """
    pipeline = \
        [
            ('format', save.formatter.format_output),
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
        # Placeholder that will mimic progressbar function.
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

        for st in pipeline_iterator:
            if isinstance(st, int):
                raise
            i, (stage, func) = st

            try:
                output = func(data, external)   # Execute stage
            except error.CompilerError as err:
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

