"""Tests for skills/cover-letter/bin/build-letter.

They protect three parsing rules (where the `## Letter` section ends, which
trailing words are contact details, what the word count includes), where a
build is written (never beside the source), and the two render faults that
still exit 0: a hyphenated word split across two lines, and substitute fonts.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "cover-letter" / "bin" / "build-letter"
loader = importlib.machinery.SourceFileLoader("build_letter", str(SCRIPT))
spec = importlib.util.spec_from_loader("build_letter", loader)
build_letter = importlib.util.module_from_spec(spec)
loader.exec_module(build_letter)

SIGNATURE = "Alex Rivera\nalex.rivera@example.com\n555-0142"


class LetterSectionTests(unittest.TestCase):
    def test_stops_at_the_next_heading_whatever_it_is_called(self):
        text = "# Title\n\n## Letter\n\nHi there,\n\n## Surprise Heading\n\nrulings text\n"
        self.assertEqual(build_letter.letter_section(text), ("Hi there,", None))

    def test_missing_heading_is_an_error(self):
        self.assertEqual(build_letter.letter_section("# Title\n\nbody\n"),
                         (None, "no '## Letter' heading"))

    def test_a_longer_heading_is_not_the_section(self):
        section, error = build_letter.letter_section("## Letterhead\n\nnot the section\n")
        self.assertIsNone(section)
        self.assertIsNotNone(error)


class LetterPayloadTests(unittest.TestCase):
    def test_splits_body_name_and_contact(self):
        section = f"Hi Team,\n\nFirst paragraph.\n\nSecond paragraph.\n\n{SIGNATURE}"
        payload, error = build_letter.letter_payload(section)
        self.assertIsNone(error)
        self.assertEqual(payload, {
            "name": "Alex Rivera",
            "contact": ["alex.rivera@example.com", "555-0142"],
            "body": ["Hi Team,", "First paragraph.", "Second paragraph."],
        })

    def test_a_wrapped_paragraph_comes_back_as_one_line(self):
        section = f"Hi,\n\nline one\nline two\nline three\n\n{SIGNATURE}"
        payload, _ = build_letter.letter_payload(section)
        self.assertEqual(payload["body"], ["Hi,", "line one line two line three"])

    def test_last_block_without_email_or_phone_is_an_error(self):
        payload, error = build_letter.letter_payload("Hi,\n\nBody.\n\nAlex Rivera")
        self.assertIsNone(payload)
        self.assertIn("email or phone", error)


class WordsLineTests(unittest.TestCase):
    def test_counts_every_block_including_greeting_and_signature(self):
        section = "Hi Team,\n\nOne two three.\n\nAlex Rivera\na@example.com"
        self.assertEqual(build_letter.words_line(section), "8, by paragraph 2/3/3")


class OutputPathTests(unittest.TestCase):
    def test_no_output_goes_to_the_temp_folder(self):
        self.assertEqual(build_letter.output_path(Path("/x/a.md"), None, "Alex Rivera"),
                         Path(tempfile.gettempdir()) / "a.pdf")

    def test_folder_gets_the_send_ready_name(self):
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work).resolve()
            expected = folder / "Alex Rivera Cover Letter.pdf"
            source = Path("/x/a.md")
            self.assertEqual(build_letter.output_path(source, str(folder), "Alex Rivera"), expected)
            self.assertEqual(
                build_letter.output_path(source, str(folder / "new") + "/", "Alex Rivera"),
                folder / "new" / "Alex Rivera Cover Letter.pdf")

    def test_a_file_path_is_used_as_given(self):
        self.assertEqual(build_letter.output_path(Path("/x/a.md"), "/tmp/x.pdf", "Alex Rivera"),
                         Path("/tmp/x.pdf").resolve())


class MainTests(unittest.TestCase):
    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = build_letter.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_extract_prints_the_section(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "app.md"
            path.write_text(f"# App\n\n## Letter\n\nHi,\n\n{SIGNATURE}\n\n## Notes\n\nno\n")
            code, out, _ = self.run_main(["--extract", str(path)])
        self.assertEqual(code, 0)
        self.assertEqual(out, f"Hi,\n\n{SIGNATURE}\n")

    def test_file_without_letter_heading_exits_1(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "app.md"
            path.write_text("# App\n\nno letter here\n")
            code, _, err = self.run_main([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("no '## Letter' heading", err)

    def test_bad_usage_exits_2(self):
        code, _, _ = self.run_main([])
        self.assertEqual(code, 2)


NEEDS = ("typst", "pdftotext", "pdffonts")


@unittest.skipUnless(all(shutil.which(tool) for tool in NEEDS), "needs typst and poppler")
class RenderTests(unittest.TestCase):
    # Checked by hand: with the `#show regex(...)` line deleted from
    # template.typ, this paragraph renders "change-data-" at the end of a line
    # and "capture" at the start of the next, and test_hyphenated_word_stays_whole
    # fails. A paragraph that never puts the word at a line end checks nothing.
    # pdftotext needs -layout: by default it dehyphenates and hides the break.
    HYPHEN_PARAGRAPH = ("At Northwind Systems Alex Rivera moved the nightly reports onto a "
                        "shared pipeline and a change-data-capture feed for the finance team.")

    def build(self, work, body):
        source = Path(work) / "app.md"
        source.write_text(f"# App\n\n## Letter\n\nHi Team,\n\n{body}\n\n{SIGNATURE}\n")
        output = Path(work) / "out.pdf"
        self.assertEqual(build_letter.main([str(source), "-o", str(output)]), 0)
        return output

    def pdf_text(self, pdf):
        return subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                              capture_output=True, text=True, check=True).stdout

    def test_hyphenated_word_stays_whole(self):
        with tempfile.TemporaryDirectory() as work, contextlib.redirect_stdout(io.StringIO()):
            text = self.pdf_text(self.build(work, self.HYPHEN_PARAGRAPH))
        self.assertIn("change-data-capture", text)
        self.assertIsNone(re.search(r"\w-\n\w", text))

    def test_fonts_are_embedded_not_substituted(self):
        with tempfile.TemporaryDirectory() as work, contextlib.redirect_stdout(io.StringIO()):
            pdf = self.build(work, "Short body.")
            fonts = subprocess.run(["pdffonts", str(pdf)], capture_output=True,
                                   text=True, check=True).stdout
        self.assertIn("Lato", fonts)
        self.assertIn("Oswald", fonts)

    def test_review_build_writes_nothing_beside_the_source(self):
        with tempfile.TemporaryDirectory() as work, contextlib.redirect_stdout(io.StringIO()):
            source = Path(work) / "review-build-probe.md"
            source.write_text(f"# App\n\n## Letter\n\nHi Team,\n\nBody.\n\n{SIGNATURE}\n")
            temp_pdf = Path(tempfile.gettempdir()) / "review-build-probe.pdf"
            self.addCleanup(lambda: temp_pdf.unlink(missing_ok=True))
            self.assertEqual(build_letter.main([str(source)]), 0)
            self.assertEqual([p.name for p in Path(work).iterdir()], ["review-build-probe.md"])
            self.assertTrue(temp_pdf.exists())


if __name__ == "__main__":
    unittest.main()
