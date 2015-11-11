# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'vmriccox'


import os
import re
import ConfigParser
import logging
import json
import fileinput
from experimental_framework.constants import conf_file_sections as cf
from experimental_framework.constants import framework_parameters as fp


# ------------------------------------------------------
# List of common variables
# ------------------------------------------------------

LOG = None
CONF_FILE = None
DEPLOYMENT_UNIT = None
ITERATIONS = None
FINGERPRINT = None

BASE_DIR = None
RESULT_DIR = None
TEMPLATE_DIR = None
TEMPLATE_NAME = None
TEMPLATE_FILE_EXTENSION = None

PKTGEN = None
PKTGEN_DIR = None
PKTGEN_DPDK_DIRECTORY = None
PKTGEN_PROGRAM = None
PKTGEN_COREMASK = None
PKTGEN_MEMCHANNEL = None
PKTGEN_BUS_SLOT_NIC_1 = None
PKTGEN_BUS_SLOT_NIC_2 = None


# ------------------------------------------------------
# Initialization and Input 'heat_templates/'validation
# ------------------------------------------------------

def init(api=False):
    global BASE_DIR
    BASE_DIR = os.getcwd()
    BASE_DIR = BASE_DIR.replace('/experimental_framework', '')
    BASE_DIR = InputValidation.validate_directory_exist_and_format(BASE_DIR, "Error 000001")

    init_conf_file(api)
    init_general_vars()
    init_log()
    if len(CONF_FILE.get_variable_list(cf.CFS_PKTGEN)) > 0:
        init_pktgen()


def init_conf_file(api=False):
    global CONF_FILE
    if api:
        CONF_FILE = ConfigurationFile(cf.get_sections_api())
    else:
        CONF_FILE = ConfigurationFile(cf.get_sections())


def init_general_vars():
    global TEMPLATE_FILE_EXTENSION
    global TEMPLATE_NAME
    global TEMPLATE_DIR
    global RESULT_DIR
    global ITERATIONS

    TEMPLATE_FILE_EXTENSION = '.yaml'

    # Check Section in Configuration File
    InputValidation.validate_configuration_file_section(cf.CFS_GENERAL,
                                                        "Section " + cf.CFS_GENERAL +
                                                        "is not present in configuration file")

    # Validate template directory
    # InputValidation.validate_configuration_file_parameter(cf.CFS_GENERAL,
    #                                                       cf.CFSG_TEMPLATE_DIR, "Parameter " +
    #                                                       cf.CFSG_TEMPLATE_DIR +
    #                                                       " is not present in the configuration file")
    # TEMPLATE_DIR = CONF_FILE.get_variable(cf.CFS_GENERAL, cf.CFSG_TEMPLATE_DIR)
    TEMPLATE_DIR = BASE_DIR + 'heat_templates/'
    # TEMPLATE_DIR = InputValidation.validate_directory_exist_and_format(TEMPLATE_DIR, 'The template directory specified '
    #                                                                                  'in configuration file does not '
    #                                                                                  'exist' + TEMPLATE_DIR)

    # Validate template name
    InputValidation.validate_configuration_file_parameter(cf.CFS_GENERAL,
                                                          cf.CFSG_TEMPLATE_NAME,
                                                          "Parameter " + cf.CFSG_TEMPLATE_NAME +
                                                          "is not present in configuration file")
    TEMPLATE_NAME = CONF_FILE.get_variable(cf.CFS_GENERAL, cf.CFSG_TEMPLATE_NAME)
    # InputValidation.validate_string(TEMPLATE_NAME, "The provided template name must be a string")
    InputValidation.validate_file_exist(TEMPLATE_DIR + TEMPLATE_NAME, "The provided template file does not exist")

    # Validate result directory
    # InputValidation.validate_configuration_file_parameter(cf.CFS_GENERAL,
    #                                                       cf.CFSG_RESULT_DIRECTORY,
    #                                                       "Parameter " + cf.CFSG_RESULT_DIRECTORY +
    #                                                       "is not present in configuration file")
    # RESULT_DIR = BASE_DIR + CONF_FILE.get_variable(cf.CFS_GENERAL, cf.CFSG_RESULT_DIRECTORY)
    # RESULT_DIR = RESULT_DIR if RESULT_DIR.endswith('/') else RESULT_DIR + '/'
    RESULT_DIR = BASE_DIR + 'results/'

    # Validate and assign Iterations
    if cf.CFSG_ITERATIONS in CONF_FILE.get_variable_list(cf.CFS_GENERAL):
        ITERATIONS = int(CONF_FILE.get_variable(cf.CFS_GENERAL, cf.CFSG_ITERATIONS))
    else:
        ITERATIONS = 1

    # Validate and assign ApexLake Fingerprint
    # TODO: TO be removed for Yardstick
    if cf.CFSG_FINGERPRINT in CONF_FILE.get_variable_list(cf.CFS_GENERAL):
        FINGERPRINT = InputValidation.validate_boolean(CONF_FILE.get_variable(cf.CFS_GENERAL, cf.CFSG_FINGERPRINT), 'The parameter ' + cf.CFSG_FINGERPRINT + 'is not a boolean')


