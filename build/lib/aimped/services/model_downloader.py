import boto3
import os
import logging
from botocore.exceptions import ClientError
from decouple import config
logger = logging.getLogger(__name__)

def download_s3_folder(bucket_name, s3_folder, aws_access_key_id, aws_secret_access_key, local_dir=None, force_download=False):
    """
    Downloads the contents of a folder from an S3 bucket to a local directory.
    
    This function connects to an AWS S3 bucket using the provided credentials,
    and downloads all files from the specified S3 folder to a local directory.
    If the local directory already contains files, it can optionally force the
    download by clearing the directory first.

    Args:
        bucket_name (str): The name of the S3 bucket.
        s3_folder (str): The path of the folder in the S3 bucket.
        aws_access_key_id (str): AWS access key ID for authentication.
        aws_secret_access_key (str): AWS secret access key for authentication.
        local_dir (str, optional): The local directory to download files to. 
                                   If None, uses the S3 folder path. Defaults to None.
        force_download (bool, optional): If True, clears the local directory before 
                                         downloading. Defaults to False.

    Returns:
        str: A message indicating the result of the operation.

    Raises:
        ClientError: If there's an error interacting with the S3 bucket.

    Note:
        This function uses the boto3 library to interact with AWS S3.
        Ensure that you have the necessary permissions to access the S3 bucket.
    """
    
    if force_download:
        if os.path.exists(local_dir):
            os.system(f"rm -rf {local_dir}")
            logger.info(f"Forced download: Cleared existing directory {local_dir}")
            
    s3_folder = os.path.join(s3_folder)
    
    # Check and set local directory
    if local_dir is None:
        local_dir = s3_folder
    
    if os.path.exists(local_dir) and os.listdir(local_dir):
        logger.info(f"Model directory is not empty: {local_dir}")
        return f'Model directory is not empty: {local_dir}'

    try:
        # Initialize S3 client
        s3 = boto3.resource('s3', 
                            region_name='us-east-1', 
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
        bucket = s3.Bucket(bucket_name)

        # Download files
        for obj in bucket.objects.filter(Prefix=s3_folder):
            target = os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
            
            if obj.key[-1] == '/':  # Skip if it's a directory
                continue
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target), exist_ok=True)
            
            # Download file
            bucket.download_file(obj.key, target)
            logger.info(f"Downloaded: {obj.key} -> {target}")
        
        logger.info(f"Model successfully downloaded: ✅ --> {local_dir}")
        return f"Model successfully downloaded: {local_dir}"
    
    except ClientError as e:
        error_message = f"Error occurred while downloading from S3 Bucket: {str(e)}"
        logger.error(error_message)
        return error_message

# if __name__ == "__main__":
#     # Configure logging
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
#     # Example usage
#     result = download_s3_folder(
#         bucket_name=config("BUCKET_NAME"),
#         s3_folder=config("S3_FOLDER"),
#         aws_access_key_id=config("AWS_ACCESS_KEY_ID"),
#         aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"),
#         local_dir="model_data",
#         force_download=True
#     )
#     print(result)