import json

from numpy import add

base = {
    "CPU": 
    {
        "Name": "WVRN Pico",
        "Arch": "WVRN",
        "Author": "Q2CK",
        "emulator":None,
        "time_per_cycle":2.0,
         "ARGUMENTS":{
            "default":{
                "arg": {
                    "size":4
                },
                "flag": {
                    "size":1
                },
                "op": {
                    "size":3
                }
            }
        },
        "ADRESSING":
        {
            "mode":"packed",
            "bin_len":8,
            "offset":0
        },

        "DEFINES":[
            "__WVRN__",
            "__WVRN_PICO__",

            ["acc", "1"],
            ["flg", "2"],
            ["seg", "3"],
            ["tr1", "4"],
            ["tr2", "5"]
        ],

        "KEYWORDS":{
            "ENTRY":{
                "offset":0,
                "write":0
            }
        },

        "SCHEMATIC": None,

        "FILL":"nop",

        "COMMANDS":{
        
        },
        "MACROS":{

        }
    }
}

def generate(opName, opCode, flag):
    return {
        f"{opName}": {
            "pattern": f"{opName} {{arg:num}}",
            "command_layout": "default",
            "bin": {
                "arg": "arg",
                "flag": flag,
                "op": opCode,
            }
        }
    }


def generate_f(opName, opCode):
    # gen opName and opName.f
    i1 = generate(opName, opCode, 0)
    i2 = generate(f"{opName}.f", opCode, 1)
    return {**i1, **i2}


def add_command_f(opName, opCode):
    base["CPU"]["COMMANDS"].update(generate_f(opName, opCode))

def add_command(opName, opCode, flag):
    base["CPU"]["COMMANDS"].update(generate(opName, opCode, flag))
 
add_command("sta", opCode=0, flag=0)
add_command_f("lda", opCode=1)
add_command_f("add", opCode=2)
add_command_f("addi", opCode=3)
# addi label
add_command_f("nand", opCode=4)
add_command_f("ld", opCode=5)
add_command_f("st", opCode=6)

def generate_branch(hint: bool, flag: str, flags: int):
    suffix = "true" if hint else "false"
    opName = f"b.{suffix} {flag}"
    return {
        opName: {
            "pattern": f"b{suffix[0]} {flag}",
            "command_layout": "default",
            "bin": {
                "reg": flags,
                "flag": 1 if hint else 0,
                "op": 7
            }
        }
    }

def add_branch(flag: str, op: int):
    # add both hints
    i1 = generate_branch(True, flag, op)
    i2 = generate_branch(False, flag, op)
    base["CPU"]["COMMANDS"].update({**i1, **i2})

add_branch("carry", 0)
add_branch("ncarry", 1)
add_branch("zero", 2)
add_branch("nzero", 3)
add_branch("odd", 4)
add_branch("nodd", 5)
add_branch("even", 5)
add_branch("neven", 4)
add_branch("sign", 6)
add_branch("nsign", 7)
add_branch("overflow", 8)
add_branch("noverflow", 9)
add_branch("true", 14)
add_branch("false", 15)

# Load immediate values from JSON
with open("profiles/wvrn/imms.json") as f:
    imms = json.load(f)

# Generate macros for immediate values
for imm, instructions in imms.items():
    base["CPU"]["MACROS"][f"lim {imm}"] = {
        "pattern": f"lim {imm}",
        "process": {},
        "expansion": instructions
    }

for i in range(1, 128):
    base["CPU"]["MACROS"][f"lim {-i}"] = {
        "pattern": f"lim {-i}",
        "process": {},
        "expansion": [
            f"lim {256 - i}",
        ]
    }

base["CPU"]["MACROS"]["b"] = {
    "pattern": "b {mode:token}",
    "process": {},
    "expansion": [
        "bt {mode}"
    ]
}

base["CPU"]["MACROS"]["nop"] = {
    "pattern": "nop",
    "process": {},
    "expansion": [
        "sta 0"
    ]
}

base["CPU"]["MACROS"]["mov"] = {
    "pattern": "mov {dest:token} {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "lda {src}",
        "sta {dest}",
        "lda tr1"
    ]
}


base["CPU"]["MACROS"]["mov.f"] = {
    "pattern": "mov.f {dest:token} {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "lda {src}",
        "sta.f {dest}",
        "lda tr1"
    ]
}

base["CPU"]["MACROS"]["swa"] = {
    "pattern": "swa {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "lda {src}",
        "sta tr2",
        "lda tr1",
        "sta {src}",
        "lda tr2"
    ]
}

base["CPU"]["MACROS"]["swa.f"] = {
    "pattern": "swa {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "lda {src}",
        "sta tr2",
        "lda tr1",
        "sta {src}",
        "lda.f tr2"
    ]
}


base["CPU"]["MACROS"]["not"] = {
    "pattern": "not {src:token}",
    "process": {},
    "expansion": [
        "lda {src}",
        "nand {src}"
    ]
}

base["CPU"]["MACROS"]["not.f"] = {
    "pattern": "not.f {src:token}",
    "process": {},
    "expansion": [
        "lda {src}",
        "nand.f {src}"
    ]
}


base["CPU"]["MACROS"]["and"] = {
    "pattern": "and {src:token}",
    "process": {},
    "expansion": [
        "nand {src}",
        "nand acc"
    ]
}


base["CPU"]["MACROS"]["and.f"] = {
    "pattern": "and {src:token}",
    "process": {},
    "expansion": [
        "nand {src}",
        "nand.f acc"
    ]
}

base["CPU"]["MACROS"]["or"] = {
    "pattern": "or{.f} {src:token}",
    "process": {},
    "expansion": [
        "nand acc",
        "sta tr1",
        "not {src}",
        "nand{.f} tr1"
    ]
}

