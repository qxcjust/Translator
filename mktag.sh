#!/bin/bash

# Check if the parameter exists
if [ -z "$1" ]; then
    echo "Usage: $0 <version> (format: vX.Y.Z)"
    exit 1
fi

version=$1

# Validate version number format
if [[ ! "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version number format should be vX.Y.Z"
    exit 1
fi

# Check if the workspace is clean
if ! git diff-index --quiet HEAD --; then
    echo "Error: There are uncommitted changes in the workspace. Please handle them first."
    exit 1
fi

# Replace the version number in gl_config.py
sed -i.bak -E "s/^VERSION[[:space:]]*=[[:space:]]*['\"].*['\"]/VERSION = \"${version}\"/" gl_config.py

# Check if the file has changed
if git diff --exit-code gl_config.py >/dev/null; then
    echo "Error: Version number has not changed. Please check the input."
    rm gl_config.py.bak  # Remove backup file
    exit 1
fi

# Commit changes
git add gl_config.py
git commit -m "Update version number to ${version}"

# Create tag
git tag -a "${version}" -m "Release version ${version}"

# Prompt to push changes and tag
echo "Version number updated and tag created."
echo "Please use the following commands to push changes and tag:"
echo "git push origin main && git push origin ${version}"

# Clean up backup file
rm gl_config.py.bak