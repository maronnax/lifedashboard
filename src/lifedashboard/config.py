"""Config parsing"""

from configparser import ConfigParser
import os

class AppConfigParser(ConfigParser):
    def get(self, config_param, section="app", type = None, is_filename = None, default = None):
        # super does not work b/c ConfigParser is an old style class.

        if default is not None:
            if not self.has_option(config_param, section = section): return default

        conf_val = ConfigParser.get(self, section, config_param)

        if type is not None:
            conf_val = type(conf_val)

        if is_filename is not None:
            conf_val = os.path.abspath(os.path.join(self.conf_directory, os.path.expanduser(conf_val)))

        return conf_val

    def has_option(self, config_param, section="app"):
        return ConfigParser.has_option(self, section, config_param)

    def read(self, fn):
        self.conf_directory = os.path.split(os.path.abspath(fn))[0]
        ConfigParser.read(self, fn)
        return
