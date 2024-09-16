"""Git pull and reload application script for GitHub Actions."""
from pythonanywhere_client import PythonAnywhereClient

pa = PythonAnywhereClient()

console_id = pa.get_first_console_id()
command = '''
clear
cd /home/clingon/job_stat
git pull --rebase
'''
pa.send_command_to_console(console_id=console_id, command=command)
pa.reload_webapps(domain_name=pa.get_domain_name())
print(pa.get_route(route='time_series'))
print(pa.get_route(route='salary_by_category'))
