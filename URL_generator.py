####### 1. Import modules #######

from requests import get
from json import dumps
from datetime import datetime
import os

home = os.path.expanduser("~")
os.chdir(f"{home}/coronavirus.data.gov.uk_URL_generator")

######### 2. Define global variables ########

types = ["overview", "nation", "region", "nhsRegion", "utla", "ltla"]  #2.1 Types defined in Developer's guide https://coronavirus.data.gov.uk/developers-guide
today = datetime.today().strftime('%Y-%m-%d')


##### 3. Function to gather all area names and catergorise by area type ######

def get_areaNames():
    ENDPOINT = "https://api.coronavirus.data.gov.uk/v1/lookup?"       #3.1 lookup query url root
    areaNames = [[]] * len(types)

    for i, type in enumerate(types):
        filters = [f"areaType={types[i]}"]   #3.2 To Add more filters enter another value in list
        structure = {"name": "areaName"}     #3.2 To add more return data enter another value in dictionary
        api_params = {"filters": str.join(";", filters), "structure": dumps(structure, separators=(",", ":")),}  #3.3 Creates query URL string
        response = get(ENDPOINT, params=api_params, timeout=10)  #3.4 API call

        if response.status_code >= 400:
            raise RuntimeError(f'Request failed: {response.text}')  #3.5 Raises error if request fails

        names = response.json()["data"]                         #3.6 Creates list of names from JSON response
        names = [x["name"].replace(" ", "%20") for x in names]  #3.7 Replaces sapce with %20 for URL
        areaNames[i] = names                                    #3.8 Adds list to master list of Area Names

    return areaNames



####### 4. Constructing all URLS ########

def get_all_urls():
    areaNames = get_areaNames()
    formats = ["csv", "json", "xml"]    #4.1 Three possible formats of the queries
    all_urls = []

    for i, type in enumerate(types):
        with open(f"URL_templates/{type}.txt", "r") as urls:    #4.2 Opens txt files with URL templates
            urls = urls.read()
            urls = urls.split("\n")                             #4.3 Creates list of URL templates
        for url in urls:
            if "{name}" in url:
                for name in areaNames[i]:
                    named_url = url.replace("{name}", name)     #4.4 Replaces {name} in template to specific selected areaName
                    if named_url[-7:] == "format=":
                        for format in formats:                  #4.5 goes through file formats to generate csv, xml, json requests.
                            formatted_url = named_url.replace("format=", f"format={format}")
                            all_urls.append(formatted_url)      #4.6 adds created URLs to list all_urls
                    elif type not in ["overview", "extras"] and named_url[-6:] == "%22%7D":
                        all_urls.append(named_url)
                        named_json = named_url + "&format=json"
                        all_urls.append(named_json)
                    else:
                        all_urls.append(named_url)              #4.6
            elif url[-7:] == "format=":
                for format in formats:
                    formatted_url = url.replace("format=", f"format={format}")
                    all_urls.append(formatted_url)              #4.6
            elif type not in ["overview", "extras"] and url[-6:] == "%22%7D":
                all_urls.append(url)
                url_json = url + "&format=json"
                all_urls.append(url_json)
            else:
                all_urls.append(url)                            #4.6

    with open("URL_templates/extras.txt", "r") as extras:
        extras = extras.read()
        extras = extras.split("\n")                         #4.7 Creats list of extra URls from extras.txt

    for extra in extras:
        all_urls.append(extra)                              #4.8 Appends extra URLs


    newrls = [url.replace("%20", "%2520") for url in all_urls  if "%20" in url]    #4.9 Creates list of urls with %2520 in place of %20 to fix replayweb.page issue.

    staging_urls = [url.replace("https://api.coronavirus.data.gov.uk", "https://api.coronavirus-staging.data.gov.uk") for url in all_urls  if "https://api.coronavirus.data.gov.uk" in url]

    all_urls = all_urls + newrls + staging_urls

    to_reorder = [url for url in all_urls if ((";" in url and url.count(";") == 1) and "overview" in url)]

    for url in to_reorder:
        split = url.split("=", 1)
        base = split[0]
        rest = split[1].split("&", 1)
        structure = rest[1]
        filters = rest[0].split(";")
        filters.reverse()
        reorder = base + "=" + ";".join(filters) + "&" + structure
        all_urls.append(reorder)


    all_urls = list(set(all_urls))                #Randomises list

    with open("URL_templates/lookups.txt", "r") as lookups:
        lookups = lookups.read()
        lookups = lookups.split("\n")               # 4.7 Creates list of lookup URls from lookups.txt

    num_urls = len(all_urls)
    num_lookups = len(lookups)
    step = num_urls / num_lookups

    for url, index in zip(lookups, range(0, num_urls, int(step))):
        all_urls.insert(index, url)                        # evenly distributes lookup queries to avoid throttling

    return all_urls                                      #4.10 Returns the list


####### 5. Function to write all generated URLs to txt file #######

def run_browsertrix(all_urls, file_name=f"{today}_covid_dashboard"):        #5.1 Takes two args, list of URLs and file name. Defualt is "{date}_covid_dashboard_urls"
    yaml_template = f"""crawls:
  - name: {file_name}
    crawl_type: custom
    crawl_depth: 2
    num_browsers: 1
    num_tabs: 2
    coll: {file_name}
    mode: record

    scopes:
      - {{DOMAINS}}

    seed_urls:
      - {{URLS}}
    behavior_max_time: 80
    browser: chrome:73
    cache: always"""

    global home
    CVDB_folder = home + "/covid_dashboard"
    if os.path.isdir(CVDB_folder) == False:
        os.mkdir(CVDB_folder)
    os.chdir(CVDB_folder)
    domains = list(set(["domain: " + x.split("/")[2] for x in all_urls]))
    domains = "\n      - ".join(domains)
    urls = "\n      - ".join(all_urls[:10])
    yaml = yaml_template.replace("{DOMAINS}", domains)
    yaml = yaml.replace("{URLS}", urls)

    with open(f"{file_name}.yaml", "w") as dest:
        dest.write(yaml)

    os.system(f"sudo browsertrix crawl create {file_name}.yaml")

    print(f"When complete, warc will be located at:\n{home}/browsertrix/webarchive/collections/{file_name}")


# ###### 6. Run Program #####

all_urls = get_all_urls()
run_browsertrix(all_urls)
#
#
# ##### NEXT STEPS
# ##### YAML as txt file to edit config easily.
# ##### Run Browsertrix job from cmd line ( os.system() )
# ##### Figure out correct input for UX
# ##### combine the warcs
# ##### rerun 429, 307, etc.
# ##### compare 404s in warc and live

