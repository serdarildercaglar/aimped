import os
import io
import base64
import json
import logging
import boto3
from botocore.exceptions import ClientError
from decouple import config
import re
logger = logging.getLogger(__name__)
try:
    from pydub import AudioSegment
    import cv2
except:
    pass

import requests
import uuid
from aimped.s3_file_manager import S3FileManager
############################################# LOGGER #############################################

def get_handler(log_file='KSERVE.log', log_level=logging.DEBUG):
    """Returns the logger object for logging the output of the server.
    Parameters:
    ----------------
    log_file: str
        The name of the log file to which the logs will be written.
    log_level: int
        The logging level (e.g., logging.DEBUG, logging.INFO, logging.ERROR).  
    Returns:
    ----------------
    logger: logging.Logger
        The configured logger object.
    """
    # Create a FileHandler for writing logs to the specified log_file.
    f_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
    # Define a log message format.
    formatter = logging.Formatter('[%(asctime)s %(filename)s:%(lineno)s] - %(message)s')
    # Set the formatter for the file handler.
    f_handler.setFormatter(formatter)
    # Set the logging level for the file handler.
    f_handler.setLevel(log_level)
    # Get the root logger.
    logger = logging.getLogger()
    # Set the logging level for the logger itself.
    logger.setLevel(log_level)
    # Add the file handler to the logger.
    logger.addHandler(f_handler)
    return logger

########################################### INPUT LIMIT CHECKER ######################################

class LimitChecker():

    def __init__(self):
        """LimitChecker class constructor"""
        pass
        
    def check_text(self, text_input, input_limit=3500):
        """ Checks if the text input is within the limit"""
        try:
            size = 0
            # text_input is a string
            if isinstance(text_input, str): 
                size = len(text_input)
            # text_input is a list of strings    
            elif isinstance(text_input, list): 
                size = sum(len(text) for text in text_input) 
            else:
                raise ValueError("Unexpected type for text_input. Expected string or a list of strings")
            return size <= input_limit  
        except:
            raise ValueError("An error occurred when processing text_input.")
            
    def check_audio(self, audio_input, input_limit=900, size=25, audio_format=""):
        """Checks if the audio input is within the limit. This needs pydub to be installed."""
        try:
            # First, check if the size is less than 25MB size
            if isinstance(audio_input, str) and os.path.getsize(audio_input) <= size * 1024 * 1024:
                return True
            elif isinstance(audio_input, bytes) and len(audio_input) <= size * 1024 * 1024:
                return True
            elif audio_format == "base64":
                decoded_audio = base64.b64decode(audio_input)
                if len(decoded_audio) <= size * 1024 * 1024:
                    return True

            # If the size check fails, proceed with the duration check
            if isinstance(audio_input, str) and os.path.isfile(audio_input):
                audio = AudioSegment.from_file(audio_input)
            elif isinstance(audio_input, bytes):
                audio = AudioSegment.from_file(io.BytesIO(audio_input))
            elif audio_format == "base64":
                audio = AudioSegment.from_file(io.BytesIO(base64.b64decode(audio_input)))
            else:
                raise ValueError("Unsupported input type. Please provide a file path (str) or binary data (bytes).")

            duration_seconds = len(audio) / 1000.0  # Convert to seconds
            return duration_seconds <= input_limit

        except Exception as e:
            raise ValueError(f"Error processing audio input: {str(e)}")

    def check_video(self, video_input, input_limit=900, size=25, video_format=""):
        """Checks if the video input is within the limit. This needs opencv-python to be installed."""
        try:
            # First, check if the size is less than 25MB size
            if isinstance(video_input, str) and os.path.getsize(video_input) <= size * 1024 * 1024:
                return True
            elif isinstance(video_input, bytes) and len(video_input) <= size * 1024 * 1024:
                return True
            elif video_format == "base64":
                decoded_video = base64.b64decode(video_input)
                if len(decoded_video) <= size * 1024 * 1024:
                    return True

            # If the size check fails, proceed with the duration check
            video = None
            if isinstance(video_input, str) and os.path.isfile(video_input):
                video = cv2.VideoCapture(video_input)
                total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
                frames_per_second = video.get(cv2.CAP_PROP_FPS)
                video_length_in_seconds = total_frames / frames_per_second
                return video_length_in_seconds <= input_limit

            elif video_format == "base64":
                video = cv2.VideoCapture(io.BytesIO(base64.b64decode(video_input)))
                return (video.get(cv2.CV_CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS) if video else 0) <= input_limit

        except Exception as e:
            raise ValueError(f"Error processing video input: {str(e)}")
        finally:
            if video:
                video.release()
    
    def check_images(self, images_list, input_limit=4):
        """ Checks if the number of images input is within the limit"""
        try:
            size = len(images_list)
            logging.info(f"Number of images: {size}")
            return size <= input_limit
        except:
            raise ValueError("Please provide a correct image list input")
            
    def check_pdf(self, pdf_input, input_limit=4, pdf_format=""):
        """ Checks if the number of pages in the pdf input is within the limit"""
        try:
            import PyPDF2
        except ImportError as e:
            print(f"Please install the required dependencies for input limit checker. {str(e)}")
        
        try:
            pdfReader = None
            if isinstance(pdf_input, str):
                # if the input is a file path
                if os.path.isfile(pdf_input):
                    pdfFileObj = open(pdf_input, 'rb')
                    pdfReader = PyPDF2.PdfReader(pdfFileObj)
            elif isinstance(pdf_input, bytes):
                # if the input is bytes (binary)
                pdfFileObj = io.BytesIO(pdf_input)
                pdfReader = PyPDF2.PdfReader(pdfFileObj)
            elif pdf_format.lower() == "base64":
                # if the input is base64 string
                pdfFileObj = io.BytesIO(base64.b64decode(pdf_input))
                pdfReader = PyPDF2.PdfReader(pdfFileObj)
            else:
                raise ValueError("Unsupported input type. Please provide a file path (str), binary data (bytes), or base64 string")

            if pdfReader:
                return len(pdfReader.pages) <= input_limit
        except Exception as e:
            raise ValueError(f"Error processing PDF. {str(e)}.")
      
    def check_dicom(self, dicom_list, input_limit=4):
        """ Checks if the number of dicom files input is within the limit"""
        try:
            size = len(dicom_list)
            logging.info(f"Number of dicom files: {size}")
            return size <= input_limit
        except:
            raise ValueError("Please provide a correct dicom list")
                  
         
