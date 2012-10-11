"""
Module containing class used for loading config files.

Copyright 2012 Red Hat, Inc.
Licensed under the GNU General Public License, version 2 as
published by the Free Software Foundation; see COPYING for details.
"""

__autor__ = """
olichtne@redhat.com (Ondrej Lichtner)
"""

import os
import sys
import logging
import re
from ConfigParser import ConfigParser
from NetTest.NetTestSlave import DefaultRPCPort
from NetUtils import verify_ip_address, verify_mac_address

class ConfigError(Exception):
    pass

class Config():
    options = None

    def __init__(self):
        self.options = dict()

        self.options['log'] = dict()
        self.options['log']['port'] = 9998
        self.options['log']['path'] = os.path.join(
                os.path.dirname(sys.argv[0]), './')

        self.options['environment'] = dict()
        self.options['environment']['mac_pool_range'] = \
                ['52:54:01:00:00:01', '52:54:01:FF:FF:FF']
        self.options['environment']['rpcport'] = DefaultRPCPort
        self.options['environment']['pool_dirs'] = []

    def get_config(self):
        return self.options

    def get_section(self, section):
        if section not in self.options:
            msg = 'Unknow section: %s' % section
            raise ConfigError(msg)
        return self.options[section]

    def get_option(self, section, option):
        sect = self.get_section(section)
        if option not in sect:
            msg = 'Unknown option: %s in section: %s' % (option, section)
            raise ConfigError(msg)
        return sect[option]

    def load_config(self, path):
        '''Parse and load the config file'''
        exp_path = os.path.expanduser(path)
        abs_path = os.path.abspath(exp_path)
        parser = ConfigParser(dict_type=dict)
        parser.read(abs_path)

        sections = parser._sections
        for section in sections:
            if section == "log":
                self.sectionLogs(sections[section], abs_path)
            elif section == "environment":
                self.sectionEnvironment(sections[section], abs_path)
            else:
                msg = "Unknown section: %s" % section
                raise ConfigError(msg)

    def sectionLogs(self, config, cfg_path):
        section = self.options['log']

        config.pop('__name__', None)
        for option in config:
            if option == 'port':
                section['port'] = self.optionPort(config[option])
            elif option == 'path':
                section['path'] = self.optionLogPath(config[option], cfg_path)
            else:
                msg = "Unknown option: %s in section log" % option
                raise ConfigError(msg)

    def sectionEnvironment(self, config, cfg_path):
        section = self.options['environment']

        config.pop('__name__', None)
        for option in config:
            if option == 'mac_pool_range':
                section['mac_pool_range'] = self.optionMacRange(config[option])
            elif option == 'rpcport':
                section['rpcport'] = self.optionPort(config[option])
            elif option == 'machine_pool_dirs':
                section['pool_dirs'] = self.optionPoolDirs(config[option],
                                                           cfg_path)
            else:
                msg = "Unknown option: %s in section environment" % option
                raise ConfigError(msg)

    def optionPort(self, option):
        try:
            int(option)
        except ValueError:
            msg = "Option port expects a number."
            raise ConfigError(msg)
        return int(option)

    def optionLogPath(self, option, cfg_path):
        exp_path = os.path.expanduser(option)
        abs_path = os.path.join(os.path.dirname(cfg_path), exp_path)
        norm_path = os.path.normpath(abs_path)
        return norm_path

    def optionMacRange(self, option):
        vals = option.split()
        if len(vals) != 2:
            msg = "Option mac_pool_range expects 2"\
                    " values sepparated by whitespaces."
            raise ConfigError(msg)
        if not verify_mac_address(vals[0]):
            msg = "Invalid MAC address: %s" % vals[0]
            raise ConfigError(msg)
        if not verify_mac_address(vals[1]):
            msg = "Invalid MAC address: %s" % vals[1]
            raise ConfigError(msg)
        return vals

    def optionPoolDirs(self, option, cfg_path):
        env = self.get_section('environment')
        paths = re.split(r'(?<!\\)\s', option)

        pool_dirs = env['pool_dirs']
        for path in paths:
            if path == '':
                continue
            exp_path = os.path.expanduser(path)
            abs_path = os.path.join(os.path.dirname(cfg_path), exp_path)
            norm_path = os.path.normpath(abs_path)
            pool_dirs.append(norm_path)

        return pool_dirs