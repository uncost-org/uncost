#!/bin/sh
# Point git at the committed hooks so the content audits run before every
# commit and push. Run once per clone: sh scripts/setup-hooks.sh
set -e
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "Hooks enabled (core.hooksPath=.githooks): audits now run on commit and push."
