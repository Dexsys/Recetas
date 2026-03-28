import paramiko
from pathlib import Path

env = {}
for ln in Path('.env').read_text(encoding='utf-8').splitlines():
    ln = ln.strip()
    if not ln or ln.startswith('#') or '=' not in ln:
        continue
    k, v = ln.split('=', 1)
    env[k.strip()] = v.strip().strip('"').strip("'")

host = '192.168.0.89'
user = 'ubuntu'
pw = env.get('DEPLOY_SSH_PASSWORD')
svc = env.get('DEPLOY_SERVICE_NAME', 'recetas')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, 22, user, pw, timeout=15)

commands = [
    f"systemctl status {svc}.service --no-pager -l",
    f"journalctl -xeu {svc}.service -n 80 --no-pager",
]

for cmd in commands:
    print(f"\n===== {cmd} =====")
    _, stdout, stderr = ssh.exec_command(f"echo '{pw}' | sudo -S {cmd}")
    print(stdout.read().decode(errors='ignore'))
    print(stderr.read().decode(errors='ignore'))

ssh.close()