def init_log():
    global LOG
    # TODO: Change logging level from config file
    logging.basicConfig(level=logging.INFO)
    LOG = logging.getLogger()
    # LOG.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter("%(asctime)s --- %(message)s")
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(log_formatter)
    # console_handler.setLevel(logging.INFO)
    # LOG.addHandler(console_handler)

    file_handler = logging.FileHandler("{0}/{1}.log".format("./", "benchmark"))
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.DEBUG)
    LOG.addHandler(file_handler)


# ------------------------------------------------------
# Packet Generator conf variables
# ------------------------------------------------------
def init_pktgen():
    global PKTGEN
    global PKTGEN_DIR
    global PKTGEN_PROGRAM
    global PKTGEN_COREMASK
    global PKTGEN_MEMCHANNEL
    global PKTGEN_BUS_SLOT_NIC_1
    global PKTGEN_BUS_SLOT_NIC_2
    global PKTGEN_DPDK_DIRECTORY

    InputValidation.validate_configuration_file_section(cf.CFS_PKTGEN, "Section " + cf.CFS_PKTGEN +
                                                        " is not present in the configuration file")
    pktgen_var_list = CONF_FILE.get_variable_list(cf.CFS_PKTGEN)

    PKTGEN = 'dpdk_pktgen'  # default value
    if cf.CFSP_PACKET_GENERATOR in pktgen_var_list:
        InputValidation.validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                              cf.CFSP_PACKET_GENERATOR,
                                                              "Parameter " + cf.CFSP_PACKET_GENERATOR +
                                                              " is not present in section " + cf.CFS_PKTGEN)
        PKTGEN = CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_PACKET_GENERATOR)

    if PKTGEN not in fp.get_supported_packet_generators():
        raise ValueError('The specified packet generator is not supported by the framework')

    # Check if the packet gen is dpdk_pktgen
    if PKTGEN == cf.CFSP_PG_DPDK:
        InputValidation.validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                              cf.CFSP_DPDK_PKTGEN_DIRECTORY,
                                                              "Parameter " + cf.CFSP_DPDK_PKTGEN_DIRECTORY +
                                                              " is not present in section " + cf.CFS_PKTGEN)
        PKTGEN_DIR = CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_PKTGEN_DIRECTORY)
        PKTGEN_DIR = InputValidation.validate_directory_exist_and_format(PKTGEN_DIR, "The directory " + PKTGEN_DIR +
                                                                         "does not exist")

        InputValidation.validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                              cf.CFSP_DPDK_PROGRAM_NAME,
                                                              "Parameter " + cf.CFSP_DPDK_PROGRAM_NAME +
                                                              " is not present in section " + cf.CFS_PKTGEN)
        PKTGEN_PROGRAM = CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_PROGRAM_NAME)

        InputValidation.validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                              cf.CFSP_DPDK_COREMASK,
                                                              "Parameter " + cf.CFSP_DPDK_COREMASK +
                                                              " is not present in section " + cf.CFS_PKTGEN)
        PKTGEN_COREMASK = CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_COREMASK)
        # TODO: coremask to be further validated

        InputValidation.validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                              cf.CFSP_DPDK_MEMORY_CHANNEL,
                                                              "Parameter " + cf.CFSP_DPDK_MEMORY_CHANNEL +
                                                              " is not present in section " + cf.CFS_PKTGEN)
        PKTGEN_MEMCHANNEL = CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_MEMORY_CHANNEL)
        # TODO: memchannel to be further validated

        InputValidation.\
            validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                  cf.CFSP_DPDK_BUS_SLOT_NIC_1,
                                                  "Parameter " +
                                                  cf.CFSP_DPDK_BUS_SLOT_NIC_1 +
                                                  " is not present in "
                                                  "section " + cf.CFS_PKTGEN)
        PKTGEN_BUS_SLOT_NIC_1 = \
            CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_BUS_SLOT_NIC_1)
        # TODO: to be further validated

        InputValidation.\
            validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                  cf.CFSP_DPDK_BUS_SLOT_NIC_2,
                                                  "Parameter " +
                                                  cf.CFSP_DPDK_BUS_SLOT_NIC_2 +
                                                  " is not present in "
                                                  "section " + cf.CFS_PKTGEN)
        PKTGEN_BUS_SLOT_NIC_2 = \
            CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_BUS_SLOT_NIC_2)
        # TODO: to be further validated

        InputValidation.\
            validate_configuration_file_parameter(cf.CFS_PKTGEN,
                                                  cf.CFSP_DPDK_DPDK_DIRECTORY,
                                                  "Parameter " +
                                                  cf.CFSP_DPDK_DPDK_DIRECTORY +
                                                  " is not present in "
                                                  "section " + cf.CFS_PKTGEN)
        PKTGEN_DPDK_DIRECTORY = \
            CONF_FILE.get_variable(cf.CFS_PKTGEN, cf.CFSP_DPDK_DPDK_DIRECTORY)
        # TODO: to be further validated


