# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:12:49 2025

@author: d.sysoev
"""

import toml
def filter_beltpack_log(log_file_name_path: str, out_file_name: str) -> None:

    with open(log_file_name_path) as inp_file:
        beltpack_log = inp_file.readlines()

    with open(out_file_name, "w") as out_file:
        num_line = 1
        for entry in beltpack_log:
            filter = [entry.rfind("tm:") != -1]
            filter.append(entry.rfind("tm=") != -1)
            filter.append(entry.find("~~~~~~~~~~~~~   CONNECTION LOST") != -1)
            filter.append(entry.find("~~~~~~~~~~ SOUND CONNECT") != -1)
            filter.append(entry.find("~~~~~~~~~~~~~   CONNECTION ESTABLISHED") != -1)
            filter.append(entry.find("~~~~~~~~~~~ Output every 5 sec") != -1)
            filter.append(entry.find("Option ") != -1)

            if any(filter): # tm: - timelabels, tm= - strings when try to find BS
                if len(entry) > 100:
                    print(f"Long line in output file, check string number {num_line}")
                out_file.write(entry)
                num_line += 1

if __name__ == "__main__":
    config = toml.load(r"config.toml")
    input_file = config['files']['input_file']
    output_file = config['files']['output_file']
    filter_beltpack_log(input_file, output_file)