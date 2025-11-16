#!/bin/bash

# This script creates a deployment package for the AWS Lambda function.

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

# 4. Create the zip file
echo "Creating the deployment package: $ZIP_FILE..."
cd $PACKAGE_DIR
zip -r ../$ZIP_FILE .
cd ..

# 5. Clean up the package directory
echo "Cleaning up..."
rm -rf $PACKAGE_DIR

echo "✅ Deployment package created successfully: $ZIP_FILE"
