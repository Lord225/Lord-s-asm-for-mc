import json
# TODO FIX:
# *not
# *adc, sbc, and, or ect
base = \
    {
        "CPU":
        {
            "Name": "PotaDOS",
            "Arch": "POTDOS",
            "Author": "Gwiezdny Kartofel - Lord225",
            "emulator": "potados_emulator",
            "time_per_cycle": 3.3,

            "ARGUMENTS": {
                "variants":
                {
                    "const16":
                    {
                        "pdec": {
                            "size": 2
                        },
                        "const": {
                            "size": 16
                        },
                        "dst": {
                            "size": 4
                        }
                    },
                    "branch":
                    {
                        "pridec": {
                            "size": 2
                        },
                        "secdec": {
                            "size": 3
                        },
                        "r2": {
                            "size": 4
                        },
                        "offsetHi": {
                            "size": 5
                        },
                        "r1": {
                            "size": 4
                        },
                        "offsetLo": {
                            "size": 4
                        }
                    },
                    "aluimm":
                    {
                        "pridec": {
                            "size": 2
                        },
                        "secdec": {
                            "size": 3
                        },
                        "r2": {
                            "size": 4
                        },
                        "I": {
                            "size": 1
                        },
                        "R1": {
                            "size": 8
                        },
                        "dst": {
                            "size": 4
                        }
                    },
                    "alufpu":
                    {
                        "pridec": {
                            "size": 2
                        },
                        "secdec": {
                            "size": 3
                        },
                        "r2": {
                            "size": 4
                        },
                        "flags": {
                            "size": 3
                        },
                        "4th": {
                            "size": 2
                        },
                        "r1": {
                            "size": 4
                        },
                        "dst": {
                            "size": 4
                        }
                    },
                    "indirectlsh":
                    {
                        "pridec": {
                            "size": 2
                        },
                        "secdec": {
                            "size": 3
                        },
                        "ptr": {
                            "size": 4
                        },
                        "3th": {
                            "size": 3
                        },
                        "lsh": {
                            "size": 2
                        },
                        "offset": {
                            "size": 4
                        },
                        "srcdst": {
                            "size": 4
                        }
                    },
                    "indirect":
                    {
                        "pridec": {
                            "size": 2
                        },
                        "secdec": {
                            "size": 3
                        },
                        "ptr": {
                            "size": 4
                        },
                        "3th": {
                            "size": 3
                        },
                        "offset": {
                            "size": 6
                        },
                        "srcdst": {
                            "size": 4
                        }
                    },
                    "other":
                    {
                        "pridec": {
                            "size": 2
                        },
                        "secdec": {
                            "size": 3
                        },
                        "src": {
                            "size": 4
                        },
                        "3th": {
                            "size": 3
                        },
                        "4th": {
                            "size": 2
                        },
                        "pad": {
                            "size": 4
                        },
                        "dst": {
                            "size": 4
                        }
                    },
                    "inject":
                    {
                        "value": {
                            "size": 22
                        }
                    }
                }
            },

            "ADRESSING":
            {
                "mode": "align",
                "bin_len": 22,
                "offset": 0
            },

            "DEFINES": [
                "__POTDOS__",
                ["SP", "15"],  # Stack Ptr
                ["PC", "7"],   # Program Counter
                ["PT", "1"],   # Offset Pointer 
                ["FL", "8"]    # Flags
            ],
            "KEYWORDS":{
                "CORE0":{
                    "offset":0,
                    "write":0
                }
            },
            "FILL":"nop",
            "COMMANDS": {
            }
        }
    }