base["CPU"]["MACROS"]["or"] = {
    "pattern": "or.f {src:token}",
    "process": {},
    "expansion": [
        "nand acc",
        "sta tr1",
        "not {src}",
        "nand.f tr1"
    ]
}


base["CPU"]["MACROS"]["xor"] = {
    "pattern": "xor {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "nand {src}",
        "sta tr2",
        "nand tr1",
        "sta tr1",
        "lda tr2",
        "nand {src}",
        "nand{.f} tr1"
    ]
}

base["CPU"]["MACROS"]["xor.f"] = {
    "pattern": "xor.f {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "nand {src}",
        "sta tr2",
        "nand tr1",
        "sta tr1",
        "lda tr2",
        "nand {src}",
        "nand.f tr1"
    ]
}


base["CPU"]["MACROS"]["andi"] = {
    "pattern": "andi {src:label} {imm:token}",
    "process": {},
    "expansion": [
        "lim {imm}",
        "and {src}"
    ]
}

base["CPU"]["MACROS"]["andi.f"] = {
    "pattern": "andi.f {src:token} {imm:token}",
    "process": {},
    "expansion": [
        "lim {imm}",
        "and.f {src}"
    ]
}

base["CPU"]["MACROS"]["ori"] = {
    "pattern": "ori {src:token} {imm:token}",
    "process": {},
    "expansion": [
        "lim {imm}",
        "or{.f} {src}"
    ]
}

base["CPU"]["MACROS"]["ori.f"] = {
    "pattern": "ori.f {src:token} {imm:token}",
    "process": {},
    "expansion": [
        "lim {imm}",
        "or.f {src}"
    ]
}

base["CPU"]["MACROS"]["xori"] = {
    "pattern": "xori {src:token} {imm:token}",
    "process": {},
    "expansion": [
        "lim {imm}",
        "xor {src}"
    ]
}

base["CPU"]["MACROS"]["xori.f"] = {
    "pattern": "xori.f {src:token} {imm:token}",
    "process": {},
    "expansion": [
        "lim {imm}",
        "xor.f {src}"
    ]
}

base["CPU"]["MACROS"]["sub"] = {
    "pattern": "sub {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "nand {src}",
        "addi 1",
        "add tr1"
    ]
}

base["CPU"]["MACROS"]["sub.f"] = {
    "pattern": "sub.f {src:token}",
    "process": {},
    "expansion": [
        "sta tr1",
        "nand {src}",
        "addi 1",
        "add.f tr1"
    ]
}

base["CPU"]["MACROS"]["suba"] = {
    "pattern": "suba {src:token}",
    "process": {},
    "expansion": [
        "nand acc",
        "addi 1",
        "add {src}"
    ]
}

base["CPU"]["MACROS"]["suba.f"] = {
    "pattern": "suba.f {src:token}",
    "process": {},
    "expansion": [
        "nand acc",
        "addi 1",
        "add.f {src}"
    ]
}

base["CPU"]["MACROS"]["brc-label"] = {
    "pattern": "brc {cond:token} {addr:label}",
    "process": {
    },
    "expansion": [
        "brc {cond} {addr}"
    ]
}

base["CPU"]["MACROS"]["brc-const"] = {
    "pattern": "brc {cond:token} {addr:num}",
    "process": {
    },
    "expansion": [
        "brct {cond} {addr}"
    ]
}


base["CPU"]["MACROS"]["brc-expansion-true"] = {
    "pattern": "brct {cond:token} {addr:num}",
    "process": {
        "lowAddr": "u16(int(addr)).low_byte().int()",
        "highAddr": "u16(int(addr)).high_byte().int()"
    },
    "expansion": [
        "lim {lowAddr}",
        "sta 3",
        "lim {highAddr}",
        "bt {cond}"
    ]
}

base["CPU"]["MACROS"]["brc-expansion-false"] = {
    "pattern": "brcf {cond:token} {addr:num}",
    "process": {
        "lowAddr": "u16(int(addr)).low_byte().int()",
        "highAddr": "u16(int(addr)).high_byte().int()"
    },
    "expansion": [
        "lim {lowAddr}",
        "sta 3",
        "lim {highAddr}",
        "bf {cond}"
    ]
}

base["CPU"]["MACROS"]["jmp"] = {
    "pattern": "jmp {addr:token}",
    "expansion": [
        "brc true {addr}"
    ]
}

# load instruction
base["CPU"]["MACROS"]["load"] = {
    "pattern": "load {addr:num}",
    "process": {
        "lowAddr": "u16(int(addr)).low_byte().int()",
        "highAddr": "u16(int(addr)).high_byte().int()"
    },
    "expansion": [
        "lim {lowAddr}",
        "sta 3",
        "lim {highAddr}",
        "sta tr1",
        "ld tr1",
    ]
}

base["CPU"]["MACROS"]["load.f"] = {
    "pattern": "load {addr:num}",
    "process": {
        "lowAddr": "u16(int(addr)).low_byte().int()",
        "highAddr": "u16(int(addr)).high_byte().int()"
    },
    "expansion": [
        "lim {lowAddr}",
        "sta 3",
        "lim {highAddr}",
        "sta tr1",
        "ld.f tr1",
    ]
}


# store instruction
base["CPU"]["MACROS"]["store"] = {
    "pattern": "store {addr:num}",
    "process": {
        "lowAddr": "u16(int(addr)).low_byte().int()",
        "highAddr": "u16(int(addr)).high_byte().int()"
    },
    "expansion": [
        "lim {lowAddr}",
        "sta 3",
        "lim {highAddr}",
        "sta tr1",
        "st tr1",
    ]
}



# Save the updated base configuration to a file
with open("profiles/wvrn/wvrn.jsonc", "w") as f:
    json.dump(base, f, indent=4)
