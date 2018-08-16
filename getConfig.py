import configparser
import sys

class getConfig:
    def __init__(self):
        self.loadConfig()
        
    def loadConfig(self):
        try:
            conf = configparser.ConfigParser()
            conf.read('config.ini')
        except FileNotFound:
            print("Config File not found.  Set config file and try again")
            sys.exit(1)
        section = "Rally"
        self.api = conf.get(section, "API Key")
        self.url = conf.get(section, "URL")
        self.wksp = conf.get(section, "Workspace")
        self.proj = conf.get(section, "Project")
        self.query = conf.get(section, "Query")
