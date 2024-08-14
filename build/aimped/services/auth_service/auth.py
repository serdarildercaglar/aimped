import requests
from datetime import datetime


class Connect:
    """Class representing a connection to A3m API."""

    default_option = {
        'base_url': 'base_url',
        'scope': 'scope',
    }

    default_token_data = {
        'access_token': '',
        'refresh_token': '',
        'token_type': '',
        'expires_in': 0,
        'scope': '',
    }

    def __init__(self, user_key: str, user_secret: str, options):
        """
        Initialize A3mConnect instance.

        Parameters:
        - user_key (str): User key for authentication.
        - user_secret (str): User secret for authentication.
        - options (dict): Additional options for the connection.
        """
        self.user_key = user_key
        self.user_secret = user_secret
        # Merge default options with provided options
        self.options = {**self.default_option, **options}
        self.is_init = False
        self.token_data = {**self.default_token_data}
        self.time_data = {
            'token_time': None,
            'ref_token_time': None,
        }

    def get_user_keys(self):
        """
        Get user keys.

        Returns:
        dict: Dictionary containing user_key and user_secret.
        """
        return {
            'user_key': self.user_key,
            'user_secret': self.user_secret,
        }

    def get_options(self):
        """
        Get connection options.

        Returns:
        dict: Connection options.
        """
        return self.options

    def get_token_data(self):
        """
        Get token data.

        Returns:
        dict: Token data.
        """
        if not self.is_init:
            self.init()
        return self.token_data

    def is_token_expired(self):
        """
        Check if the access token is expired.

        Returns:
        bool: True if the access token is expired, False otherwise.
        """
        cur_date = datetime.utcnow()
        return (
            (cur_date - self.time_data['token_time']).total_seconds() >
            (self.token_data['expires_in'] - 180)
        )

    def is_ref_token_expired(self):
        """
        Check if the refresh token is expired.

        Returns:
        bool: True if the refresh token is expired, False otherwise.
        """
        cur_date = datetime.utcnow()
        return (cur_date - self.time_data['ref_token_time']).days > 6

    def get_all_data(self):
        """
        Get all data related to the connection.

        Returns:
        A3mConnect: A3mConnect instance.
        """
        if not self.is_init:
            self._init()
        return self

    def is_connected(self):
        """
        Check if the instance is connected and handle token refreshing.

        Returns:
        A3mConnect: A3mConnect instance.
        """
        try:
            if not self.is_init:
                return self.init()
            elif self.is_ref_token_expired():
                return self.init()
            elif self.is_token_expired():
                return self.refresh_access_token()
            else:
                return self
        except Exception as e:
            raise Exception(e)

    def init(self):
        """
        Initialize the connection and retrieve access and refresh tokens.

        Returns:
        A3mConnect: A3mConnect instance.
        """
        try:
            params = {
                'grant_type': 'password',
                'username': self.user_key,
                'password': self.user_secret,
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(
                f"{self.options['base_url']}/token", headers=headers,
                data=params
            )

            response_data = response.json()
            self.token_data = {**self.token_data, **response_data}
            self.time_data = {
                'token_time': datetime.utcnow(),
                'ref_token_time': datetime.utcnow(),
            }

            self.is_init = True
            return self
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error during initialization: {e}")

    def refresh_access_token(self):
        """
        Refresh the access token using the refresh token.

        Returns:
        A3mConnect: A3mConnect instance.
        """
        try:
            params = {
                'grant_type': 'refresh_token',
                'refresh_token': self.token_data['refresh_token'],
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            response = requests.post(
                f"{self.options['base_url']}/token", headers=headers,
                data=params
            )

            response_data = response.json()
            self.token_data = {**self.token_data, **response_data}
            self.time_data['token_time'] = datetime.utcnow()
            return self
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error refreshing access token: {e}")