# ------------------------------------------------------
# Configuration file access
# ------------------------------------------------------

class ConfigurationFile:
    """
    Used to extract data from the configuration file
    """

    def __init__(self, sections, config_file='conf.cfg'):
        """
        Reads configuration file sections

        :param sections: list of strings representing the sections to be loaded
        :param config_file: name of the configuration file (string)
        :return: None
        """
        InputValidation.validate_string(config_file, "The configuration file name must be a string")
        config_file = BASE_DIR + config_file
        InputValidation.validate_file_exist(config_file, 'The provided configuration file does not exist')
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_file)
        for section in sections:
            setattr(self, section, ConfigurationFile._config_section_map(section, self.config))

    @staticmethod
    def _config_section_map(section, config_file):
        """
        Returns a dictionary with the configuration values for the specific section

        :param section: section to be loaded (string)
        :param config_file: name of the configuration file (string)
        :return: dict
        """
        dict1 = dict()
        options = config_file.options(section)
        for option in options:
            try:
                dict1[option] = config_file.get(section, option)
            except:
                LOG.debug("exception on %s!" % option)
                dict1[option] = None
        return dict1

    def get_variable(self, section, variable_name):
        """
        Returns the value correspondent to a variable

        :param section: section to be loaded (string)
        :param variable_name: name of the variable (string)
        :return: string
        """
        InputValidation.validate_string(variable_name, "The variable name must be a string")
        if variable_name in self.get_variable_list(section):
            sect = getattr(self, section)
            return sect[variable_name]
        else:
            raise ValueError('Parameter ' + variable_name + ' is not in the ' + section + ' section of the conf file')

    def get_variable_list(self, section):
        """
        Returns the list of the available variables in a section
        :param section: section to be loaded (string)
        :return: list
        """
        try:
            return getattr(self, section)
        except:
            raise ValueError('Section ' + section + ' not found in the configuration file')


