"""This file provides functionality for getting and parsing a project's
configuration.
"""

import collections
import json
import os.path
import re
import sys

try:
    import jsonschema
except ImportError:
    jsonschema = None

import userfiles_handling


CONFIG_FILENAME = ".licensing.json"

CONFIG_SCHEMA = {
    "properties": {
        "CommentedFiles": {
            "additionalProperties": False,
            "patternProperties": {
                "^.+$": {
                    "insertAtLine": {
                        "maximum": userfiles_handling.HEADER_IN_FIRST_N_LINES,
                        "type": "integer",
                        "minimum": 1,
                        "default": 1
                    },
                    "oneOf": [
                        {
                            "properties": {
                                "BlockComments": {
                                    "properties": {
                                        "BlockEnd": {
                                            "type": "string",
                                        },
                                        "BlockLine": {
                                            "type": "string",
                                            "default": "",
                                        },
                                        "BlockStart": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "BlockStart",
                                        "BlockEnd",
                                    ],
                                    "type": "object",
                                },
                            },
                            "required": [
                                "BlockComments",
                            ],
                            "type": "object",
                        },
                        {
                            "properties": {
                                "LineCommentStart": {
                                    "type": "string",
                                },
                            },
                            "required": [
                                "LineCommentStart",
                            ],
                            "type": "object",
                        },
                        {
                            "properties": {
                                "Uncommented": {
                                    "type": "null",
                                },
                            },
                            "required": [
                                "Uncommented",
                            ],
                            "type": "object",
                        },
                    ],
                },
            },
            "type": "object",
        },
        "IgnoredFiles": {
            "items": {
                "type": "string",
            },
            "type": "array",
        },
        "License": {
            "type": "string",
        },
        "LicenseParameters": {
            "additionalProperties": False,
            "patternProperties": {
                "^[a-zA-Z0-9_-]+$": {},
            },
            "type": "object",
        },
    },
    "required": [
        "License",
    ],
    "type": "object",
}

CONFIG_DEFAULT = {
    "IgnoredFiles": [
        ".licensing.json",
        ".git/**",
        ".gitignore",
    ],
    "License": "",
    "LicenseParameters": {
        "ProjectName": "",
        "fullname": "",
    },
    "CommentedFiles": {},
}


# antpatterns: https://ant.apache.org/manual/dirtasks.html#patterns
def antpattern_to_regex(pattern):
    """Convert an Apache antpattern to a python regex string. Assumes POSIX
    path separator ('/').
    """
    # Escape other regex symbols
    pattern = re.sub(
        r"([.+^$|{}()\[\]])",
        r"\\\1",
        pattern,
    )

    # Convert ant '?' to re '.'
    pattern = re.sub(
        r"\?",
        r".",
        pattern,
    )

    # ant '*' doesn't leave cwd
    pattern = re.sub(
        r"([^*]|^)\*([^*]|$)",
        r"\1[^/]*\2",
        pattern,
    )

    # patterns that begin with **/ match any amount of leading directories.
    pattern = re.sub(
        r"^\*\*/",
        r"(.*?/|/?)",
        pattern,
    )

    # patterns that end with /** match all files under any directories that
    # match the earlier part of the pattern.
    pattern = re.sub(
        r"/\*\*$",
        r"/.*?",
        pattern,
    )

    # patterns that contain /**/ match zero or more infix directories.
    pattern = re.sub(
        r"/\*\*/",
        r"(/|/.*?/)",
        pattern,
    )

    # replace misused double asterisks with single asterisk
    # TODO: maybe show a warning/error for this
    pattern = re.sub(
        r"\*\*+",
        r"[^/]*",
        pattern,
    )

    return "^(" + pattern + ")$"


def param_ignoredfiles_to_regex(ignore_string):
    """Converts a configuration pattern for 'IgnoredFiles' to a regex string.
    A pattern can have a 're:' prefix to denote it is already a regex or a
    'ant:' prefix to explicitly show it is an ant pattern. Without a prefix,
    an ant pattern is assumed.
    """
    if ignore_string.startswith("re:"):
        return ignore_string.lstrip("re:")
    elif ignore_string.startswith("ant:"):
        return antpattern_to_regex(ignore_string.lstrip("ant:"))
    else:
        return antpattern_to_regex(ignore_string)


def load_configfile(cwd=".", info_level=""):
    """Parses the project config file in 'cwd'. If the 'jsonschema' module is
    available, the config file is checked for data errors.
    """
    config = json.load(
        open(os.path.join(cwd, CONFIG_FILENAME), "rt"),
        object_pairs_hook=collections.OrderedDict,
    )

    if jsonschema:
        jsonschema.validate(config, CONFIG_SCHEMA)
    elif info_level == "verbose":
        print(
            "\nWARNING: 'jsonschema' module could not be found. User"
            " configuration will not be checked for errors.",
            file=sys.stderr,
        )

    return config


def write_default_configfile(cwd="."):
    """This function generates and writes a simple configuration file
    with filler values.
    """
    with open(CONFIG_FILENAME, 'w') as new_configfile:
        json.dump(CONFIG_DEFAULT, new_configfile, indent=4)
