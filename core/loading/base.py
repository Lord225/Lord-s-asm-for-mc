import core.error as error

def load_preproces(path):
    Program = []
    Settings = []
    with open(path,"r") as file:
        for i, line in enumerate(file):
            if line[0] == '[' and line[-2] == ']':
                Settings = {a:b for a,b in [x.strip(" ").split(" ") for x in line[1:-2].split(",")]}
            else:
                lb = line.replace("\t",' ').replace("\n",'')
                if "//" in lb:
                    lb = lb[:lb.find("//")]
                if lb.strip():
                    Program.append((i+1, lb.strip()))
    file.close()
    return Program, Settings

