import os

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import posixpath

from config import Config


class PythonAnywhereClient:
    """
    Client for pythonanyware.com API
    """
    def __init__(self, ):
        self.username = Config.PA_USERNAME
        self.headers = {'Authorization': f'Token {os.getenv("PA_TOKEN")}'}
        self.base_url = f'https://www.pythonanywhere.com/api/v0/user/{self.username}'
        self.site_url = f'https://{self.username}.pythonanywhere.com'
        self.app_dir = Config.PA_APP_DIR

    def get_file(self, file_name: str) -> int:
        url = posixpath.join(self.base_url, 'files/path/home/',
                             self.username, self.app_dir, file_name)
        response = requests.get(url, headers=self.headers)
        return response.status_code

    def upload_file(self, file_name: str) -> int:
        encoder = MultipartEncoder(
            [('content', (os.path.basename(file_name), open(file_name, 'rb'), 'text/plain'))],
            None)
        self.headers['Content-Type'] = encoder.content_type
        url = posixpath.join(self.base_url, 'files/path/home', self.username, self.app_dir, file_name)
        response = requests.post(url=url, data=encoder, headers=self.headers)
        return response.status_code

    def delete_file(self, file_name: str) -> int:
        url = posixpath.join(self.base_url, 'files/path/home', self.username, self.app_dir, file_name)
        response = requests.delete(url=url, headers=self.headers)
        return response.status_code

    def create_new_console(self) -> dict:
        url = posixpath.join(self.base_url, 'consoles/')
        response = requests.post(url, headers=self.headers)
        return response.json()

    def get_consoles_list(self) -> dict:
        url = posixpath.join(self.base_url, 'consoles/')
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_console_info(self, console_id: str) -> str:
        url = posixpath.join(self.base_url, f'consoles/{console_id}')
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_first_console_id(self) -> str:
        url = posixpath.join(self.base_url, 'consoles/')
        response = requests.get(url, headers=self.headers)
        return str(response.json()[0]['id'])

    def get_route(self, route: str) -> str:
        url = posixpath.join(self.site_url, route)
        response = requests.get(url, headers=self.headers)
        return str(response.status_code)

    def send_command_to_console(self, console_id: str, command: str) -> int:
        """
        Input format: 'pwd\n ls\n'
        Add a "\n" to the command line end for return.
        """
        command_json = {'input': f'{command}'}
        url = posixpath.join(self.base_url, f'consoles/{console_id}/send_input/')
        response = requests.post(url=url, json=command_json, headers=self.headers)
        return response.status_code

    def get_latest_output(self, console_id: str) -> str:
        url = posixpath.join(self.base_url, f'consoles/{console_id}/get_latest_output/')
        response = requests.get(url=url, headers=self.headers)
        return response.json()['output']

    def get_domain_name(self) -> str:
        url = posixpath.join(self.base_url, 'webapps/')
        response = requests.get(url=url, headers=self.headers)
        return response.json()[0]['domain_name']

    def reload_webapps(self, domain_name: str) -> int:
        url = posixpath.join(self.base_url, f'webapps/{domain_name}/reload/')
        response = requests.post(url=url, headers=self.headers)
        return response.status_code
