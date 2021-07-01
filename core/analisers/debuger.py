import core.error as error
import core.loading as loading
import core.config as config
from core.analisers.parser import *

def generate_ram_display(RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "bin", ADD_ASCII_VIEW = True, start = 0, end = None):
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
    WORD_SIZE = base.PROFILE.profile["CPU"]["parametrs"]["word len"]

    if rows%subrows != 0:
        raise error.UndefinedSetting("Row number should be dividable by subrow count.")
    def generate_value(PAD = -1, MODE = "dec"):
        ADRESS = ""
        try:
            val = RAM[adress + i]
        except IndexError:
            raise "END"
        if MODE == "dec":
            PAD = len(str(int(2**WORD_SIZE)-1))+1
            ADRESS = str(val)
        elif MODE == "hex":
            PAD = len(str(hex(2**WORD_SIZE-1)[2:]))+1
            ADRESS = str(padhex(val, 2, False))
        elif MODE == "bin":
            PAD = len(str(bin(2**WORD_SIZE-1)[2:]))+1
            ADRESS = padbin(val, 8, False)
        return '{}{}'.format(" "*(PAD-len(ADRESS)), ADRESS)

    totalrows = rows
    rows //= subrows
    LINE_START = 0
    subrow_cunter = 0
    OUTPUT = "\n"
    
    if config.RAM_DEBUG_MODE == "simple":
        return '\n'.format(RAM)
    elif config.RAM_DEBUG_MODE == "row":
        try:
            for adress in range(0, len(RAM), rows):
                if not (adress in range(start, end)):
                    continue

                if subrow_cunter == 0:
                    LINE_START = adress
                rows_data = ""
                for i in range(rows):
                    rows_data += generate_value(-1, VALUE_AS)
                
                if ADD_ASCII_VIEW:
                    if subrow_cunter == (subrows-1):
                        asciirep = ""
                        for i in range(totalrows):
                            char_id = RAM[LINE_START+i]
                            asciirep += chr(char_id) if char_id >= 32 and char_id < 127 else "."

                        rows_data += "\t{}".format(asciirep)
                
                if ADRESS_AS_HEX:
                    OUTPUT += " {}:{}{}".format(padhex(adress, len(hex(len(RAM))[2:])), rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                else:
                    OUTPUT += " {}:{}{}".format(adress, rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                subrow_cunter = (subrow_cunter+1)%subrows
        except Exception as err:
            pass
            
        return OUTPUT

def execute_debug_command(device, target_core:int, debug_cmd:str):
    output_stream = print

    debug_cmd = debug_cmd[1:] # remove '#'
    if config.DEBUG_MODE == "simple":
        if debug_cmd == "regs":
            output_stream("Core{} regs =".format(target_core),device.CORES[target_core].get_regs_status())
        elif debug_cmd == "break":
            output_stream("CPU hit breakpoint")
            input()
        elif debug_cmd == "ram":
            output_stream(generate_ram_display(device.RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "dec", ADD_ASCII_VIEW = True))
        elif debug_cmd.startswith("ramslice"):
            values = extract_from_brackets(debug_cmd,'(',')')
            start, end = [get_value(val) for val in values.split(',')]
            output_stream(generate_ram_display(device.RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "dec", ADD_ASCII_VIEW = True, start = start, end = end))
        elif debug_cmd[:4] == "log ":
            output_stream(solve_log_command(debug_cmd[4:], device, target_core))
        else:
            check_for_custom_debug_function(debug_cmd, device, target_core)

def check_for_custom_debug_function(cmd: str, device, target_core: int):
    cmd_name = cmd[:cmd.find('(')];
    values = extract_from_brackets(cmd,'(',')')
    try:
        function = getattr(device.CORES[target_core], cmd_name)
        args = values.split(',') if values != '' else []
        
        function(*args)
    except:
        raise error.LoadError("Cannot find debug function called: '{}' with arguments '{}'".format(cmd_name, values));

def solve_log_command(cmd: str, device, target_core: int):
    MAP = device.CORES[target_core].__dict__
    return cmd.format_map(MAP)


def find_if_line_is_marked(line: int, JUMP_LIST: dict()):
        for key, val in JUMP_LIST.items():
            if val+1 == line:
                return str(key)
        return None