from __future__ import absolute_import, unicode_literals, print_function
import codecs
import os
import tempfile
import unittest
import shutil
from libraries.resource_container.ResourceContainer import RC
from libraries.client.preprocessors import do_preprocess
from libraries.general_tools.file_utils import unzip


class TestBiblePreprocessor(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """
        Runs before each test
        """
        self.out_dir = ''
        self.temp_dir = ""

    def tearDown(self):
        """
        Runs after each test
        """
        # delete temp files
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_BiblePreprocessorComplete(self):
        # given
        file_name = os.path.join('raw_sources', 'aa_php_text_ulb.zip')
        repo_name = 'aa_php_text_ulb'
        expected_output = '51-PHP.usfm'
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)

        # when
        folder, preprocessor = self.runBiblePreprocessor(rc, repo_dir)

        # then
        self.verifyTransform(folder, expected_output, preprocessor)

    def test_BiblePreprocessorMultipleBooks(self):
        # given
        file_name = os.path.join('raw_sources', 'en-ulb.zip')
        repo_name = 'en-ulb'
        expected_output = ['01-GEN.usfm', '02-EXO.usfm', '03-LEV.usfm', '05-DEU.usfm']
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)

        # when
        folder, preprocessor = self.runBiblePreprocessor(rc, repo_dir)

        # then
        self.verifyTransform(folder, expected_output, preprocessor)

    def test_BiblePreprocessorMultipleBooksSeparateProjects(self):
        # given
        file_name = os.path.join('raw_sources', 'en-ulb-separate-projects.zip')
        repo_name = 'en-ulb'
        expected_output = ['01-GEN.usfm', '02-EXO.usfm', '03-LEV.usfm', '04-NUM.usfm', '05-DEU.usfm']
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)

        # when
        folder, preprocessor = self.runBiblePreprocessor(rc, repo_dir)

        # then
        self.verifyTransform(folder, expected_output, preprocessor)

    def test_BiblePreprocessorActsWithSlashInText(self):
        # given
        file_name = os.path.join('raw_sources', 'awa_act_text_reg.zip')
        repo_name = 'awa_act_text_reg'
        expected_output = '45-ACT.usfm'
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)

        # when
        folder, preprocessor = self.runBiblePreprocessor(rc, repo_dir)

        # then
        self.verifyTransform(folder, expected_output, preprocessor)

    @classmethod
    def extractFiles(cls, file_name, repo_name):
        file_path = os.path.join(TestBiblePreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = temp_dir

        # 2) Get the resource container
        rc = RC(repo_dir)
        return rc, repo_dir, temp_dir

    def runBiblePreprocessor(self, rc, repo_dir):
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        results, preprocessor = do_preprocess(rc, repo_dir, self.out_dir)
        return self.out_dir, preprocessor

    def verifyTransform(self, folder, expected_name, preprocessor):
        if type(expected_name) is list:
            for f in expected_name:
                self.verifyFile(f, folder)
            self.assertTrue(preprocessor.is_multiple_jobs())
            self.assertEqual(len(preprocessor.get_book_list()), len(expected_name))
        else:
            self.verifyFile(expected_name, folder)
            self.assertFalse(preprocessor.is_multiple_jobs())
            self.assertTrue(expected_name in preprocessor.get_book_list())
            self.assertEqual(len(preprocessor.get_book_list()), 1)

    def verifyFile(self, expected_name, folder):
        file_name = os.path.join(folder, expected_name)
        self.assertTrue(os.path.isfile(file_name), 'Bible usfm file not found: {0}'.format(expected_name))
        with codecs.open(file_name, 'r', 'utf-8-sig') as usfm_file:
            usfm = usfm_file.read()
        self.assertIsNotNone(usfm)
        self.assertTrue(len(usfm) > 10, 'Bible usfm file contents missing: {0}'.format(expected_name))
