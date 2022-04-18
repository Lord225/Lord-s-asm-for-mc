from numpy import dtype, ndarray, split
import core.config as config
import core.error as error
import core.save.formatter as formatter
import tabulate

def breakpoint():
    if not config.disable_breakpoints:
        print("breakpoint", end='')
        input()

def ram_display(ram, word_size, start, end):
    print(
        generate_ram_display(
            ram, 
            rows = config.debug_ram_rows_count, 
            subrows = config.debug_ram_subrows_count,
            ADRESS_AS_HEX = config.debug_ram_adress_as_hex,
            VALUE_AS = config.debug_ram_values_mode,
            ADD_ASCII_VIEW = config.debug_ram_add_ascii_view,
            start = start,
            end = end
        )
    )
def log(message):
    print(message)

def generate_ram_display(RAM: ndarray, rows = 8, subrows = 2, ADRESS_AS_HEX = True, VALUE_AS = "bin", ADD_ASCII_VIEW = True, start = 0, end = None):
    """
    It just works.
    """
    if start != 0:
        start = start + (rows - start % rows)-rows
    else:
        start = 0

    if end is not None:
        end = end + (rows - end % rows)
    else:
        end = len(RAM)

    #TODO Make it use profiles values
    if RAM.dtype == dtype('uint8'):
        WORD_SIZE = 8
    elif RAM.dtype == dtype('uint16'):
        WORD_SIZE = 16
    else:
        WORD_SIZE = 32

    if rows%subrows != 0:
        raise error.EmulationError("Row number should be dividable by subrow count.")

    def generate_value(val, MODE = "hex"):
        if MODE == "dec":
            return f'{str(int(val))}'
        elif MODE == "hex":
            return f'{str(formatter.padhex(int(val), WORD_SIZE)):>4}'
        elif MODE == "bin":
            return f'{str(formatter.padbin(int(val), WORD_SIZE)):>16}'
        
    def generate_row(array):
        return [generate_value(val) for val in array]

    def generate_ascii(array):
        def to_ascii(x) -> str:
            return chr(x) if x >= 32 and x < 127 else "."
        return ''.join((''.join([to_ascii(x) for x in chunk]) for chunk in array))

    RAM_VIEW = RAM[start:end]
    chunk_size = len(RAM_VIEW)//rows
    
    if config.RAM_DEBUG_MODE == "simple":
        return '\n'.format(RAM)
    elif config.RAM_DEBUG_MODE == "row":
        chunks = split(RAM_VIEW, chunk_size)
        chunks = [split(y, subrows) for y in chunks]

        as_str = [[generate_row(chunk)+[' '] for chunk in superchunks] for superchunks in chunks]
        
        out_rows = list()
        for i, (superchunk, y) in enumerate(zip(as_str, chunks)):
            d = list()
            d.append(hex(i*rows))
            d.append(" ")
            for x in superchunk:
                d.extend(x)
            d.append(generate_ascii(y))
            out_rows.append(d)

        return tabulate.tabulate(out_rows)


