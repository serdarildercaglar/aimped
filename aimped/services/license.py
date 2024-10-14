import requests
from cryptography.hazmat.primitives import serialization
import jwt
from datetime import datetime, timezone, timedelta
from decouple import config

LICENSE_MANAGER_URL = config("LICENSE_MANAGER_URL")
# LICENSE_MANAGER_URL = "http://44.223.95.254:8000"

class PublicKeyManager:
    """
    Singleton class to manage and validate public keys for JWT token validation.

    Attributes:
        MAX_RETRIES (int): The maximum number of retries to check License Manager health.
        RETRY_DELAY (int): The delay in seconds between each retry attempt.
        _instance (PublicKeyManager): Singleton instance of the PublicKeyManager class.
        _public_key (str): The public key used for JWT token validation.

    Methods:
        get_public_key(model_name): Retrieves the public key for a given model.
        check_license_manager_health(): Checks the health status of the License Manager.
        request_public_key(model_name): Requests the public key from the License Manager.
        validate_token(token): Validates a given JWT token.
    """

    MAX_RETRIES = 5
    RETRY_DELAY = 5  # seconds
    _instance = None
    _public_key = None

    def __new__(cls, *args, **kwargs):
        """
        Ensures that only one instance of PublicKeyManager exists (singleton pattern).

        Returns:
            PublicKeyManager: The singleton instance of the PublicKeyManager class.
        """
        if not cls._instance:
            cls._instance = super(PublicKeyManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def get_public_key(self, model_name):
        """
        Retrieves the public key for the specified model. If the public key is not already cached,
        it checks the License Manager's health and requests a new public key.

        Args:
            model_name (str): The name of the model for which the public key is needed.

        Returns:
            str: The public key.
        """
        if not self._public_key:
            self.check_license_manager_health()
            self.request_public_key(model_name)
        return self._public_key

    def check_license_manager_health(self):
        """
        Checks the health status of the License Manager by making multiple attempts to contact it.

        Raises:
            Exception: If the License Manager cannot be contacted after the maximum number of retries.

        Returns:
            bool: True if the License Manager is reachable, otherwise raises an exception.
        """
        for _ in range(self.MAX_RETRIES):
            try:
                response = requests.get(f"{LICENSE_MANAGER_URL}/aimped/ok/")
                response.raise_for_status()
                return True
            except requests.RequestException as e:
                print(f"Error checking License Manager health: {e}")
                time.sleep(self.RETRY_DELAY)
        raise Exception("Failed to contact License Manager after multiple attempts")

    def request_public_key(self, model_name):
        """
        Requests the public key for the specified model from the License Manager.

        Args:
            model_name (str): The name of the model for which the public key is needed.

        Raises:
            Exception: If the request for the public key fails.
        """
        try:
            response = requests.post(
                f"{LICENSE_MANAGER_URL}/aimped/credentials/",
                json={"model_name": model_name}
            )
            data = response.json()
            response.raise_for_status()
            self._public_key = data.get("public_key").strip()
            print('New public key received: ', self._public_key)
        except requests.RequestException as e:
            if data.get('message'):
                raise Exception(data.get('message'))
            print(f"Error requesting public key: {e}")
            raise Exception("Failed to request public key from License Manager")

    def validate_token(self, token):
        """
        Validates the provided JWT token using the public key associated with the token's model name.

        Args:
            token (str): The JWT token to be validated.

        Raises:
            jwt.ExpiredSignatureError: If the token has expired.
            jwt.InvalidTokenError: If the token is invalid.
            Exception: For other validation errors.

        Returns:
            dict: The decoded token if validation is successful.
        """
        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            model_name = decoded_token.get("model_name")
            public_key_pem = self.get_public_key(model_name)
            print('public_key :', public_key_pem)
            public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
            decoded_token = jwt.decode(token, public_key, algorithms=['RS256'])
            exp = decoded_token.get('exp')
            if exp and datetime.now(timezone.utc) >= datetime.fromtimestamp(exp, timezone.utc):
                raise jwt.ExpiredSignatureError("Token has expired")
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise
        except jwt.InvalidTokenError:
            raise
        except Exception as e:
            raise Exception(f"Token validation error: {e}")