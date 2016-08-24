"""This file provides functionality for using the license repository included
 in the software_dmv project.
"""

import re
import string

import licenses

DEFAULT_LICENSE = "generic"


def get_license_list():
    """Return a sorted list of supported license names.
    """
    return sorted(licenses.license_dict.keys())


def get_license_parameters_list(license_name):
    """Return a list of parameter names required for the license text.
    """
    return [
        name
        for _, name, _, _ in string.Formatter().parse(
            licenses.license_dict[license_name].license)
        if name is not None
    ] + [
        name
        for _, name, _, _ in string.Formatter().parse(
            licenses.license_dict[license_name].header)
        if name is not None
    ]


def get_formatted_license(license_name, config, user_filepath):
    """Return a dictionary containing the formatted text of the license and
    header.
    """
    user_license = licenses.license_dict[license_name]

    license_text = user_license.license.format(**config["LicenseParameters"])
    header_text = user_license.header.format(**config["LicenseParameters"])

    header_lines = header_text.splitlines(keepends=True)

    if "CommentedFiles" in config:
        matched_comment_formats = [
            regex
            for regex in sorted(config["CommentedFiles"])
            if re.match(regex, user_filepath)
        ]

        if len(matched_comment_formats) > 1:
            print(
                "WARNING: {} matches more than one commenting format.".format(
                    user_filepath)
            )
            print("List of matches: {}".format(matched_comment_formats))

        if matched_comment_formats:
            comment_format = (
                config["CommentedFiles"][matched_comment_formats[0]]
            )

            if "BlockComments" in comment_format:
                header_lines = [
                    comment_format["BlockComments"]["BlockStart"]
                    + header_lines[0]
                ] + [
                    comment_format["BlockComments"].get("BlockLine", "") + line
                    for line in header_lines[1:]
                ] + [
                    comment_format["BlockComments"]["BlockEnd"] + "\n"
                ]

            else:  # elif "LineCommentStart" in comment_format:
                header_lines = [
                    comment_format["LIneCommentStart"] + line
                    for line in header_lines
                ]

    return {
        "license_text" : license_text,
        "header_lines" : header_lines,
    }
