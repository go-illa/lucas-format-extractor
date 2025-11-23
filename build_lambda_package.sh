#!/bin/bash

# This script creates a lean deployment package for the AWS Lambda function.

# --- Configuration ---
# Set S3_BUCKET environment variable to upload to S3.
# Example: export S3_BUCKET="your-bucket-name"
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

# 4. Slim down the deployment package
echo "Slimming down the deployment package..."
find $PACKAGE_DIR -type d -name "__pycache__" -exec rm -r {} + 
find $PACKAGE_DIR -type d -name "*.dist-info" -exec rm -r {} + 
find $PACKAGE_DIR -type d -name "*.egg-info" -exec rm -r {} + 
# Add other file types to remove if needed, e.g., tests
# find $PACKAGE_DIR -type d -name "tests" -exec rm -r {} + 

# 5. Create the zip file
echo "Creating the deployment package: $ZIP_FILE..."
cd $PACKAGE_DIR
zip -r ../$ZIP_FILE .
cd ..

# 6. Optional: Upload the zip file to S3
if [ "$SKIP_S3_UPLOAD" = "true" ]; then
  echo "Skipping S3 upload as SKIP_S3_UPLOAD is set to true."
else
  if [ -z "$S3_BUCKET" ]; then
    echo "Error: S3_BUCKET environment variable is not set. Cannot upload to S3."
    echo "To skip S3 upload, set SKIP_S3_UPLOAD=\"true\""
    exit 1
  fi
  echo "Uploading $ZIP_FILE to s3://$S3_BUCKET..."
aws s3 cp $ZIP_FILE s3://$S3_BUCKET/
  echo "✅ Deployment package uploaded to s3://$S3_BUCKET successfully."
fi

# 7. Clean up local package directory
echo "Cleaning up local package directory..."
rm -rf $PACKAGE_DIR

if [ "$SKIP_S3_UPLOAD" = "true" ]; then
  echo "✅ Deployment package created locally: $ZIP_FILE"
else
  rm $ZIP_FILE # Remove local zip if it was uploaded to S3
  echo "✅ Deployment package created and uploaded to S3 successfully."
fi