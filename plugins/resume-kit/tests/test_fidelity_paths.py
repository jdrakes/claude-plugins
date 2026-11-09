"""The renderer scripts must find their inputs from their own location.

An earlier version of `check-fidelity.sh` anchored its inputs at a fixed
absolute path built from `$HOME`. That path is correct on exactly one
machine: a CI runner checks the repository out somewhere else entirely, with
`$HOME` set to something like `/root`, and the check failed with
"fixture ... missing" before it ever compiled anything. The first test pins
that fix.

The other two pin the `-P` in `cd -P "$(dirname "$0")/.."`, in
`tools/check-fidelity.sh` and in `bin/build`. Physical and logical
resolution disagree only when a symlink sits at or below the directory being
walked out of, so each of those tests builds a holder directory whose single
entry is a symlink to the real `tools/` or `bin/`. Logical `..` lands in the
holder, which has no template, fixture or font in it, and the script fails;
physical `..` lands in the skill directory and it works. Symlinking the
whole skill directory instead, which is what this file used to do,
distinguishes nothing: logical `..` climbs back through that link to the
same directory the physical walk reaches, so both scripts passed with `-P`
removed.

Only the path tests were carried over from the renderer's original suite.
The rest covered a golden-reference comparison script, deleted along with
the fixture it pointed at when the snapshot test replaced it.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(PLUGIN_ROOT, "skills", "resume")
CHECK_FIDELITY_PATH = os.path.join(SKILL_DIR, "tools", "check-fidelity.sh")
SAMPLE_RESUME = os.path.join(SKILL_DIR, "examples", "sample-resume.yaml")


@unittest.skipUnless(shutil.which("typst") and shutil.which("pdftotext"),
                     "needs typst and pdftotext")
class SkillDirResolutionTests(unittest.TestCase):
    def _run(self, argv, env_home):
        env = dict(os.environ, HOME=env_home)
        return subprocess.run(argv, capture_output=True, text=True, env=env)

    def _assert_check_fidelity_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("PASS:", result.stdout)

    def _holder_with_symlink(self, tmp, name):
        """A directory whose only entry is a symlink to <name> in the real
        skill directory."""
        holder = os.path.join(tmp, "holder")
        os.mkdir(holder)
        os.symlink(os.path.join(SKILL_DIR, name), os.path.join(holder, name))
        return holder

    def test_check_fidelity_passes_with_an_unrelated_home(self):
        with tempfile.TemporaryDirectory() as fake_home:
            result = self._run([CHECK_FIDELITY_PATH], fake_home)
        self._assert_check_fidelity_ok(result)

    def test_check_fidelity_resolves_through_a_symlinked_tools_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            holder = self._holder_with_symlink(tmp, "tools")
            script = os.path.join(holder, "tools", "check-fidelity.sh")
            result = self._run([script], tmp)
        self._assert_check_fidelity_ok(result)

    def test_build_resolves_through_a_symlinked_bin_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            holder = self._holder_with_symlink(tmp, "bin")
            output = os.path.join(tmp, "sample-resume.pdf")
            script = os.path.join(holder, "bin", "build")
            result = self._run([script, SAMPLE_RESUME, "-o", output], tmp)
            built = os.path.exists(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(built, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
