#!/usr/bin/env python3
"""Check that a plugin's version names one set of shipped files.

Each plugin keeps a stamp, plugins/<name>/.claude-plugin/shipped.json:
{"version": "X.Y.Z", "sha256": "<hex>"}. The hash covers every shipped file.
If the files change and the version does not, this fails.

Shipped files are the plugin's files that git tracks (git ls-files, content
and executable bit read from disk), except tests/, evals/ and evals2/ at the
plugin's top level (they do not change how a plugin works) and the stamp
itself. Untracked and ignored files never count, so caches, local settings
and build output on a laptop do not fail the check. git ls-files needs no
history, so a shallow clone gives the same answer as a full one; a copy
without .git is not supported.

Check:     python3 scripts/check_versions.py
Stamp:     python3 scripts/check_versions.py --write <plugin>
Self-test: python3 scripts/check_versions.py --self-test
"""
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

TOP_LEVEL_EXCLUDED = {"tests", "evals", "evals2"}
STAMP_RELATIVE = ".claude-plugin/shipped.json"


def tracked_files(plugin_dir):
    """Paths git tracks under plugin_dir, relative to it, or None outside git."""
    result = subprocess.run(
        ["git", "-C", str(plugin_dir), "ls-files", "-z", "--", "."],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        return None
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def is_shipped(relative):
    """False for top-level tests/, evals/, evals2/ and the stamp."""
    return (relative != STAMP_RELATIVE
            and relative.split("/", 1)[0] not in TOP_LEVEL_EXCLUDED)


def shipped_files(plugin_dir):
    """Sorted relative paths of the files a plugin ships, or None outside git.

    A tracked file deleted from disk is left out, so deleting one changes
    the fingerprint.
    """
    tracked = tracked_files(plugin_dir)
    if tracked is None:
        return None
    return sorted(
        relative for relative in tracked
        if is_shipped(relative) and (Path(plugin_dir) / relative).is_file()
    )


def executable_flag(path):
    """b"x" when the owner may execute the file (what git records), else b"-"."""
    return b"x" if Path(path).stat().st_mode & stat.S_IXUSR else b"-"


def fingerprint(plugin_dir):
    """SHA-256 over each shipped file as path, NUL, flag, NUL, bytes, NUL.

    None when plugin_dir is not in a git work tree.
    """
    files = shipped_files(plugin_dir)
    if files is None:
        return None
    digest = hashlib.sha256()
    for relative in files:
        path = Path(plugin_dir) / relative
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(executable_flag(path) + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def read_json(path):
    """The parsed object, or None when the file is missing, not valid JSON,
    or valid JSON that is not an object."""
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def check_plugin(plugin_dir):
    """None when the stamp matches the tree, else a message saying what to do."""
    name = Path(plugin_dir).name
    manifest = read_json(Path(plugin_dir) / ".claude-plugin" / "plugin.json") or {}
    declared = manifest.get("version", "(none)")
    current = fingerprint(plugin_dir)
    if current is None:
        return f"{name}: not in a git work tree; the check reads git ls-files."
    stamp = read_json(Path(plugin_dir) / STAMP_RELATIVE)
    if stamp is None:
        return (f"{name} {declared}: no stamp. "
                f"Run python3 scripts/check_versions.py --write {name}.")
    if stamp.get("version") != declared:
        return (f"{name} {declared}: the stamp says {stamp.get('version')}. "
                f"Run scripts/release.sh {name} <next version>.")
    if stamp.get("sha256") != current:
        return (f"{name} {declared}: shipped files changed since {declared} "
                f"was stamped. Run scripts/release.sh {name} <next version>.")
    return None


def plugin_dirs(plugins_root):
    """Every directory under plugins_root that has a plugin manifest."""
    return sorted(
        manifest.parent.parent
        for manifest in Path(plugins_root).glob("*/.claude-plugin/plugin.json")
    )


def check_all(plugins_root):
    """One message per plugin that fails its check."""
    return [m for m in map(check_plugin, plugin_dirs(plugins_root)) if m]


def write_stamp(plugin_dir):
    """Rewrite the stamp from the manifest's version and the current tree.

    None on success, else a message saying why nothing was written.
    """
    name = Path(plugin_dir).name
    manifest = read_json(Path(plugin_dir) / ".claude-plugin" / "plugin.json")
    if manifest is None or "version" not in manifest:
        return f"{name}: the manifest has no version."
    current = fingerprint(plugin_dir)
    if current is None:
        return f"{name}: not in a git work tree; the check reads git ls-files."
    stamp = {"version": manifest["version"], "sha256": current}
    (Path(plugin_dir) / STAMP_RELATIVE).write_text(
        json.dumps(stamp) + "\n", encoding="utf-8")
    return None


def git(work_tree, *arguments):
    """Run git in work_tree for the self-test; raise if it fails."""
    subprocess.run(["git", "-C", str(work_tree), *arguments], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_plugin(plugins_root, name, version):
    """Build a small stamped plugin tree, tracked by git, for the self-test."""
    plugin_dir = Path(plugins_root) / name
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / "skills" / "one").mkdir(parents=True)
    (plugin_dir / "bin").mkdir()
    (plugin_dir / "tests").mkdir()
    (plugin_dir / "evals").mkdir()
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": version}), encoding="utf-8")
    (plugin_dir / "skills" / "one" / "SKILL.md").write_text("skill\n", encoding="utf-8")
    (plugin_dir / "bin" / "build").write_text("#!/bin/sh\n", encoding="utf-8")
    (plugin_dir / "bin" / "build").chmod(0o755)
    (plugin_dir / ".claude-plugin" / "plugin.json").chmod(0o644)
    (plugin_dir / "skills" / "one" / "SKILL.md").chmod(0o644)
    (plugin_dir / "tests" / "test_one.py").write_text("test\n", encoding="utf-8")
    (plugin_dir / "evals" / "case.md").write_text("eval\n", encoding="utf-8")
    git(plugin_dir, "add", "-f", "--", ".")
    write_stamp(plugin_dir)
    return plugin_dir


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_changed(plugin, what):
    message = check_plugin(plugin)
    expect(message is not None and "shipped files changed" in message,
           f"{what} must fail the check, got {message!r}")


def run_self_test():
    root = tempfile.mkdtemp(prefix="check_versions_")
    try:
        git(root, "init", "-q")
        plugin = make_plugin(root, "alpha", "1.0.0")
        expect(check_plugin(plugin) is None, "a fresh stamp must pass")

        # Hand-written: the known hash of the shipped set for the tree above,
        # so a change to the hashing recipe (path, NUL, executable flag, NUL,
        # bytes, NUL, sorted by path) fails.
        recipe = hashlib.sha256(
            b".claude-plugin/plugin.json\0-\0"
            + b'{"name": "alpha", "version": "1.0.0"}\0'
            + b"bin/build\0x\0#!/bin/sh\n\0"
            + b"skills/one/SKILL.md\0-\0skill\n\0"
        ).hexdigest()
        expect(fingerprint(plugin) == recipe,
               "fingerprint must be sha256 of path NUL flag NUL bytes NUL, sorted")

        for ignored in ["tests/test_one.py", "evals/case.md"]:
            path = plugin / ignored
            path.write_text("changed\n", encoding="utf-8")
            expect(check_plugin(plugin) is None, f"editing {ignored} must stay ok")
        (plugin / "evals2").mkdir()
        (plugin / "evals2" / "new.md").write_text("new\n", encoding="utf-8")
        git(plugin, "add", "-f", "--", "evals2")
        expect(check_plugin(plugin) is None, "a tracked evals2 file must not count")

        # Untracked files (caches, local settings, build output) do not ship.
        (plugin / ".pytest_cache").mkdir()
        (plugin / ".pytest_cache" / "x").write_text("x\n")
        (plugin / ".claude").mkdir()
        (plugin / ".claude" / "settings.local.json").write_text("{}\n")
        (plugin / "skills" / "one" / "examples").mkdir()
        (plugin / "skills" / "one" / "examples" / "sample.pdf").write_text("pdf\n")
        expect(check_plugin(plugin) is None,
               "untracked files must not count, got "
               f"{check_plugin(plugin)!r}")

        # A tracked tests directory below the top level ships with its skill.
        (plugin / "skills" / "one" / "tests").mkdir()
        (plugin / "skills" / "one" / "tests" / "t.md").write_text("t\n")
        git(plugin, "add", "-f", "--", "skills/one/tests")
        expect_changed(plugin, "a tracked nested tests dir")
        git(plugin, "rm", "-q", "-r", "--cached", "--", "skills/one/tests")
        shutil.rmtree(plugin / "skills" / "one" / "tests")
        expect(check_plugin(plugin) is None, "removing the nested dir must pass")

        (plugin / "skills" / "one" / "SKILL.md").write_text("edited\n")
        message = check_plugin(plugin)
        expect(message == ("alpha 1.0.0: shipped files changed since 1.0.0 was "
                           "stamped. Run scripts/release.sh alpha <next version>."),
               f"a shipped edit must fail with the fix, got {message!r}")
        (plugin / "skills" / "one" / "SKILL.md").write_text("skill\n")
        expect(check_plugin(plugin) is None, "reverting must pass")

        (plugin / "bin" / "build").chmod(0o644)
        expect_changed(plugin, "clearing the executable bit")
        (plugin / "bin" / "build").chmod(0o755)
        expect(check_plugin(plugin) is None, "restoring the bit must pass")

        (plugin / "skills" / "one" / "SKILL.md").unlink()
        expect_changed(plugin, "deleting a tracked shipped file")
        (plugin / "skills" / "one" / "SKILL.md").write_text("skill\n")
        expect(check_plugin(plugin) is None, "restoring the file must pass")

        (plugin / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "alpha", "version": "1.0.1"}))
        message = check_plugin(plugin)
        expect(message is not None and "the stamp says 1.0.0" in message,
               f"a bumped manifest with an old stamp must fail, got {message!r}")
        expect(write_stamp(plugin) is None, "--write must succeed")
        expect(check_plugin(plugin) is None, "--write must make it pass")

        # Valid JSON that is not an object reads as missing, not a traceback.
        stamp_path = plugin / ".claude-plugin" / "shipped.json"
        stamp_path.write_text("[1]\n")
        message = check_plugin(plugin)
        expect(message is not None and "no stamp" in message,
               f"a stamp that is not an object must read as missing, got {message!r}")
        manifest_path = plugin / ".claude-plugin" / "plugin.json"
        manifest_path.write_text('["1.0.1"]\n')
        message = check_plugin(plugin)
        expect(message == ("alpha (none): no stamp. "
                           "Run python3 scripts/check_versions.py --write alpha."),
               f"a manifest that is not an object must read as missing, got {message!r}")
        message = write_stamp(plugin)
        expect(message == "alpha: the manifest has no version.",
               f"--write without a manifest version must say so, got {message!r}")
        manifest_path.write_text(json.dumps({"name": "alpha", "version": "1.0.1"}))

        stamp_path.unlink()
        message = check_plugin(plugin)
        expect(message is not None and "no stamp" in message,
               f"a missing stamp must fail, got {message!r}")
        write_stamp(plugin)

        # A plugin that lands later is found without editing the script.
        make_plugin(root, "beta", "0.1.0")
        (Path(root) / "beta" / "skills" / "one" / "SKILL.md").write_text("edited\n")
        messages = check_all(root)
        expect(len(messages) == 1 and messages[0].startswith("beta 0.1.0:"),
               f"check_all must cover every plugin on disk, got {messages!r}")

        # Outside a git work tree the check says so instead of hashing nothing.
        loose = Path(tempfile.mkdtemp(prefix="check_versions_loose_"))
        try:
            (loose / "gamma" / ".claude-plugin").mkdir(parents=True)
            message = check_plugin(loose / "gamma")
            expect(message == "gamma: not in a git work tree; the check reads "
                              "git ls-files.",
                   f"a plugin outside git must say so, got {message!r}")
        finally:
            shutil.rmtree(loose)
        print("self-test passed")
        return 0
    finally:
        shutil.rmtree(root)


def main(arguments):
    repo_root = Path(__file__).resolve().parent.parent
    plugins_root = repo_root / "plugins"
    if arguments == ["--self-test"]:
        return run_self_test()
    if len(arguments) == 2 and arguments[0] == "--write":
        plugin_dir = plugins_root / arguments[1]
        if not (plugin_dir / ".claude-plugin" / "plugin.json").is_file():
            print(f"no such plugin: {arguments[1]}", file=sys.stderr)
            return 1
        message = write_stamp(plugin_dir)
        if message:
            print(message, file=sys.stderr)
            return 1
        return 0
    if arguments:
        print(__doc__, file=sys.stderr)
        return 1
    messages = check_all(plugins_root)
    for message in messages:
        print(message)
    return 1 if messages else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
