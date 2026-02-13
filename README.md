1st is syntax for wider Python compatibility so i dit was change this line 

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

to:

            if filename == "absolllute.megahack.dll":
                if data == (data := ID_CHECK_PAT.sub(lambda m: PATCH_DATA1 + m.group(0)[len(PATCH_DATA1):], data, 1)):
                    err("Failed to find pattern for the id check!")
                if data == (data := JSON_SIGNATURE_CHECK_PAT.sub(lambda m: PATCH_DATA1 + m.group(0)[len(PATCH_DATA1):], data, 1)):
                    err("Failed to find pattern for the json signature check!")
                if data == (data := KEY_BYBASS_PAT.sub(PATCH_DATA2, data, 1)):
                    err("Failed to find pattern for the key bypass!")

                # need to update the filename too
                item.filename = "absolllute.megahack.cracked.dll"
            elif filename == "mod.json":
                # we need to modify the id to match the output filename, all the other changes are cosmetic
                mod = json.loads(data)
                mod["id"] = "absolllute.megahack.cracked"
                mod["name"] = "Mega Hack Cracked"
                mod["description"] = "ts pmo"
                data = json.dumps(mod, indent="\t").encode()

2nd is im getting 404 

i remove

        with urlopen(MEGAHACK_URL) as r:
            megahack_zip = r.read()
    except HTTPError as e:
        err(f"HTTP error: {e.code}")
    except URLError as e:
        err(f"URL error: {e.reason}")

and change it to:

        with urlopen(MEGAHACK_URL) as r:
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
