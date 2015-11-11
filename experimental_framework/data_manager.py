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


import csv
import json
import os


class Experiment:
    """
    This class represents the results of an Experiment
    """

    def __init__(self, name):
        self.name = name
        self._metadata = dict()
        self._configuration = dict()
        self._benchmarks = dict()
        # self._data_points = list()

    def add_experiment_metadata(self, metadata):
        """
        Add metadata to the experiment
        """
        if not isinstance(metadata, dict):
            raise ValueError
        for key in metadata.keys():
            self._metadata[key] = metadata[key]

    def add_experiment_configuration(self, configuration):
        """
        Add configuration parameters to the experiment
        """
        if not isinstance(configuration, dict):
            raise ValueError
        for key in configuration.keys():
            self._configuration[key] = configuration[key]

    def add_benchmark(self, benchmark):
        """
        Initializes a new benchmark as a list of dictionaries that will contain the data points for this benchmark
        """
        if not isinstance(benchmark, str):
            raise ValueError
        self._benchmarks[benchmark] = list()

    def add_data_point(self, benchmark, data_point):
        """
        Adds a data point to a benchmark
        :param benchmark:
        :param data_point: dictionary
        :return:
        """

        if not isinstance(data_point, dict):
            raise ValueError
        if benchmark not in self._benchmarks.keys():
            raise ValueError
        self._benchmarks[benchmark].append(data_point)

    def get_metadata(self):
        """
        Returns all the metadata for the experiment
        """
        return self._metadata

    def get_configuration(self):
        """
        Returns all the configuration for the experiment
        """
        return self._configuration

    def get_data_points(self, benchmark):
        """
        Returns all the data points for a benchmark (list of dict)
        :param benchmark: benchmark to be returned (string)
        """
        if benchmark in self._benchmarks.keys():
            return self._benchmarks[benchmark]
        return list()

    def get_benchmarks(self):
        """
        Returns all the benchmarks registered for an experiment
        """
        return self._benchmarks.keys()


