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
        pass
    else:
        pass


def create_header(license_name, commentfmt, config):
    header_text = licenses_dict[license_name].header

    comment_format = (
        config["CommentedFiles"][commentfmt]
    )

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


def rank_license_text(userfile_path, config):
    header_start_line = userfile_handling.find_header_start_line(userfile_path)

    with open(userfile_path, "rt") as userfile:
        commentfmt = userfile_handling.commentfmt_userfile(
            userfile_path,
            config
        )

        userfile_header_iter = iter(
            (index, line)
            for index, line in enumerate(userfile, 1)
            if index >= header_start_line
        )

        userfile_header_license_pair = zip(
            licenses.list,
            itertools.tee(userfile_header_iter, len(licenses.list),
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

        def snd_ratio_call(pair):
            return pair[1].ratio()

        return sorted(_license_sequence_matcher_gen(), snd_ratio_call)
