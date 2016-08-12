#! /usr/bin/env python3

import argparse
import functools
import glob
import json
import itertools
import operator
import os
import pprint
import re

import config_handling
import license_handling
import userfiles_handling


def main_check(args, config):
    if args.files:
        filepaths = set(args.files)
    else:
        filepaths = (os.path.join(cwd, file)
                     for cwd, dirs, files in os.walk(".")
                     for file in files)

    if (not args.no_ignore) and config["IgnoredFiles"]:
        ignore_regex = "|".join(
            config_handling.param_ignoredfiles_to_regex(ignore_string)
            for ignore_string
            in config["IgnoredFiles"]
        )

        filepaths = (file for file in filepaths
                     if not re.match(ignore_regex, file))

    for path in filepaths:
        print(path)
        #userfiles_handling.check_file(path, args, config)


def main_choose(args, config):
    if args.license in license_handling.get_license_list():
        def arg_to_parameters(string_list):
            return dict(pair.split(":")
                        for arg in string_list
                        for pair in arg.split(","))

        if args.parameters:
            try:
                args.parameters = arg_to_parameters(args.parameters)
            except TypeError:
                print("ERROR: Parameter input not formatted properly")
                exit(1)

        license_fd, header_fd = license_handling.get_license_files(args.license)

        try:
            same = filecmp.cmp(license_fd.name, "LICENSE", shallow=False)
        except FileNotFoundError:
            same = False

        if not same:
            config["License"] = args.license

            with open("LICENSE", "wt") as project_license:
                project_license.write(license_fd)

    else:
        print(("{} is not a supported license. Please use the list command to"
               " see a list of supported licenses.").format(args.license))


def main_list(args, config):
    for license in license_handling.get_license_list():
        print(license)


#def main_info(args):
#    license = json.load(_license_dir + args.license)
#
#    license["name"]


def main_settings(args, config):
    if args.info_level != "verbose":
        pprint.pprint(config, depth=2)
    else:
        def dict_doc_print(d, doc, acc=""):
            indent = "  "

            if hasattr(d, "items"):
                for key, value in sorted(d.items()):
                    if doc.get(key):
                        print("\n" + acc + "# " + str(doc.get(key)))
                    print(acc + str(key) + ":")

                    if hasattr(value, "items"):
                        dict_doc_print(value, doc, acc + indent)
                    elif hasattr(value, "__iter__") and value != str(value):
                        for x in value:
                            print(acc + indent + str(x))
                    else:
                        print(acc + indent + str(value))

        config_doc = {
            "License": ("The license that will be used to generate the LICENSE"
                        " file"),
            "LicenseParameters": ("Necessary user input to be inserted into"
                                  " the license"),
        }

        dict_doc_print(config, config_doc)


def create_main_parser():
    parser = argparse.ArgumentParser(
        description="Where you go to get your software license.",
    )
    subparsers = parser.add_subparsers(
        title="Commands",
        dest="command",
    )
    subparsers.required = True

    parser_check = subparsers.add_parser(
        "check",
        help="Check all project files for licensing information",
        description="Check all project files for licensing information.",
    )
    parser_check.add_argument(
        "--no-ignore",
        action="store_true",
        help="Also check files that are set to be ignored",
    )
    parser_check.add_argument(
        "-a",
        "--add-missing",
        action="store_true",
        help="Add project license to files that fail the check",
    )
    parser_check.add_argument(
        "-f",
        "--files",
        metavar="FILE",
        nargs="+",
        help="Check these files only",
    )

    parser_choose = subparsers.add_parser(
        "choose",
        help="Choose a license to insert into your project",
        description="Choose a license to insert into your project.",
    )

    verbosity_group = parser_choose.add_mutually_exclusive_group()

    verbosity_group.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="verbose",
        dest="info_level",
        default="",
        help="Output more information about executed command",
    )
    verbosity_group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="quiet",
        dest="info_level",
        default="",
        help="Silence all non-error output",
    )

    parser_choose.add_argument(
        "-p",
        "--parameter",
        action="append",
        dest="parameters",
        help=("Set a license parameter. Input is in key:value form and"
              " multiple parameters can be set by using multiple flags or by"
              " concatenating key-value pairs with commas. e.g. '--parameter="
              "project:foo,author:bar'."),
    )
    parser_choose.add_argument(
        "license",
        metavar="LICENSE",
        help=("License to be created for your project. Use the 'list' command"
              " to see all supported licenses."),
    )

    parser_list = subparsers.add_parser(
        "list",
        help="List supported licenses",
        description="List supported licenses.",
    )

    parser_info = subparsers.add_parser(
        "info",
        help="Show summary of license and necessary user parameters",
        description="Show summary of license and necessary user parameters.",
    )
    parser_info.add_argument(
        "license",
        metavar="LICENSE",
        help="License name",
    )
    parser_info.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="verbose",
        dest="info_level",
        default="",
        help="Show full license text instead of summary",
    )

    parser_settings = subparsers.add_parser(
        "settings",
        help="Show current license settings for your project",
        description="Show current license settings for your project.",
    )
    parser_settings.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="verbose",
        dest="info_level",
        default="",
        help="Show all settings and their documentation",
    )

    return parser


def main(args):
    config = config_handling.load_project_config(args.info_level)

    if args.command == "check":
        pass
    elif args.command == "choose":
        pass
    elif args.command == "list":
        main_list(args, config)
#    elif args.command == "info":
#        main_info(args)
    elif args.command == "settings":
        main_settings(args, config)


if __name__ == "__main__":
    main(create_main_parser().parse_args())
