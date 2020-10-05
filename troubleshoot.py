from ukgwa_BX import ukgwa_BX

home = os.path.expanduser("~") + "/"
folder = home + "troubleshoot/"

yaml = ukgwa_BX.create_yaml(["https://www.local.gov.uk", "https://www.nhs.uk"], folder, default=True)

ukgwa_BX.run_BX(yaml)