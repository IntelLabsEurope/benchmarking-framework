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

'''
The Benchmarking Unit manages the Benchmarking of VNFs orchestrating the
initialization, execution and finalization
'''

__author__ = "vmriccox"


import os
import json
import time
import inspect

from experimental_framework.benchmarks import benchmark_base_class as base
from experimental_framework import common
from experimental_framework import data_manager as data
from experimental_framework import heat_template_generation as heat
from experimental_framework import deployment_unit as deploy

# TODO: TO be removed for Yardstick
if common.FINGERPRINT:
    from experimental_framework.libraries import apexlake_analytics as al


class BenchmarkingUnit:
    """
    Management of the overall Benchmarking process
    """

    def __init__(self, heat_template_name, openstack_credentials, heat_template_parameters, iterations, benchmarks):
        # Loads vars from configuration file
        self.template_file_extension = common.TEMPLATE_FILE_EXTENSION
        self.template_dir = common.get_template_dir()
        self.results_directory = common.RESULT_DIR + str(time.time())
        self.fingerprint = common.FINGERPRINT

        # Initializes other internal variable from parameters
        self.template_name = heat_template_name
        self.iterations = iterations
        self.required_benchmarks = benchmarks
        self.template_files = []
        self.benchmarks = list()
        self.benchmark_names = list()
        self.data_manager = data.DataManager(self.results_directory)
        self.heat_template_parameters = heat_template_parameters
        self.template_files = heat.get_all_heat_templates(self.template_dir, self.template_file_extension)
        common.DEPLOYMENT_UNIT = deploy.DeploymentUnit(openstack_credentials)

    def initialize(self):
        """
        Initialize the environment in order to run the benchmarking
        :return: None
        """
        common.LOG.info('Initialization of benchmarks')
        for benchmark in self.required_benchmarks:
            # benchmark_class = ''
            # try:
            #     benchmark_class = BenchmarkingUnit.get_benchmark_class(benchmark['name'])
            # except Exception as e:
            #     pass
            benchmark_class = BenchmarkingUnit.get_benchmark_class(benchmark['name'])
            # Need to generate a unique name for the benchmark
            # (since there is the possibility to have different instances of the same benchmark)
            self.benchmarks.append(benchmark_class(self.get_benchmark_name(benchmark['name']), benchmark['params']))
        common.LOG.info('Data Manager initialization')
        for template_file_name in self.template_files:
            experiment_name = BenchmarkingUnit.extract_experiment_name(template_file_name)
            self.data_manager.create_new_experiment(experiment_name)
            for benchmark in self.benchmarks:
                self.data_manager.add_benchmark(experiment_name, benchmark.get_name())

            # TODO: YARDSTICK - Remove these instructions
            # TODO: move fingerprint literal into constant file
            if common.FINGERPRINT:
                self.data_manager.add_benchmark(experiment_name, 'fingerprint')
                self.data_manager.add_benchmark(experiment_name, 'bound')

    def finalize(self):
        """
        Finalizes the Benchmarking Unit
        :return:
        """
        for template_file_name in self.template_files:
            experiment_name = BenchmarkingUnit.extract_experiment_name(template_file_name)
            self.data_manager.close_experiment(experiment_name)
        self.data_manager.generate_result_csv_file()
        # Destroy all deployed VMs
        common.DEPLOYMENT_UNIT.destroy_all_deployed_stacks()

    def run_benchmarks(self):
        """
        :return:
        """
        common.LOG.info('Run Benchmarking Unit')
        for iteration in range(0, self.iterations):
            common.LOG.info('Iteration ' + str(iteration))
            for template_file_name in self.template_files:
                experiment_name = BenchmarkingUnit.extract_experiment_name(template_file_name)
                configuration = self.get_experiment_configuration(template_file_name)
                metadata = dict()
                metadata['experiment_name'] = experiment_name
                self.data_manager.add_metadata(experiment_name, metadata)
                for benchmark in self.benchmarks:
                    common.LOG.info('Benchmark ' + benchmark.get_name() + ' started on ' + template_file_name)
                    benchmark.init()
                    common.LOG.info('Template ' + experiment_name + ' deployment START')
                    if common.DEPLOYMENT_UNIT.deploy_heat_template(self.template_dir + template_file_name, experiment_name, self.heat_template_parameters):
                            common.LOG.info('Template ' + experiment_name + ' deployment COMPLETED')
                    else:
                        common.LOG.info('Template ' + experiment_name + ' deployment FAILED')
                        continue
                    result = benchmark.run()
                    self.data_manager.add_data_points(experiment_name, benchmark.get_name(), result)

                    # TODO: YARDSTICK - Remove Fingerprints from release version
                    if common.FINGERPRINT:
                        common.LOG.info('Calculating Fingerprints')
                        fingerprint = al.ApexlakeAnalytics.get_fingerprint(experiment_name)
                        # TODO: move fingerprint literal into constant file
                        self.data_manager.add_data_points(experiment_name, 'fingerprint', fingerprint)
                        bound = al.ApexlakeAnalytics.format_fingerprint(fingerprint)
                        self.data_manager.add_data_points(experiment_name, 'bound', bound)

                    common.LOG.info('Destroying deployment for experiment ' + experiment_name)
                    common.DEPLOYMENT_UNIT.destroy_heat_template(experiment_name)
                    benchmark.finalize()
                    common.LOG.info('Benchmark ' + benchmark.__class__.__name__ + ' terminated')
                    self.data_manager.generate_result_csv_file()
                common.LOG.info('Benchmark Finished')
                # self.data_manager.add_metadata(experiment_name, metadata)
                self.data_manager.add_configuration(experiment_name, configuration)
        common.LOG.info('Benchmarking Unit: Experiments completed!')

    def get_experiment_configuration(self, template_file_name):
        """
        Load and return the configuration for the specific experiment (template)
        :param template_file_name:
        :return: dict()
        """
        with open(self.template_dir + template_file_name + ".json") as json_file:
            configuration = json.load(json_file)
        return configuration

    def get_benchmark_name(self, name, instance=0):
        if name + "_" + str(instance) in self.benchmark_names:
            instance += 1
            return self.get_benchmark_name(name, instance)
        self.benchmark_names.append(name + "_" + str(instance))
        return name + "_" + str(instance)

    @staticmethod
    def extract_experiment_name(template_file_name):
        """
        Algorithm to generate a unique experiment name for a given template ;)
        :param template_file_name: File name of the template used during the experiment string
        :return: Experiment Name (string)
        """
        strings = template_file_name.split('.')
        return ".".join(strings[:(len(strings)-1)])

    @staticmethod
    def get_benchmark_class(complete_module_name):
        """
        Returns the class for a given module
        :param complete_module_name: Complete name of the module as returned by get_available_test_cases (string)
        :return: Class correspondent to the indicated module
        """
        # current = None
        # [pkg_name, class_name] = complete_module_name.rsplit('.', 1)
        strings = complete_module_name.split('.')
        pkg = __import__('experimental_framework.benchmarks.' + strings[0], globals(), locals(), [], -1)
        module = getattr(getattr(pkg, 'benchmarks'), strings[0])
        members = inspect.getmembers(module)
        for m in members:
            if inspect.isclass(m[1]):
                class_name = m[1]("", dict()).__class__.__name__
                if isinstance(m[1]("", dict()), base.BenchmarkBaseClass) and \
                        not class_name == 'BenchmarkBaseClass':
                    return m[1]

    @staticmethod
    def get_required_benchmarks(required_benchmarks):
        """
        Returns instances of required test cases
        :param required_benchmarks: list() of strings
        :return: list() of BenchmarkBaseClass
        """
        benchmarks = list()
        for b in required_benchmarks:
            class_ = BenchmarkingUnit.get_benchmark_class(b)
            instance = class_("", dict())
            benchmarks.append(instance)
        return benchmarks

    @staticmethod
    def get_available_test_cases():
        """
        Returns a list of available test cases from the file system
        :return:
        """
        modules = list()
        ret_val = list()

        # bench.BenchmarkingUnit.get_benchmark_class('rfc2544_throughput_benchmark.RFC2544ThroughputBenchmark')
        for dirname, dirnames, filenames in os.walk('./benchmarks'):
            for file in filenames:
                if file.endswith('py'):
                    modules.append(file.replace(".py", ""))
                    classes = __import__("benchmarks." + file.replace(".py", ""))
        cls = list()
        for mod in modules:
            members = inspect.getmembers(getattr(classes, mod))
            for m in members:
                if inspect.isclass(m[1]):
                    class_name = m[1]("", dict()).__class__.__name__
                    if isinstance(m[1]("", dict()), base.BenchmarkBaseClass) and \
                            not class_name == 'BenchmarkBaseClass':
                        ret_val.append(mod + "." + class_name)
        return ret_val