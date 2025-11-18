# AWS Lambda Deployment Guide (for AWS Web Console)

This guide provides step-by-step instructions for deploying the `lucas-format-extractor` project as an AWS Lambda function using the AWS Management Console (the web application).

---

### Step 1: Build and Upload the Deployment Package

First, you need to create the `.zip` deployment package on your local machine and upload it to an S3 bucket.

1.  **Build the package locally:** On your local machine, open a terminal and run the following commands. This will create the `lucas-format-extractor-lambda.zip` file in your project folder.
    ```bash
    export SKIP_S3_UPLOAD="true"
    ./build_lambda_package.sh
    unset SKIP_S3_UPLOAD
    ```

2.  **Create an S3 Bucket for Your Code:**
    *   In the AWS Console, navigate to the **S3** service.
    *   Create a new, private S3 bucket to hold your Lambda code (e.g., `your-name-lambda-code-storage`). This bucket should be different from your input/output buckets.

3.  **Manually upload the `.zip` file:**
    *   Navigate to the S3 bucket you just created.
    *   Click **"Upload"**, select your `lucas-format-extractor-lambda.zip` file, and upload it.

---

### Step 2: Create S3 Buckets for Input and Output

You need two more S3 buckets: one for your raw Excel files (input) and one for the transformed files (output).

1.  In the **S3** service, create two new buckets:
    *   An **input bucket** (e.g., `your-name-lucas-input-files`).
    *   An **output bucket** (e.g., `your-name-lucas-output-files`).
2.  Take note of these exact bucket names.

---

### Step 3: Create the IAM Role with S3 Permissions

This is the most critical step for security. You will create a role that gives your Lambda function permission to access *only* the specific resources it needs.

1.  In the AWS Console, navigate to the **IAM** service.
2.  On the left menu, click **"Roles"**, then click **"Create role"**.
3.  For "Trusted entity type", select **"AWS service"**.
4.  For "Use case", choose **"Lambda"**, then click **"Next"**.
5.  On the "Add permissions" page, click **"Next"** again (we will add permissions manually).
6.  On the final page, for "Role name", enter `LucasFormatExtractorLambdaRole`, then click **"Create role"**.
7.  From the list of roles, click on the `LucasFormatExtractorLambdaRole` you just created.
8.  On the role's summary page, under the "Permissions policies" tab, click the **"Add permissions"** dropdown and select **"Create inline policy"**.
9.  This will open the policy editor. Click on the **"JSON"** tab.
10. **Copy and paste the following policy** into the JSON editor.

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::your-input-s3-bucket-name/*"
            },
            {
                "Effect": "Allow",
                "Action": "s3:PutObject",
                "Resource": "arn:aws:s3:::your-output-s3-bucket-name/*"
            }
        ]
    }
    ```

11. **IMPORTANT:** In the policy text you just pasted, you **must** replace `your-input-s3-bucket-name` and `your-output-s3-bucket-name` with the actual names of the buckets you created in Step 2.
12. Click **"Review policy"**.
13. For "Name", enter `S3AndLoggingPermissions`, then click **"Create policy"**.

---

### Step 4: Create and Configure the Lambda Function

1.  In the AWS Console, navigate to the **Lambda** service.
2.  Click **"Create function"**.
3.  Select **"Author from scratch"**.
4.  **Function name:** `lucas-format-extractor`.
5.  **Runtime:** Select `Python 3.8`.
6.  **Architecture:** Leave it as `x86_64`.
7.  Expand **"Change default execution role"**:
    *   Select **"Use an existing role"**.
    *   Choose the `LucasFormatExtractorLambdaRole` from the dropdown.
8.  Click **"Create function"**.

#### Configure the Function

1.  **Point to the Code in S3:**
    *   On the function's page, in the **"Code source"** section, click **"Edit"**.
    *   Select **"Amazon S3 location"**.
    *   For "S3 URI", enter the S3 URI of your uploaded `.zip` file. You can get this by navigating to the file in the S3 console and copying its URI. It will look like `s3://your-name-lambda-code-storage/lucas-format-extractor-lambda.zip`.
    *   Click **"Save"**.

2.  **Set Environment Variables:**
    *   Go to the **"Configuration"** tab, then **"Environment variables"**.
    *   Click **"Edit"**, then **"Add environment variable"** for the following keys (note that the AWS keys are no longer needed):
        *   `GROQ_API_KEY`: `your_groq_api_key_here`
        *   `OUTPUT_S3_BUCKET`: The name of your output bucket from Step 2.
    *   Click **"Save"**.

3.  **Increase Timeout and Memory:**
    *   In the **"Configuration"** tab, go to **"General configuration"**.
    *   Click **"Edit"**.
    *   Set **Timeout** to **5 min**.
    *   Set **Memory** to **512** MB.
    *   Click **"Save"**.

---

### Step 5: Add the S3 Trigger

1.  In the **"Function overview"** diagram, click **"+ Add trigger"**.
2.  Select **"S3"** from the dropdown.
3.  **Bucket:** Choose your **input bucket** from Step 2.
4.  **Event types:** Leave it as **"All object creation events"**.
5.  **Suffix:** Enter `.xlsx`.
6.  Check the acknowledgement box.
7.  Click **"Add"**.

---

### Step 6: Test

1.  Navigate to your **input S3 bucket**.
2.  Upload a sample Excel file.
3.  Check your **output S3 bucket**. The transformed file should appear within a few minutes.
4.  To debug, go to the **"Monitor"** tab in your Lambda function and click **"View CloudWatch logs"**.

This completes the secure, web-console-based deployment process. Shall I commit these final changes?
