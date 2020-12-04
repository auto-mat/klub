import os
import posixpath
import re
from collections import namedtuple
from urllib.parse import unquote, urldefrag

from django.conf import settings
from django.contrib.staticfiles import storage


class CustomStaticFilesStorage(storage.StaticFilesStorage):

    def __handle_comments(self, matchobj, matched):
        Position = namedtuple('Position', 'start end')

        # Ignore css statement, rule which is inside css comment
        comment_regex = re.compile('/\\*[^*]*\\*+(?:[^/*][^*]*\\*+)*/')
        comments = re.finditer(comment_regex, matchobj.string)

        for comment in comments:
            if matched in comment.group(0):
                comment_position = Position(*comment.span())
                matched_inside_comment = re.search(re.escape(matched), comment.group(0))

                matched_position_inside_comment = Position(*matched_inside_comment.span())

                comment_position = comment_position._replace(
                    start=comment_position.start + matched_position_inside_comment.start,
                )

                if matchobj.span()[0] == comment_position.start:
                    return matched

    def url_converter(self, name, hashed_files, template=None):
        """
        Return the custom URL converter for the given file name.
        """
        if template is None:
            template = self.default_template

        def converter(matchobj):
            """
            Convert the matched URL to a normalized and hashed URL.

            This requires figuring out which files the matched URL resolves
            to and calling the url() method of the storage.
            """
            matched, url = matchobj.groups()

            # Ignore absolute/protocol-relative and data-uri URLs.
            if re.match(r'^[a-z]+:', url):
                return matched

            # Ignore absolute URLs that don't point to a static file (dynamic
            # CSS / JS?). Note that STATIC_URL cannot be empty.
            if url.startswith('/') and not url.startswith(settings.STATIC_URL):
                return matched

            # Jump over comment
            comment = self.__handle_comments(matchobj, matched)
            if comment:
                return comment

            # Strip off the fragment so a path-like fragment won't interfere.
            url_path, fragment = urldefrag(url)

            if url_path.startswith('/'):
                # Otherwise the condition above would have returned prematurely.
                assert url_path.startswith(settings.STATIC_URL)
                target_name = url_path[len(settings.STATIC_URL):]
            else:
                # We're using the posixpath module to mix paths and URLs conveniently.
                source_name = name if os.sep == '/' else name.replace(os.sep, '/')
                target_name = posixpath.join(posixpath.dirname(source_name), url_path)

            # Determine the hashed name of the target file with the storage backend.
            hashed_url = self._url(
                self._stored_name, unquote(target_name),
                force=True, hashed_files=hashed_files,
            )

            transformed_url = '/'.join(url_path.split('/')[:-1] + hashed_url.split('/')[-1:])

            # Restore the fragment that was stripped off earlier.
            if fragment:
                transformed_url += ('?#' if '?#' in url else '#') + fragment

            # Return the hashed version to the file
            return template % unquote(transformed_url)

        return converter
