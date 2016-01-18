import os
import pdb

def getApplicationConfigFile():
    conf_fn = os.path.abspath(os.path.join(os.path.split(__file__)[0], "../..", "conf/app.conf"))
    return conf_fn

def editFileInteractively(fn):
    os.system("emacsclient {}".format(fn))
