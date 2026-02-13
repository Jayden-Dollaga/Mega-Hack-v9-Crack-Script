r"""
-- Mega Hack v9 Crack Script --

Prerequisites: Have Geode installed. If you don't, figure out how to install it.

1. Copy this file and place it somewhere on your desktop, doesn't matter where.
2. Go to your Microsoft Store app and install "Python" (Many versions may appear, just pick the first one e.g. Python 3.13).
3. Press Win + R, then type in "cmd" into the pop-up, a terminal should appear.
4. In the terminal, type "python " (with the space after it), and then drag the file containing this script into the terminal.
5. You should now see something *like* "python C:\path\to\crack.py" in your terminal, press Enter.
6. Let the script run, next steps will be in the output depending on what happens.

Tested for the following MH versions: v9.0.3, v9.0.7, v9.0.9
"""

import platform

err = lambda msg: print(f"[ERROR] {msg}") or exit(1)
warn = lambda msg: print(f"[WARNING] {msg}")

if platform.system().lower() != 'windows':
    err(f"This crack is meant for windows versions of Mega Hack. {platform.system()} is not supported.")

# MegaHack uses SHGetKnownFolderPath to find the local appdata directory. If it fails we can fall back to using the environment variable.
import ctypes
import uuid
import os

FOLDERID_LocalAppData =  uuid.UUID("{F1B32785-6FBA-4FCF-9D55-7B8E7F157091}").bytes_le
appdata_dir_buf = ctypes.c_wchar_p()

if ctypes.windll.shell32.SHGetKnownFolderPath(
    ctypes.byref(ctypes.create_string_buffer(FOLDERID_LocalAppData, 16)),
    0, 0,
    ctypes.byref(appdata_dir_buf)
):
    warn("Failed to find the local appdata directory using SHGetKnownFolderPath. Trying %LOCALAPPDATA%.")
    LOCALAPPDATA = os.getenv("LOCALAPPDATA", None)
    if not LOCALAPPDATA:
        err("Unable to find the local AppData directory with SHGetKnownFolderPath or %LOCALAPPDATA%. Aborting.")
else:
    LOCALAPPDATA = appdata_dir_buf.value

print(f"Found the local appdata directory at '{LOCALAPPDATA!s}'")

# the rest of the shit we need
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import zipfile
import io
import json
import re
import time
import base64
import functools
import shutil
from contextlib import contextmanager

# convenience
CWD = os.path.dirname(__file__)
os.chdir(CWD)
print = functools.partial(print, flush=True)

@contextmanager
def progress_log(msg: str):
    print(msg, end="... ")
    success = False
    try:
        yield
        success = True
    finally:
        print("Done!" if success else "Failed.")

# Part 1: Downloading current version

# json containing all megahack version and information
INSTALL_JSON_URL = "https://absolllute.com/api/mega_hack/v9/install.json"

