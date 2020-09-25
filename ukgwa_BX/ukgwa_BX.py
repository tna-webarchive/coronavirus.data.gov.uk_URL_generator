import subprocess, os, json

def run_BX(yaml_loc):
    # initialise = "cd ~; cd browsertrix; sudo git pull; sudo ./install-browsers.sh; sudo docker-compose build; sudo docker-compose up -d; cd ~; browsertrix crawl remove-all; cd coronavirus.data.gov.uk_URL_generator"
    # os.system(initialise)

    check = subprocess.run(f"sudo browsertrix crawl create {yaml_loc}", shell=True,
                           stdout=subprocess.PIPE).stdout.decode("utf-8")
    print(check)
    check = check.split("\n")[1]
    crawl_id = check.split(": ")[1]

    return crawl_id


def create_yaml(urls, folder):
    while "" in urls:
        urls.remove("")
    while None in urls:
        urls.remove(None)

    crawl_name = folder.rsplit("/")[-2]

    if f"{crawl_name}.yaml" in os.listdir(folder):
        file_name = "PATCH" + crawl_name
    else:
        file_name = crawl_name

    yaml_template = f"""crawls:
  - name: {file_name}
    crawl_type: custom
    crawl_depth: 2
    num_browsers: 1
    num_tabs: 2
    coll: {crawl_name}
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

    print("YAML created, launching browsertrix...")
    domains = list(set(["domain: " + x.split("/")[2] for x in urls]))
    domains = "\n      - ".join(domains)
    urls = "\n      - ".join(urls)

    yaml = yaml_template.replace("{DOMAINS}", domains)
    yaml = yaml.replace("{URLS}", urls)

    with open(f"{folder}{file_name}.yaml", "w") as dest:
        dest.write(yaml)

    return f"{folder}{file_name}.yaml"


def check_crawl(crawl_id):
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
    try:
        with open(cdx, "r") as cdx:
            cdx = cdx.read()
            cdx = cdx.split("\n")
    except:
        print("It seems as though Browsertrix didn't produce a CDX for this crawl.")
        return False

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


def patch(statuses, crawl_loc):
    if type(statuses) != dict:
        return False

    result = {code:len(statuses[code]) for code in statuses if statuses[code]}           #compare with previous result if patch

    if "HTTP_responses.json" in os.listdir(crawl_loc):
        with open(f"{crawl_loc}HTTP_responses.json", "r") as prev:
            prev = json.load(prev)
        for status in prev.keys():
            result[status] -= int(prev[status])


    with open(f"{crawl_loc}HTTP_responses.json", "w") as dest:
        json.dump(result, dest)

    print("\nHere are the HTTP responses for this crawl and their frequency:\n")

    for x in result:
        print(x)

    patch=None
    while patch not in ["y", "n"]:
        patch = input("\nWould you like to launch a patch? [Y/n]").lower()
        if patch == "y":
            to_add = [403, 404]
            add=None
            while add not in ["y", "n"]:
                add = input(
                    "\nPatch will automatically rerun any 403 and 404 errors.\nWould you like to add others? [Y/n]").lower()
                if add == "y":
                    valid = False
                    while not valid:
                        others = input("\nEnter other responses to patch separated by a comma e.g. 429,503,504\n>")
                        split_others = others.split(",")
                        try:
                            to_add += [int(code.strip()) for code in split_others if
                                       int(code.strip()) in range(100, 600)]
                            valid = True
                        except:
                            print(f"\nThere is an issue with your input: {others}\nPlease renter.")
                            valid = False
            patch_urls = []
            for code in to_add:
                if statuses[code] != None:
                    patch_urls += (statuses[code])
            return patch_urls

        elif patch == "n":
            return False



#patch should be function of check_errors