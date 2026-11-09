"""Tests for skills/cover-letter/bin/build-letter.

They protect three parsing rules (where the `## Letter` section ends, which
lines of the last block are contact details, what the word count includes),
where a build is written (never beside the source, never inside the current
folder), and the two render faults that still exit 0: a hyphenated word split
across two lines, and substitute fonts.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_each_contact_line_is_kept_whole_and_the_name_is_the_first_line(self):
        # Breaks if contact details are picked out word by word again: the
        # spaced phone formats split, and a profile URL joins the name.
        for line in ("(512) 555-0142", "+1 512 555 0142", "linkedin.com/in/alexrivera"):
            with self.subTest(line=line):
                section = f"Hi,\n\nBody.\n\nAlex Rivera\nalex.rivera@example.com\n{line}"
                payload, error = build_letter.letter_payload(section)
                self.assertIsNone(error)
                self.assertEqual(payload["name"], "Alex Rivera")
                self.assertEqual(payload["contact"], ["alex.rivera@example.com", line])

    def test_last_block_without_email_or_phone_is_an_error(self):
        payload, error = build_letter.letter_payload("Hi,\n\nBody.\n\nAlex Rivera")
        self.assertIsNone(payload)
        self.assertIn("email or phone", error)


class WordsLineTests(unittest.TestCase):
    def test_counts_every_block_including_greeting_and_signature(self):
        section = "Hi Team,\n\nOne two three.\n\nAlex Rivera\na@example.com"
        self.assertEqual(build_letter.words_line(section), "8, by paragraph 2/3/3")


class OutputPathTests(unittest.TestCase):
    CWD = Path("/x/cwd")

    def test_no_output_goes_to_the_temp_folder(self):
        self.assertEqual(build_letter.output_path(Path("/x/a.md"), None, "Alex Rivera", self.CWD),
                         (Path(tempfile.gettempdir()) / "a.pdf", None))

    def test_folder_gets_the_send_ready_name(self):
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work).resolve()
            expected = folder / "Alex Rivera Cover Letter.pdf"
            source = Path("/x/a.md")
            self.assertEqual(build_letter.output_path(source, str(folder), "Alex Rivera", self.CWD),
                             (expected, None))
            self.assertEqual(
                build_letter.output_path(source, str(folder / "new") + "/", "Alex Rivera", self.CWD),
                (folder / "new" / "Alex Rivera Cover Letter.pdf", None))

    def test_a_file_path_is_used_as_given(self):
        self.assertEqual(
            build_letter.output_path(Path("/x/a.md"), "/tmp/x.pdf", "Alex Rivera", self.CWD),
            (Path("/tmp/x.pdf").resolve(), None))


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


def fake_render(payload, output):
    """Stands in for typst: these tests are about where the PDF goes."""
    output.write_bytes(b"%PDF-1.7\n")


class OutputFolderTests(unittest.TestCase):
    """main with -o, the render stubbed, in a throwaway layout:

    <work>/home       HOME for the test
    <work>/letters    holds app.md, the source
    <work>/cwd        the current folder
    """

    def setUp(self):
        self.work = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.work)
        for folder in ("home", "letters", "cwd"):
            (self.work / folder).mkdir()
        self.source = self.work / "letters" / "app.md"
        self.source.write_text(f"# App\n\n## Letter\n\nHi Team,\n\nBody.\n\n{SIGNATURE}\n")
        previous = Path.cwd()
        os.chdir(self.work / "cwd")
        self.addCleanup(os.chdir, previous)
        patches = (mock.patch.dict(os.environ, {"HOME": str(self.work / "home")}),
                   mock.patch.object(build_letter, "render", fake_render))
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def run_main(self, output_arg):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = build_letter.main([str(self.source), "-o", output_arg])
        return code, err.getvalue()

    def written(self):
        return sorted(str(path.relative_to(self.work))
                      for path in self.work.rglob("*") if path.is_file())

    def test_a_quoted_tilde_is_the_home_folder(self):
        # Breaks if -o is not expanded: "~/out/" then lands at <cwd>/~/out/.
        code, _ = self.run_main("~/out/")
        self.assertEqual(code, 0)
        self.assertEqual(self.written(),
                         ["home/out/Alex Rivera Cover Letter.pdf", "letters/app.md"])

    def test_a_relative_output_is_refused(self):
        # Breaks if outputs inside the current folder are written, as before.
        code, err = self.run_main("out/")
        self.assertNotEqual(code, 0)
        self.assertIn("current folder", err)
        self.assertEqual(self.written(), ["letters/app.md"])

    def test_an_output_beside_the_source_is_refused(self):
        # Breaks if outputs inside the application file's folder are written.
        code, err = self.run_main(str(self.work / "letters" / "sent") + "/")
        self.assertNotEqual(code, 0)
        self.assertIn("application file's folder", err)
        self.assertEqual(self.written(), ["letters/app.md"])


    def test_a_differently_cased_source_folder_is_refused(self):
        # Breaks if the folders are compared as strings: on a case-insensitive
        # disk <work>/LETTERS is the source's folder under another spelling.
        upper = self.work / "LETTERS"
        if not upper.exists():
            self.skipTest("the temp filesystem is case-sensitive, so LETTERS is another folder")
        code, err = self.run_main(str(upper / "letter.pdf"))
        self.assertNotEqual(code, 0)
        self.assertIn("application file's folder", err)
        self.assertEqual(self.written(), ["letters/app.md"])

    def test_a_draft_cannot_write_into_the_folder_above_drafts(self):
        # Breaks if only the draft's own folder is guarded: drafts/ sits inside
        # the content folder, which must stay free of PDFs too.
        (self.work / "letters" / "drafts").mkdir()
        self.source = self.source.rename(self.work / "letters" / "drafts" / "app.md")
        code, err = self.run_main(str(self.work / "letters" / "letter.pdf"))
        self.assertNotEqual(code, 0)
        self.assertIn("the folder that holds drafts/", err)
        self.assertEqual(self.written(), ["letters/drafts/app.md"])

    def test_a_name_that_climbs_into_the_source_folder_is_refused(self):
        # Breaks if the path is not resolved again after the name is joined:
        # "../letters/Alex" walks out of the send folder into the source's.
        self.source.write_text(
            "# App\n\n## Letter\n\nHi,\n\n../letters/Alex\nalex.rivera@example.com\n")
        code, err = self.run_main(str(self.work / "send") + "/")
        self.assertNotEqual(code, 0)
        self.assertIn("application file's folder", err)
        self.assertEqual(self.written(), ["letters/app.md"])

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
        (Path(work) / "letters").mkdir()
        source = Path(work) / "letters" / "app.md"
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
            self.assertEqual([path.name for path in Path(work).iterdir()], ["review-build-probe.md"])
            self.assertTrue(temp_pdf.exists())


if __name__ == "__main__":
    unittest.main()
