import requests
import os


username = 'clingon'
TOKEN = os.getenv('PA_TOKEN')
headers = {'Authorization': f'Token {TOKEN}'}
prefix = f'https://www.pythonanywhere.com/api/v0/user/{username}/'
print(prefix)
# response = requests.post(prefix, json={'executable': 'bash', "working_directory": 'job_stat'}, headers=headers)
# print(response.status_code)
# print(response.text)

# Get first console ID
response = requests.get(prefix + 'consoles/', headers=headers)
print(response.json())
console_id = str(response.json()[0]['id'])

# Send command to first console
command = {'input': 'cd ~\n cd job_stat\n git pull\n'}
response = requests.post(prefix + f'consoles/{console_id}/send_input/',
                         json=command, headers=headers)
print('send_input: ', response.status_code)

# Get first webapps name
response = requests.get(prefix + 'webapps/', headers=headers)
domain_name = response.json()[0]['domain_name']
print(domain_name)

# Reload first webapps
response = requests.post(prefix + f'webapps/{domain_name}/reload/', headers=headers)
print(response.status_code)
