import json
import boto3
import os
import logging
from etl.pipeline import process_client_file
import config

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    This function is triggered by an S3 event. It downloads the file from S3,
    processes it using the process_client_file function, and uploads the
    transformed file to an output S3 bucket.
    """
    try:
        # 1. Get the bucket and key from the S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        # Define input and output paths in the Lambda's temporary directory
        download_path = f'/tmp/{os.path.basename(key)}'
        output_path = f'/tmp/transformed-{os.path.basename(key)}'

        # 2. Download the file from S3
        logger.info(f"Downloading file s3://{bucket}/{key} to {download_path}")
        s3.download_file(bucket, key, download_path)

        # Define the schema file path
        schema_file_path = os.path.join(os.path.dirname(__file__), 'schema', 'lucas_target_schema.json')

        # 3. Process the file
        logger.info("Processing the downloaded file...")
        process_client_file(
            client_file_path=download_path,
            schema_file_path=schema_file_path,
            output_excel_path=output_path
        )

        # 4. Check if the output file was created
        if not os.path.exists(output_path):
            logger.error(f"Processing failed. Output file not found at {output_path}.")
            return {
                'statusCode': 500,
                'body': json.dumps(f'Failed to process {key}. Output file was not generated.')
            }

        # 5. Upload the transformed file to the output bucket
        output_bucket = os.environ.get('OUTPUT_S3_BUCKET')
        if not output_bucket:
            raise ValueError("OUTPUT_S3_BUCKET environment variable not set.")

        output_key = f"transformed-files/{os.path.basename(output_path)}"
        logger.info(f"Uploading transformed file to s3://{output_bucket}/{output_key}")
        s3.upload_file(output_path, output_bucket, output_key)

        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed {key} and uploaded to {output_key}')
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred in lambda_handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps('An internal error occurred.')
        }