# if __name__ == "__main__":
#     checker = LimitChecker()
# #     text = "This is a text"
# #     print("Text: {}".format(checker.check_text(text)))
#     # audio = "audio_gt_25mb.mp3"
#     # audio = "audio_lt_25mb.mp3"
#     # print("Audio: {}".format(checker.check_audio(audio)))
# #     images = ["image1.jpg", "image2.jpg"]
# #     print("Images: {}".format(checker.check_images(images)))
# #     pdf = "pdf.pdf"
#     # print("PDF: {}".format(checker.check_pdf(pdf)))
#     # video = "audio_gt_25mb.mp3"
#     # print("Video: {}".format(checker.check_video(video)))
# #     dicom = ["dicom1.dcm", "dicom2.dcm"]
# #     print("Dicom: {}".format(checker.check_dicom(dicom)))


########################################### Model Downloader ######################################


def download_model(bucket_name, s3_folder, aws_access_key_id, aws_secret_access_key, local_dir=None, force_download=False):
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
    else:
        if os.path.exists(local_dir) and os.listdir(local_dir):
            logger.info(f"Model directory is not empty: {local_dir}")
            return f'{local_dir}'
            
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
        return f"{local_dir}"
    
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



########################################### Payload Parser ######################################

def payload_is_valid(payload):
    if payload is None:
        raise ValueError("Payload is None")
    
    # GET INPUT
    try:
        if isinstance(payload, str):
            payload = json.loads(payload)
            return payload
        elif isinstance(payload, dict):
            return payload
        else:
            raise ValueError("Payload is not a JSON string or dictionary")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON: {str(e)}")


def determine_data_source(data):
    # S3 URI kontrolü (input/ ile başlar)
    if isinstance(data, str) and data.startswith("input/"):
        return "s3_uri"
    
    # URL kontrolü (http:// veya https:// ile başlar)
    url_pattern = re.compile(r'^(http://|https://)')
    if isinstance(data, str) and url_pattern.match(data):
        return "url"
    
    # Local path kontrolü (dosya mevcutsa)
    if isinstance(data, str) and os.path.exists(data):
        return "local_path"
    
    # Base64 kontrolü (Base64 string olup olmadığını kontrol eder)
    try:
        if isinstance(data, str):
            # Base64 string boşluk ve newline karakterlerinden temizlenir
            base64_bytes = base64.b64decode(data, validate=True)
            if base64_bytes:
                return "base64"
    except Exception:
        pass
    
    return "plain_text"

