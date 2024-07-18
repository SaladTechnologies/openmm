#! /usr/bin/env bash

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null
then
    echo "Error: AWS CLI is not installed. Please install it and try again."
    exit 1
fi

# Function to display usage information
usage() {
    echo "Usage: $0 --bucket BUCKET_NAME --prefix PREFIX [--directory DIRECTORY]"
    echo
    echo "Options:"
    echo "  --bucket BUCKET_NAME   Specify the R2 bucket name"
    echo "  --prefix PREFIX        Specify the prefix for uploaded files"
    echo "  --directory DIRECTORY  Specify the directory to upload (default: current directory)"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --bucket)
        BUCKET="$2"
        shift
        shift
        ;;
        --prefix)
        PREFIX="$2"
        shift
        shift
        ;;
        --directory)
        DIRECTORY="$2"
        shift
        shift
        ;;
        *)
        usage
        ;;
    esac
done

# Check if required arguments are provided
if [ -z "$BUCKET" ] || [ -z "$PREFIX" ]; then
    echo "Error: Both --bucket and --prefix are required."
    usage
fi

# Set default directory to current directory if not specified
DIRECTORY=${DIRECTORY:-.}

# Perform the recursive upload
aws s3 sync "$DIRECTORY" "s3://$BUCKET/$PREFIX" --endpoint-url "$AWS_ENDPOINT_URL"

echo "Upload complete."
