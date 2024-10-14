# Author: Russell
# Date: 2021-12-11
import logging
try:
    import boto3
except ImportError as e:
    logging.warning(f"Please install the required dependencies for S3FileManager. {str(e)}")


class S3FileManager:
    """ Class to manage files in S3"""
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        self.s3 = boto3.client('s3',
                              aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key,
                              region_name=region_name)

    def write_file_to_s3(self, local_file_path, bucket_name, s3_file_path):
        """ Write a local file to S3"""
        try:
            self.s3.upload_file(local_file_path, bucket_name, s3_file_path)
            logging.info(f"File uploaded successfully to s3://{bucket_name}/{s3_file_path}")
        except Exception as e:
            logging.error(f"Error uploading file to S3: {e}")

            
    def download_file_from_s3(self, bucket_name, s3_file_path, local_file_path):
        """ Download a file from S3 to local"""
        try:
            self.s3.download_file(bucket_name, s3_file_path, local_file_path)
            logging.info(f"File downloaded successfully from s3://{bucket_name}/{s3_file_path} to {local_file_path}")
        except Exception as e:
            logging.error(f"Error downloading file from S3: {e}")



            
# if __name__ == "__main__":
#     from decouple import config
#     aws_access_key_id = config('AWS_ACCESS_KEY_ID')
#     aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY')
#     region_name = "us-east-1"
    
#     file_manager = S3FileManager(aws_access_key_id, aws_secret_access_key, region_name)
    
#     local_file_path = "test.json"
#     bucket_name = "www.aimped.ai"
#     s3_file_path = f"output/{'user_id'}/{'model_id'}/{'testx.json'}"
    
#     file_manager.write_file_to_s3(local_file_path, bucket_name, s3_file_path)
