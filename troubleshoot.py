from ukgwa_BX import ukgwa_BX
import os

home = os.path.expanduser("~") + "/"
folder = home + "troubleshoot/"

if os.path.isdir(folder) == False:
    os.mkdir(folder)

yaml = ukgwa_BX.create_yaml(["https://www.local.gov.uk", "https://www.nhs.uk"], folder, default=True)

ukgwa_BX.run_BX(yaml)