#
# Others Part 1
#
cmds = \
{
    "nop": {
        "pattern": "nop",
        "command_layout": "const16",
        "bin": {
            "pdec": 0,
            "const": 0,
            "dst": 0
        }
    },
    "load imm": {
        "pattern": "mov reg[{dst:num}], {val:num}",
        "command_layout": "const16",
        "bin": {
            "pdec": 0,
            "const": "val",
            "dst": "dst"
        }
    },
    # Alias load imm
    "jmp": {
        "pattern": "jmp {label:label}", 
        "command_layout": "const16",
        "bin": {
            "pdec": 0,
            "const": "label",
            "dst": 7
        }
    },
    "mov": {
        "pattern": "mov reg[{dst:num}], {label:label}", 
        "command_layout": "const16",
        "bin": {
            "pdec": 0,
            "const": "label",
            "dst": "dst"
        }
    },
    "copy": {
        "pattern": "mov reg[{dst:num}], reg[{src:num}]", 
        "command_layout": "alufpu",
        "bin": {
            "pridec": 1,
            "secdec": 2,
            "r2": "src",
            "flags": 0,
            "4th": 3,
            "r1": 0,
            "dst": "dst"
        }
    },
    "call": {
        "pattern": "call {label:label}",
        "command_layout": "const16",
        "bin": {
            "pdec": 3,
            "const": "label",
            "dst": 7
        }
    },
    "ret":{
        "pattern": "ret",
        "command_layout": "other",
        "bin": {   
            "pridec": 1,
            "secdec": 1,
            "src": 0,
            "3th": 5,
            "4th": 0,
            "pad": 0,
            "dst":7
        }           
    }
}
base["CPU"]["COMMANDS"].update(cmds)

decoder = json.decoder.JSONDecoder()

#
# branches
#
branch ="""
{{
    "branch {cmd_name} {sub_name}":
    {{
        "pattern": "{cmd_name} reg[{{arg1:num}}], reg[{{arg2:num}}], {{offset:offset_label}}",
        "command_layout": "branch",
        "bin": {{
            "pridec": 2,
            "secdec": {value},
            "r2": "{arg2}",
            "offsetHi": "offset>>4",
            "r1": "{arg1}",
            "offsetLo": "offset%16"
        }}
    }}
}}
"""
tokens = [
    ("jge", 0, False), 
    ("jl", 1, False), 
    ("je", 2, False), 
    ("jne", 3, False), 
    ("jae", 4, False), 
    ("jb", 5, False),
    # Rev args
    ("jg", 1, True), 
    ("ja", 5, True),

    ("jle", 0, True), 
    ("jbe", 4, True),
]

for token, value, rev in tokens:
    arg1, arg2 = ("arg2", "arg1") if rev else ("arg1", "arg2") 
    formated = decoder.decode(branch.format(cmd_name=token, value=value, arg1=arg1, arg2=arg2, sub_name= "imm" if rev else ""))
    base["CPU"]["COMMANDS"].update(formated)

#
# Branch IMM
#
branchimm ="""
{{
    "branch {cmd_name} {symbol}":
    {{
        "pattern": "{cmd_name} reg[1]{symbol}, reg[{{reg:num}}], {{offset:offset_label}}",
        "command_layout": "branch",
        "bin": {{
            "pridec": 2,
            "secdec": {value},
            "r2": "reg",
            "offsetHi": "offset>>4",
            "r1": {decoder},
            "offsetLo": "offset%16"
        }}
    }}
}}
"""
base["CPU"]["COMMANDS"].update(decoder.decode(branchimm.format(cmd_name="jge", value=6, symbol="++", decoder=1)))
base["CPU"]["COMMANDS"].update(decoder.decode(branchimm.format(cmd_name="jge", value=6, symbol="--", decoder=2)))
base["CPU"]["COMMANDS"].update(decoder.decode(branchimm.format(cmd_name="jne", value=7, symbol="++", decoder=1)))
base["CPU"]["COMMANDS"].update(decoder.decode(branchimm.format(cmd_name="jne", value=7, symbol="--", decoder=2)))

#
# ALU PART 1
#
alulong = """
{{
    "{name}":
    {{
        "pattern": "{name} reg[{{dst:num}}], reg[{{arg1:num}}], reg[{{arg2:num}}]",
        "command_layout": "aluimm",
        "bin": {{
            "pridec": 1,
            "secdec": {sec},
            "r2": "arg1",
            "I": 0,
            "R1": "arg2 if arg2 < 16 else None",
            "dst": "dst"
        }}
    }},
    "{name} const":
    {{
        "pattern": "{name} reg[{{dst:num}}], reg[{{arg1:num}}], {{const:num}}",
        "command_layout": "aluimm",
        "bin": {{
            "pridec": 1,
            "secdec": {sec},
            "r2": "arg1",
            "I": 1,
            "R1": "const",
            "dst": "dst"
        }}
    }}
}}
"""
tokens = [
    ("add", 0),
    ("sub", 7),
    ("arsh", 6),
    ("rsh", 5),
    ("lsh", 4),
    ("mul", 3),
]
for token, value in tokens:
    formated = decoder.decode(alulong.format(name=token, sec=value))
    base["CPU"]["COMMANDS"].update(formated)