try:
    request = Request(
        INSTALL_JSON_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    r = urlopen(request)
except HTTPError as e:
    if e.code == 403:
        err("Access to the install API was denied (HTTP 403). Use the official Mega Hack installer instead of this script.")
    err(f"Unable to get installation json. HTTP error: {e.code}")
except URLError as e:
    err(f"Unable to get installation json. URL error: {e.reason}")

if r.status != 200:
    err(f"Unable to get installation json. Status Code: {r.status}")

cur_package = json.load(r)["packages"][0]
if cur_package["name"] != "Mega Hack v9":
    print(f"[WARNING] This was tested for Mega Hack v9, most recent version seems to now be {cur_package['name']}")

cur_bundle = cur_package["bundles"][0]

group = cur_bundle["group"]
filename = cur_bundle["file"]

MEGAHACK_URL = "https://absolllute.com/api/mega_hack/v9/files/{}/{}".format(group, filename)

with progress_log(f"Downloading {cur_bundle['name']}"):
    try:
        request = Request(
            MEGAHACK_URL,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urlopen(request) as r:
            megahack_zip = r.read()
    except HTTPError as e:
        if e.code == 403:
            err("Access to the Mega Hack package download was denied (HTTP 403). This script can no longer fetch releases; use the official Mega Hack installer instead.")
        err(f"HTTP error: {e.code}")
    except URLError as e:
        err(f"URL error: {e.reason}")

# Part 2: Extracting the geode

with progress_log("Extracting geode file and patching"):
    OUT_FILENAME = "absolllute.megahack.cracked.geode"
    with zipfile.ZipFile(io.BytesIO(megahack_zip), 'r') as zip_in, \
        zipfile.ZipFile(OUT_FILENAME, 'w') as zip_out:

        # Part 3: Setting up patching shit
        # Patterns tested on v9.0.3, v9.0.7, and v9.0.9

        # 56 57 48 83 EC ? 48 83 79 10 40
        # patch id verification
        ID_CHECK_PAT = re.compile(rb'\x56\x57\x48\x83\xEC.\x48\x83\x79\x10\x40', re.DOTALL | re.MULTILINE)
        # 55 41 56 56 57 53 48 83 EC ? 48 8D 6C 24 ? 48 C7 45 ? ? ? ? ? ? ? ? ? 0F 84 ? ? ? ? 4C 89 C7
        # patch json signature verification
        JSON_SIGNATURE_CHECK_PAT = re.compile(rb'\x55\x41\x56\x56\x57\x53\x48\x83\xEC.\x48\x8D\x6C\x24.\x48\xC7\x45.........\x0F\x84....\x4C\x89\xC7', re.DOTALL | re.MULTILINE)
        # 31 C9 41 B8 ? ? ? ? E8 ? ? ? ? 48 83 7F
        # patch out checksum result of hardware manufacturer to make the key 0x00000000 no matter what
        KEY_BYBASS_PAT = re.compile(rb'(?<=\x31\xC9\x41\xB8....)\xE8....(?=\x48\x83\x7F)', re.DOTALL | re.MULTILINE)

        # the first two functions we need to patch involve forcing it to return 1 lol
        PATCH_DATA1 = b"".join([
            b"\xb8\x01\x00\x00\x00", # mov eax, 1
            b"\xc3", # ret
        ])
        
        # overwriting the function call to instead just set rax to 0
        PATCH_DATA2 = b"".join([
            b"\xb8\x00\x00\x00\x00", # mov eax, 0
        ])
        
        # Part 4: Patching shit
        for item in zip_in.infolist():
            filename = item.filename
            data = zip_in.read(filename)
            
            match filename:
                case "absolllute.megahack.dll":
                    if data == (data := ID_CHECK_PAT.sub(lambda m: PATCH_DATA1 + m.group(0)[len(PATCH_DATA1):], data, 1)):
                        err("Failed to find pattern for the id check!")
                    if data == (data := JSON_SIGNATURE_CHECK_PAT.sub(lambda m: PATCH_DATA1 + m.group(0)[len(PATCH_DATA1):], data, 1)):
                        err("Failed to find pattern for the json signature check!")
                    if data == (data := KEY_BYBASS_PAT.sub(PATCH_DATA2, data, 1)):
                        err("Failed to find pattern for the key bypass!")

                    # need to update the filename too
                    item.filename = "absolllute.megahack.cracked.dll"
                case "mod.json":
                    # we need to modify the id to match the output filename, all the other changes are cosmetic
                    mod = json.loads(data)
                    mod["id"] = "absolllute.megahack.cracked"
                    mod["name"] = "Mega Hack Cracked"
                    mod["description"] = "ts pmo"
                    data = json.dumps(mod, indent="\t").encode()
            
            zip_out.writestr(item, data)

# Part 5: Writing a now valid license to the expected directory
with progress_log("Creating fake license file"):
    mh_local_dir = os.path.join(LOCALAPPDATA, "absolllute.megahack")
    os.makedirs(mh_local_dir, exist_ok=True)
    mh_license_path = os.path.join(mh_local_dir, "license")
    mh_license_fallback_path = os.path.join(CWD, "license")

    EXPECTED_CHACHA_KEY = bytes.fromhex("0E 84 1F A5 BF E5 CE 8F C9 1E B1 1A DD 1D CE F6 94 04 5B EE AF CF 52 1B F4 34 1D 39 97 C1 C2 19")

    def random_hex(length):
        assert length % 2 == 0
        return os.urandom(length // 2).hex().upper()

    signature = os.urandom(256) # we bypass this check, so just set it to whatever
    identifier = random_hex(64) # this is possible to generate legitamately, but it really bloats the code bc it involves a lot of winapi stuff
    token = random_hex(32) # honestly, I have no idea what this is for, it's not used anywhere from what I can tell
    secret = random_hex(32) # same with this, couldn't find anywhere that reads this

    data = {
        "id": identifier,
        "token": token,
        "secret": secret,
        "timestamp": str(int(time.time())),
        # this is used to decrypt some resources or something else important (didn't really dig into it) but it's requried to be this
        "guid2": EXPECTED_CHACHA_KEY.hex().upper()
    }

    data_dump = json.dumps(data, separators=(",", ":"))

    license = {
        "data": base64.b64encode(data_dump.encode()).decode('utf-8'),
        "sig": base64.b64encode(signature).decode('utf-8'),
        "token": token
    }

    license_str = json.dumps(license, separators=(",", ":"))
    with open(mh_license_path, "w") as f:
        f.write(license_str)
    with open(mh_license_fallback_path, "w") as f:
        f.write(license_str)

    assert os.path.exists(mh_license_path) or os.path.exists(mh_license_fallback_path)

# Yay all done, past this point is just printing stuff to make it nice and pretty

def get_terminal_width():
    try:
        size = shutil.get_terminal_size()
        return size.columns
    except OSError:
        # Fallback if the terminal size cannot be determined
        return 80

output_file = os.path.join(CWD, OUT_FILENAME)
if not os.path.exists(output_file):
    err("The patching process went well, but the patched geode was never created.")

BORDER = '#' * get_terminal_width()
print(f"""
{BORDER}
Cracking process finished!
* The license file was created in {mh_local_dir} and {CWD}.
* If you don't see the license file in {mh_local_dir}, copy the one in {CWD} to there.
* The cracked geode can be found at {output_file}
* After installing Geode, you can manually import this cracked geode to use Mega Hack
{BORDER}\
""")
