import os

print os.popen("echo %EMAIL%").read().strip()
