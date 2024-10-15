#!/bin/bash

# Get all images that start with 'docudive'
images=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^docudive")

# Loop through each image and retag them to v1
for image in $images; do
    # Extract the repository name (e.g., docudive/nginx from docudive/nginx:v1.0.0.3)
    repository=$(echo "$image" | cut -d ':' -f 1)

    # Retag the image to v1
    docker tag "$image" "${repository}:v1"
    echo "Retagged $image to ${repository}:v1"
done

