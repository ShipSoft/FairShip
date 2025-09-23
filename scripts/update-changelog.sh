#!/bin/bash
docker run \
  --rm \
  --network host \
  -v $(pwd):/app:z \
  registry.cern.ch/docker.io/orhunp/git-cliff:latest \
  -o CHANGELOG.md
