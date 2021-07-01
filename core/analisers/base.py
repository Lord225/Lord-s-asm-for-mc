import core.error as error
import core.loading as loading
import core.config as config

G_INFO_CONTAINER = {"Warnings": list(), "info": list(), "skip": False, "stop": False}

PROFILE = None

def load_profie(profile, emulator):
    global PROFILE
    PROFILE = loading.PROFILE_DATA(profile=profile, emulator=emulator)
    print("Profile Loaded")


def reset_G_INFO_CONTAINER():
    global G_INFO_CONTAINER
    if len(G_INFO_CONTAINER["Warnings"]) != 0:
        G_INFO_CONTAINER["Warnings"] = list()
    if len(G_INFO_CONTAINER["info"]) != 0:
        G_INFO_CONTAINER["info"] = list()
    if G_INFO_CONTAINER["skip"] != False:
        G_INFO_CONTAINER["skip"] = False
    if G_INFO_CONTAINER["stop"] != False:
        G_INFO_CONTAINER["stop"] = False


def cliping_beheivior(arg, Max):
    """Way that solver will treat cliping"""
    if config.G_RISE_ERROR_ON_BAD_RANGES:
        raise error.ExpectedValue(Max, arg)
    G_INFO_CONTAINER["info"].append("Value has been cliped: {}".format(arg))

def check_argument_ranges(args):
    for arg, Type in args:
        try:
            cliping_beheivior(arg, PROFILE.PARAMETERS["arguments sizes"][Type])
        except KeyError as err:
            raise error.ProfileStructureError("Expected custom argument size definiton.", custom=True)


def args_equal(args1, args2, TypesOnly = False):
    """Will compare all passed arguments
    if TypesOnly == True -> will compare only types of arguments (not values)"""
    if type(args1) is not list:
        args1 = [args1]
    if type(args2) is not list:
        args2 = [args2]    
    if TypesOnly:
        return all(arg1[1] == arg2[1] for arg1, arg2 in zip(args1, args2))
    else:
        return all(arg1[1] == arg2[1] and arg1[0] == arg2[0] for arg1, arg2 in zip(args1, args2))
