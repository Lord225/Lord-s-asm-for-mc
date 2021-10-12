import core.error as error
import core.config as config
import os
from tabulate import tabulate

def save(program, context):
    outfile = config.outfile
    dirname = os.path.dirname(outfile)
    filename, ext = os.path.splitext(os.path.basename(outfile))
    for chunk, data in program.items():
        new_filename = os.path.join(dirname, f"{filename}_{chunk}{ext}")
        with open(new_filename, 'w') as file:
            if context['tabulate']:
                collected = [line.formatted for line in data]
                file.write(tabulate(collected))
            else:
                for line in data:
                    assert isinstance(line.formatted, str)
                    file.write(f'{line.formatted}\n')


    return program, context