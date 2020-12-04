from datetime import datetime, date, timedelta
import sys, os, csv, time
from requests import get
from json import dumps

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/"
home = os.path.expanduser("~") + "/"
sys.path.insert(1, f"{home}BX_tools")
import capture

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

    with open(f"current_areaNames_{today[:8]}.csv", "w") as dest:
        writer = csv.writer(dest)
        writer.writerows(areaNames)

def get_all_urls(areaNames):
    formats = ["csv", "json", "xml"]    #4.1 Three possible formats of the queries
    all_urls = []

    for i, type in enumerate(types):
        with open(f"{ROOT}URL_templates/{type}.txt", "r") as urls:    #4.2 Opens txt files with URL templates
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

    with open(f"{ROOT}URL_templates/extras.txt", "r") as extras:
        extras = extras.read()
        extras = extras.split("\n")                         #4.7 Creats list of extra URls from extras.txt

    for extra in extras:
        all_urls.append(extra)                              #4.8 Appends extra URLs


    newrls = [url.replace("%20", "%2520") for url in all_urls  if "%20" in url]    #4.9 Creates list of urls with %2520 in place of %20 to fix replayweb.page issue.

    #staging_urls = [url.replace("https://api.coronavirus.data.gov.uk", "https://api.coronavirus-staging.data.gov.uk") for url in all_urls  if "https://api.coronavirus.data.gov.uk" in url]

    all_urls += newrls #+ staging_urls

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

    with open(f"{ROOT}URL_templates/lookups.txt", "r") as lookups:
        lookups = lookups.read()
        lookups = lookups.split("\n")               # 4.7 Creates list of lookup URLs from lookups.txt

    all_urls += lookups

    stamp = (date.today() - timedelta(6)).isoformat()
    stamp2 = (date.today() - timedelta(19)).isoformat()
    map_urls = []
    for view in ["utla", "ltla", "msoa"]:
        with open(f"{ROOT}areaCodes/{view}codes.txt", "r") as codes, open(f"{ROOT}URL_templates/{view}map.txt", "r") as urls:
            codes = codes.read().split("\n")
            urls = urls.read().split("\n")
        for code in codes:
            for url in urls:
                url = eval("f\"" + url + "\"")
                map_urls.append(url)

    return [all_urls, map_urls]                                  #4.10 Returns the list


os.chdir(home)
today = datetime.today().strftime("%Y%m%d")
types = ["overview", "nation", "region", "nhsRegion", "utla", "ltla"]

CVDB_folder = home + "covid_dashboard/"

if os.path.isdir(CVDB_folder) == False:
    os.mkdir(CVDB_folder)

os.chdir(CVDB_folder)

areaName_files = [x for x in os.listdir() if (x.startswith("current_areaNames")) and (x.endswith(".csv"))]

if f"current_areaNames_{today}.csv" not in areaName_files:
    get_areaNames()
    for x in areaName_files:
        os.remove(x)

with open(f"current_areaNames_{today}.csv", "r") as areaNames:
    reader = csv.reader(areaNames)
    areaNames = list(reader)

both_sets = get_all_urls(areaNames)
map_urls = list(set(both_sets[1]))

capture_name = capture.check_validity(input("Please enter name of capture.>"))

with open("map_urls.txt", "w") as dest:
    dest.write(f"{capture_name}\n")
    dest.write("\n".join(map_urls))

capture.capture(both_sets[0], capture_name=capture_name, area=CVDB_folder, crawl_depth=1, browser="chrome:84", warc_name="dashboard_combined", progress=False)

capture_folder = capture_name + "_" + datetime.today().strftime("%d%m%Y")

while not os.path.isfile(f"{CVDB_folder}{capture_folder}/lastpatch_map.warc.gz"):
    print("\rWaiting for map urls crawl to finish...", end="")
    time.sleep(30)


capture.combine_warcs(f"{CVDB_folder}{capture_folder}", name="FINALcombined_map_db")