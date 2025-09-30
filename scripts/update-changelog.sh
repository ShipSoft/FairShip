#!/bin/bash

set -euxo pipefail

# Commit ref were we want to start to use git-cliff for the changelog
from_ref="f5620fe0"

git-cliff -o CHANGELOG.md "$from_ref.."
