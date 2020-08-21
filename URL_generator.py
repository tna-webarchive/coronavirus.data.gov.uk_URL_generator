####### 1. Import modules #######

from requests import get
from json import dumps
from datetime import datetime


######### 2. Define global variables ########

types = ["overview", "nation", "region", "nhsRegion", "utla", "ltla"]  #2.1 Types defined in Developer's guide https://coronavirus.data.gov.uk/developers-guide
today = datetime.today().strftime('%Y-%m-%d')


##### 3. Function to gather all area names and catergorise by area type ######

def get_areaNames():
    ENDPOINT = "https://api.coronavirus.data.gov.uk/v1/lookup?"
    areaNames = [[]] * len(types)

    for i, type in enumerate(types):
        filters = [f"areaType={types[i]}"]   #3.1 Filters by date so only one entry per name. To Add more enter another value in list
        structure = {"name": "areaName"}     #3.2 These are the datapoints returned. To add more enter another value in dictionary
        api_params = {"filters": str.join(";", filters), "structure": dumps(structure, separators=(",", ":")),}  #3.3 Creates URL string
        response = get(ENDPOINT, params=api_params, timeout=10)  #3.4 API call

        if response.status_code >= 400:
            raise RuntimeError(f'Request failed: {response.text}')  #3.5 Raises error if request fails

        names = response.json()["data"]                         #3.6 Creates list of names from JSON response
        names = [x["name"].replace(" ", "%20") for x in names]  #3.7 Replaces sapec with %20 for URL
        areaNames[i] = names                                    #3.8 Adds list to master list of Area Names

    return areaNames



####### 4. Constructing all URLS ########

def get_all_urls():
    areaNames = get_areaNames()
    formats = ["csv", "json", "xml"]    #4.1 Three possible formats of the queries
    all_urls = []

    for i, type in enumerate(types):
        with open(f"{type}.txt", "r") as urls:    #4.2 Opens txt files with URL templates
            urls = urls.read()
            urls = urls.split("\n")
        for url in urls:
            if "{name}" in url:
                for name in areaNames[i]:
                    named_url = url.replace("{name}", name)
                    if "format=" in named_url:
                        for format in formats:
                            formatted_url = named_url.replace("format=", f"format={format}")
                            all_urls.append(formatted_url)
                    else:
                        all_urls.append(named_url)
            elif "format=" in url:
                for format in formats:
                    formatted_url = url.replace("format=", f"format={format}")
                    all_urls.append(formatted_url)
            else:
                all_urls.append(url)

    with open("extras.txt", "r") as extras:
        extras = extras.read()
        extras = extras.split("\n")

    for extra in extras:
        all_urls.append(extra)

    return set(all_urls)

####### 5. Function to write all generated URLs to txt file #######
def export_urls(all_urls, file_name=f"{today}_covid_dashboard_urls"):
    all_urls = "\n".join(all_urls)
    with open(f"{file_name}.txt", "w") as dest:
        dest.write(all_urls)


###### 6. Run Program #####

all_urls = get_all_urls()
export_urls(all_urls)


##### NEXT STEPS
##### Export straight to YAML
##### Run Browsertrix job from cmd line ( os.system() )

