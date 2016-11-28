"""Submodule for 'write' command functionality.
"""

import difflib
import itertools

import licenses
import userfiles_handling


def main(args, config):
    """'write' command entrypoint.
    """
    if args.license_only:
        pass

    if args.headers_only:
        for userfile_path in args.headers_only:
            print(userfile_path)
            print(list(rank_license_text(userfile_path, config)))
    else:
        create_header(config["License"], "**/*.c", config)


def create_header(license_name, commentfmt, config):
    header_text = licenses.license_dict[license_name].header

    comment_format = (
        config["CommentedFiles"][commentfmt]
    )

    header_lines = header_text.splitlines(keepends=True)

    if "BlockComments" in comment_format:
        block_format = comment_format["BlockComments"]

        if block_format["BlockEnd"] in header_text:
            print(
                "WARNING: the license header contains the comment token"
                " used to indicate a block comment end."
            )
        elif block_format["BlockEnd"].strip() in header_text:
            print(
                "WARNING: the license header contains a whitespace-"
                "stripped version of the block comment end token."
            )

        header_lines = [
            block_format["BlockStart"] + header_lines[0]
        ] + [
            block_format.get("BlockLine", "") + line
            if not line.isspace()
            else block_format.get("BlockLine", "").rstrip() + line
            for line in header_lines[1:]
        ] + [
            block_format["BlockEnd"] + "\n"
        ]

    else:  # elif "LineCommentStart" in comment_format:
        header_lines = [
            comment_format["LineCommentStart"] + line
            if line != "\n"
            else comment_format["LineCommentStart"].rstrip() + line
            for line in header_lines
        ]

    return "".join(header_lines)


def rank_license_text(userfile_path, config):
    """Returns a list of licenses sorted based on their percentage chance of
    matching the current header in the userfile.
    """
    header_start_line = userfiles_handling.find_header_start_line(userfile_path)

    if header_start_line is not None:
        with open(userfile_path, "rt") as userfile:
            commentfmt = userfiles_handling.commentfmt_userfile(
                userfile_path,
                config,
            )

            userfile_header_iter = iter(
                line
                for index, line in enumerate(userfile, 1)
                if index >= header_start_line
            )

            userfile_header_license_pair = zip(
                licenses.license_dict.keys(),
                itertools.tee(userfile_header_iter,
                              len(licenses.license_dict.keys())),
            )

            def _license_sequence_matcher_gen():
                for license_name, userfile_header_iter in \
                    userfile_header_license_pair:

                    commented_header = license_handling.create_header(
                        license_name,
                        commentfmt,
                        config,
                    )

                    yield (
                        license_name,
                        difflib.SequenceMatcher(
                            a=commented_header,
                            b="".join(
                                itertools.islice(
                                    userfile_header_iter,
                                    len(commented_header.splitlines())
                                )
                            ),
                        ),
                    )

            def _snd_ratio_call(pair):
                return (pair[0], pair[1].ratio())

            return sorted(
                map(_snd_ratio_call, _license_sequence_matcher_gen()),
                key=lambda x: x[1],
                reverse=True,
            )

    else:
        return []
