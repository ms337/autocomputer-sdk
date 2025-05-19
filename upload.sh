#!/bin/bash
BUCKET=autocomputer-sdk
VERSION=$(cat pyproject.toml | grep version | cut -d'=' -f2 | tr -d '" ')

# Copy from dist directory
gsutil cp dist/autocomputer_sdk-${VERSION}-py3-none-any.whl  gs://${BUCKET}/sdk/
gsutil cp README.md gs://${BUCKET}/sdk/
gsutil cp LICENSE gs://${BUCKET}/sdk/
gsutil cp pyproject.toml gs://${BUCKET}/sdk/


