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

    def on_model(self, m, output, hashes):
        symbols = m.symbols(shown=True)
        output.append([])
        cur_pos = len(output) - 1
        for symbol in symbols:
            output[cur_pos].append(str(symbol))

        output[cur_pos].sort()

        hashes[(hash(tuple(output[cur_pos])))] = cur_pos

    def parse(self, config, timeout = 1800, clingo_mockup = False, idlv_mockup = False, hybrid_grounding_idlv_mockup = False, hybrid_grounding_gringo_mockup = False, ground_and_solve = True, run_all_examples = False, optimization_benchmarks = False):
        parser = argparse.ArgumentParser(prog='Primitive Benchmark', description='Benchmarks hybrid_grounding vs. Clingo (total grounding + solving time).')

        parser.add_argument('input_folder')
        parser.add_argument('output_file')
        args = parser.parse_args()

        input_path = args.input_folder
        output_filename = args.output_file

        instance_files = []

        for f in os.scandir(input_path):
            if f.is_file():
                if not "encoding" in str(f.name) and not "additional_instance" in str(f.name):
                    instance_files.append(str(f.name))

        instance_files.sort()


        encoding_path = os.path.join(input_path, "encoding.lp")
        encoding_file_contents = open(encoding_path, 'r').read()

        additional_instance_path = os.path.join(input_path, "additional_instance.lp")
        additional_instance_file_contents = open(additional_instance_path, 'r').read()

        total_time_output_filename = f"{output_filename}_total_time.csv"
        grounding_time_output_filename = f"{output_filename}_grounding_time.csv"
        grounding_size_output_filename = f"{output_filename}_grounding_size.csv"

        with open(total_time_output_filename, "w") as output_file:
            write_string = "instance,gringo-duration,gringo-timeout-occurred,idlv-duration,idlv-timeout-occured,hybrid_grounding-idlv-duration,hybrid_grounding-idlv-timeout-occured,hybrid_grounding-gringo-duration,hybrid_grounding-gringo-timeout-occured"
            output_file.write(write_string)

        with open(grounding_time_output_filename, "w") as output_file:
            write_string = "instance,gringo-duration,gringo-timeout-occurred,idlv-duration,idlv-timeout-occured,hybrid_grounding-idlv-duration,hybrid_grounding-idlv-timeout-occured,hybrid_grounding-gringo-duration,hybrid_grounding-gringo-timeout-occured"
            output_file.write(write_string)

        with open(grounding_size_output_filename, "w") as output_file:
            write_string = "instance,gringo-size,gringo-timeout-occurred,idlv-size,idlv-timeout-occured,hybrid_grounding-idlv-size,hybrid_grounding-idlv-timeout-occured,hybrid_grounding-gringo-size,hybrid_grounding-gringo-timeout-occured"
            output_file.write(write_string)

        # ------------------------ START BENCHMARK HERE -------------------------

        for instance_file in instance_files:
            print("")
            print(f">>>> Now solving: {instance_file}")
            print("")
            instance_path = os.path.join(input_path, instance_file)
            instance_file_contents = open(instance_path, 'r').read()

            instance_file_contents += additional_instance_file_contents

            benchmarks = {}
            benchmarks["GRINGO"] = {"mockup":clingo_mockup,
                    "helper":"start_benchmark_gringo_helper.py",
                    "program_input": (instance_file_contents + encoding_file_contents).encode()} 
            benchmarks["IDLV"] = {"mockup":idlv_mockup,
                    "helper":"start_benchmark_idlv_helper.py",
                    "program_input": (instance_file_contents + encoding_file_contents).encode()}
            benchmarks["hybrid_grounding-IDLV"] = {"mockup":hybrid_grounding_idlv_mockup,
                    "helper":"start_benchmark_hybrid_grounding_helper.py",
                    "program_input": (instance_file_contents + "\n#program rules.\n" + encoding_file_contents).encode()}
            benchmarks["hybrid_grounding-GRINGO"] = {"mockup":hybrid_grounding_gringo_mockup,
                    "helper":"start_benchmark_hybrid_grounding_helper.py",
                    "program_input": (instance_file_contents + "\n#program rules.\n" + encoding_file_contents).encode()}

            total_time_string = f"\n{instance_file},"
            grounding_time_string = f"\n{instance_file},"
            grounding_size_string = f"\n{instance_file},"


            counter = 0
            for strategy in benchmarks.keys():

                strategy_dict = benchmarks[strategy]

                if not strategy_dict["mockup"]:
                    timeout_occurred, total_duration, grounding_duration, grounding_file_size  = Benchmark.benchmark_caller(strategy_dict["program_input"], config, strategy_dict["helper"], strategy, timeout = timeout, ground_and_solve = ground_and_solve, optimization_benchmarks = optimization_benchmarks)
                else:
                    timeout_occurred = True
                    total_duration = timeout
                    grounding_duration = timeout
                    grounding_file_size = 0

                # Print current console info:
                if timeout_occurred:
                    print(f"[INFO] - {strategy} timed out ({total_duration})!")
                    
                    if not run_all_examples:
                        strategy_dict["mockup"] = True
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
    #config["rewriting_strategy"] = "--aggregate-strategy=rewrite-no-body"
    #config["rewriting_strategy"] = "--aggregate-strategy=rewrite"
    config["rewriting_strategy"] = "--aggregate-strategy=replace"

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





