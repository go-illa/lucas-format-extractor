# AWS Lambda Deployment Guide

This guide provides step-by-step instructions for deploying the `lucas-format-extractor` project as an AWS Lambda function.

## Prerequisites

1.  **AWS Account:** You need an AWS account with permissions to create S3 buckets, IAM roles, and Lambda functions.
2.  **AWS CLI:** The AWS Command Line Interface (CLI) should be installed and configured on your local machine. You can find installation instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html).
3.  **Python 3.8+:** Ensure you have Python 3.8 or a later version installed.
4.  **`.env` file:** Create a `.env` file in the root of the project and add the following environment variables:
    ```
    GROQ_API_KEY="your_groq_api_key_here"
    AWS_REGION="your-aws-region"
    AWS_ACCESS_KEY_ID="your-aws-access-key-id"
    AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
    OUTPUT_S3_BUCKET="your-output-s3-bucket-name"
    ```

## Step 1: Build the Deployment Package

Run the `build_lambda_package.sh` script to create the deployment package. This script will install all the dependencies and package them with your application code into a `lucas-format-extractor-lambda.zip` file.

```bash
./build_lambda_package.sh
```

## Step 2: Set Up AWS Resources

### a) Create S3 Buckets

You need two S3 buckets: one for the input files and one for the output files. You can create them using the AWS CLI:

```bash
aws s3 mb s3://your-input-s3-bucket-name
aws s3 mb s3://your-output-s3-bucket-name
```

Replace `your-input-s3-bucket-name` and `your-output-s3-bucket-name` with your desired bucket names.

### b) Create a Basic IAM Role

Even when using access keys, your Lambda function still needs a basic execution role to allow it to run and write to CloudWatch logs.

1.  **Create a trust policy file** named `lambda-trust-policy.json`:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": {
            "Service": "lambda.amazonaws.com"
          },
          "Action": "sts:AssumeRole"
        }
      ]
    }
    ```

2.  **Create the IAM role:**
    ```bash
    aws iam create-role --role-name LucasFormatExtractorLambdaRole --assume-role-policy-document file://lambda-trust-policy.json
    ```

3.  **Attach the basic execution policy to the role:**
    ```bash
    aws iam attach-role-policy --role-name LucasFormatExtractorLambdaRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    ```

## Step 3: Create and Configure the Lambda Function

1.  **Create the Lambda function:**
    ```bash
    aws lambda create-function \
      --function-name lucas-format-extractor \
      --runtime python3.8 \
      --role arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/LucasFormatExtractorLambdaRole \
      --handler lambda_function.lambda_handler \
      --zip-file fileb://lucas-format-extractor-lambda.zip \
      --timeout 300 \
      --memory-size 512 \
      --environment "Variables={GROQ_API_KEY=your_groq_api_key_here,OUTPUT_S3_BUCKET=your-output-s3-bucket-name,AWS_REGION=your-aws-region,AWS_ACCESS_KEY_ID=your-aws-access-key-id,AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key}"
    ```
    **Important:**
    *   Replace `YOUR_AWS_ACCOUNT_ID` with your actual AWS account ID.
    *   Fill in the values for the environment variables.

    > **⚠️ Security Warning:** Storing access keys in environment variables is not a recommended security practice. For production environments, it is highly recommended to use an IAM role with fine-grained permissions to access AWS resources.

2.  **Add an S3 Trigger:**
    *   Create a file named `s3-trigger-config.json` with the following content:
        ```json
        {
          "LambdaFunctionConfigurations": [
            {
              "LambdaFunctionArn": "arn:aws:lambda:YOUR_REGION:YOUR_AWS_ACCOUNT_ID:function:lucas-format-extractor",
              "Events": ["s3:ObjectCreated:*"],
              "Filter": {
                "Key": {
                  "FilterRules": [
                    {
                      "Name": "suffix",
                      "Value": ".xlsx"
                    }
                  ]
                }
              }
            }
          ]
        }
        ```
        **Important:** Replace `YOUR_REGION` and `YOUR_AWS_ACCOUNT_ID` with your actual AWS region and account ID.

    *   Apply the S3 trigger configuration to your input bucket:
        ```bash
        aws s3api put-bucket-notification-configuration \
          --bucket your-input-s3-bucket-name \
          --notification-configuration file://s3-trigger-config.json
        ```
        **Important:** Replace `your-input-s3-bucket-name` with your actual input S3 bucket name.

## Step 4: Test the Lambda Function

1.  Upload an Excel file to your input S3 bucket.
2.  Check the output S3 bucket for the transformed file.
3.  Check the CloudWatch logs for the `lucas-format-extractor` Lambda function to see the execution logs.