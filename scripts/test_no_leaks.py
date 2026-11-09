#!/usr/bin/env python3
"""Scan skills/, agents/, docs/, evals/, evals2/ and tests/ for leaked
private references.

Real run:  python3 scripts/test_no_leaks.py
Self-test: python3 scripts/test_no_leaks.py --self-test
"""
import io
import os
import subprocess
import shutil
import sys
import tempfile
from pathlib import Path

# Matching is case-insensitive and substring-based. Case-insensitive because
# a lowercase "james" or "drakes" is the same leak as a capitalised one and
# used to pass; one uniform rule beats a second list of identity-only
# strings. Measured before the switch: every string below, matched
# case-insensitively over all 117 publishable files in the scan set, returns
# exactly the hits it returned case-sensitively, so nothing already written
# breaks.
#
# Two false-positive risks are worth knowing about, both widened slightly by
# the case fold. One needle is also an ordinary English word, and its
# lowercase form now matches too. "job_search" will not
# fire on the phrase "job search", but "job-search-archive" would fire on any
# future prose naming a job-search archive that means something else.
# "James_Drakes" is deliberately absent: it contains "James", which already
# matches.
LEAK_STRINGS = [
    "James",
    "jdrakes",
    "~/workspace",
    "knowledge-base",
    "jamesdrakes.com",
    "Drakes",
    "H-E-B",
    "Spruce",
    "IdealSpot",
    "job-search-archive",
    "job_search",
    "james-drakes",
    "resumeio-",
    "claude-config",
    "$HOME/workspace",
    "974d05a",
    "superpowers",
]
PRIVATE_NEEDLES_VARIABLE = "LEAK_NEEDLES_FILE"
SCAN_DIR_NAMES = {"skills", "agents", "docs", "evals", "evals2", "tests"}
EXCLUDED_DIR_NAMES = {".claude-plugin", "scripts", ".git"}


def find_scan_roots(repo_root):
    """Find every directory named skills/agents/docs/evals/evals2/tests
    anywhere under repo_root, without descending into excluded
    directories."""
    roots = []
    for dirpath, dirnames, _ in os.walk(repo_root):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIR_NAMES]
        if os.path.basename(dirpath) in SCAN_DIR_NAMES:
            roots.append(dirpath)
    return roots


def scan_file(path, needles):
    """Return a list of (line_number, needle) hits in one file."""
    hits = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                lowered = line.lower()
                for needle in needles:
                    if needle.lower() in lowered:
                        hits.append((line_number, needle))
    except (IsADirectoryError, PermissionError):
        pass
    return hits


def publishable_files(repo_root):
    """Relative paths of the files that could reach the published repo:
    tracked, plus untracked ones git is not ignoring. Walking the
    filesystem instead fails on run artifacts that are ignored and never
    ship, and a scanner that cries wolf on its own eval output gets turned
    off. Outside a git checkout, fall back to walking."""
    try:
        listing = subprocess.run(
            ["git", "-C", repo_root, "ls-files", "--cached", "--others",
             "--exclude-standard"],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [line for line in listing if line]


def scan_repo(repo_root, needles):
    """Return a list of (relative_path, line_number, needle) hits under
    repo_root's skills/, agents/, docs/, evals/, evals2/ and tests/
    directories.

    The repository's own README.md is never scanned: nothing above it is a
    scan directory, so it is the one file allowed to name the author. A
    README nested under a scan directory is content and is scanned."""
    all_hits = []
    candidates = publishable_files(repo_root)
    if candidates is not None:
        for relative_path in sorted(candidates):
            parts = relative_path.split(os.sep)
            if not any(part in SCAN_DIR_NAMES for part in parts[:-1]):
                continue
            if any(part in EXCLUDED_DIR_NAMES for part in parts[:-1]):
                continue
            for line_number, needle in scan_file(os.path.join(repo_root, relative_path), needles):
                all_hits.append((relative_path, line_number, needle))
        return all_hits
    for scan_root in find_scan_roots(repo_root):
        for dirpath, dirnames, filenames in os.walk(scan_root):
            dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIR_NAMES]
            for filename in sorted(filenames):
                file_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(file_path, repo_root)
                for line_number, needle in scan_file(file_path, needles):
                    all_hits.append((relative_path, line_number, needle))
    return all_hits


