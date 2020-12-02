import os, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/"
home = os.path.expanduser("~") + "/"
sys.path.insert(1, f"{home}BX_tools")

import capture

CVDB_folder = home + "covid_dashboard/"

with open(f"{CVDB_folder}map_urls.txt", "r") as source:
    map_urls = source.read().split("\n")

capture_name = map_urls.pop(0)

capture.capture(map_urls, f"maps_{capture_name}", CVDB_folder, crawl_depth=1, patch="y", patch_codes="403", progress=False, warc_name="map_combined")






