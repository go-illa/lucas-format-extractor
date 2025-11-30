# AWS Lambda Deployment Guide

This guide provides step-by-step instructions for deploying the `lucas-format-extractor` project as an AWS Lambda function using a secure, 3-bucket architecture.

-   **Code Bucket:** Stores the Lambda function's `.zip` code package.
-   **Data Input Bucket:** Receives raw data files, which triggers the Lambda.
-   **Data Output Bucket:** Stores the processed results.

## Prerequisites

1.  **AWS Account & CLI:** An AWS account and the AWS CLI installed and configured.
2.  **Python 3.8+:** Python 3.8 or later.
3.  **`.env` file:** For local testing, create a `.env` file in the project root. See `example.env` for the required variables.

## Step 1: Build and Upload the Deployment Package

You have two options for getting the deployment package (`lucas-format-extractor-lambda.zip`) to your **code bucket**.

### Option A: Automatic Upload via Script (Recommended)

1.  **Set the `S3_CODE_BUCKET` environment variable:**
    ```bash
    export S3_CODE_BUCKET="your-code-bucket-name"
    ```
2.  **Run the build script:** This will create the package and upload it to the S3 bucket you specified.
    ```bash
    ./build_lambda_package.sh
    ```

### Option B: Manual Upload via AWS S3 Console

1.  **Build the package locally:**
    ```bash
    export SKIP_S3_UPLOAD="true"
    ./build_lambda_package.sh
    unset SKIP_S3_UPLOAD
    ```
2.  **Manually upload** the created `lucas-format-extractor-lambda.zip` file to your **code bucket** using the AWS S3 Console.

## Step 2: Set Up AWS Resources

### a) Create S3 Buckets

Create three separate S3 buckets:
```bash
aws s3 mb s3://your-code-bucket-name
aws s3 mb s3://your-data-input-bucket-name
aws s3 mb s3://your-data-output-bucket-name
```

### b) Create an IAM Role

Your Lambda function needs an IAM role with permissions to access the S3 buckets and write to CloudWatch Logs.

1.  **Create a trust policy file** named `lambda-trust-policy.json`:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [ { "Effect": "Allow", "Principal": { "Service": "lambda.amazonaws.com" }, "Action": "sts:AssumeRole" } ]
    }
    ```
2.  **Create the IAM role:**
    ```bash
    aws iam create-role --role-name LucasFormatExtractorLambdaRole --assume-role-policy-document file://lambda-trust-policy.json
    ```
3.  **Create a permissions policy file** named `lambda-permissions-policy.json`. This policy grants the necessary permissions for the 3-bucket setup.
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": [
                    "arn:aws:s3:::your-code-bucket-name/*",
                    "arn:aws:s3:::your-data-input-bucket-name/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::your-data-output-bucket-name/*"
            },
            {
                "Effect": "Allow",
                "Action": [ "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents" ],
                "Resource": "arn:aws:logs:*:*:*"
            }
        ]
    }
    ```
    **Important:** Replace the bucket names with your actual bucket names.

4.  **Attach the permissions policy to the role:**
    ```bash
    aws iam put-role-policy --role-name LucasFormatExtractorLambdaRole --policy-name LucasFormatExtractorLambdaPolicy --policy-document file://lambda-permissions-policy.json
    ```

## Step 3: Create and Configure the Lambda Function

1.  **Create the Lambda function:**
    This command now points to the `.zip` file in your **code bucket**.
    ```bash
    aws lambda create-function \
      --function-name lucas-format-extractor \
      --runtime python3.8 \
      --role arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/LucasFormatExtractorLambdaRole \
      --handler lambda_function.lambda_handler \
      --code S3Bucket=your-code-bucket-name,S3Key=lucas-format-extractor-lambda.zip \
      --timeout 300 \
      --memory-size 512 \
      --environment "Variables={GROQ_API_KEY=your_groq_api_key,GEMINI_API_KEY=your_gemini_api_key,OUTPUT_S3_BUCKET=your-data-output-bucket-name}"
    ```
    **Important:**
    *   Replace `YOUR_AWS_ACCOUNT_ID` with your AWS account ID.
    *   Replace the bucket names and API key values.
    *   Note that we are **not** passing AWS credentials here, as the IAM role handles permissions.

2.  **Add the S3 Trigger:**
    Apply the trigger to your **data-input bucket**.
    ```bash
    aws s3api put-bucket-notification-configuration \
      --bucket your-data-input-bucket-name \
      --notification-configuration file://s3-trigger-config.json # Use the s3-trigger-config.json from previous steps
    ```

## Step 4: Test and Update

*   **Test:** Upload an Excel file to your **data-input bucket**. Check the **data-output bucket** for the result.
*   **Update:** To update the function, simply run the build script again (`./build_lambda_package.sh`) and then run the `aws lambda update-function-code` command as described in the GitHub Actions workflow.