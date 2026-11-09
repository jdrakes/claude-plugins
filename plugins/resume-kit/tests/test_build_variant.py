"""Tests for skills/resume/bin/build-variant.

A variant is a subtractive overlay on a content file: it removes entries
from the flat-list sections and then proves, against the rendered PDF text,
that named strings are gone. These tests protect the filtering rules, where
`base:` is looked up, where the PDF is written, and that a failed absent
check writes nothing.

typst and pdftotext are replaced by stubs on PATH, so the script runs on any
machine. The pdftotext stub prints the file named by PDFTOTEXT_STUB_TEXT, so
each test chooses the "rendered" text.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "resume" / "bin" / "build-variant"
loader = importlib.machinery.SourceFileLoader("build_variant", str(SCRIPT))
spec = importlib.util.spec_from_loader("build_variant", loader)
build_variant = importlib.util.module_from_spec(spec)
loader.exec_module(build_variant)

PHONE = "tel:5550142"
EMAIL = "mailto:alex@example.com"
CODE = "https://example.com/code"


def details():
    return {"details": ["Portland", {"text": "(555) 0142", "link": PHONE},
                        {"text": "alex@example.com", "link": EMAIL}]}


class MatchesTests(unittest.TestCase):
    def test_string_entry_without_the_pattern_does_not_match(self):
        self.assertFalse(build_variant.matches("Portland", ["Seattle"]))

    def test_string_entry_with_the_pattern_matches(self):
        self.assertTrue(build_variant.matches("Portland", ["Port"]))

    def test_dict_entry_matches_by_its_link_not_only_its_text(self):
        # Breaks if matches looks only at the text: the phone is omitted by
        # its link, which the reader never sees.
        self.assertTrue(build_variant.matches({"text": "Phone", "link": PHONE}, ["tel:"]))


class ResolveTests(unittest.TestCase):
    def test_omit_removes_the_matching_entry_only(self):
        result, error = build_variant.resolve(details(), {"details": ["tel:"]})
        self.assertIsNone(error)
        self.assertEqual(result["details"],
                         ["Portland", {"text": "alex@example.com", "link": EMAIL}])

    def test_no_match_keeps_every_entry(self):
        result, error = build_variant.resolve(details(), {"details": ["nonexistent"]})
        self.assertIsNone(error)
        self.assertEqual(result["details"], details()["details"])

    def test_a_section_absent_from_the_content_stays_absent(self):
        # Breaks if an omitted absent section becomes an empty list, which
        # would render an empty heading.
        result, error = build_variant.resolve(details(), {"hobbies": ["x"]})
        self.assertIsNone(error)
        self.assertNotIn("hobbies", result)

    def test_an_unsupported_section_is_an_error_naming_it_and_the_allowed_ones(self):
        result, error = build_variant.resolve(details(), {"experience": ["x"]})
        self.assertIsNone(result)
        self.assertIn("experience", error)
        self.assertIn("details, hobbies, links, skills", error)

    def test_a_section_that_is_not_a_list_is_an_error_naming_its_type(self):
        # Breaks if a string section is iterated character by character.
        result, error = build_variant.resolve({"details": "oops"}, {"details": ["x"]})
        self.assertIsNone(result)
        self.assertIn("details", error)
        self.assertIn("str", error)

    def test_an_entry_of_another_type_is_an_error_naming_the_type(self):
        result, error = build_variant.resolve({"skills": ["Python", 123]}, {"skills": ["x"]})
        self.assertIsNone(result)
        self.assertIn("int", error)

    def test_a_dict_entry_with_a_non_string_value_is_an_error_naming_the_key(self):
        result, error = build_variant.resolve(
            {"skills": [{"text": "Python", "years": 5}]}, {"skills": ["x"]})
        self.assertIsNone(result)
        self.assertIn("years", error)

    def test_filters_links(self):
        content = {"links": [{"text": "Code", "link": CODE},
                             {"text": "Portfolio", "link": "https://example.com"}]}
        result, error = build_variant.resolve(content, {"links": ["/code"]})
        self.assertIsNone(error)
        self.assertEqual(result["links"], [{"text": "Portfolio", "link": "https://example.com"}])

    def test_filters_skills(self):
        result, error = build_variant.resolve({"skills": ["Python", "Vue.js", "Typst"]},
                                              {"skills": ["Vue"]})
        self.assertIsNone(error)
        self.assertEqual(result["skills"], ["Python", "Typst"])

    def test_does_not_mutate_the_input(self):
        # Breaks if resolve filters the list in place.
        content = details()
        original_list = content["details"]
        first, _ = build_variant.resolve(content, {"details": ["tel:"]})
        first_copy = list(first["details"])
        second, _ = build_variant.resolve(content, {"details": ["tel:", "mailto:", "Portland"]})
        self.assertIs(content["details"], original_list)
        self.assertEqual(content["details"], details()["details"])
        self.assertEqual(first["details"], first_copy)
        self.assertEqual(second["details"], [])


class ContentFolderTests(unittest.TestCase):
    def test_is_the_folder_above_variants(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work).resolve()
            self.assertEqual(build_variant.content_folder(root / "variants" / "web.yaml"), root)


class LoadVariantTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.folder = Path(work.name).resolve()
        (self.folder / "variants").mkdir()
        self.variant = self.folder / "variants" / "web.yaml"

    def write_variant(self, spec):
        self.variant.write_text(yaml.safe_dump(spec), encoding="utf-8")

    def write_base(self, content):
        (self.folder / "base.yaml").write_text(yaml.safe_dump(content), encoding="utf-8")

    def test_a_missing_base_file_is_an_error_naming_the_resolved_path(self):
        self.write_variant({"base": "does-not-exist.yaml"})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn(str(self.folder / "does-not-exist.yaml"), error)

    def test_a_missing_base_key_is_an_error_naming_the_variant(self):
        self.write_variant({"omit": {}})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn(str(self.variant), error)
        self.assertIn("base", error)

    def test_a_variant_that_is_not_a_mapping_is_an_error(self):
        self.write_variant(["not", "a", "mapping"])
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn(str(self.variant), error)
        self.assertIn("base", error)

    def test_invalid_yaml_is_an_error_naming_the_variant(self):
        self.variant.write_text("base: [unclosed\n", encoding="utf-8")
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn(str(self.variant), error)

    def test_a_base_that_is_not_a_string_is_an_error(self):
        self.write_variant({"base": 7})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn("base", error)

    def test_an_absolute_base_is_an_error(self):
        # Breaks if the join is trusted: joining an absolute path discards
        # the content folder and loads an unrelated file.
        self.write_variant({"base": "/etc/hosts"})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn(str(self.variant), error)
        self.assertIn("base", error)

    def test_a_base_that_is_not_a_mapping_is_an_error(self):
        (self.folder / "base.yaml").write_text("- a\n- b\n", encoding="utf-8")
        self.write_variant({"base": "base.yaml"})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    def test_omit_that_is_not_a_mapping_of_string_lists_is_an_error(self):
        self.write_base(details())
        for omit in (["details"], {"details": "tel:"}, {"details": [5]}):
            with self.subTest(omit=omit):
                self.write_variant({"base": "base.yaml", "omit": omit})
                result, error = build_variant.load_variant(self.variant)
                self.assertIsNone(result)
                self.assertIn("omit", error)

    def test_an_explicit_null_omit_counts_as_absent(self):
        self.write_base(details())
        self.write_variant({"base": "base.yaml", "omit": None})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(error)
        self.assertEqual(result["content"], details())

    def test_an_explicit_null_assert_absent_counts_as_absent(self):
        self.write_base(details())
        self.write_variant({"base": "base.yaml", "assert_absent": None})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(error)
        self.assertEqual(result["assert_absent"], [])

    def test_assert_absent_that_is_not_a_list_is_an_error(self):
        # Breaks if a bare string is accepted: it would be checked
        # character by character and fail almost every build.
        self.write_base(details())
        self.write_variant({"base": "base.yaml", "assert_absent": "(555) 0142"})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn(str(self.variant), error)

    def test_an_error_from_resolve_is_returned(self):
        self.write_base(details())
        self.write_variant({"base": "base.yaml", "omit": {"experience": ["x"]}})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(result)
        self.assertIn("experience", error)

    def test_a_valid_variant_returns_the_resolved_content(self):
        self.write_base({**details(), "summary": "Unaffected prose."})
        self.write_variant({"base": "base.yaml", "omit": {"details": ["tel:"]},
                            "assert_absent": ["(555) 0142"]})
        result, error = build_variant.load_variant(self.variant)
        self.assertIsNone(error)
        self.assertEqual(result, {
            "content": {"details": ["Portland", {"text": "alex@example.com", "link": EMAIL}],
                        "summary": "Unaffected prose."},
            "assert_absent": ["(555) 0142"],
            "content_folder": self.folder,
        })


class PlaceOutputTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name).resolve()
        self.folder = self.work / "content"
        self.folder.mkdir()
        self.elsewhere = self.work / "elsewhere"
        self.elsewhere.mkdir()

    def test_a_yaml_path_is_refused(self):
        path, error = build_variant.place_output(self.elsewhere, "resume.yaml", self.folder)
        self.assertIsNone(path)
        self.assertIn("refusing to write output over a .yaml file", error)

    def test_a_trailing_slash_is_refused(self):
        path, error = build_variant.place_output(self.elsewhere, "out/", self.folder)
        self.assertIsNone(path)
        self.assertIn("-o a file path", error)

    def test_an_existing_folder_is_refused(self):
        path, error = build_variant.place_output(self.work, "elsewhere", self.folder)
        self.assertIsNone(path)
        self.assertIn("-o a file path", error)

    def test_a_path_inside_the_content_folder_is_refused(self):
        path, error = build_variant.place_output(self.elsewhere, str(self.folder / "x.pdf"),
                                                 self.folder)
        self.assertIsNone(path)
        self.assertIn(f"it is inside the content folder, {self.folder}", error)

    def test_a_relative_path_resolves_against_the_current_folder(self):
        # Breaks if the current folder is refused, as build does: the
        # website build runs from its own repo with a relative -o.
        path, error = build_variant.place_output(self.elsewhere, "public/resume.pdf",
                                                 self.folder)
        self.assertIsNone(error)
        self.assertEqual(path, self.elsewhere / "public" / "resume.pdf")

    def test_a_leading_tilde_expands_against_home(self):
        home = self.work / "home"
        home.mkdir()
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            path, error = build_variant.place_output(self.elsewhere, "~/out.pdf", self.folder)
        self.assertIsNone(error)
        self.assertEqual(path, home / "out.pdf")


class AbsentFailuresTests(unittest.TestCase):
    def test_returns_only_the_strings_present_in_order(self):
        text = "Alex Rivera\nPortland\n(555) 0142\n"
        self.assertEqual(
            build_variant.absent_failures(text, ["(555) 0142", "example.com/code", "Portland"]),
            ["(555) 0142", "Portland"])

    def test_nothing_forbidden_is_no_failure(self):
        self.assertEqual(build_variant.absent_failures("anything", []), [])


class ScriptTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = Path(work.name).resolve()
        self.stubs = self.work / "stubs"
        self.stubs.mkdir()
        self.write_stub("typst", 'for last; do :; done\nprintf stub > "$last"\n')
        self.write_stub("pdftotext", 'cat "$PDFTOTEXT_STUB_TEXT"\n')
        self.temp_folder = self.work / "temp"
        self.temp_folder.mkdir()
        self.home = self.work / "home"
        self.home.mkdir()
        self.folder = self.work / "content"
        (self.folder / "variants").mkdir(parents=True)
        (self.folder / "base.yaml").write_text(yaml.safe_dump({"name": "Alex Rivera", **details()}),
                                               encoding="utf-8")
        self.variant = self.folder / "variants" / "web.yaml"
        self.variant.write_text(yaml.safe_dump({
            "base": "base.yaml", "omit": {"details": ["tel:"]},
            "assert_absent": ["(555) 0142"]}), encoding="utf-8")
        self.elsewhere = self.work / "elsewhere"
        self.elsewhere.mkdir()
        self.rendered_text = self.work / "rendered.txt"
        self.environment = {
            **os.environ,
            "PATH": f"{self.stubs}{os.pathsep}{os.environ['PATH']}",
            "TMPDIR": f"{self.temp_folder}/",
            "HOME": str(self.home),
            "PDFTOTEXT_STUB_TEXT": str(self.rendered_text),
        }

    def write_stub(self, name, body):
        stub = self.stubs / name
        stub.write_text(f"#!/usr/bin/env bash\n{body}", encoding="utf-8")
        stub.chmod(0o755)

    def run_script(self, *arguments):
        return subprocess.run([str(SCRIPT), str(self.variant), *arguments],
                              cwd=self.elsewhere, env=self.environment,
                              capture_output=True, text=True)

    def content_files(self):
        return sorted(str(path.relative_to(self.folder)) for path in self.folder.rglob("*"))

    def test_a_pass_writes_the_output(self):
        self.rendered_text.write_text("Alex Rivera\nPortland\n", encoding="utf-8")
        result = self.run_script("-o", "public/resume.pdf")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = self.elsewhere / "public" / "resume.pdf"
        self.assertEqual(output.read_text(encoding="utf-8"), "stub")
        self.assertEqual(result.stdout,
                         f"assert_absent: 1 check(s) passed\nbuilt {output}\n")
        self.assertEqual(self.content_files(), ["base.yaml", "variants", "variants/web.yaml"])

    def test_a_forbidden_string_in_the_text_fails_and_writes_nothing(self):
        # Breaks if the PDF is copied before the check, leaving a PDF that
        # still holds what it was meant to omit.
        self.rendered_text.write_text("Alex Rivera\n(555) 0142\n", encoding="utf-8")
        result = self.run_script("-o", "public/resume.pdf")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL: the variant still contains: ['(555) 0142']", result.stderr)
        self.assertFalse((self.elsewhere / "public").exists())
        self.assertEqual(self.content_files(), ["base.yaml", "variants", "variants/web.yaml"])

    def test_no_output_flag_writes_to_the_temp_folder(self):
        self.rendered_text.write_text("Alex Rivera\n", encoding="utf-8")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.temp_folder / "web.pdf").is_file())
        self.assertEqual(self.content_files(), ["base.yaml", "variants", "variants/web.yaml"])

    def test_a_temp_folder_inside_the_content_folder_is_refused(self):
        # Breaks if the default output skips the content folder guard: a
        # TMPDIR inside the content folder would land the PDF there.
        self.rendered_text.write_text("Alex Rivera\n", encoding="utf-8")
        self.environment["TMPDIR"] = f"{self.folder}/"
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"it is inside the content folder, {self.folder}", result.stderr)
        self.assertEqual(self.content_files(), ["base.yaml", "variants", "variants/web.yaml"])

    def test_an_output_inside_the_content_folder_is_refused(self):
        # Breaks if main stops passing -o through place_output.
        self.rendered_text.write_text("Alex Rivera\n", encoding="utf-8")
        result = self.run_script("-o", str(self.folder / "resume.pdf"))
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"it is inside the content folder, {self.folder}", result.stderr)
        self.assertEqual(self.content_files(), ["base.yaml", "variants", "variants/web.yaml"])

    def test_a_failed_render_fails_and_writes_nothing(self):
        # Breaks if bin/build's exit code is ignored and a missing or
        # partial PDF is checked and copied.
        self.write_stub("typst", 'echo "typst stub failed" >&2\nexit 1\n')
        self.rendered_text.write_text("Alex Rivera\n", encoding="utf-8")
        result = self.run_script("-o", "public/resume.pdf")
        self.assertEqual(result.returncode, 1)
        self.assertIn("typst stub failed", result.stderr)
        self.assertFalse((self.elsewhere / "public").exists())

    def test_a_failed_text_extraction_fails_and_writes_nothing(self):
        # Breaks if pdftotext's exit code is ignored: its empty output would
        # pass every absent check.
        self.write_stub("pdftotext", 'echo "pdftotext stub failed" >&2\nexit 1\n')
        result = self.run_script("-o", "public/resume.pdf")
        self.assertEqual(result.returncode, 1)
        self.assertIn("pdftotext stub failed", result.stderr)
        self.assertFalse((self.elsewhere / "public").exists())

    def test_empty_extracted_text_fails_when_there_is_something_to_check(self):
        # Breaks if empty text is checked as it is: every forbidden string
        # would be absent from it and the check would pass vacuously.
        self.rendered_text.write_text(" \n\f\n", encoding="utf-8")
        result = self.run_script("-o", "public/resume.pdf")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no text extracted; cannot check assert_absent", result.stderr)
        self.assertFalse((self.elsewhere / "public").exists())

    def test_empty_extracted_text_passes_when_there_is_nothing_to_check(self):
        # Breaks if the empty text check runs with no assert_absent, which
        # would refuse a variant that asked for no check.
        self.variant.write_text(yaml.safe_dump({"base": "base.yaml"}), encoding="utf-8")
        self.rendered_text.write_text("", encoding="utf-8")
        result = self.run_script("-o", "public/resume.pdf")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.elsewhere / "public" / "resume.pdf").is_file())

    def test_an_unknown_flag_is_a_usage_error(self):
        result = self.run_script("--force")
        self.assertEqual(result.returncode, 1)
        self.assertIn("usage: build-variant <variant-file> [-o <output.pdf>]", result.stderr)

    def test_output_flag_without_a_value_is_a_usage_error(self):
        result = self.run_script("-o")
        self.assertEqual(result.returncode, 1)
        self.assertIn("usage: build-variant", result.stderr)


class MissingPdftotextTests(unittest.TestCase):
    def test_missing_pdftotext_fails_before_anything_is_built(self):
        # Breaks if a missing pdftotext is skipped, as check-fidelity.sh
        # does: the variant would ship unchecked.
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work).resolve()
            (folder / "variants").mkdir()
            (folder / "base.yaml").write_text(yaml.safe_dump(details()), encoding="utf-8")
            variant = folder / "variants" / "web.yaml"
            variant.write_text(yaml.safe_dump({"base": "base.yaml"}), encoding="utf-8")
            real_which = build_variant.shutil.which
            stderr = io.StringIO()
            with mock.patch.object(build_variant.shutil, "which",
                                   side_effect=lambda name: None if name == "pdftotext"
                                   else real_which(name)), \
                    mock.patch.object(build_variant.subprocess, "run",
                                      side_effect=AssertionError("subprocess.run called")), \
                    contextlib.redirect_stderr(stderr):
                code = build_variant.main([str(variant)])
        self.assertEqual(code, 1)
        self.assertIn("pdftotext not found", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
