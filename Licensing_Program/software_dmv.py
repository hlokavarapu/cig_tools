#! /usr/bin/env python3

import argparse
import os
import pprint
import re

import config_handling
import license_handling
import userfiles_handling

import cli_parser.main_parser

import program_commands.check_command
import program_commands.write_command
import program_commands.config_command

def main_check(args, config):
    """CLI program command: check
    Check project files for license/header text.
    """
    if args.files:
        filepaths = set(args.files)
    else:
        filepaths = (os.path.relpath(os.path.join(cwd, file))
                     for cwd, dirs, files in os.walk(".")
                     for file in files
                     if file != config_handling.CONFIG_FILENAME)

    if (not args.no_ignore) and config["IgnoredFiles"]:
        ignore_regex = "|".join(
            config_handling.param_ignoredfiles_to_regex(ignore_string)
            for ignore_string
            in config["IgnoredFiles"]
        )

        filepaths = (file for file in filepaths
                     if not re.match(ignore_regex, file))

    if filepaths:
        text_dict = license_handling.fill_in_license(
            config["License"], config
        )

        license_text = text_dict["license_text"]
        header_text = text_dict["header_text"]

    for path in filepaths:
        if not userfiles_handling.file_has_correct_header(path, args, config):
            if args.add_missing:
                if args.info_level == "verbose":
                    print("Adding header to {}.".format(path))

                commented_header_text, comment_format = \
                    license_handling.comment_out_header(
                        header_text, path, args, config
                    )

                userfiles_handling.write_header(
                    commented_header_text,
                    path,
                    (
                        comment_format.get("InsertAtLine", 0)
                        if comment_format
                        else 0
                    ),
                )
            else:
                if args.info_level == "quiet":
                    print(path)
                else:
                    print(
                        "{} has an incorrect or missing header.".format(path)
                    )


def main_choose(args, config):
    """CLI program command: choose
    Select or change a project license.
    """
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

        config["License"] = args.license

        userfiles_handling.update_license(config)

    else:
        print(("WARNING: {} is not a supported license. Please use the list"
               " command to see a list of supported licenses."
              ).format(args.license))


def main_list(args, config):
    """CLI program command: list
    Output each supported license by name.
    """
    for license_name in license_handling.get_license_list():
        print(license_name)


def main_settings(args, config):
    """CLI program command: settings
    Display or edit project license configuration.
    """
    if args.info_level != "verbose":
        pprint.pprint(config, depth=2)
    else:
        def dict_doc_print(d, doc, acc=""):
            indent = "  "

            if hasattr(d, "items"):
                for key, value in d.items():
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
    """Create CLI parser for this program.
    """
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

    verbosity_group = parser_check.add_mutually_exclusive_group()

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
        "--no-apply",
        action="store_false",
        dest="apply_choice",
        help="Write/update config file, but do not apply license to project",
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
    """Program entrypoint.
    Calls requested CLI command.
    """

    if args.command == "check":
        config = config_handling.load_configfile()
        program_commands.check_command.main(args, config)
    elif args.command == "config":
        program_commands.config_command.main(args)
    elif args.command == "write":
        config = config_handling.load_configfile()
        program_commands.write_command.main(args, config)

if __name__ == "__main__":
    main(cli_parser.main_parser.create_main_parser().parse_args())
