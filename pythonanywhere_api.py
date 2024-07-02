"""Git pull and reload application script for GitHub Actions."""
from pythonanywhere_client import PythonAnywhereClient

pa = PythonAnywhereClient()

console_id = pa.get_first_console_id()
command = 'clear\n cd /home/clingon/job_stat\n git pull --rebase\n'
pa.send_command_to_console(console_id=console_id, command=command)
domain_name = pa.get_first_webapps_name()
pa.reload_webapps(domain_name=domain_name)

