"""Tests for skills/resume/bin/build's output path.

typst is replaced by a stub on PATH that writes its last argument, so these
run on any machine and test only where the PDF goes. The render itself is
tested by tools/check-fidelity.sh and test_fidelity_paths.py.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
BUILD = PLUGIN / "skills" / "resume" / "bin" / "build"


class OutputPathTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name).resolve()
        stubs = self.work / "stubs"
        stubs.mkdir()
        typst = stubs / "typst"
        typst.write_text(
            '#!/usr/bin/env bash\nfor last; do :; done\nprintf stub > "$last"\n',
            encoding="utf-8",
        )
        typst.chmod(0o755)
        self.temp_folder = self.work / "temp"
        self.temp_folder.mkdir()
        self.home = self.work / "home"
        self.home.mkdir()
        self.content_folder = self.work / "content"
        self.content_folder.mkdir()
        self.content = self.content_folder / "resume-v1.yaml"
        self.content.write_text("name: Alex Rivera\n", encoding="utf-8")
        self.elsewhere = self.work / "elsewhere"
        self.elsewhere.mkdir()
        self.environment = {
            **os.environ,
            "PATH": f"{stubs}{os.pathsep}{os.environ['PATH']}",
            "TMPDIR": f"{self.temp_folder}/",
            "HOME": str(self.home),
        }

    def build(self, *arguments, cwd=None):
        return subprocess.run(
            [str(BUILD), str(self.content), *arguments],
            cwd=cwd or self.content_folder, env=self.environment,
            capture_output=True, text=True,
        )

    def content_folder_files(self):
        return sorted(path.name for path in self.content_folder.iterdir())

    def test_no_output_goes_to_the_temp_folder(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.temp_folder / "resume-v1.pdf").is_file())
        self.assertIn(f"built {self.temp_folder}/resume-v1.pdf", result.stdout)
        self.assertEqual(self.content_folder_files(), ["resume-v1.yaml"])

    def test_a_relative_output_is_refused(self):
        result = self.build("-o", "resume.pdf")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to write", result.stderr)
        self.assertEqual(self.content_folder_files(), ["resume-v1.yaml"])

    def test_an_output_in_the_content_folder_is_refused_from_elsewhere(self):
        result = self.build("-o", str(self.content_folder / "resume.pdf"), cwd=self.elsewhere)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the content file's folder", result.stderr)
        self.assertEqual(self.content_folder_files(), ["resume-v1.yaml"])

    def test_an_output_under_the_current_folder_is_refused(self):
        result = self.build("-o", str(self.elsewhere / "nested" / "resume.pdf"), cwd=self.elsewhere)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the current folder", result.stderr)
        self.assertFalse((self.elsewhere / "nested").exists())

    def test_a_leading_tilde_is_expanded(self):
        result = self.build("-o", "~/send/resume.pdf")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / "send" / "resume.pdf").is_file())

    def test_a_folder_output_is_named_from_the_content(self):
        result = self.build("-o", f"{self.work}/send/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.work / "send" / "Alex Rivera Resume.pdf").is_file())

    def test_an_existing_folder_without_a_slash_is_a_folder(self):
        (self.work / "send").mkdir()
        result = self.build("-o", str(self.work / "send"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.work / "send" / "Alex Rivera Resume.pdf").is_file())

    def test_a_folder_output_needs_a_name_in_the_content(self):
        self.content.write_text("title: Engineer\n", encoding="utf-8")
        result = self.build("-o", f"{self.work}/send/")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no name", result.stderr)
        self.assertFalse((self.work / "send").exists())

    def test_a_differently_cased_content_folder_is_refused(self):
        # Breaks if the folders are compared as strings: on a case-insensitive
        # disk <work>/CONTENT is the content folder under another spelling.
        upper = self.work / "CONTENT"
        if not upper.exists():
            self.skipTest("the temp filesystem is case-sensitive, so CONTENT is another folder")
        result = self.build("-o", str(upper / "resume.pdf"), cwd=self.elsewhere)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the content file's folder", result.stderr)
        self.assertEqual(self.content_folder_files(), ["resume-v1.yaml"])

    def test_a_draft_cannot_write_into_the_folder_above_drafts(self):
        # Breaks if only the draft's own folder is guarded: drafts/ sits inside
        # the content folder, which must stay free of PDFs too.
        drafts = self.content_folder / "drafts"
        drafts.mkdir()
        self.content = drafts / "resume-v1-draft.yaml"
        self.content.write_text("name: Alex Rivera\n", encoding="utf-8")
        result = self.build("-o", str(self.content_folder / "resume.pdf"), cwd=self.elsewhere)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the folder that holds drafts/", result.stderr)
        self.assertEqual(self.content_folder_files(), ["drafts", "resume-v1.yaml"])

    def test_a_name_that_climbs_into_the_content_folder_is_refused(self):
        # Breaks if the path is not resolved again after the name is joined:
        # "../content/Alex" walks out of the send folder into the content one.
        self.content.write_text("name: ../content/Alex\n", encoding="utf-8")
        result = self.build("-o", f"{self.work}/send/", cwd=self.elsewhere)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the content file's folder", result.stderr)
        self.assertEqual(self.content_folder_files(), ["resume-v1.yaml"])

    def test_output_over_a_yaml_file_is_refused(self):
        result = self.build("-o", str(self.elsewhere / "resume.yaml"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to write output over a .yaml file", result.stderr)


if __name__ == "__main__":
    unittest.main()
