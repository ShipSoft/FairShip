#!/bin/bash

set -euxo pipefail

# Commit ref were we want to start to use git-cliff for the changelog
from_ref="0921ba5a"

git-cliff -o CHANGELOG.md "$from_ref.."
