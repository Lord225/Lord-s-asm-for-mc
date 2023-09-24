import core.error as error
import core.config as config
import os
from subprocess import check_output
from urllib.parse import urlparse
from pathlib import Path

def download_and_install_profile(profile_url, quiter: bool = False):
    profile_name = os.path.splitext(os.path.basename(urlparse(profile_url).path))[0]
    profile_name = Path(profile_url).stem
    profile_path = os.path.join(config.HOME_DIR, "profiles", profile_name)

    if not quiter:
        print("Profile will be installed to", profile_path)

    if not os.path.exists(profile_path):
        # download profile
        cmd = f"git clone {profile_url} \"{profile_path}\""
        
        # safe to out folder
        try:
            check_output(cmd, shell=True).decode()
        except Exception as e:
            print(f"Can't download profile. {e}")
            return
        
        if not quiter:
            print(f"Done. Now you can use profile by adding #profile {profile_name} to your code.")
        else:
            print(f"Done. Profile {profile_name} installed.")
    else:
        # checkout if profile exists
        if not quiter:
            print("Profile with that name already exists. Updating...")
        
        cmd = f"git -C \"{profile_path}\" pull"
        try:
            check_output(cmd, shell=True).decode()
        except Exception as e:
            print(f"Can't update profile. {e}")
    
    return profile_name
        
def create_blank(name: str, home_location: bool):
    # if profile folder does not exists, create it
    if not home_location:
        ROOT = "./profiles"
        if not os.path.exists(ROOT):
            os.mkdir(ROOT)
    else:
        ROOT = os.path.join(config.HOME_DIR, "profiles")
        if not os.path.exists(ROOT):
            os.mkdir(ROOT)
        
    # create profile folder
    profile_path = os.path.join(ROOT, name)
    if not os.path.exists(profile_path):
        os.mkdir(profile_path)
    else:
        print("Profile with that name already exists. Remove it or choose another name.")
        return
    
    # create blank profile by copying default profile and renaming it
    default_profile_path = os.path.join(config.HOME_DIR, "core", "blank", "blank.jsonc")

    # open default profile
    with open(default_profile_path, "r") as f:
        default_profile = f.read()
    
    # save it to profile folder with new name
    with open(os.path.join(profile_path, f"{name}.jsonc" ), "w") as f:
        f.write(default_profile)
    
    # create file with #profile {name} in it named init.lor
    with open(os.path.join(profile_path, "init.lor"), "w") as f:
        f.write(f"#profile {name}")
    
    
    print(f"Profile created at \"{profile_path}\"")
    print(f"Now you can edit and use profile by adding #profile {name} to your code.")
    print(f"You also can view guide on how to create profile at https://github.com/Lord225/Lord-s-asm-for-mc/wiki/Profile")
    print(f"There is also example profile in root profiles folder.")

def show_installed_profiles():
    profiles_names = []

    # check profiles in ROOT
    ROOT = "./profiles"
    if os.path.exists(ROOT):
        profiles_names = os.listdir(ROOT)
    
    # check profiles in HOME_DIR
    HOME = os.path.join(config.HOME_DIR, "profiles")
    if os.path.exists(HOME):
        profiles_names += os.listdir(HOME)
    
    # remove duplicates
    profiles_names = list(set(profiles_names) - {"__pycache__", "blank", ".git"})

    # print profiles
    print("Installed profiles:")
    for profile_name in profiles_names:
        print(f" - {profile_name}")