"""The title and date lines must extract as words, not spaced-out letters.

Applicant tracking systems read the PDF's text layer, not the picture. With
1pt tracking at 6pt, pdftotext returned the title as "S TA F F S O F T W A R
E E N G I N E E R" and dates as "J U N 2 0 1 7 - M AY 2 0 1 9", so a parser
could miss the title and every tenure. Twenty screener reads of one resume
flagged it independently (resumes repo, assessments, 2026-09-24).

Skips when typst or pdftotext is missing.
"""
import re
import pathlib
import shutil
import subprocess
import tempfile
import unittest

SKILL = pathlib.Path(__file__).resolve().parent.parent / "skills" / "resume"
FIXTURE = SKILL / "examples" / "sample-resume.yaml"


def _extracted_text():
    missing = [tool for tool in ("typst", "pdftotext") if shutil.which(tool) is None]
    if missing:
        message = f"{', '.join(missing)} not installed"
        raise unittest.SkipTest(message)
    with tempfile.TemporaryDirectory() as work:
        pdf = pathlib.Path(work) / "sample-resume.pdf"
        subprocess.run([str(SKILL / "bin" / "build"), str(FIXTURE), "-o", str(pdf)],
                       check=True, capture_output=True)
        return subprocess.run(["pdftotext", str(pdf), "-"], check=True,
                              capture_output=True, text=True).stdout


class TextLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = _extracted_text()

    def test_the_title_extracts_as_words(self):
        self.assertIn("SENIOR SOFTWARE ENGINEER", self.text)

    def test_job_dates_extract_as_words(self):
        self.assertIn("AUGUST 2017 - MAY 2019", self.text)

    def test_no_line_extracts_as_spaced_letters(self):
        # Four single characters in a row, each followed by a space, is the
        # signature of tracking the extractor split: "S E N I", "2 0 1 7".
        spaced = re.compile(r"(?:\b\w ){4}")
        offenders = [line for line in self.text.splitlines() if spaced.search(line)]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
