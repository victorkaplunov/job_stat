"""Reload application script for GitHub Actions."""

import requests
import os


username = 'clingon'
TOKEN = os.getenv('PA_TOKEN')
headers = {'Authorization': f'Token {TOKEN}'}
base_url = f'https://www.pythonanywhere.com/api/v0/user/{username}/'

# Get first console ID
response = requests.get(base_url + 'consoles/', headers=headers)
print(response.json())
console_id = response.json()[0]['id']

# Send command to first console
command = {'input': 'cd /home/clingon/job_stat\n git pull --rebase\n'}
response = requests.post(base_url + f'consoles/{str(console_id)}/send_input/',
                         json=command, headers=headers)
print('send_input: ', command['input'])
print(response.status_code)
print(response.text)

# Get first webapps name
response = requests.get(base_url + 'webapps/', headers=headers)
domain_name = response.json()[0]['domain_name']
print(domain_name)

# Reload first webapps
response = requests.post(base_url + f'webapps/{domain_name}/reload/', headers=headers)
print(response.status_code)
