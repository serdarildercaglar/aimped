# Author: Russell C.
# Date: 2023-Sep-17
# Description: This is the utils file for the sound module.

import os
import io
import logging

try:
    from pydub import AudioSegment
except ImportError:
    raise ImportError("The 'pydub' library is required to use this module. You can install it with 'pip install pydub'.")

# Default values
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1

def mp3_mp4_to_wav(input_file, output_file, sample_rate=DEFAULT_SAMPLE_RATE):
    """
    Converts MP3/MP4 files to WAV format with optional sample rate conversion and mono channel.
    
    Args:
        input_file (str): Input audio file path (MP3/MP4).
        output_file (str): Output WAV file path.
        sample_rate (int): Target sample rate (default: 16000).
    """
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_channels(DEFAULT_CHANNELS)  # Convert to mono channel
        audio = audio.set_frame_rate(sample_rate)
        audio.export(output_file, format="wav")
        logging.info(f"Converted {input_file} to {output_file} with sample rate {sample_rate} and mono channel")
    except Exception as e:
        logging.error(f"Error converting {input_file} to WAV: {e}")

def cut_audio(input_file, output_file, start_time_ms, end_time_ms):
    """
    Cuts a portion of an audio file and saves it as a new WAV file.
    
    Args:
        input_file (str): Input audio file path (WAV).
        output_file (str): Output WAV file path.
        start_time_ms (int): Start time of the cut in milliseconds.
        end_time_ms (int): End time of the cut in milliseconds.
    """
    try:
        audio = AudioSegment.from_file(input_file)
        cut_audio = audio[start_time_ms:end_time_ms]
        cut_audio.export(output_file, format="wav")
        logging.info(f"Cut {input_file} and saved as {output_file}")
    except Exception as e:
        logging.error(f"Error cutting {input_file}: {e}")

def change_sample_rate(input_file, output_file, new_sample_rate=DEFAULT_SAMPLE_RATE):
    """
    Changes the sample rate of an audio file and saves it as a new WAV file.
    
    Args:
        input_file (str): Input audio file path (WAV).
        output_file (str): Output WAV file path.
        new_sample_rate (int): New sample rate (default: 16000).
    """
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_frame_rate(new_sample_rate)
        audio.export(output_file, format="wav")
        logging.info(f"Changed sample rate of {input_file} to {new_sample_rate} and saved as {output_file}")
    except Exception as e:
        logging.error(f"Error changing sample rate of {input_file}: {e}")

def change_channels(input_file, output_file, num_channels=DEFAULT_CHANNELS):
    """
    Changes the number of channels of an audio file and saves it as a new WAV file.
    
    Args:
        input_file (str): Input audio file path (WAV).
        output_file (str): Output WAV file path.
        num_channels (int): Number of channels (default: 1, mono).
    """
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_channels(num_channels)
        audio.export(output_file, format="wav")
        logging.info(f"Changed channels of {input_file} to {num_channels} channel(s) and saved as {output_file}")
    except Exception as e:
        logging.error(f"Error changing channels of {input_file}: {e}")

def get_audio_duration(input_file):
    """
    Gets the duration of an audio file in seconds.

    Args:
        input_file (str or bytes): Input audio file path (MP3/MP4/WAV) or binary data.

    Returns:
        float: Duration in seconds, or None if an error occurs.
    """
    if isinstance(input_file, str):
        # If input_file is a string (file path)
        try:
            audio = AudioSegment.from_file(input_file)
            duration_ms = len(audio)
            duration_seconds = duration_ms / 1000.0  # Convert to seconds
            return duration_seconds
        except Exception as e:
            error_message = f"Error getting duration of {input_file}: {e}"
            logging.error(error_message)
            return None
    elif isinstance(input_file, bytes):
        # If input_file is binary data
        try:
            audio = AudioSegment.from_file(io.BytesIO(input_file))
            duration_ms = len(audio)
            duration_seconds = duration_ms / 1000.0  # Convert to seconds
            return duration_seconds
        except Exception as e:
            error_message = f"Error getting duration from binary data: {e}"
            logging.error(error_message)
            return None
    else:
        error_message = "Unsupported input type. Please provide a file path (str) or binary data (bytes)."
        logging.error(error_message)
        return None

def get_audio_info(input_file):
    """
    Gets information about an audio file using pydub and Python standard libraries.
    
    Args:
        input_file (str): Input audio file path (MP3/MP4/WAV).
    
    Returns:
        dict: A dictionary containing audio information.
            - 'duration' (float): Duration in seconds.
            - 'sample_rate' (int): Sample rate in Hz.
            - 'channels' (int): Number of channels (1 for mono, 2 for stereo).
            - 'format' (str): Audio format (e.g., 'mp3', 'wav').
            - 'size' (int): File size in bytes.
    """
    audio_info = {}
    
    if not os.path.exists(input_file):
        error_message = f"File {input_file} does not exist."
        logging.error(error_message)
        return None
    
    try:
        audio = AudioSegment.from_file(input_file)
        
        # Duration in seconds
        duration = len(audio) / 1000  # Convert to seconds
        audio_info['duration'] = duration
        
        # Sample rate
        audio_info['sample_rate'] = audio.frame_rate
        
        # Number of channels
        audio_info['channels'] = audio.channels
        
        # Audio format
        audio_info['format'] = os.path.splitext(input_file)[-1][1:].lower()
        
        # File size
        audio_info['size'] = os.path.getsize(input_file)
        
        return audio_info
    except Exception as e:
        error_message = f"Error getting information for {input_file}: {e}"
        logging.error(error_message)
        return None

# if __name__ == "__main__":
#     input_file = "input.mp3"
#     output_file = "output.wav"

#     audio_info = get_audio_info(input_file)
#     if audio_info is not None:
#         logging.info(f"Audio info for {input_file}: {audio_info}")

#     mp3_mp4_to_wav(input_file, output_file)  # Using default sample rate and mono channel
#     cut_audio(output_file, "cut_output.wav", 1000, 4000)
#     change_sample_rate(output_file, "sample_rate_output.wav")  # Using default sample rate
#     change_channels(output_file, "channels_output.wav")  # Using default mono channel

#     duration = get_audio_duration(output_file)
#     if duration is not None:
#         logging.info(f"Duration of {output_file}: {duration} seconds")

#     audio_info = get_audio_info(output_file)
#     if audio_info is not None:
#         logging.info(f"Audio info for {output_file}: {audio_info}")
