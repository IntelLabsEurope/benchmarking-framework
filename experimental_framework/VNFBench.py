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

__author__ = "vmriccox"


from experimental_framework import heat_template_generation, common
from experimental_framework import benchmarking_unit as bench_unit


# Initialization of the utilities tools
common.init()

common.LOG.info("Generation of all the heat templates required by the experiment ...")
heat_template_generation.generates_templates(common.TEMPLATE_NAME,
                                             common.get_deployment_configuration_variables_from_conf_file())

common.LOG.info("Running Benchmarks ...")
required_benchmarks = common.get_benchmarks_from_conf_file()
test_case_params = common.get_testcase_params()
benchmarks = list()
for benchmark in required_benchmarks:
    bench = dict()
    bench['name'] = benchmark
    bench['params'] = dict()
    for param in test_case_params.keys():
        bench['params'][param] = test_case_params[param]
    benchmarks.append(bench)
b_unit = bench_unit.BenchmarkingUnit(common.TEMPLATE_NAME, common.get_credentials(), common.get_heat_template_params(),
                                     common.ITERATIONS, benchmarks)

try:
    common.LOG.info("Initialization of Benchmarking Unit")
    b_unit.initialize()

    common.LOG.info("Benchmarking Unit Running")
    b_unit.run_benchmarks()
finally:
    common.LOG.info("Benchmarking Unit Finalization")
#     b_unit.finalize()

# Deployment Engine
# deployment_engine = sd.SmartDeployment()
# deployment_engine.deploy_vtc()
