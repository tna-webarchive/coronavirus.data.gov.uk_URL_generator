def run_BX(yaml_loc):
    import subprocess
    check = subprocess.run(f"sudo browsertrix crawl create {yaml_loc}", shell=True,
                           stdout=subprocess.PIPE).stdout.decode("utf-8")
    check = check.split("\n")[1]
    crawl_id = check.split(": ")[1]

    return crawl_id


def create_yaml(urls, file_name, folder):
    while "" in urls:
        urls.remove("")
    while None in urls:
        urls.remove(None)


    yaml_template = f"""crawls:
  - name: {file_name}
    crawl_type: custom
    crawl_depth: 2
    num_browsers: 1
    num_tabs: 2
    coll: {folder.split("/")[-2]}
    mode: record

    scopes:
      - {{DOMAINS}}

    seed_urls:
      - {{URLS}}

    behavior_max_time: 80
    browser: chrome:73
    cache: always"""

    with open(f"{folder}yaml_template.yaml", "w") as dest:
        dest.write(yaml_template)

    default = input("Would you like to use default YAML template? [Y/n]").lower()

    while default == "n":
        default = input(f"""
Make your changes to the YAML template {folder}yaml_template.yaml
(Please do not change 'name' or 'coll' fields)
When happy with the template, save it and hit return here in the terminal>""")

        with open(f"{folder}yaml_template.yaml", "r") as yaml_template:
            yaml_template = yaml_template.read()

    domains = list(set(["domain: " + x.split("/")[2] for x in urls]))
    domains = "\n      - ".join(domains)
    urls = "\n      - ".join(urls)

    yaml = yaml_template.replace("{DOMAINS}", domains)
    yaml = yaml.replace("{URLS}", urls)

    with open(f"{folder}{file_name}.yaml", "w") as dest:
        dest.write(yaml)

    return f"{folder}{file_name}.yaml"


def check_crawl(crawl_id):
    import subprocess
    check = subprocess.run("browsertrix crawl list", shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8")
    check = check.split("\n")
    while "" in check:
        check.remove("")
    for i, x in enumerate(check):
        clean = x.split("  ")
        while "" in clean:
            clean.remove("")
        clean = [x.strip() for x in clean]
        if i%2 == 0:
            headings = clean
        else:
            response = dict(zip(headings, clean))
            if response["CRAWL ID"] == crawl_id:
                break

    return response
#####MAKE SURE IT DOESNT BREAK IF NOT CRAWLS######


def check_errors(cdx):
    with open(cdx, "r") as cdx:
        cdx = cdx.read()
        cdx = cdx.split("\n")

    while "" in cdx:
        cdx.remove("")

    cdx = [eval(line.split(" ")[2]) for line in cdx]

    statuses = {}
    for x in range(100, 600):
        statuses[x] = None

    for line in cdx:
        if "status" not in line.keys():
            continue
        try:
            statuses[int(line["status"])].append(line["url"])
        except:
            statuses[int(line["status"])] = [line["url"]]

    return statuses


def patch(statuses):
    print("\nHere are the HTTP responses for this crawl and their frequency:\n")

    for x in [[code, len(statuses[code])] for code in statuses if statuses[code]]:
        print(x)

    while patch not in ["y", "n"]:
        patch = input("\nWould you like to launch a patch? [Y/n]").lower()
        if patch == "y":
            to_add = [403, 404]
            while add not in ["y", "n"]:
                add = input(
                    "\nPatch will automatically rerun any 403 and 404 errors. would you like to add others? [Y/n]").lower()
                if add == "y":
                    valid = False
                    while not valid:
                        others = input("\nEnter other responses to patch separated by a comma e.g. 429,503,504")
                        split_others = others.split(",")
                        try:
                            to_add += [int(code.strip()) for code in split_others if
                                       int(code.strip()) in range(100, 600)]
                            patch_urls = []
                            for code in to_add:
                                if statuses[code] != None:
                                    patch_urls += (statuses[code])
                            return patch_urls
                        except:
                            print(f"\nThere is an issue with your input: {others}\nPlease renter.")
                            valid = False
        elif patch == "n":
            return False