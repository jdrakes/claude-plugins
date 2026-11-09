#!/usr/bin/env bash
set -e

python3 scripts/test_no_leaks.py --self-test
python3 scripts/test_no_leaks.py

python3 scripts/check_versions.py --self-test
python3 scripts/check_versions.py

python3 -m unittest discover -s plugins/resume-kit/tests -v

plugins/resume-kit/skills/resume/tools/check-fidelity.sh
