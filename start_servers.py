import os
import subprocess
import sys

#python start_servers.py

def start_servers():
    commands = [
        ("Django Server", ["python", "manage.py", "runserver"]),
        ("Celery Worker", ["celery", "-A", "config", "worker", "--pool=solo"]),
        ("Celery Beat", ["celery", "-A", "config", "beat"]),
        ("Redis Server", ["redis-server"])
    ]
    
    for title, cmd in commands:
        if sys.platform == "win32":
            subprocess.Popen(['start', title] + cmd, shell=True)
        else:
            subprocess.Popen(['gnome-terminal', '--title', title, '--', 'bash', '-c', ' '.join(cmd) + '; exec bash'])

if __name__ == "__main__":
    start_servers()