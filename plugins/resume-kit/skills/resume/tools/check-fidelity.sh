#!/usr/bin/env bash
# Renderer regression test: render the example and compare its geometry
# against the committed baseline.
#
#   tools/check-fidelity.sh            check against examples/sample-resume.baseline.json
#   tools/check-fidelity.sh --update   rewrite that baseline from this render
#
# Run it after any edit to template.typ or components.typ. If it fails and
# the change was deliberate, --update and commit the new baseline with it.

set -euo pipefail

# Derived from this script's own location, not from $HOME, which says
# nothing about where the plugin is installed. -P resolves the symlinked
# plugin directory to the real one before applying "..", so a plugin reached
# through a symlink still finds its own fonts and template.
skill_dir="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$skill_dir/examples/sample-resume.yaml"
baseline="$skill_dir/examples/sample-resume.baseline.json"

mode="--check"
if [[ "${1:-}" == "--update" ]]; then
  mode="--write"
fi

# A missing tool is a skip, not a failure: a contributor's laptop may not
# carry typst or poppler.
for tool in typst pdftotext python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "SKIP: $tool not installed"
    exit 0
  fi
done

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

"$skill_dir/bin/build" "$fixture" -o "$work/sample-resume.pdf" >/dev/null
python3 "$skill_dir/tools/snapshot.py" "$work/sample-resume.pdf" "$mode" "$baseline"
