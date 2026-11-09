"""Tests for skills/resume/bin/check-tools and its run at the end of
bin/new-content-folder.

Each test runs a script with PATH set to one folder that holds only the
commands the scripts use plus stubs, so a tool installed on this machine
never hides a missing one. The stubs stand in for typst, pdftotext, brew
and python3; the python3 stub answers check-tools' three questions (does
it run, can it import yaml, is it externally managed) with exit codes.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
BIN = PLUGIN / "skills" / "resume" / "bin"
CHECK_TOOLS = BIN / "check-tools"
NEW_FOLDER = BIN / "new-content-folder"
REAL_COMMANDS = ("bash", "dirname", "ls", "mkdir", "cp")
HOMEBREW_INSTALL = "curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
PRESENT = "exit 0"


def python_stub(runs=True, has_yaml=False, managed=False):
    """A python3 stub: exit 0 means yes to the question its -c asks."""
    if not runs:
        return "exit 1"
    return ('case "$*" in\n'
            f'  *EXTERNALLY-MANAGED*) exit {0 if managed else 1} ;;\n'
            f'  *yaml*) exit {0 if has_yaml else 1} ;;\n'
            '  *) exit 0 ;;\n'
            'esac')


def command_folder(work, stubs):
    """A folder of links to REAL_COMMANDS plus one script per stub."""
    folder = Path(work) / "bin"
    folder.mkdir()
    for name in REAL_COMMANDS:
        (folder / name).symlink_to(shutil.which(name))
    for name, body in stubs.items():
        path = folder / name
        path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        path.chmod(0o755)
    return folder


def run(script, work, stubs, *arguments):
    folder = command_folder(work, stubs)
    return subprocess.run([str(script), *arguments], env={"PATH": str(folder)},
                          capture_output=True, text=True)


ALL_MISSING = {"python3": python_stub()}
ALL_PRESENT = {"typst": PRESENT, "pdftotext": PRESENT, "brew": PRESENT,
               "python3": python_stub(has_yaml=True)}


class CheckToolsTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.work = work.name

    def check(self, stubs):
        return run(CHECK_TOOLS, self.work, stubs)

    def test_a_bare_mac_gets_every_install_command(self):
        result = self.check(ALL_MISSING)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Missing tools", result.stdout)
        for expected in (HOMEBREW_INSTALL,
                         "- typst: brew install typst",
                         "- pdftotext: brew install poppler",
                         "- PyYAML: python3 -m pip install --user pyyaml"):
            self.assertIn(expected, result.stdout)

    def test_homebrew_comes_before_the_tools_it_installs(self):
        stdout = self.check(ALL_MISSING).stdout
        self.assertLess(stdout.index(HOMEBREW_INSTALL), stdout.index("brew install typst"))

    def test_homebrew_is_not_offered_when_brew_is_there(self):
        result = self.check({"brew": PRESENT, "pdftotext": PRESENT,
                             "python3": python_stub(has_yaml=True)})
        self.assertEqual(result.returncode, 1)
        self.assertIn("- typst: brew install typst", result.stdout)
        self.assertNotIn(HOMEBREW_INSTALL, result.stdout)
        self.assertNotIn("pdftotext", result.stdout)
        self.assertNotIn("PyYAML", result.stdout)

    def test_homebrew_is_not_offered_when_only_pyyaml_is_missing(self):
        result = self.check({"typst": PRESENT, "pdftotext": PRESENT,
                             "python3": python_stub()})
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(HOMEBREW_INSTALL, result.stdout)
        self.assertIn("- PyYAML: python3 -m pip install --user pyyaml", result.stdout)

    def test_an_externally_managed_python_gets_a_pip_command_it_accepts(self):
        result = self.check({"typst": PRESENT, "pdftotext": PRESENT,
                             "python3": python_stub(managed=True)})
        self.assertIn("- PyYAML: python3 -m pip install --user --break-system-packages pyyaml",
                      result.stdout)

    def test_a_python3_that_does_not_run_is_reported(self):
        result = self.check({"typst": PRESENT, "pdftotext": PRESENT,
                             "python3": python_stub(runs=False)})
        self.assertEqual(result.returncode, 1)
        self.assertIn("- python3: xcode-select --install", result.stdout)
        self.assertIn("- PyYAML, after python3: python3 -m pip install --user pyyaml",
                      result.stdout)

    def test_no_python3_on_the_path_is_reported(self):
        result = self.check({"typst": PRESENT, "pdftotext": PRESENT})
        self.assertIn("- python3: xcode-select --install", result.stdout)

    def test_everything_present_says_so(self):
        result = self.check(ALL_PRESENT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout,
                         "All tools found: typst, pdftotext, python3 with PyYAML.\n")


class NewContentFolderTests(unittest.TestCase):
    def test_setup_names_the_missing_tools_and_still_creates_the_folder(self):
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work) / "dana"
            result = run(NEW_FOLDER, work, ALL_MISSING, str(folder))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((folder / "resume-v1.yaml").is_file())
            self.assertIn("Missing tools", result.stdout)
            self.assertIn("- typst: brew install typst", result.stdout)
            self.assertIn("- PyYAML: python3 -m pip install --user pyyaml", result.stdout)

    def test_setup_with_every_tool_says_so(self):
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work) / "dana"
            result = run(NEW_FOLDER, work, ALL_PRESENT, str(folder))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("All tools found", result.stdout)


if __name__ == "__main__":
    unittest.main()
