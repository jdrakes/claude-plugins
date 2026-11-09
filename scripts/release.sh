#!/usr/bin/env bash
set -e

plugin="$1"
version="$2"

if [ -z "$plugin" ] || [ -z "$version" ]; then
  echo "usage: scripts/release.sh <plugin> <version>" >&2
  exit 1
fi

manifest="plugins/$plugin/.claude-plugin/plugin.json"

if [ ! -f "$manifest" ]; then
  echo "no such plugin: $manifest" >&2
  exit 1
fi

if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "version must be X.Y.Z, got: $version" >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "working tree is not clean, commit or stash first" >&2
  exit 1
fi

python3 - "$manifest" "$version" <<'PYEOF'
import json
import sys

path, version = sys.argv[1], sys.argv[2]
with open(path) as f:
    manifest = json.load(f)
manifest["version"] = version
with open(path, "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
PYEOF

python3 scripts/check_versions.py --write "$plugin"

bash scripts/test.sh

tag="$plugin-v$version"
git add "$manifest" "plugins/$plugin/.claude-plugin/shipped.json"
git commit -m "Release $plugin v$version"
git tag -a "$tag" -m "Release $plugin v$version"

echo
echo "Committed and tagged $tag."
echo "Auto-update won't pick this up until the commit and tag reach GitHub:"
echo "  git push origin main --follow-tags"