# ------------------------------------------------------
# Get OpenStack Credentials
# ------------------------------------------------------
def get_credentials():
    """
    Returns the credentials for OpenStack access from the configuration file
    :return: dictionary
    """
    credentials = dict()
    credentials[cf.CFSO_IP_CONTROLLER] = CONF_FILE.get_variable(cf.CFS_OPENSTACK, cf.CFSO_IP_CONTROLLER)
    credentials[cf.CFSO_HEAT_URL] = CONF_FILE.get_variable(cf.CFS_OPENSTACK, cf.CFSO_HEAT_URL)
    credentials[cf.CFSO_USER] = CONF_FILE.get_variable(cf.CFS_OPENSTACK, cf.CFSO_USER)
    credentials[cf.CFSO_PASSWORD] = CONF_FILE.get_variable(cf.CFS_OPENSTACK, cf.CFSO_PASSWORD)
    credentials[cf.CFSO_AUTH_URI] = CONF_FILE.get_variable(cf.CFS_OPENSTACK, cf.CFSO_AUTH_URI)
    credentials[cf.CFSO_PROJECT] = CONF_FILE.get_variable(cf.CFS_OPENSTACK, cf.CFSO_PROJECT)
    return credentials


# ------------------------------------------------------
# Manage files
# ------------------------------------------------------

def load_json_from_file(filename):
    """
    Loads the content of a JSON file

    :param filename: name of the file (string)
    :return: JSON object
    """
    InputValidation.validate_string(filename)
    InputValidation.validate_file_exist(filename, 'File ' + filename + ' does not exist')
    if '.json' not in filename:
        raise Exception("The specified file has not a JSON format")
    with open(filename) as json_file:
        retval = json.load(json_file)
    return retval


def get_heat_template_params():
    """
    Returns the list of deployment parameters from the configuration file for the heat template

    :return: dict
    """
    heat_parameters_list = CONF_FILE.get_variable_list(cf.CFS_DEPLOYMENT_PARAMETERS)
    testcase_parameters = dict()
    for param in heat_parameters_list:
        testcase_parameters[param] = CONF_FILE.get_variable(cf.CFS_DEPLOYMENT_PARAMETERS, param)
    return testcase_parameters


def get_testcase_params():
    """
    Returns the list of testcase parameters from the configuration file

    :return: dict
    """
    testcase_parameters = dict()
    parameters = CONF_FILE.get_variable_list(cf.CFS_TESTCASE_PARAMETERS)
    for param in parameters:
        testcase_parameters[param] = CONF_FILE.get_variable(cf.CFS_TESTCASE_PARAMETERS, param)
    return testcase_parameters


def get_file_first_line(file_name):
    """
    Returns the first line of a file

    :param file_name: name of the file to be read (str)
    :return: str
    """
    InputValidation.validate_string(file_name, "The name of the file must be a string")
    InputValidation.validate_file_exist(file_name, 'The file ' + file_name + ' does not exist')
    res = open(file_name, 'r')
    return res.readline()


def replace_in_file(file, text_to_search, text_to_replace):
    """
    Replaces a string within a file

    :param file: name of the file (str)
    :param text_to_search: text to be replaced
    :param text_to_replace: new text that will replace the previous
    :return: None
    """
    InputValidation.validate_string(text_to_search, 'The text to be replaced in the file must be a string')
    InputValidation.validate_string(text_to_replace, 'The text to replace in the file must be a string')
    InputValidation.validate_string(file, "The name of the file must be a string")
    InputValidation.validate_file_exist(file, "The file does not exist")
    for line in fileinput.input(file, inplace=True):
        print(line.replace(text_to_search, text_to_replace).rstrip())


# ------------------------------------------------------
# Shell interaction
# ------------------------------------------------------

def run_command(command):
    LOG.info("Running command: " + command)
    return os.system(command)


def get_interface_name_by_bus_address(bus_address):
    # TODO: Call the DPDK tool to ge the address
    if bus_address == '01:00.0':
        return 'enp1s0f0'
    if bus_address == '01:00.1':
        return 'enp1s0f1'
    return None


# ------------------------------------------------------
# Expose variables to other modules
# ------------------------------------------------------

def get_base_dir():
    return BASE_DIR


def get_template_dir():
    return TEMPLATE_DIR