def run_scan(repo_root, needles):
    hits = scan_repo(repo_root, needles)
    for relative_path, line_number, needle in hits:
        print(f"{relative_path}:{line_number}: {needle}")
    return 1 if hits else 0


def parse_needles(text):
    """One needle per line; blank lines and lines starting with # are ignored."""
    needles = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            needles.append(stripped)
    return needles


def read_private_needles(environment):
    """Return (needles, error). needles is None when LEAK_NEEDLES_FILE is
    unset; error is a message when it is set but cannot be read, is not
    UTF-8, or holds no needles (a scan that checks nothing must not pass)."""
    path = environment.get(PRIVATE_NEEDLES_VARIABLE)
    if not path:
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            needles = parse_needles(handle.read())
    except (OSError, UnicodeDecodeError) as problem:
        return None, f"{PRIVATE_NEEDLES_VARIABLE} is set but unreadable: {problem}"
    if not needles:
        return None, f"{PRIVATE_NEEDLES_VARIABLE} is set but the file has no needles: {path}"
    return needles, None


def run_checked_scan(repo_root, environment):
    """Scan with the public list plus the private file, if one is named."""
    private_needles, error = read_private_needles(environment)
    if error:
        print(error)
        return 1
    if private_needles is None:
        print(f"{PRIVATE_NEEDLES_VARIABLE} not set: private needle list not checked")
        return run_scan(repo_root, LEAK_STRINGS)
    return run_scan(repo_root, LEAK_STRINGS + private_needles)


def capture_stdout(function, *arguments):
    captured = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured
    try:
        result = function(*arguments)
    finally:
        sys.stdout = original_stdout
    return result, captured.getvalue()