# # Örnek kullanım:
# data_list = [
#     "s3://bucket-name/file.txt",
#     "https://example.com/image.png",
#     "/mnt/sdb1/tasks/aimped-rev/notebooks/test.ipynb",
#     "aGVsbG8gd29ybGQ=",
#     "invalid data"
# ]

# results = [determine_data_source(data) for data in data_list]
# print(results)


# file_manager = S3FileManager( aws_access_key_id=config("AWS_ACCESS_KEY_ID"),
# 	                        aws_secret_access_key=config("AWS_SECRET_ACCESS_KEY"),
#                             region_name="us-east-1")

def get_file_type(file_path):
    return os.path.splitext(file_path)[1]

def process_payload(payload:str, file_manager):
    
    payload = payload_is_valid(payload)
    
    
    
    if not os.path.exists("input_data_folder"):
        os.makedirs("input_data_folder")
    
    aimped_file_type = payload.get("file_type",None)
    if not aimped_file_type:
        data_type = "data_json"
    elif aimped_file_type == "pdf":
        data_type = "data_pdf"
        file_extension = ".pdf"
    elif aimped_file_type == "txt":
        data_type = "data_txt"
        file_extension = ".txt"
    elif aimped_file_type == "image":
        data_type = "data_image"
        file_extension = ".jpg"
    elif aimped_file_type == "audio":
        data_type = "data_audio"
        file_extension = ".mp3"
    elif aimped_file_type == "dcm":
        data_type = "data_dicom"
        file_extension = ".dcm"
    elif aimped_file_type == "svg":
        data_type = "data_svg"
        file_extension = ".svg"
    

    
    
    valid_data_types = ["data_char", "data_pdf", "data_txt", "data_file", "data_json",
                        "data_image", "data_audio", "data_dicom", "data_svg"]
    if not data_type:
        raise ValueError("data_type is required")
    elif data_type not in valid_data_types:
        raise ValueError(f"Invalid data_type. Must be one of {valid_data_types}")   
    

    ################# Data JSON #################
    if data_type == "data_json":
        try:
            if payload["text"]:
                pass
        except:
            raise ValueError("text key is required in the payload")
        
        input_datas = payload.get("text", None)
        if not input_datas:
            raise ValueError("No data found in the payload.")
        
        if not isinstance(input_datas, list):
            raise ValueError("input must be a list of strings")
        
        data_sources = [determine_data_source(data) for data in input_datas]
        model_input = []
        for data_source, input_data in zip(data_sources, input_datas):
            if data_source == "plain_text":
                # control plain_text whether it is a local path or not
                if os.path.exists(input_data):
                    raise ValueError("data_json cannot be a file path. Only plain text is allowed.")
                else:
                    model_input.append(input_data)
            elif data_source == "s3 uri":
                raise ValueError("data_json cannot be a S3 URI. Only plain text is allowed.")
            elif data_source == "url":
                raise ValueError("data_json cannot be a URL. Only plain text is allowed.")
            elif data_source == "local_path":
                raise ValueError("data_json cannot be a local path. Only plain text is allowed.")
            elif data_source == "base64":
                raise ValueError("data_json cannot be a base64 string. Only plain text is allowed.")
        return model_input
    ################# Data Char #################    
    elif data_type == "data_char":
        pass # Todo: data_char için işlem yapılacak
    ################# Data PDF #################
    elif data_type == "data_pdf":
        if payload.get("file_type", None) != "pdf":
            raise ValueError("file_type must be pdf and list of data's key must be 'pdf'")
        input_datas = payload.get("pdf", None)
        if not input_datas:
            raise ValueError("No data found in the payload")
        if not isinstance(input_datas, list):
            raise ValueError("input must be a list")
        
        data_sources = [determine_data_source(data) for data in input_datas]

        model_input = []
        for data_source, input_data in zip(data_sources, input_datas):
            uniq_id = str(uuid.uuid4())
            if data_source == "plain_text": # 1
                # control plain_text whether it is a local path or not
                if os.path.exists(input_data):
                    if get_file_type(input_data) != ".pdf":
                        raise ValueError("data_pdf must be a PDF file")
                    model_input.append(input_data)
                else:
                    raise ValueError("data_pdf must be a file path or S3 URI or URL or base64 string.")
            elif data_source == "s3_uri": # 2
                if get_file_type(input_data) != ".pdf":
                    raise ValueError("data_pdf must be a PDF file")
                file_manager.download_file_from_s3(config("PRIVATE_BUCKET_NAME",default="aimped-model-files"), input_data,f"input_data_folder/{uniq_id}{file_extension}")
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "url": # 3
                if get_file_type(input_data) != ".pdf":
                    raise ValueError("data_pdf must be a PDF file")
                response = requests.get(input_data)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(response.content)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "local_path": # 4
                if get_file_type(input_data) != ".pdf":
                    raise ValueError("data_pdf must be a PDF file")
                model_input.append(input_data)
            elif data_source == "base64": # 5
                base64_bytes = base64.b64decode(input_data, validate=True)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(base64_bytes)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            else:
                raise ValueError("data_pdf must be a file path or S3 URI or URL or base64 string")
        return model_input
    ################# Data TXT #################
    elif data_type == "data_txt":
        if payload.get("file_type", None) != "txt":
            raise ValueError("file_type must be txt and list of data's key must be 'txt'")
        input_datas = payload.get("txt", None)
        if not input_datas:
            raise ValueError("No data found in the payload")
        if not isinstance(input_datas, list):
            raise ValueError("input must be a list")
        
        data_sources = [determine_data_source(data) for data in input_datas]

        model_input = []
        for data_source, input_data in zip(data_sources, input_datas):
            uniq_id = str(uuid.uuid4())            
            if data_source == "plain_text":
                # control plain_text whether it is a local path or not
                if os.path.exists(input_data):
                    if get_file_type(input_data) != ".txt":
                        raise ValueError("data_txt must be a TXT file")
                    model_input.append(input_data)
                else:
                    raise ValueError("data_txt must be a file path or S3 URI or URL or base64 string.")
            elif data_source == "s3_uri":
                if get_file_type(input_data) != ".txt":
                    raise ValueError("data_txt must be a TXT file")
                file_manager.download_file_from_s3(config("PRIVATE_BUCKET_NAME",default="aimped-model-files"), input_data,f"input_data_folder/{uniq_id}{file_extension}")
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "url":
                if get_file_type(input_data) != ".txt":
                    raise ValueError("data_txt must be a TXT file")
                response = requests.get(input_data)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(response.content)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "local_path":
                if get_file_type(input_data) != ".txt":
                    raise ValueError("data_txt must be a TXT file")
                model_input.append(input_data)
            elif data_source == "base64":
                base64_bytes = base64.b64decode(input_data, validate=True)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(base64_bytes)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            else:
                raise ValueError("data_txt must be a file path or S3 URI or URL or base64 string")
        return model_input
            
    ################# Data File #################
    
    elif data_type == "data_file":
        pass # Todo: data_file için işlem yapılacak  
    
    ################# Data Image #################
    elif data_type == "data_image":
        if payload.get("file_type", None) != "image":
            raise ValueError("file_type must be image and list of data's key must be 'image'")
        valid_img_extensions = [".jpg", ".jpeg", ".png"]
        input_datas = payload.get("image", None)
        if not input_datas:
            raise ValueError("No data found in the payload")
        if not isinstance(input_datas, list):  
            raise ValueError("input must be a list")
        
        data_sources = [determine_data_source(data) for data in input_datas]
        
        model_input = []
        for data_source, input_data in zip(data_sources, input_datas):
            uniq_id = str(uuid.uuid4())            
            if data_source == "plain_text":
                # control plain_text whether it is a local path or not
                if os.path.exists(input_data):
                    if get_file_type(input_data) not in valid_img_extensions:
                        raise ValueError("data_image must be a JPG, JPEG or PNG file")
                    model_input.append(input_data)
                else:
                    raise ValueError("data_image must be a file path or S3 URI or URL or base64 string")
            elif data_source == "s3_uri":
                if get_file_type(input_data) not in valid_img_extensions:
                    raise ValueError("data_image must be a JPG, JPEG or PNG file")
                file_manager.download_file_from_s3(config("PRIVATE_BUCKET_NAME",default="aimped-model-files"), input_data,f"input_data_folder/{uniq_id}{file_extension}")
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "url":
                if get_file_type(input_data) not in valid_img_extensions:
                    raise ValueError("data_image must be a JPG, JPEG or PNG file")
                response = requests.get(input_data)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(response.content)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "local_path":
                if get_file_type(input_data) not in valid_img_extensions:
                    raise ValueError("data_image must be a JPG, JPEG or PNG file")
                model_input.append(input_data)
            elif data_source == "base64":
                base64_bytes = base64.b64decode(input_data, validate=True)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(base64_bytes)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            else:
                raise ValueError("data_image must be a file path or S3 URI or URL or base64 string")
        return model_input
    ################# Data Audio #################
    elif data_type == "data_audio":
        if payload.get("file_type", None) != "audio":
            raise ValueError("file_type must be audio and list of data's key must be 'audio'")
        valid_audio_extensions = [".wav", ".mp3", ".mp4"]
        input_datas = payload.get("audio", None)
        if not input_datas:
            raise ValueError("No data found in the payload")
        if not isinstance(input_datas, list):
            raise ValueError("input must be a list")
        
        data_sources = [determine_data_source(data) for data in input_datas]
        
        model_input = []
        for data_source, input_data in zip(data_sources, input_datas):
            uniq_id = str(uuid.uuid4())            
            if data_source == "plain_text":
                # control plain_text whether it is a local path or not
                if os.path.exists(input_data):
                    if get_file_type(input_data) not in valid_audio_extensions:
                        raise ValueError("data_audio must be a WAV, MP3 or MP4 file")
                    model_input.append(input_data)
                else:
                    raise ValueError("data_audio must be a file path or S3 URI or URL or base64 string")
            elif data_source == "s3_uri":
                if get_file_type(input_data) not in valid_audio_extensions:
                    raise ValueError("data_audio must be a WAV, MP3 or MP4 file")
                file_manager.download_file_from_s3(config("PRIVATE_BUCKET_NAME",default="aimped-model-files"), input_data,f"input_data_folder/{uniq_id}{file_extension}")
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "url" and ("youtube.com" in input_data or "youtu.be" in input_data):
                model_input.append(input_data)
            elif data_source == "url":
                if get_file_type(input_data) not in valid_audio_extensions:
                    raise ValueError("data_audio must be a WAV, MP3 or MP4 file")
                response = requests.get(input_data)
                if response.status_code == 200:
                    with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                        f.write(response.content)
                    model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
                else:
                    raise ValueError("URL is not reachable")
            elif data_source == "local_path":
                if get_file_type(input_data) not in valid_audio_extensions:
                    raise ValueError("data_audio must be a WAV, MP3 or MP4 file")
                model_input.append(input_data)
            elif data_source == "base64":
                base64_bytes = base64.b64decode(input_data, validate=True)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(base64_bytes)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            else:
                raise ValueError("data_audio must be a file path or S3 URI or   URL or base64 string")
        return model_input
    ################# Data Dicom #################
    elif data_type == "data_dicom":
        if payload.get("file_type", None) != "dcm":
            raise ValueError("file_type must be dcm and list of data's key must be 'dcm'")
        input_datas = payload.get("dicom", None)
        if not input_datas:
            raise ValueError("No data found in the payload")
        if not isinstance(input_datas, list):
            raise ValueError("input must be a list")
        
        data_sources = [determine_data_source(data) for data in input_datas]
        
        model_input = []
        for data_source, input_data in zip(data_sources, input_datas):
            uniq_id = str(uuid.uuid4())            
            if data_source == "plain_text":
                # control plain_text whether it is a local path or not
                if os.path.exists(input_data):
                    if get_file_type(input_data) != ".dcm":
                        raise ValueError("data_dicom must be a DCM file")
                    model_input.append(input_data)
                else:
                    raise ValueError("data_dicom must be a file path or S3 URI or URL or base64 string")
            elif data_source == "s3_uri":
                if get_file_type(input_data) != ".dcm":
                    raise ValueError("data_dicom must be a DCM file")
                file_manager.download_file_from_s3(config("PRIVATE_BUCKET_NAME",default="aimped-model-files"), input_data,f"input_data_folder/{uniq_id}{file_extension}")
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "url":
                if get_file_type(input_data) != ".dcm":
                    raise ValueError("data_dicom must be a DCM file")
                response = requests.get(input_data)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(response.content)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            elif data_source == "local_path":
                if get_file_type(input_data) != ".dcm":
                    raise ValueError("data_dicom must be a DCM file")
                model_input.append(input_data)
            elif data_source == "base64":
                base64_bytes = base64.b64decode(input_data, validate=True)
                with open(f"input_data_folder/{uniq_id}{file_extension}", "wb") as f:
                    f.write(base64_bytes)
                model_input.append(f"input_data_folder/{uniq_id}{file_extension}")
            else:
                raise ValueError("data_dicom must be a file path or S3 URI or URL or base64 string")
        return model_input
    ################# Data SVG #################
    elif data_type == "data_svg":
        pass # Todo: data_svg için işlem yapılacak
    
    else:
        raise ValueError("Invalid data_type")
            
    
    
    
    
    