def get_dpdk_pktgen_vars():
    if not (PKTGEN == 'dpdk_pktgen'):
        return dict()
    ret_val = dict()
    ret_val[cf.CFSP_DPDK_PKTGEN_DIRECTORY] = PKTGEN_DIR
    ret_val[cf.CFSP_DPDK_PROGRAM_NAME] = PKTGEN_PROGRAM
    ret_val[cf.CFSP_DPDK_COREMASK] = PKTGEN_COREMASK
    ret_val[cf.CFSP_DPDK_MEMORY_CHANNEL] = PKTGEN_MEMCHANNEL
    ret_val[cf.CFSP_DPDK_BUS_SLOT_NIC_1] = PKTGEN_BUS_SLOT_NIC_1
    ret_val[cf.CFSP_DPDK_BUS_SLOT_NIC_2] = PKTGEN_BUS_SLOT_NIC_2
    ret_val[cf.CFSP_DPDK_DPDK_DIRECTORY] = PKTGEN_DPDK_DIRECTORY
    return ret_val


# ------------------------------------------------------
# Configuration Variables from Config File
# ------------------------------------------------------
def get_deployment_configuration_variables_from_conf_file():
    variables = dict()
    types = dict()
    all_variables = CONF_FILE.get_variable_list(cf.CFS_EXPERIMENT_VNF)
    for var in all_variables:
        v = CONF_FILE.get_variable(cf.CFS_EXPERIMENT_VNF, var)
        type = re.findall(r'@\w*', v)
        values = re.findall(r'\"(.+?)\"', v)
        variables[var] = values
        try:
            types[var] = type[0][1:]
        except IndexError:
            LOG.debug("No type has been specified for variable " + var)
    return variables


# ------------------------------------------------------
# benchmarks from Config File
# ------------------------------------------------------
def get_benchmarks_from_conf_file():
    requested_benchmarks = list()
    benchmarks = CONF_FILE.get_variable(cf.CFS_GENERAL, cf.CFSG_BENCHMARKS).split(', ')
    for benchmark in benchmarks:
        requested_benchmarks.append(benchmark)
    return requested_benchmarks


# ------------------------------------------------------
# Extraction of the VLAN ID of a Network
# ------------------------------------------------------
# TODO: to be completed
# from neutronclient.neutron import client as neutron
# from keystoneclient.v2_0 import client as keystoneClient
# vlan_id = 0
# credentials = get_credentials()
# neutron = neutron.Client("2.0", username=credentials['user'], password=credentials['password'], tenant_name=credentials['project'], auth_url=credentials['auth_uri'])
# networks = neutron.list_networks(name='inbound_traffic_network')
# if networks['networks'][0]['provider:network_type'] == 'vlan':
#     vlan_id = networks['networks'][0]['provider:segmentation_id']
# print vlan_id


class InputValidation(object):

    @staticmethod
    def validate_string(param, message):
        if not isinstance(param, str):
            raise ValueError(message)
        return True

    @staticmethod
    def validate_file_exist(file_name, message):
        if not os.path.isfile(file_name):
            raise ValueError(message + ' ' + file_name)

    @staticmethod
    def validate_directory_exist_and_format(directory, message):
        if not os.path.isdir(directory):
            raise ValueError(message)
        if not directory.endswith('/'):
            return directory + '/'
        return directory

    @staticmethod
    def validate_configuration_file_parameter(section, parameter, message):
        params = CONF_FILE.get_variable_list(section)
        if parameter not in params:
            raise ValueError(message)

    @staticmethod
    def validate_configuration_file_section(section, message):
        if section not in cf.get_sections():
            raise ValueError(message)

    @staticmethod
    def validate_boolean(boolean, message):
        if isinstance(boolean, bool):
            return boolean
        if isinstance(boolean, str):
            if boolean == 'True':
                return True
            if boolean == 'False':
                return False
        raise ValueError(message)

    @staticmethod
    def validate_openstack_credentials(credentials):
        pass
        # if not isinstance(credentials, dict):
        #     raise ValueError('The provided openstack_credentials variable must be a dictionary')
        # credential_keys = ['', '']
        # missing = [credential_key for credential_key in credential_keys if credential_key not in credentials.keys()]
        # # TODO: to be finished