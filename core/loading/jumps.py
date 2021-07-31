import core.error as error

def jump_preprocesing(Programs, KEYWORDS):
    JUMPLIST = {a:dict() for a in KEYWORDS}
    for Device in KEYWORDS:
        rom_id = 0
        for cmd_i in range(len(Programs[Device])):
            if Programs[Device][cmd_i][1][0] == ":":
                name = Programs[Device][cmd_i][1]
                cmd_i += 1
                if cmd_i >= len(Programs[Device]):
                    if name[1:] in JUMPLIST[Device]:
                        raise error.LoadError("Jump identifier '{}' has appear multiple times.".format(name[1:]))
                    JUMPLIST[Device][name[1:]] = rom_id-1
                    continue
                while Programs[Device][cmd_i][1][0] == ":":
                        cmd_i += 1
                if name[1:] in JUMPLIST[Device]:
                    raise error.LoadError("Jump identifier '{}' has appear multiple times.".format(name[1:]))
                JUMPLIST[Device][name[1:]] = rom_id-1
            else:
                rom_id += 1
        
    for Device in KEYWORDS:
        Programs[Device] = [a for a in Programs[Device] if a[1][0] != ':']
    return Programs, JUMPLIST

def indices(Programs, KEYWORDS):
    line_indicator = dict()
    for Device in KEYWORDS:
        line_indicator[Device] = [x[0] for x in Programs[Device]]
        Programs[Device] = [x[1] for x in Programs[Device]]
    return line_indicator


def split_sectors(Program, KEYWORDS):
    Programs = {a:[] for a in KEYWORDS}
    currentSector = ""
    for line in Program:
        if line[1][1:] in KEYWORDS:
            currentSector = line[1][1:]
        if len(currentSector) == 0:
            err = error.LoadError("'{}' is in undefined sector (valid sectors: {})".format(line[1], KEYWORDS))
            err.line = line[0]
            raise err
        Programs[currentSector].append(line)
    for Sector in KEYWORDS:
        Programs[Sector] = Programs[Sector][1:]
    return Programs