from ukgwa_BX import ukgwa_BX
from datetime import datetime
import os, time, csv
from requests import get
from json import dumps


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

    all_urls = all_urls + newrls #+ staging_urls

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
        lookups = lookups.split("\n")               # 4.7 Creates list of lookup URls from lookups.txt

    all_urls = lookups + all_urls

    return all_urls                                      #4.10 Returns the list


def run_crawl(urls, file_name, collection_loc):
    yaml = ukgwa_BX.create_yaml(urls, crawl_loc)
    crawl_id = ukgwa_BX.run_BX(yaml)
    response = ukgwa_BX.check_crawl(crawl_id)
    while response["STATUS"] != "done":
        response = ukgwa_BX.check_crawl(crawl_id)
        total = int(response["SEEN"])
        crawled = total - int(response["TO CRAWL"])
        ratio = int((crawled / total) * 40)
        done = ratio * "■"
        to_do = (40 - ratio) * " "
        print(f"Crawling... {done}{to_do}| {crawled}/{total} URLs crawled", flush=True, end="\r")
        time.sleep(60)

    print("\nCrawl finished")
    os.system(f"browsertrix crawl remove {crawl_id}")

    status = ukgwa_BX.check_errors(f"{collection_loc}/indexes/autoindex.cdxj")
    patch_urls = ukgwa_BX.patch(status, crawl_loc)
    if patch_urls:
        run_crawl(patch_urls, "PATCH"+crawl_name, collection_loc)
    else:
        os.system(f"sudo cp -r {collection_loc} {crawl_loc}")
        print(f"Crawl finished. Crawl files located in:\n{crawl_loc}{crawl_name}/")


ROOT = os.path.dirname(os.path.abspath(__file__)) + "/"
home = os.path.expanduser("~") + "/"
os.chdir(home)
today = datetime.today().strftime('%Y%m%d%H%M%S')
types = ["overview", "nation", "region", "nhsRegion", "utla", "ltla"]

crawl_name = input("What is the name of this crawl? >") + "_" + today
while any(punctuation in crawl_name for punctuation in [".", "-", "/", ":", ",", "?", "!", ";", "(", ")", "[", "]", "{", "}"]):
    crawl_name = input("Crawl name cannot include punctuation (except underscore _). Please re-enter: >") + "_" + today

collection_loc = f"{home}browsertrix/webarchive/collections/{crawl_name}/"
CVDB_folder = home + "covid_dashboard/"
crawl_loc = CVDB_folder + crawl_name + "/"

if os.path.isdir(CVDB_folder) == False:
    os.mkdir(CVDB_folder)
os.mkdir(crawl_loc)
os.chdir(CVDB_folder)


areaName_files = [x for x in os.listdir() if (x.startswith("current_areaNames")) and (x.endswith(".csv"))]

if f"current_areaNames_{today[:8]}.csv" not in areaName_files:
    get_areaNames()
    apt_updates = "sudo apt-get update; sudo apt update; sudo apt-get upgrade; sudo apt upgrade"
    initialise = "cd ~; cd browsertrix; sudo git pull; sudo ./install-browsers.sh; sudo docker-compose build; sudo docker-compose up -d; cd ~; browsertrix crawl remove-all; cd coronavirus.data.gov.uk_URL_generator; cd ~; cd covid_dashboard"
    os.system(apt_updates + "; " + initialise)
    os.system(apt_updates)
    for x in areaName_files:
        os.remove(x)

with open(f"current_areaNames_{today[:8]}.csv", "r") as areaNames:
    reader = csv.reader(areaNames)
    areaNames = list(reader)

all_urls = get_all_urls(areaNames)[:500]

run_crawl(all_urls, crawl_name, collection_loc)





### Make patch show changes (write to .txt)