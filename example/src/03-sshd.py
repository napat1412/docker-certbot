import os

os.system('ssh-keygen -A')
os.system('exec /usr/sbin/sshd -D -e')
