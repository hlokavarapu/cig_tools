"""Submodule for 'check' command functionality.
"""

import userfiles_handling


def main(args, config):
    """'check' command entrypoint.
    """
    if args.files:
        args.files = set(
            userfile_handling.sanitize_path(path, userproject_dir)
            for path in args.files
        )
    else:
        args.files = userfile_handling.userfiles_iter(userproject_dir)

    if not args.no_ignore:
        args.files = userfiles_handling.remove_ignored_userfiles(
            args.files,
            config,
        )

    commentfmt_userfiles_pairing = \
        userfiles_handling.commentfmt_userfiles_pairing(
            args.files,
            config,
        )

    for commentfmt, userfile_path in commentfmt_userfiles_pairing:
        generated_header = generate_header(commentfmt, config)

        header_match_prob = userfiles_handling.match_header_in_file(
            userfile_path,
            generated_header,
        )

        if header_match_prob >= COMPLETE_MATCH_PROB:
            pass
        elif header_match_prob >= OUTOFDATE_LICENSE_MATCH_PROB:
            pass
        elif header_match_prob >= SIMILAR_LICENSE_MATCH_PROB:
            pass  # is this useful?
        else:
            pass  # no license header