class DataManager:
    """
    Manages data for the experiments and guarantee the persistency of data
    """

    def __init__(self, experiment_directory):
        self.experiment_directory = experiment_directory
        self.experiments = dict()
        os.system("mkdir -p " + self.experiment_directory)

    def create_new_experiment(self, experiment_name):
        """
        Adds a new experiment to the data
        :param experiment_name: name of the experiment (it will be used as key)
        :return:
        """
        if experiment_name not in self.experiments.keys():
            self.experiments[experiment_name] = Experiment(experiment_name)

    def add_metadata(self, experiment_name, metadata):
        """
        Add metadata to the experiment data.
        If some keys were already in the metadata they will not be included
        :param experiment_name: name of the experiment (it will be used as key)
        :param metadata: metadata to add to the experiment
        :return: Returns the keys that have not been included (if any)
        """
        if not self.is_experiment_present(experiment_name):
            raise ValueError("The provided experiment name has not been founded")
        self.experiments[experiment_name].add_experiment_metadata(metadata)

    def add_configuration(self, experiment_name, configuration):
        """
        Add configuration parameters to the experiment data.
        If some keys were already in the metadata they will not be included
        :param experiment_name: name of the experiment (it will be used as key)
        :param configuration: configuration to add to the experiment
        :return: Returns the keys that have not been included (if any)
        """
        if not self.is_experiment_present(experiment_name):
            raise ValueError("The provided experiment name has not been founded")
        self.experiments[experiment_name].add_experiment_configuration(configuration)

    def add_benchmark(self, experiment_name, benchmark_name):
        """
        Add a new benchmark to an experiment

        :param experiment_name:
        :param benchmark_name:
        :return: None
        """
        if experiment_name in self.experiments.keys():
            self.experiments[experiment_name].add_benchmark(benchmark_name)

    def add_data_points(self, experiment_name, benchmark, data_points):
        """
        Add one or more data points to an experiment

        :param experiment_name: name of experiment (string)
        :param data_points: dictionary or list of dictionaries
        :return: None
        """
        if not self.is_benchmark_present(experiment_name, benchmark):
            raise ValueError("Experiment or benchmark not previously declared")
        if isinstance(data_points, list):
            for data_point in data_points:
                if isinstance(data_point, dict):
                    self.experiments[experiment_name].add_data_point(benchmark, data_point)
        elif isinstance(data_points, dict):
            self.experiments[experiment_name].add_data_point(benchmark, data_points)

    def get_metadata(self, experiment_name):
        """
        Returns the metadata of an experiment

        :param experiment_name: name of the experiment to get data for
        :return: dict()
        """
        if not self.is_experiment_present(experiment_name):
            raise ValueError("The provided experiment name has not been founded")
        return self.experiments[experiment_name].get_metadata()

    def get_configuration(self, experiment_name):
        """
        Returns the configuration parameter values for an experiment

        :param experiment_name: name of the experiment to get data for
        :return: dict()
        """
        if not self.is_experiment_present(experiment_name):
            raise ValueError("The provided experiment name has not been found")
        return self.experiments[experiment_name].get_configuration()

    def get_list_experiment_names(self):
        """
        Returns the list of all the experiments recorded so far
        :return: list
        """
        return self.experiments.keys()

    def close_experiment(self, experiment_name):
        """
        Stores metadata on a file
        :param experiment_name: name of the experiment to be stored
        :param location: file system location where to store the file
        :return: None
        """
        if not self.is_experiment_present(experiment_name):
            raise ValueError("The experiment with name " + experiment_name +
                             " has not been found")

        directory = self.experiment_directory + "/" + experiment_name
        os.system("mkdir -p " + directory)

        json_file = self.experiment_directory + "/" + experiment_name + '/metadata.json'
        metadata = dict()
        metadata['location'] = json_file
        self.add_metadata(experiment_name, metadata)
        with open(json_file, 'a') as outfile:
            json.dump(self.experiments[experiment_name].get_metadata(), outfile)
        # Store also the data points for the experiment into a csv
        self.write_experiment_csv_file(experiment_name, None)

    def generate_result_csv_file(self):
        """
        Generates a CSV file with the results of all the experiments
        :param performance_indexes:
        :return: None
        """
        for benchmark in self.get_all_benchmarks():
            res_file = self.experiment_directory + '/results_' + benchmark + '.csv'
            with open(res_file, 'wb') as csvfile:
                metadata = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                titles = self._get_all_titles(benchmark)
                # Write titles on the first line of the file
                metadata.writerow(titles)
                # Write values for each experiment
                for experiment_name in self.experiments.keys():
                    for row in self._get_data_for_csv(self.experiments[experiment_name], benchmark, titles):
                        metadata.writerow(row)

    def get_all_benchmarks(self):
        benchmarks = set()
        for experiment in self.experiments.keys():
            for b in self.experiments[experiment].get_benchmarks():
                benchmarks.add(b)
        return benchmarks

    def write_experiment_csv_file(self, experiment_name, performance_indexes):
        """
        Generates a CSV file with the metadata of all the experiments and all the benchmarks
        :param experiment_name:
        :param benchmark:
        :param performance_indexes:
        :return:
        """
        for benchmark in self.experiments[experiment_name].get_benchmarks():
            res_file = self.experiment_directory + "/" + experiment_name + '/' + benchmark + '.csv'
            with open(res_file, 'wb') as csvfile:
                metadata = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                titles = self._get_all_titles(benchmark)
                # Write titles on the first line of the file
                metadata.writerow(titles)
                # Write values for each experiment
                for row in DataManager._get_data_for_csv(self.experiments[experiment_name], benchmark, titles):
                    metadata.writerow(row)

    def is_experiment_present(self, experiment_name):
        """
        Checks if a certain experiment name has been already registered in the data
        :param experiment_name:
        :return:
        """
        if experiment_name in self.experiments.keys():
            return True
        return False

    def is_benchmark_present(self, experiment_name, benchmark):
        """
        Checks if a certain experiment name has been already registered in the data
        :param experiment_name:
        :return:
        """
        if experiment_name in self.experiments.keys():
            if benchmark in self.experiments[experiment_name].get_benchmarks():
                return True
        return False

    # def _get_all_titles(self, benchmark, performance_index):
    def _get_all_titles(self, benchmark):
        """
        Returns all the titles form the experiments stored by the module so far
        :return: list of strings
        """
        titles = set()
        dp_titles = set()
        for experiment in self.experiments.keys():
            # Take the titles from the Data points
            if len(self.experiments[experiment].get_data_points(benchmark)) > 0:
                for key in self.experiments[experiment].get_data_points(benchmark)[0].keys():
                    dp_titles.add(key)

            # Take the titles from the experiment configuration
            for key in self.experiments[experiment].get_configuration().keys():
                if key not in dp_titles:
                    titles.add(key)

            # Take the titles from the experiment data points
            for dp in self.experiments[experiment].get_data_points(benchmark):
                for key in dp.keys():
                    if key not in dp_titles:
                        titles.add(key)

        # Add at the end the performance index
        title_list = list(titles)
        for key in dp_titles:
            title_list.append(key)
        return title_list

    @staticmethod
    def _get_data_for_csv(experiment, benchmark, titles):
        """
        Return rows to be written on the CSV file
        If the same key appear in both the experiment metadata and the data point or the configuration parameters,
        the priority is given to the data point, then to the configuration, and finally to the metadata.

        :param experiment: class Experiment
        :param titles: list(string)
        :return:
        """
        rows = list()
        for dp in experiment.get_data_points(benchmark):
            row = list()
            for title in titles:
                # First check in data point
                if title in dp.keys():
                    row.append(dp[title])
                elif title in experiment.get_configuration().keys():
                    row.append(experiment.get_configuration()[title])
                elif title in experiment.get_metadata().keys():
                    row.append(experiment.get_metadata()[title])
                else:
                    row.append('?')
            rows.append(row)
        return rows