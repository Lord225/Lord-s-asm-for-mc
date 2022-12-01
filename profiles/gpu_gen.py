import json

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
                    "const": {
                        "dec1": {
                            "size": 3,
                        },
                        "const": {
                            "size": 16,
                        },
                        "dst": {
                            "size": 3,
                        }
                    },
                    "r1r2": {
                        "dec1": {
                            "size": 3,
                        },
                        "dec2": {
                            "size": 3,
                        },
                        "r2": {
                            "size": 3,
                        },
                        "Iy": {
                            "size": 1,
                        },
                        "y": {
                            "size": 4,
                        },
                        "pad": {
                            "size": 2,
                        },
                        "r1": {
                            "size": 3,
                        },
                        "dst": {
                            "size": 3,
                        }
                    },
                    "r2imm":
                    {
                        "dec1": {
                            "size": 3,
                        },
                        "dec2": {
                            "size": 3,
                        },
                        "r2": {
                            "size": 3,
                        },
                        "I": {
                            "size": 1,
                        },
                        "imm": {
                            "size": 9,
                        },
                        "dst": {
                            "size": 3,
                        }
                    },
                    "par":
                    {
                        "dec1": {
                            "size": 1,
                        },
                        "c": {
                            "size": 1,
                        },
                        "op": {
                            "size": 4,
                        },
                        "r2": {
                            "size": 3,
                        },
                        "I": {
                            "size": 1,
                        },
                        "y": {
                            "size": 4,
                        },
                        "immf": {
                            "size": 1,
                        },
                        "val": {
                            "size": 4,
                        },
                        "dst": {
                            "size": 3,
                        }
                    },
                }
            },

            "ADRESSING":
            {
                "mode": "align",
                "bin_len": 22,
                "offset": 0
            },

            "DEFINES": [
            ],
            "KEYWORDS": {
                "CORE0": {
                    "offset": 0,
                    "write": 0
                }
            },
            "FILL": "nop",
            "COMMANDS": {},
            "MACROS": {}
        }
    }

# let fun begin

cmds = \
    {
        "halt": {
            "pattern": "halt",
            "command_layout": "const",
            "bin": {
                "dec1": 0,
                "const": 0,
                "dst": 0
            }
        },
    }

base["CPU"]["COMMANDS"].update(cmds)

with open('profiles/gpu.jsonc', 'w') as f:
    json.dump(base, f, indent=4)