def run_private_needles_self_test():
    """Invented needles only. Saves and restores the caller's variable so the
    suite passes whether or not it is set."""
    temp_dir = tempfile.mkdtemp(prefix="test_no_leaks_private_")
    saved = os.environ.get(PRIVATE_NEEDLES_VARIABLE)
    try:
        clean_root = os.path.join(temp_dir, "clean")
        planted_root = os.path.join(temp_dir, "planted")
        for root, text in [(clean_root, "Nothing private here.\n"),
                           (planted_root, "The zorblaxquent is mentioned here.\n")]:
            os.makedirs(os.path.join(root, "skills", "example"))
            with open(os.path.join(root, "skills", "example", "note.md"), "w",
                      encoding="utf-8") as handle:
                handle.write(text)
        needle_path = os.path.join(temp_dir, "needles.txt")
        with open(needle_path, "w", encoding="utf-8") as handle:
            handle.write("# a comment naming plimbrotack\n\n  \nzorblaxquent\n")

        os.environ[PRIVATE_NEEDLES_VARIABLE] = needle_path
        code, output = capture_stdout(run_checked_scan, planted_root, os.environ)
        assert code == 1, f"planted needle: expected exit 1, got {code}"
        assert "skills/example/note.md:1: zorblaxquent".replace("/", os.sep) in output, (
            f"planted needle: hit not printed, got: {output!r}"
        )
        assert "not checked" not in output, f"file was read, got: {output!r}"

        code, output = capture_stdout(run_checked_scan, clean_root, os.environ)
        assert code == 0, f"clean repo with needle file: expected exit 0, got {code}"

        # Comment and blank lines are not needles: a comment's words must not hit.
        with open(os.path.join(clean_root, "skills", "example", "note.md"), "w",
                  encoding="utf-8") as handle:
            handle.write("plimbrotack appears here, and so does a blank-ish line.\n")
        code, output = capture_stdout(run_checked_scan, clean_root, os.environ)
        assert code == 0, f"comment text must not be a needle, got: {output!r}"
        # The scan above passes even without the # filter, because the whole
        # comment line is not a substring of the planted text. This pins it.
        parsed = parse_needles("# x\n\n  \ny\n")
        assert parsed == ["y"], f"comment and blank lines must be dropped, got: {parsed!r}"

        undecodable_path = os.path.join(temp_dir, "undecodable.txt")
        with open(undecodable_path, "wb") as handle:
            handle.write(b"zorblaxquent\n\xff\n")
        os.environ[PRIVATE_NEEDLES_VARIABLE] = undecodable_path
        code, output = capture_stdout(run_checked_scan, clean_root, os.environ)
        assert code == 1, f"non-UTF-8 file: expected exit 1, got {code}"
        assert PRIVATE_NEEDLES_VARIABLE in output, (
            f"non-UTF-8 file: message must name the variable, got: {output!r}"
        )

        for label, text in [("empty", ""), ("comments only", "# only a comment\n\n")]:
            empty_path = os.path.join(temp_dir, "empty.txt")
            with open(empty_path, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.environ[PRIVATE_NEEDLES_VARIABLE] = empty_path
            code, output = capture_stdout(run_checked_scan, clean_root, os.environ)
            assert code == 1, f"{label} needle file: expected exit 1, got {code}"
            assert PRIVATE_NEEDLES_VARIABLE in output and "no needles" in output, (
                f"{label} needle file: message must name the variable and say "
                f"it has no needles, got: {output!r}"
            )

        os.environ[PRIVATE_NEEDLES_VARIABLE] = os.path.join(temp_dir, "missing.txt")
        code, output = capture_stdout(run_checked_scan, clean_root, os.environ)
        assert code == 1, f"missing file: expected exit 1, got {code}"
        assert PRIVATE_NEEDLES_VARIABLE in output, (
            f"missing file: message must name the variable, got: {output!r}"
        )

        del os.environ[PRIVATE_NEEDLES_VARIABLE]
        code, output = capture_stdout(run_checked_scan, clean_root, os.environ)
        assert code == 0, f"unset, clean repo: expected exit 0, got {code}"
        assert "not checked" in output, f"unset: expected not-checked line, got: {output!r}"
        code, output = capture_stdout(run_checked_scan, planted_root, os.environ)
        assert code == 0, f"unset: private needle must not be scanned, got: {output!r}"
    finally:
        if saved is None:
            os.environ.pop(PRIVATE_NEEDLES_VARIABLE, None)
        else:
            os.environ[PRIVATE_NEEDLES_VARIABLE] = saved
        shutil.rmtree(temp_dir)


def run_self_test():
    temp_dir = tempfile.mkdtemp(prefix="test_no_leaks_")
    try:
        skills_dir = os.path.join(temp_dir, "skills", "example")
        os.makedirs(skills_dir)
        clean_path = os.path.join(skills_dir, "clean.md")
        bad_path = os.path.join(skills_dir, "bad.md")
        with open(clean_path, "w", encoding="utf-8") as handle:
            handle.write("This file has no private references.\n")
        with open(bad_path, "w", encoding="utf-8") as handle:
            handle.write("This file mentions jdrakes by name.\n")

        case_dir = os.path.join(temp_dir, "evals2", "some-case")
        os.makedirs(case_dir)
        prompt_path = os.path.join(case_dir, "prompt.md")
        with open(prompt_path, "w", encoding="utf-8") as handle:
            handle.write("A written prompt that names jdrakes.\n")

        nested_readme = os.path.join(case_dir, "README.md")
        with open(nested_readme, "w", encoding="utf-8") as handle:
            handle.write("This nested README names jdrakes.\n")

        # Pins that tests/ is a scan directory and that each string below is
        # on the list: every assertion names its own needle, so dropping that
        # string from LEAK_STRINGS drops exactly that expected line. A line
        # may report more than one needle ("james-drakes" reports three under
        # the case fold), which the presence assertions tolerate.
        #
        # The last line is the case-fold pin: written in lowercase, it must
        # still be reported under the capitalised needles "James" and
        # "Drakes". Case-sensitive matching leaves it silent, which is how a
        # private path reached a published file once already.
        leaky_dir = os.path.join(temp_dir, "tests")
        os.makedirs(leaky_dir)
        with open(os.path.join(leaky_dir, "leaky.md"), "w", encoding="utf-8") as handle:
            handle.write(
                "Drakes\n"
                "H-E-B\n"
                "Spruce\n"
                "IdealSpot\n"
                "job-search-archive\n"
                "job_search\n"
                "james-drakes\n"
                "resumeio-\n"
                "claude-config\n"
                "$HOME/workspace\n"
                "974d05a\n"
                "superpowers\n"
                "written by james drakes in lowercase\n"
            )

        captured = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured
        try:
            exit_code = run_scan(temp_dir, LEAK_STRINGS)
        finally:
            sys.stdout = original_stdout

        output = captured.getvalue()
        assert exit_code == 1, f"expected exit 1, got {exit_code}"
        assert "bad.md" in output, f"expected bad.md named in output, got: {output!r}"
        assert "clean.md" not in output, f"expected clean.md absent, got: {output!r}"
        assert "prompt.md" in output, f"expected evals2 scanned, got: {output!r}"
        assert os.path.join("evals2", "some-case", "README.md") in output, (
            f"a README nested under a scan directory must be scanned, got: {output!r}"
        )
        leaky_relative = os.path.join("tests", "leaky.md")
        for line_number, needle in [
            (1, "Drakes"),
            (2, "H-E-B"),
            (3, "Spruce"),
            (4, "IdealSpot"),
            (5, "job-search-archive"),
            (6, "job_search"),
            (7, "james-drakes"),
            (8, "resumeio-"),
            (9, "claude-config"),
            (10, "$HOME/workspace"),
            (11, "974d05a"),
            (12, "superpowers"),
            (13, "James"),
            (13, "Drakes"),
        ]:
            expected_line = f"{leaky_relative}:{line_number}: {needle}"
            assert expected_line in output, (
                f"expected {expected_line!r} in output, got: {output!r}"
            )
        run_git_self_test()
        run_private_needles_self_test()
        print("self-test passed")
        return 0
    finally:
        shutil.rmtree(temp_dir)


def run_git_self_test():
    """The bug this catches: scanning the filesystem rather than what git
    would publish, so an ignored run artifact holding a machine path fails
    the build. A scanner that cries wolf on its own eval output gets turned
    off. Here the ignored file leaks and must be skipped; the tracked one
    leaks and must be caught. It also pins the README rule: the repository
    root README.md is the one file allowed to name the author, while a
    README nested under a scan directory is content and is scanned."""
    temp_dir = tempfile.mkdtemp(prefix="test_no_leaks_git_")
    try:
        subprocess.run(["git", "init", "-q", temp_dir], check=True)
        skills_dir = os.path.join(temp_dir, "skills", "example")
        results_dir = os.path.join(temp_dir, "skills", "example", "results")
        os.makedirs(results_dir)
        with open(os.path.join(temp_dir, ".gitignore"), "w", encoding="utf-8") as handle:
            handle.write("**/results/\n")
        with open(os.path.join(results_dir, "run.json"), "w", encoding="utf-8") as handle:
            handle.write('{"root": "/Users/jdrakes/somewhere"}\n')
        with open(os.path.join(skills_dir, "tracked.md"), "w", encoding="utf-8") as handle:
            handle.write("This one mentions jdrakes and is not ignored.\n")
        with open(os.path.join(skills_dir, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("This nested README mentions jdrakes.\n")
        with open(os.path.join(temp_dir, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("The root README names James, which is allowed.\n")

        captured = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = captured
        try:
            exit_code = run_scan(temp_dir, LEAK_STRINGS)
        finally:
            sys.stdout = original_stdout

        output = captured.getvalue()
        assert exit_code == 1, f"expected exit 1, got {exit_code}"
        assert "tracked.md" in output, f"expected tracked.md named, got: {output!r}"
        assert "run.json" not in output, f"ignored file must be skipped, got: {output!r}"
        assert os.path.join("skills", "example", "README.md") in output, (
            f"a README nested under a scan directory must be scanned, got: {output!r}"
        )
        assert "\nREADME.md" not in "\n" + output, (
            f"the root README.md must stay exempt, got: {output!r}"
        )
    finally:
        shutil.rmtree(temp_dir)


def main():
    if "--self-test" in sys.argv:
        sys.exit(run_self_test())
    repo_root = Path(__file__).resolve().parent.parent
    sys.exit(run_checked_scan(str(repo_root), os.environ))


if __name__ == "__main__":
    main()
