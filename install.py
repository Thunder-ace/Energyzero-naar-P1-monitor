# script to install prijzen.py automated
#
# automatisch installeren van de prijzen.py OF prijzen_salderen.py voor P1 Monitor en de dynamische prijzen add-on
# WEL een paar zaken aanpassen (zie opmerkingen in code) !!!
#
# History:
# 1.0.0   01-03-2023  Initial version

"""
Copyright (c) 2023 by R.C.Bleeker
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import paramiko                 # misschien nog installeren in terminal > pip3 install paramiko
import re                       # misschien nog installeren in terminal > pip3 install re

# SSH credentials
hostname = '192.168.1.10'       # <--- verander naar het IP adres van je eigen P1 Monitor
username = 'p1mon'              # <--- verander naar je eigen login naam (standard = "p1mon")
password = 'verandermij'        # <--- verander naar je eigen paswoord (standard = "verandermij")

# SSH client setup
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Connect to SSH
ssh.connect(hostname=hostname, username=username, password=password)

# Check Python version
stdin, stdout, stderr = ssh.exec_command('python3 --version')
version_output = stdout.read().decode().strip()
match = re.match(r'Python\s+(\d+\.\d+\.\d+)', version_output)
if match:
    version_number = match.group(1)
    if version_number < '3.9.0':
        print(f"Python versie ({version_number}) is niet de juiste.")
        ssh.close()
        exit()
else:
    print(f"Kan de Python versie niet vaststellen : {version_output}")
    ssh.close()
    exit()


# Check if Energyzero is already installed
stdin, stdout, stderr = ssh.exec_command('pip3 freeze | grep energyzero')
output = stdout.read().decode().strip()

if 'energyzero' in output:
    print("Energyzero module is al geïnstalleerd.")
else:
    # Install Energyzero
    stdin, stdout, stderr = ssh.exec_command('pip3 install energyzero')
    output = stdout.read().decode().strip()
    if 'error' in output.lower():
        print("Er is een fout opgetreden bij het installeren van de Energyzero module :")
        print(output)
        ssh.close()
        exit()

# Copy prijzen.py to Raspberry Pi --------------------------------------------------------------------------------------

local_path = 'prijzen.py'                       # <--- zorg dat de locatie van prijzen.py correct is opgegeven
remote_path = '/p1mon/scripts/prijzen.py'       # <--- verander prijzen.py naar prijzen_salderen.py als u die versie gebruikt
                                                #      installeer NIET beide !

# ----------------------------------------------------------------------------------------------------------------------
try:
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()
except Exception as e:
    print(f"Er is een fout opgetreden bij het kopiëren van {local_path} : {e}")
    ssh.close()
    exit()

# Check if crontab already contains the Energyzero job
stdin, stdout, stderr = ssh.exec_command('crontab -l')
current_crontab = stdout.read().decode().strip()

if 'Energyzero_Update' in current_crontab:
    print("De crontab opdracht is al verwerkt.")
else:
    # Add job to crontab
    new_line = '5 * * * * /usr/bin/python3 /p1mon/scripts/prijzen.py >> /p1mon/var/tmp/update_prijzen_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1; ls -t /p1mon/var/tmp/update_prijzen_*.log | tail -n +25 | xargs rm -f # Energyzero_Update'
    updated_crontab = current_crontab + '\n' + new_line

    # Install updated crontab
    cmd = 'echo "' + updated_crontab + '" | crontab -'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode().strip()
    if 'error' in output.lower():
        print("Er is een fout opgetreden bij het toevoegen van de crontab opdracht :")
        print(output)
        ssh.close()
        exit()
    else:
        print("Opdracht is succesvol toegevoegd in de crontab.")



# Close file objects explicitly
stdout.close()
stderr.close()

# Close SSH connection
ssh.close()

print("Script is succesvol verwerkt.")
