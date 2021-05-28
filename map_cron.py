import os, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/"
home = "/home/ubuntu/"
sys.path.insert(1, f"{home}BX_tools")
today = datetime.today().strftime("%d%m%Y")

import capture_cron

CVDB_folder = home + "covid_dashboard/"

os.chdir(CVDB_folder)

with open(f"map_urls.txt", "r") as source:
    map_urls = source.read().split("\n")

capture_name = map_urls.pop(0) + "_" + today

map_dir = CVDB_folder+capture_name+'/map'

os.mkdir(map_dir)

os.rename("map_urls.txt", f"{map_dir}/map_urls.txt")

os.chdir(map_dir)

patch = 0

while True:
    if patch > 0:
        t = datetime.today()
        if t.minute > 30:
            wait = 90 - t.minute
        else:
            wait = 30 - t.minute
        if patch > 3:
            wait = 15
        print(f"{datetime.now().strftime('%H:%M:%S')}: Waiting {wait} minutes to relaunch {len(to_patch)} URLs")
        time.sleep(wait*60)
    os.system(f'wget -O "temp.html" --no-verbose --input-file={"patch"*patch}map_urls.txt -e robots=off --tries=2 --waitretry=5 --user-agent="The National Archives UK Government Web Archive webarchive@nationalarchives.gov.uk" --warc-file="{"patch"*patch}map_capture" --warc-max-size=1G --wait=0.2 --limit-rate=300k')
    os.system(f"cdxj-indexer {'patch'*patch}map_capture-00000.warc.gz > {'patch'*patch}map_patch.cdxj")
    cdx = capture_cron.Cdx(f"{'patch'*patch}map_patch.cdxj")
    rud = cdx.create_rud()
    to_patch = rud.get_urls("403,429")
    if patch > 18:
        print("Patched 18 times so exiting capture.")
        break
    if len(to_patch) > 0:
        print(f"\nPATCHING {len(to_patch)} URLs....")
        patch += 1
        l = "\n".join(to_patch)
        with open(f"{'patch'*patch}map_urls.txt", "w") as dest:
            dest.write(l)
    else:
        capture_cron.combine_warcs(map_dir, name='lastpatch_map')
        print("\ncapture is complete")
        print(f"\nWait for dashboard capture to finish. Final combined WARC will be located at: \n{CVDB_folder}{capture_name}/FINALcombined_map_db.warc.gz")
        break

os.rename(f"lastpatch_map.warc.gz", f"{CVDB_folder+capture_name}/lastpatch_map.warc.gz")