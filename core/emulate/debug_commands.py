import core.config as config
import core.error as error
import core.save.formatter as formatter

def breakpoint():
    if not config.disable_breakpoints:
        print("breakpoint")
        input()

def ram_display(ram, word_size, start, end):
    print(
        generate_ram_display(
            ram, 
            rows=config.debug_ram_rows_count, 
            subrows=config.debug_ram_subrows_count,
            ADRESS_AS_HEX = config.debug_ram_adress_as_hex,
            VALUE_AS = config.debug_ram_values_mode,
            ADD_ASCII_VIEW = config.debug_ram_add_ascii_view,
            start = start,
            end = end
        )
    )
def log(message):
    print(message)

def generate_ram_display(RAM, rows = 16, subrows = 1, ADRESS_AS_HEX = True, VALUE_AS = "bin", ADD_ASCII_VIEW = True, WORD_SIZE=8,  start = 0, end = None):
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
            ADRESS = str(formatter.padhex(val, 2, False))
        elif MODE == "bin":
            PAD = len(str(bin(2**WORD_SIZE-1)[2:]))+1
            ADRESS = formatter.padbin(val, 8, False)
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
                    OUTPUT += " {}:{}{}".format(formatter.padhex(adress, len(hex(len(RAM)-1)[2:])), rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                else:
                    OUTPUT += " {}:{}{}".format(adress, rows_data, " " if subrow_cunter != (subrows-1) else "\n")
                subrow_cunter = (subrow_cunter+1)%subrows
        except Exception as err:
            pass
            
        return OUTPUT


