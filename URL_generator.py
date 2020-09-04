####### 1. Import modules #######

from requests import get
from json import dumps
from datetime import datetime

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

    return set(all_urls)                                   #4.10 Returns the list, randomised (set())


####### 5. Function to write all generated URLs to txt file #######

def export_urls(all_urls, file_name=f"{today}_covid_dashboard_urls"):        #5.1 Takes two args, list of URLs and file name. Defualt is "{date}_covid_dashboard_urls"
    all_urls = "\n".join(all_urls)
    with open(f"{file_name}.txt", "w") as dest:
        dest.write(all_urls)


###### 6. Run Program #####

all_urls = get_all_urls()
export_urls(all_urls)


##### NEXT STEPS
##### Export straight to YAML
##### Run Browsertrix job from cmd line ( os.system() )

