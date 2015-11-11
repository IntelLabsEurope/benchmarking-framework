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


import experimental_framework.benchmarking_unit as bench
from experimental_framework import heat_template_generation, common


class FrameworkApi(object):

    @staticmethod
    def init():
        common.init(api=True)

    @staticmethod
    def get_available_test_cases():
        """
        Returns the available test cases
        This list include user developed modules
        :return: list of strings
        """
        return bench.BenchmarkingUnit.get_available_test_cases()

    @staticmethod
    def get_test_case_features(test_case):
        """
        Return a list of the features (description, parameters, allowed values) for a test case
        :param test_case: Test case to be explored (string)
                            The string represents a test case and it is one of the strings provided by the
                            "get_available_test_cases()" function output.
        :return:
        """
        if not isinstance(test_case, str):
            raise ValueError('The provided test_case parameter has to be a string')
        benchmark = bench.BenchmarkingUnit.get_required_benchmarks([test_case])[0]
        return benchmark.get_features()

    @staticmethod
    def execute_framework(test_cases, iterations, base_heat_template, heat_template_parameters,
                          deployment_configuration, openstack_credentials):
        """
        Runs the framework
        :param test_cases: Test cases to be ran on the workload (dict() of dict())
                            Each string represents a test case and it is one of the strings provided by the
                            "get_available_test_cases()" function output.
        :param iterations: Number of iterations to be executed (int)
        :param base_heat_template: File name of the base heat template of the workload to be deployed (string)
        :param heat_template_parameters: Dictionary of parameters to be given as input to the heat template ( dict() )
                            See http://docs.openstack.org/developer/heat/template_guide/hot_guide.html
                            Section "Template input parameters"
        :param deployment_configuration: Dictionary of parameters representing the deployment configuration of the workload
                            The key is a string representing the name of the parameter,
                            the value is a list of strings representing the value to be assumed by a specific param.
                            The format is: ( dict[string] = list(strings) ) )
                            The parameters are user defined: they have to correspond to the place holders provided in
                            the heat template. (Use "#" in the syntax,
                            es. - heat template "#param", - config_var "param")
        :return: the name of the csv file where the results have been stored
        """

        # TODO: replace with user credentials
        credentials = common.get_credentials()

        # TODO: improve Input validation
        if not isinstance(base_heat_template, str):
            raise ValueError('The provided base_heat_template variable must be a string')
        if not isinstance(iterations, int):
            raise ValueError('The provided iterations variable must be an integer value')

        if not isinstance(credentials, dict):
            raise ValueError('The provided openstack_credentials variable must be a dictionary')
        credential_keys = ['', '']
        missing = [credential_key for credential_key in credential_keys if credential_key not in credentials.keys()]

        if not isinstance(heat_template_parameters, dict):
            raise ValueError('The provided heat_template_parameters variable must be a dictionary')

        if not isinstance(test_cases, list):
            raise ValueError('The provided test_cases variable must be a dictionary')

        # Heat template generation (base_heat_template, deployment_configuration)
        common.LOG.info("Generation of all the heat templates required by the experiment")
        heat_template_generation.generates_templates(base_heat_template, deployment_configuration)


        # Benchmarking Unit (test_cases, iterations, heat_template_parameters)\
        benchmarking_unit = bench.BenchmarkingUnit(base_heat_template, common.get_credentials(),
                                                   heat_template_parameters, iterations, test_cases)
        try:
            common.LOG.info("Benchmarking Unit initialization")
            benchmarking_unit.initialize()
            common.LOG.info("Becnhmarking Unit Running")
            benchmarking_unit.run_benchmarks()
        finally:
            common.LOG.info("Benchmarking Unit Finalization")
            benchmarking_unit.finalize()