#
# ALU PART 2 (AND FPU)
#
ops2 = """
{{
    "{name}":
    {{
        "pattern": "{name} reg[{{dst:num}}], reg[{{arg1:num}}], reg[{{arg2:num}}]",
        "command_layout": "alufpu",
        "bin": {{
            "pridec": 1,
            "secdec": {sec},
            "r2": "arg1",
            "flags": {flags},
            "4th": {last},
            "r1": "arg2",
            "dst": "dst"
        }}
    }}
}}
"""
tokens = [
    ("xor", 2, 0, 1),
    ("and", 2, 0, 2),
    ("or", 2, 0, 3),
    ("fadd", 1, 0, 0),
    ("fsub", 1, 0, 1),
    ("fmul", 1, 0, 2),
    ("fdiv", 1, 0, 3), 
    ("xnor", 2, 4, 1),
    ("nand", 2, 4, 2),
    ("nor", 2, 4, 3),
]
for name, sec, flags, last in tokens:
    formated = decoder.decode(ops2.format(name=name, sec=sec, flags=flags, last=last))
    base["CPU"]["COMMANDS"].update(formated)

#
# loads and stores
#

unique_id = 0
def generate(pattern, decoder_value, lsh_value, offset, src_dst, neg_offset = False):
    global unique_id
    if not (lsh_value is None):
        val = {
        "pattern":pattern,
        "command_layout":"indirectlsh",
        "bin": {
            "pridec": 1,
            "secdec": 1,
            "ptr": "ptr",
            "3th": decoder_value,
            "lsh": lsh_value,
            "offset": f"{'-' if neg_offset else ''}offset" if offset else 0,
            "srcdst": "src" if src_dst else "dst"
            }
        }
    else:
        val = {
        "pattern":pattern,
        "command_layout":"indirect",
        "bin": {
            "pridec": 1,
            "secdec": 1,
            "ptr": "ptr",
            "3th": decoder_value,
            "offset": f"{'-' if neg_offset else ''}offset" if offset else 0,
            "srcdst": "src" if src_dst else "dst"
            }
        }
    val = {f"ptr src/dst {src_dst} offset {offset} lsh {lsh_value} id: {unique_id}":val}
    unique_id += 1
    return val

# loads
pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + {lsh}*reg[8] + {{offset:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=0), 2, None, True, False))
for i in [0,1,2,3]:
    base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=2**i), 1, i, True, False))
pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + {lsh}*reg[8] - {{offset:num}}]"
for i in [0,1,2,3]:
    base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=2**i), 1, i, True, False, True))


pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + {lsh}*reg[8]]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=0), 2, None, False, False))
for i in [0,1,2,3]:
    base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=2**i), 1, i, False, False))

pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + {{offset:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 2, None, True, False))
pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] - {{offset:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 2, None, True, False, True))


pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}]]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 2, None, False, False))

pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + reg[8]]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 1, 0, False, False))

pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + reg[8] + {{offset:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 1, 0, True, False))
pattern = "mov reg[{{dst:num}}], ram[reg[{{ptr:num}}] + reg[8] - {{offset:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 1, 0, True, False, True))

# writes
pattern = "mov ram[reg[{{ptr:num}}] + {lsh}*reg[8] + {{offset:num}}], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=0), 4, None, True, True))
for i in [0,1,2,3]:
    base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=2**i), 3, i, True, True))
pattern = "mov ram[reg[{{ptr:num}}] + {lsh}*reg[8] - {{offset:num}}], reg[{{src:num}}]"
for i in [0,1,2,3]:
    base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=2**i), 3, i, True, True, True))

pattern = "mov ram[reg[{{ptr:num}}] + {lsh}*reg[8]], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=0), 4, None, False, True))
for i in [0,1,2,3]:
    base["CPU"]["COMMANDS"].update(generate(pattern.format(lsh=2**i), 3, i, False, True))

pattern = "mov ram[reg[{{ptr:num}}] + {{offset:num}}], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 4, None, True, True))
pattern = "mov ram[reg[{{ptr:num}}] - {{offset:num}}], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 4, None, True, True, True))

pattern = "mov ram[reg[{{ptr:num}}]], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 4, None, False, True))

pattern = "mov ram[reg[{{ptr:num}}] + reg[8]], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 4, 0, False, True))

