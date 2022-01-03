#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, argparse
from applaudgen.generators.python import PythonSDKGenerator

def main():
    cur_path = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(description='Generate Python SDK code for the App Store Connect API.')
    parser.add_argument('-s', '--spec', dest='spec_file',
                        default=f'{cur_path}/app_store_connect_api.json',
                        help='Path to the App Store Connect API specification file.')
    parser.add_argument('-o', '--output', dest='output_dir',
                        default=f'{cur_path}/PythonPackage/applaud/',
                        help='Path to the package output directory.')

    args = parser.parse_args()

    generator = PythonSDKGenerator(spec_file=args.spec_file, output_dir=args.output_dir)
    generator.generate()

if __name__ == "__main__":
    main()
