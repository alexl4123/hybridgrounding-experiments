#!/home/thinklex/programs/python3.11.3/bin/python3
import os
import sys
import io

import time

import subprocess

import tempfile
import argparse

import resource

import json
import base64
import pickle

from start_benchmark_utils import StartBenchmarkUtils

def limit_virtual_memory():
    max_virtual_memory = 1024 * 1024 * 1024 * 64 # 64GB

    # TUPLE -> (soft limit, hard limit)
    resource.setrlimit(resource.RLIMIT_AS, (max_virtual_memory, max_virtual_memory))

class Benchmark:

    def __init__(self):
        self.clingo_output = []
        self.hybrid_grounding_output = []

        self.clingo_hashes = {}
        self.hybrid_grounding_hashes = {} 

    def parse(self, config, timeout = 1800, clingo_mockup = False, idlv_mockup = False, hybrid_grounding_idlv_mockup = False, hybrid_grounding_gringo_mockup = False, ground_and_solve = True, run_all_examples = False, optimization_benchmarks = False):
        parser = argparse.ArgumentParser(prog='Primitive Benchmark', description='Benchmarks hybrid_grounding vs. Clingo (total grounding + solving time).')

        parser.add_argument('input_folder')
        parser.add_argument('output_file')

        args = parser.parse_args()

        input_path = args.input_folder
        output_filename = args.output_file

        instance_files = []
        hg_encoding_file = None
        traditional_encoding_file = None

        instance_files_dir = {}

        for f in os.scandir(input_path):
            if f.is_file():
                if "hg" in f.name:
                    hg_encoding_file = f
                elif "traditional" in f.name:
                    traditional_encoding_file = f
            elif f.is_dir():

                if f.name not in instance_files_dir:
                    instance_files_dir[f.name] = {}

                edge_probability = f.name

                for instance_size_folders in os.scandir(f):
                    instance_size = instance_size_folders.name

                    if instance_size_folders.name not in instance_files_dir[f.name]:
                        instance_files_dir[f.name][instance_size_folders.name] = []

                    for repetition_file in os.scandir(instance_size_folders):
                        instance_files_dir[f.name][instance_size_folders.name].append(repetition_file.name)
                        instance_files.append((edge_probability,instance_size,repetition_file.name))

        

        if None in [hg_encoding_file, traditional_encoding_file]:
            if hg_encoding_file is None:
                print(f"Could not find ''hg'' encoding file in specified input path {input_path}.")

            if traditional_encoding_file is None:
                print(f"Could not find ''traditional'' encoding file in specified input path {input_path}.")

            print("Exiting due to missing required files!")
            return 
        
        instance_files.sort()

        repetition_file_length = -1
        for prob_key in instance_files_dir.keys():
            for size_key in instance_files_dir[prob_key].keys():
                if repetition_file_length == -1:
                    repetition_file_length = len(instance_files_dir[prob_key][size_key])
                elif repetition_file_length != len(instance_files_dir[prob_key][size_key]):
                    print(f"Found instance where number of repetition files diverges from the others {prob_key},{size_key}")
                    quit()

        hg_encoding_file_path = os.path.join(input_path, hg_encoding_file.name)
        hg_encoding_file_contents = open(hg_encoding_file_path, "r").read()

        traditional_encoding_file_path = os.path.join(input_path, traditional_encoding_file.name)
        traditional_encoding_file_contents = open(traditional_encoding_file_path, "r").read()

        total_time_output_filename = f"{output_filename}_total_time.csv"
        grounding_time_output_filename = f"{output_filename}_grounding_time.csv"
        grounding_size_output_filename = f"{output_filename}_grounding_size.csv"

        standard_csv_header = [
            "edge-probability",
            "number-of-vertices",
            "repetition-number",
            "seed"
        ]

        with open(total_time_output_filename, "w") as output_file:
            write_string = f"{','.join(standard_csv_header)},gringo-duration,gringo-timeout-occurred,idlv-duration,idlv-timeout-occured,hybrid_grounding-idlv-duration,hybrid_grounding-idlv-timeout-occured,hybrid_grounding-gringo-duration,hybrid_grounding-gringo-timeout-occured"
            output_file.write(write_string)

        with open(grounding_time_output_filename, "w") as output_file:
            write_string = f"{','.join(standard_csv_header)},gringo-duration,gringo-timeout-occurred,idlv-duration,idlv-timeout-occured,hybrid_grounding-idlv-duration,hybrid_grounding-idlv-timeout-occured,hybrid_grounding-gringo-duration,hybrid_grounding-gringo-timeout-occured"
            output_file.write(write_string)

        with open(grounding_size_output_filename, "w") as output_file:
            write_string = f"{','.join(standard_csv_header)},gringo-size,gringo-timeout-occurred,idlv-size,idlv-timeout-occured,hybrid_grounding-idlv-size,hybrid_grounding-idlv-timeout-occured,hybrid_grounding-gringo-size,hybrid_grounding-gringo-timeout-occured"
            output_file.write(write_string)

        # ------------------------ START BENCHMARK HERE -------------------------

        failed_instances_dict = {}

        for instance_file in instance_files:

            self.benchmark_instance(config, timeout, clingo_mockup, idlv_mockup, hybrid_grounding_idlv_mockup, hybrid_grounding_gringo_mockup, ground_and_solve, run_all_examples, optimization_benchmarks, input_path, hg_encoding_file_contents, traditional_encoding_file_contents, total_time_output_filename, grounding_time_output_filename, grounding_size_output_filename, instance_file, failed_instances_dict, repetition_file_length)

    def benchmark_instance(self, config, timeout, clingo_mockup, idlv_mockup, hybrid_grounding_idlv_mockup, hybrid_grounding_gringo_mockup, ground_and_solve, run_all_examples, optimization_benchmarks, input_path, hg_encoding_file_contents, traditional_encoding_file_contents, total_time_output_filename, grounding_time_output_filename, grounding_size_output_filename, instance_file, failed_instances_dict, repetition_file_length):
        print("")
        print(f">>>> Now solving: {instance_file}")
        print("")
        instance_path = os.path.join(input_path, instance_file[0], instance_file[1], instance_file[2])
        instance_file_contents = open(instance_path, 'r').read()

        if "seed(" in instance_file_contents:
            seed_content = instance_file_contents.split("seed(")[1]

            seed = ""
            for char in seed_content:
                if char is not ")":
                    seed = seed + char
                else:
                    break

        else:
            print(f"Seed not found in file {instance_file}")
            print("EXITING due to necessary condition not fulfilled.")
            quit()


        instance_file_contents += traditional_encoding_file_contents

        benchmarks = {}
        benchmarks["GRINGO"] = {"mockup":clingo_mockup,
                    "mockup_probability":{},
                    "helper":"start_benchmark_gringo_helper.py",
                    "program_input": (instance_file_contents + hg_encoding_file_contents).encode()} 
        benchmarks["IDLV"] = {"mockup":idlv_mockup,
                    "mockup_probability":{},
                    "helper":"start_benchmark_idlv_helper.py",
                    "program_input": (instance_file_contents + hg_encoding_file_contents).encode()}
        benchmarks["hybrid_grounding-IDLV"] = {"mockup":hybrid_grounding_idlv_mockup,
                    "mockup_probability":{},
                    "helper":"start_benchmark_hybrid_grounding_helper.py",
                    "program_input": (instance_file_contents + "\n#program rules.\n" + hg_encoding_file_contents).encode()}
        benchmarks["hybrid_grounding-GRINGO"] = {"mockup":hybrid_grounding_gringo_mockup,
                    "mockup_probability":{},
                    "helper":"start_benchmark_hybrid_grounding_helper.py",
                    "program_input": (instance_file_contents + "\n#program rules.\n" + hg_encoding_file_contents).encode()}

        print(instance_file[2])
        total_time_string = f"\n{instance_file[0]},{instance_file[1]},{instance_file[2].split('.')[0]},{seed},"
        grounding_time_string = total_time_string
        grounding_size_string = total_time_string


        counter = 0
        for strategy in benchmarks.keys():
            strategy_dict = benchmarks[strategy]

            if not strategy_dict["mockup"] and instance_file[0] not in strategy_dict["mockup_probability"]:
                timeout_occurred, total_duration, grounding_duration, grounding_file_size  = Benchmark.benchmark_caller(strategy_dict["program_input"], config, strategy_dict["helper"], strategy, timeout = timeout, ground_and_solve = ground_and_solve, optimization_benchmarks = optimization_benchmarks)
            else:
                timeout_occurred = True
                total_duration = timeout
                grounding_duration = timeout
                grounding_file_size = 0

                # Print current console info:
            if timeout_occurred:
                print(f"[INFO] - {strategy} timed out ({total_duration})!")

                if strategy not in failed_instances_dict:
                    failed_instances_dict[strategy] = {}

                if instance_file[0] not in failed_instances_dict[strategy]:
                    failed_instances_dict[strategy][instance_file[0]] = {}

                if instance_file[1] not in failed_instances_dict[strategy][instance_file[0]]:
                    failed_instances_dict[strategy][instance_file[0]][instance_file[1]] = []

                failed_instances_dict[strategy][instance_file[0]][instance_file[1]].append(instance_file)

                if len(failed_instances_dict[strategy][instance_file[0]][instance_file[1]]) == repetition_file_length:
                    if not run_all_examples:
                        strategy_dict["mockup_probability"] = instance_file[0]

            else:
                print(f"[INFO] - {strategy} needed {total_duration} seconds!")

            total_time_string += f"{total_duration},{timeout_occurred}"
            grounding_time_string += f"{grounding_duration},{timeout_occurred}"
            grounding_size_string += f"{grounding_file_size},{timeout_occurred}"

            if counter < 3:
                total_time_string += ","
                grounding_time_string += ","
                grounding_size_string += ","

            counter += 1

            # Add info to .csv files
        with open(total_time_output_filename, "a") as output_file:
            output_file.write(total_time_string)

        with open(grounding_time_output_filename, "a") as output_file:
            output_file.write(grounding_time_string)

        with open(grounding_size_output_filename, "a") as output_file:
            output_file.write(grounding_size_string)


    @classmethod
    def benchmark_caller(cls, program_input, config, helper_script, strategy, timeout = 1800, ground_and_solve = True, optimization_benchmarks = False):

        to_encode_list = [config, timeout, ground_and_solve, strategy, optimization_benchmarks]

        encoded_list = [f"{StartBenchmarkUtils.encode_argument(argument)}" for argument in to_encode_list]

        arguments = [config["python_command"], helper_script] + encoded_list

        ret_vals = None 

        try:
            p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=limit_virtual_memory)       
            (ret_vals_encoded, error_vals_encoded) = p.communicate(input = program_input, timeout = int(timeout*1.1))
            ret_vals = StartBenchmarkUtils.decode_argument(ret_vals_encoded.decode())

            if p.returncode != 0:
                print(f">>>>> Other return code than 0 in helper: {p.returncode}")

        except Exception as ex:
            try:
                p.kill()
            except Exception as e:
                pass

            print(ex)

        if ret_vals is None or not isinstance(ret_vals, tuple):
            ret_vals = (True, timeout, timeout, sys.maxsize)

        print(ret_vals)

        return ret_vals

        
if __name__ == "__main__":

    config = {}
    config["clingo_command"] = "./clingo"
    config["gringo_command"] = "./gringo"
    config["idlv_command"] = "./idlv.bin"
    config["python_command"] = "./python3"

    # Strategies ->  {replace,rewrite,rewrite-no-body}
    config["rewriting_strategy"] = "--aggregate-strategy=RS"
    #config["rewriting_strategy"] = "--aggregate-strategy=RA"

    checker = Benchmark()

    timeout = 1800

    optimization_benchmarks = True

    gringo_mockup = False
    idlv_mockup = False
    hybrid_grounding_idlv_mockup = False
    hybrid_grounding_gringo_mockup = False

    ground_and_solve = True
    run_all_examples = True


    checker.parse(config, timeout = timeout, clingo_mockup = gringo_mockup, idlv_mockup = idlv_mockup, hybrid_grounding_idlv_mockup = hybrid_grounding_idlv_mockup, hybrid_grounding_gringo_mockup = hybrid_grounding_gringo_mockup, ground_and_solve = ground_and_solve, run_all_examples = run_all_examples, optimization_benchmarks = True)