pattern = "mov ram[reg[{{ptr:num}}] + reg[8] + {{offset:num}}], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 4, 0, True, True))
pattern = "mov ram[reg[{{ptr:num}}] + reg[8] - {{offset:num}}], reg[{{src:num}}]"
base["CPU"]["COMMANDS"].update(generate(pattern.format(), 4, 0, True, True, True))

#
# others
#
values = {
    "pop": {
        "pattern": "pop reg[{dst:num}]",
        "command_layout": "other",
        "bin": {
            "pridec": 1,
            "secdec": 1,
            "src": 0,
            "3th": 5,
            "4th": 0,
            "pad": 0,
            "dst": "dst"
        }
    },
    "push": {
        "pattern": "push reg[{src:num}]",
        "command_layout": "other",
        "bin": {
            "pridec": 1,
            "secdec": 1,
            "src": "src",
            "3th": 6,
            "4th": 0,
            "pad": 0,
            "dst": 0
        }
    },
    "push": {
        "pattern": "push reg[{src:num}]",
        "command_layout": "other",
        "bin": {
            "pridec": 1,
            "secdec": 1,
            "src": "src",
            "3th": 6,
            "4th": 0,
            "pad": 0,
            "dst": 0
        }
    },
    "int": {
        "pattern": "int {type:num}",
        "command_layout": "other",
        "bin": {
            "pridec": 1,
            "secdec": 1,
            "src": 0,
            "3th": 7,
            "4th": 3,
            "pad": 0,
            "dst": "type"
        }
    },
    "not": {
        "pattern": "not reg[{dst:num}], reg[{src:num}]",
        "command_layout": "alufpu",
        "bin": {
            "pridec": 1,
            "secdec": 2,
            "r2": 0,
            "flags": 1,
            "4th": 1,
            "r1": "src",
            "dst": "dst"
        }
    },
    "inject":{
        "pattern": "inject {value:num}",
        "command_layout": "inject",
        "bin": {
            "value":"value"
        }
    },
    "inc": {
        "pattern": "inc reg[{target:num}]",
        "command_layout": "aluimm",
        "bin": {
            "pridec": 1,
            "secdec": 0,
            "r2": "target",
            "I": 1,
            "R1": 1,
            "dst": "target"
        }
    },
    "dec": {
        "pattern": "dec reg[{target:num}]",
        "command_layout": "aluimm",
        "bin": {
            "pridec": 1,
            "secdec": 7,
            "r2": "target",
            "I": 1,
            "R1": 1,
            "dst": "target"
        }
    }
}
base["CPU"]["COMMANDS"].update(values)
pattern = """
{{
    "{name}": {{
        "pattern": "{name} reg[{{dst:num}}], reg[{{src:num}}]",
        "command_layout": "other",
        "bin": {{
            "pridec": 1,
            "secdec": 1,
            "src": "{src}",
            "3th": 7,
            "4th": {val},
            "pad": 0,
            "dst": "{dst}"
        }}
    }}
}}"""
base["CPU"]["COMMANDS"].update(decoder.decode(pattern.format(name="ftoi", src="src", val=0, dst="dst")))
base["CPU"]["COMMANDS"].update(decoder.decode(pattern.format(name="itof", src="src", val=1, dst="dst")))
base["CPU"]["COMMANDS"].update(decoder.decode(pattern.format(name="utof", src="src", val=2, dst="dst")))

IOSCHEM="""
{{
    "{name}":{{
        "pattern": "{name} reg[{{srcdst:num}}]",
        "command_layout":"indirect",
        "bin": {{
            "pridec": 1,
            "secdec": 1,
            "ptr": 0,
            "3th": {ls},
            "offset": {address},
            "srcdst": "srcdst"
        }}
    }}
}}
"""

def add_io(name, is_load, address):
    formated = decoder.decode(IOSCHEM.format(name=name, ls = 1 if is_load else 4, address=address))
    base["CPU"]["COMMANDS"].update(formated)

add_io("print", True, 0x0005)
add_io("dbg", True, 0x0006)
add_io("clk set", True, 0x0001)
add_io("clk get", False, 0x0001)
add_io("tim set", True, 0x0002)
add_io("tim get", False, 0x0002)
add_io("tim state set", True, 0x0003)
add_io("tim state get", False, 0x0003)
add_io("gpu status", True, 0x000c)
add_io("gpu invoke", False, 0x000d)

with open('profiles/potados.jsonc', 'w') as f:
    json.dump(base, f, indent=4)
