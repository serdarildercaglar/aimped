import requests
from typing import Any, Dict, Callable, Optional
from datetime import datetime
import os
import time
from aimped.services.auth_service import Connect
# from aimped.a3mconnect import A3mConnect


class AimpedAPI(Connect):
    """
    Class representing a connection to the Aimped API, extending A3mConnect.

    Args:
        user_key (str): User key for authentication.
        user_secret (str): User secret for authentication.
        options (dict): Additional options for the connection.
    """

    def __init__(self, user_key, user_secret, options):
        """
        Initialize Aimped instance.

        Args:
            user_key (str): User key for authentication.
            user_secret (str): User secret for authentication.
            options (dict): Additional options for the connection.
        """
        super().__init__(user_key, user_secret, options)

    def run_model(self, model_id: int, payload: Dict[str, Any]) -> Any:
        """
        Run a model prediction.

        Args:
            model_id (int): The ID of the model to run.
            payload (dict): Input payload for the model.

        Returns:
            Any: Result of the model prediction.
        """
        try:
            if self.is_connected():
                headers = {
                    'Authorization': f'Bearer {self.token_data["access_token"]}',
                    'Content-Type': 'application/json',
                }
                # print("istek atıldı")
                result = requests.request(
                    'POST',
                    f'{self.options["base_url"]}/pub/backend/api/v1/model_run_prediction/{model_id}/',
                    json=payload, headers=headers
                )

                return result.json()

        except requests.exceptions.RequestException as e:
            raise Exception(e)

    def get_pod_log_result(self, model_id: int) -> Dict[str, Any]:
        """
        Get the result of the pod logs for a specific model.

        Args:
            model_id (int): The ID of the model.

        Returns:
            dict: Result of the pod logs.
        """
        try:
            result = requests.request(
                'GET',
                f'{self.options["base_url"]}/pub/backend/get_pod_log?model_id={model_id}&instance_id=&is_dedicated='
            )
            return result.json()
        except requests.exceptions.RequestException as e:
            raise Exception(e)

    def run_model_callback(
        self,
        model_id: int,
        payload: Dict[str, Any],
        callback: Callable[[str, str, str, Optional[str]], str]
    ) -> Any:
        """
        Run a model with a callback function to monitor its progress.

        Args:
            model_id (int): The ID of the model to run.
            payload (dict): Input payload for the model.
            callback (Callable): Callback function to monitor model progress.

        Returns:
            Any: Result of the model prediction.
        """
        try:
            if self.is_connected():
                callback(
                    event='start',
                    message='start model run',
                    time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                result = self.run_model(model_id, payload)
                return result

                keep_running = True
                while keep_running:
                    time.sleep(15)
                    pod_log_result = self.get_pod_log_result(model_id)

                    waiting = pod_log_result.get('waiting', '').replace(
                        'Container', '') if pod_log_result.get('waiting') else None

                    if waiting:
                        if waiting == 'CrashLoopBackOff':
                            callback(
                                event='error',
                                message='Model is CrashLoopBackOff.',
                                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            )
                            keep_running = False
                        else:
                            callback(
                                event='proccess',
                                message=f'Model is {waiting}',
                                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            )
                    elif pod_log_result.get('error'):
                        callback(
                            event='error',
                            message=pod_log_result['error'],
                            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )
                        keep_running = False

                    elif pod_log_result.get('running'):
                        time.sleep(10)
                        result = self.run_model(model_id, payload)
                        callback(
                            event='end',
                            message='ok',
                            data=result,
                            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )
                        keep_running = False
                    else:
                        callback(
                            event='proccess',
                            message='Waiting for model to be ready',
                            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )

        except Exception as e:
            callback(
                event='error',
                message=str(e),
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

    def file_upload(self, model_id: int, source: str):
        """
        Upload a file to the specified model.

        Args:
            model_id (int): The ID of the model.
            filepath (str): Path to the file to be uploaded.

        Returns:
            dict: Result of the file upload operation.
        """
        try:
            if self.is_connected():
                with open(source, 'rb') as file:
                    files = {'file': (os.path.basename(source), file)}
                    headers = {
                        'Authorization': f'Bearer {self.token_data["access_token"]}'
                    }
                    result = requests.post(
                        f'{self.options["base_url"]}/pub/backend/api/v1/file_upload/{model_id}',
                        files=files,
                        headers=headers,
                    )
                    return result.json()
        except requests.exceptions.RequestException as e:
            raise Exception(e)

    def file_download_and_save(self, source: str, target: str):
        """
        Download a file from the specified source and save it to the target.

        Args:
            filepath (str): Path to the file to be downloaded.
            destination (str): Path where the downloaded file will be saved.

        Returns:
            str: Path of the downloaded file.
        """
        try:
            if self.is_connected():
                headers = {
                    'Authorization': f'Bearer {self.token_data["access_token"]}',
                }
                result = requests.get(
                    f'{self.options["base_url"]}/pub/backend/api/v1/file_download?file={source}',
                    headers=headers,
                    stream=True,
                )

                with open(target, 'wb') as file:
                    for chunk in result.iter_content(chunk_size=128):
                        file.write(chunk)
                return target
        except requests.exceptions.RequestException as e:
            raise Exception(e)
