#!/usr/bin/env python3
"""Check that a plugin's version names one set of shipped files.

Each plugin keeps a stamp, plugins/<name>/.claude-plugin/shipped.json:
{"version": "X.Y.Z", "sha256": "<hex>"}. The hash covers every shipped file.
If the files change and the version does not, this fails. It walks the
filesystem and never calls git, so a shallow clone and a .git-less export
give the same answer as a full checkout.

Shipped files are everything under the plugin except tests/, evals/ and
evals2/ at the plugin's top level (they do not change how a plugin works),
any __pycache__ or results directory, .DS_Store, and the stamp itself.

Check:     python3 scripts/check_versions.py
Stamp:     python3 scripts/check_versions.py --write <plugin>
Self-test: python3 scripts/check_versions.py --self-test
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TOP_LEVEL_EXCLUDED = {"tests", "evals", "evals2"}
ANY_LEVEL_EXCLUDED = {"__pycache__", "results"}
STAMP_RELATIVE = ".claude-plugin/shipped.json"


def shipped_files(plugin_dir):
    """Sorted relative paths (forward slashes) of the files a plugin ships."""
    found = []
    for dirpath, dirnames, filenames in os.walk(plugin_dir):
        is_top = Path(dirpath) == Path(plugin_dir)
        dirnames[:] = [
            name for name in dirnames
            if name not in ANY_LEVEL_EXCLUDED
            and not (is_top and name in TOP_LEVEL_EXCLUDED)
        ]
        for filename in filenames:
            relative = (Path(dirpath) / filename).relative_to(plugin_dir).as_posix()
            if filename != ".DS_Store" and relative != STAMP_RELATIVE:
                found.append(relative)
    return sorted(found)


def fingerprint(plugin_dir):
    """SHA-256 over each shipped file as path, NUL, bytes, NUL."""
    digest = hashlib.sha256()
    for relative in shipped_files(plugin_dir):
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update((Path(plugin_dir) / relative).read_bytes() + b"\0")
    return digest.hexdigest()


def read_json(path):
    """The parsed file, or None when it is missing or not valid JSON."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def check_plugin(plugin_dir):
    """None when the stamp matches the tree, else a message saying what to do."""
    name = Path(plugin_dir).name
    manifest = read_json(Path(plugin_dir) / ".claude-plugin" / "plugin.json") or {}
    declared = manifest.get("version", "(none)")
    stamp = read_json(Path(plugin_dir) / STAMP_RELATIVE)
    if stamp is None:
        return (f"{name} {declared}: no stamp. "
                f"Run python3 scripts/check_versions.py --write {name}.")
    if stamp.get("version") != declared:
        return (f"{name} {declared}: the stamp says {stamp.get('version')}. "
                f"Run scripts/release.sh {name} <next version>.")
    if stamp.get("sha256") != fingerprint(plugin_dir):
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
    """Rewrite the stamp from the manifest's version and the current tree."""
    manifest = read_json(Path(plugin_dir) / ".claude-plugin" / "plugin.json")
    stamp = {"version": manifest["version"], "sha256": fingerprint(plugin_dir)}
    (Path(plugin_dir) / STAMP_RELATIVE).write_text(
        json.dumps(stamp) + "\n", encoding="utf-8")


def make_plugin(plugins_root, name, version):
    """Build a small stamped plugin tree for the self-test."""
    plugin_dir = Path(plugins_root) / name
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / "skills" / "one").mkdir(parents=True)
    (plugin_dir / "tests").mkdir()
    (plugin_dir / "evals").mkdir()
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": version}), encoding="utf-8")
    (plugin_dir / "skills" / "one" / "SKILL.md").write_text("skill\n", encoding="utf-8")
    (plugin_dir / "tests" / "test_one.py").write_text("test\n", encoding="utf-8")
    (plugin_dir / "evals" / "case.md").write_text("eval\n", encoding="utf-8")
    write_stamp(plugin_dir)
    return plugin_dir


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


def run_self_test():
    root = tempfile.mkdtemp(prefix="check_versions_")
    try:
        plugin = make_plugin(root, "alpha", "1.0.0")
        expect(check_plugin(plugin) is None, "a fresh stamp must pass")

        # Hand-written: the known hash of the shipped set for the tree above,
        # so a change to the hashing recipe (path, NUL, bytes, NUL) fails.
        recipe = hashlib.sha256(
            b".claude-plugin/plugin.json\0"
            + b'{"name": "alpha", "version": "1.0.0"}\0'
            + b"skills/one/SKILL.md\0skill\n\0"
        ).hexdigest()
        expect(fingerprint(plugin) == recipe,
               "fingerprint must be sha256 of path NUL bytes NUL, sorted")

        for ignored in ["tests/test_one.py", "evals/case.md"]:
            path = plugin / ignored
            path.write_text("changed\n", encoding="utf-8")
            expect(check_plugin(plugin) is None, f"editing {ignored} must stay ok")
        (plugin / "evals2").mkdir()
        (plugin / "evals2" / "new.md").write_text("new\n", encoding="utf-8")
        (plugin / "skills" / "one" / "__pycache__").mkdir()
        (plugin / "skills" / "one" / "__pycache__" / "x.pyc").write_text("x")
        (plugin / "skills" / "one" / "results").mkdir()
        (plugin / "skills" / "one" / "results" / "r.json").write_text("{}")
        (plugin / "skills" / ".DS_Store").write_text("x")
        expect(check_plugin(plugin) is None,
               "evals2, __pycache__, results and .DS_Store must not count")

        # A tests directory below the top level ships with its skill.
        (plugin / "skills" / "one" / "tests").mkdir()
        (plugin / "skills" / "one" / "tests" / "t.md").write_text("t\n")
        message = check_plugin(plugin)
        expect(message is not None and "shipped files changed" in message,
               f"a nested tests dir must count, got {message!r}")
        shutil.rmtree(plugin / "skills" / "one" / "tests")
        expect(check_plugin(plugin) is None, "removing the nested dir must pass")

        (plugin / "skills" / "one" / "SKILL.md").write_text("edited\n")
        message = check_plugin(plugin)
        expect(message == ("alpha 1.0.0: shipped files changed since 1.0.0 was "
                           "stamped. Run scripts/release.sh alpha <next version>."),
               f"a shipped edit must fail with the fix, got {message!r}")
        (plugin / "skills" / "one" / "SKILL.md").write_text("skill\n")
        expect(check_plugin(plugin) is None, "reverting must pass")

        (plugin / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "alpha", "version": "1.0.1"}))
        message = check_plugin(plugin)
        expect(message is not None and "the stamp says 1.0.0" in message,
               f"a bumped manifest with an old stamp must fail, got {message!r}")
        write_stamp(plugin)
        expect(check_plugin(plugin) is None, "--write must make it pass")

        (plugin / ".claude-plugin" / "shipped.json").unlink()
        message = check_plugin(plugin)
        expect(message is not None and "no stamp" in message,
               f"a missing stamp must fail, got {message!r}")

        # A plugin that lands later is found without editing the script.
        make_plugin(root, "beta", "0.1.0")
        (Path(root) / "beta" / "skills" / "one" / "SKILL.md").write_text("edited\n")
        messages = check_all(root)
        expect(len(messages) == 2 and messages[1].startswith("beta 0.1.0:"),
               f"check_all must cover every plugin on disk, got {messages!r}")
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
        write_stamp(plugin_dir)
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
