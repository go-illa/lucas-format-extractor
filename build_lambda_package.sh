#!/bin/bash

# This script creates a lean deployment package for the AWS Lambda function.
# It can optionally upload the package to the S3 code bucket.

# --- Configuration ---
# Set S3_CODE_BUCKET environment variable to upload the code package to S3.
# Example: export S3_CODE_BUCKET="your-code-bucket-name"
#
# Set SKIP_S3_UPLOAD to "true" to skip the S3 upload step.
# Example: export SKIP_S3_UPLOAD="true"
# --- End Configuration ---


# Stop on any error
set -e

# Variables
PACKAGE_DIR="package"
ZIP_FILE="lucas-format-extractor-lambda.zip"

# 1. Create a clean package directory
echo "Creating a clean package directory..."
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# 2. Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -t $PACKAGE_DIR

# 3. Copy application code
echo "Copying application code..."
cp -r etl $PACKAGE_DIR/
cp -r prompts $PACKAGE_DIR/
cp -r schema $PACKAGE_DIR/
cp *.py $PACKAGE_DIR/

# 4. Slim down the package
echo "Slimming down the deployment package..."
find $PACKAGE_DIR -type d -name "__pycache__" -exec rm -r {} +
find $PACKAGE_DIR -type d -name "*.dist-info" -exec rm -r {} +
find $PACKAGE_DIR -type d -name "*.egg-info" -exec rm -r {} +

# 5. Create the zip file
echo "Creating the deployment package: $ZIP_FILE..."
cd $PACKAGE_DIR
zip -r ../$ZIP_FILE .
cd ..

# 6. Optional: Upload the zip file to S3
if [ "$SKIP_S3_UPLOAD" = "true" ]; then
  echo "Skipping S3 upload as SKIP_S3_UPLOAD is set to true."
else
  if [ -z "$S3_CODE_BUCKET" ]; then
    echo "Error: S3_CODE_BUCKET environment variable is not set. Cannot upload to S3."
    echo "To skip S3 upload, set SKIP_S3_UPLOAD=\"true\".