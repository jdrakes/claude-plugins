"""Tests for the shipped example variant, examples/variants/public.yaml.

These render for real, so they prove the assert_absent check means
something: the base resume's text contains the phone number and the
variant's does not. They break if the variant stops omitting the phone, if
sample-resume.yaml stops containing it, or if a failed check still writes a
PDF. Skipped only when typst is missing; a missing pdftotext fails.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
RESUME_SKILL = PLUGIN / "skills" / "resume"
BUILD = RESUME_SKILL / "bin" / "build"
BUILD_VARIANT = RESUME_SKILL / "bin" / "build-variant"
SAMPLE = RESUME_SKILL / "examples" / "sample-resume.yaml"
VARIANT = RESUME_SKILL / "examples" / "variants" / "public.yaml"
PHONE = "(555) 0142"


def pdf_text(pdf):
    return subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout


class ExampleVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("typst") is None:
            raise unittest.SkipTest("typst is not installed")

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, ignore_errors=True)
        # bin/build refuses an -o inside the current folder, so run from a
        # folder of its own and write outputs beside it.
        self.cwd = self.temp / "cwd"
        self.cwd.mkdir()

    def run_script(self, script, *arguments):
        return subprocess.run([str(script), *map(str, arguments)], capture_output=True,
                              text=True, cwd=self.cwd)

    def test_the_base_render_contains_the_phone_number(self):
        output = self.temp / "base.pdf"
        result = self.run_script(BUILD, SAMPLE, "-o", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(PHONE, pdf_text(output))

    def test_the_variant_render_lacks_the_phone_number_but_keeps_the_name(self):
        output = self.temp / "public.pdf"
        result = self.run_script(BUILD_VARIANT, VARIANT, "-o", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output.is_file())
        self.assertIn("assert_absent: 1 check(s) passed", result.stdout)
        text = pdf_text(output)
        self.assertNotIn(PHONE, text)
        self.assertIn("Alex Rivera", text)

    def test_an_assert_absent_the_variant_does_not_omit_fails_and_writes_nothing(self):
        content = self.temp / "content"
        (content / "variants").mkdir(parents=True)
        shutil.copy(SAMPLE, content / "sample-resume.yaml")
        variant_text = VARIANT.read_text(encoding="utf-8").replace(
            f'  - "{PHONE}"', '  - "alex.rivera@example.com"')
        self.assertIn("alex.rivera@example.com", variant_text)
        (content / "variants" / "public.yaml").write_text(variant_text, encoding="utf-8")
        output = self.temp / "out" / "public.pdf"
        output.parent.mkdir()
        result = self.run_script(BUILD_VARIANT, content / "variants" / "public.yaml", "-o", output)
        self.assertEqual(result.returncode, 1)
        self.assertIn("alex.rivera@example.com", result.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
