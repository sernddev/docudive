#!/bin/bash

# Directory where the tar files are located
IMAGE_DIR="/docudive/images"

# Check if parallel is installed
if ! command -v parallel &> /dev/null
then
    echo "parallel is not installed. Installing parallel..."
    sudo apt-get install -y parallel  # For Ubuntu/Debian
    # For CentOS/RHEL, use: sudo yum install parallel
fi

# Find all .tar files in the directory and load them in parallel
find "$IMAGE_DIR" -name '*.tar' | parallel -j 4 docker load -i {}

# Explanation:
# -j 4: This runs 4 parallel jobs (you can adjust this based on CPU capacity)
# {}: This is replaced with the path of each tar file found by `find`

