from __future__ import print_function, unicode_literals
import codecs
import os
import traceback
from libraries.linters.linter import Linter
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.usfm_tools import verifyUSFM


class UsfmLinter(Linter):

    def __init__(self, *args, **kwargs):
        super(UsfmLinter, self).__init__(*args, **kwargs)
        self.found_books = []

    def lint(self):
        """
        Checks for issues with all Bibles, such as missing books or chapters

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of .usfm files
        :return bool:
        """

        lang_code = self.rc.resource.language.identifier
        valid_lang_code = PageMetrics().validate_language_code(lang_code)
        if not valid_lang_code:
            self.log.warning("Invalid language code: " + lang_code)

        for root, dirs, files in os.walk(self.source_dir):
            for f in files:
                if os.path.splitext(f)[1].lower() != '.usfm':  # only usfm files
                    continue

                file_path = os.path.join(root, f)
                sub_path = '.' + file_path[len(self.source_dir):]
                self.parse_file(file_path, sub_path, f)

        if not len(self.found_books):
            self.log.warning("No translations found")

        return True

    def parse_file(self, file_path, sub_path, file_name):

        book_code, book_full_name = self.get_book_ids(file_name)

        try:
            with codecs.open(file_path, 'r', 'utf-8') as in_file:
                book_text = in_file.read()

            self.parse_usfm_text(sub_path, file_name, book_text, book_full_name, book_code)

        except Exception as e:
            self.log.warning("Failed to open book '{0}', exception: {1}".format(file_name, str(e)))

    def get_book_ids(self, file_name):
        file_name_parts = file_name.split('.')
        book_full_name = file_name_parts[0].upper()
        book_code = book_full_name
        book_name_parts = book_full_name.split('-')
        if len(book_name_parts) > 1:
            book_code = book_name_parts[1]
        return book_code, book_full_name

    def parse_usfm_text(self, sub_path, file_name, book_text, book_full_name, book_code):
        try:
            lang_code = self.rc.resource.language.identifier
            errors, found_book_code = verifyUSFM.verify_contents_quiet(book_text, book_full_name, book_code, lang_code)

            if found_book_code:
                book_code = found_book_code

            if book_code:
                if book_code in self.found_books:
                    self.log.warning("File '{0}' has same code '{1}' as previous file".format(sub_path, book_code))
                self.found_books.append(book_code)

            if len(errors):
                prefix = "File '{0}' book code '{1}': ".format(sub_path, book_code)
                for error in errors:
                    self.log.warning(prefix + error)

        except Exception as e:
            # for debugging
            print("Failed to verify book '{0}', exception: {1}\n{2}".format(file_name, str(e),
                                                                            traceback.format_exc()))
            self.log.warning("Failed to verify book '{0}', exception: {1}".format(file_name, str(e)))
