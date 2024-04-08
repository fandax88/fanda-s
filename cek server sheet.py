import paramiko
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Inisialisasi klien SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.20.116', username='root', password='rahasiats')

# Mengatur koneksi ke Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('update-gpu-882d30fa3cd7.json', scope)
client = gspread.authorize(creds)
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1x4Rh5K1n7iL8dcIwJR-0yVsvU64K58-qERMen2yy9oY/edit?usp=sharing'
sheet = client.open_by_url(spreadsheet_url).sheet1

# Fungsi untuk mendapatkan kata sandi dari suatu IP
def getPass(ip):
    try:
        # Menjalankan perintah 'ssbb' pada remote server
        stdin, stdout, stderr = ssh.exec_command('ssbb')
        # Mengirimkan alamat IP ke perintah 'ssbb'
        stdin.write(f'{ip}\n')
        # Membaca hasil output untuk mendapatkan kata sandi
        output = stdout.read().decode('utf-8').strip()
        if '[35m' in output and '[0m' in output:
            password = output.split("[35m")[1].split('[0m')[0]
            return [ip, password]
        else:
            print(f'No password found for {ip}')
            return 0
    except Exception as e:
        # Menangani kesalahan jika terjadi
        print(f"Error: {e}")
        return 0

# Fungsi untuk mendapatkan informasi GPU menggunakan nvidia-smi
def get_gpu_info():
    try:
        stdin, stdout, stderr = ssh.exec_command("nvidia-smi --query-gpu=name --format=csv,noheader")
        gpu_names = stdout.readlines()
        gpu_info = {}
        for name in gpu_names:
            name = name.strip()
            if name in gpu_info:
                gpu_info[name] += 1
            else:
                gpu_info[name] = 1
        return gpu_info
    except Exception as e:
        print(f"Error: {e}")
        return "No GPU information available."

# Fungsi untuk mendapatkan serial number server
def get_serial_number():
    try:
        stdin, stdout, stderr = ssh.exec_command('dmidecode -s system-serial-number')
        serial_number = stdout.read().decode('utf-8').strip()
        return serial_number
    except Exception as e:
        print(f"Error: {e}")
        return "Serial number not available."

# Membuka file yang berisi daftar alamat IP
with open('inputIp.txt', 'r') as ipAddresses:
    ipWithPass = []

    # Membaca setiap baris dari file alamat IP
    for ip in ipAddresses:
        ip = ip.strip()
        haved = getPass(ip)
        count = 0
        # Mengulang percobaan hingga 3 kali jika terjadi kesalahan
        while haved == 0 and count < 3:
            haved = getPass(ip)
            count += 1
        # Menambahkan IP dan kata sandi ke dalam list jika berhasil
        if isinstance(haved, list):
            ipWithPass.append(haved)

outputRes = []
# Menambahkan informasi IP dan password yang berhasil
for ip, password in ipWithPass:
    outputRes.append([ip, password])
    try:
        ssh.connect(ip, username='root', password=password)
        # Mendapatkan informasi server
        stdin, stdout, stderr = ssh.exec_command('hostname')
        hostname = stdout.read().decode('utf-8').strip()
        outputRes[-1].append(hostname)

        # Mendapatkan informasi CPU, RAM, HDD, OS, dan Type Server
        server_info = {'CPU': '', 'RAM': '', 'HDD': '', 'OS': '', 'Type Server': ''}
        commands = [
            'lscpu | grep "CPU(s)" | head -n 1',
            'free -h | grep Mem | awk \'{print $2}\'',
            'lsblk | grep disk | wc -l',
            'hostnamectl | grep "Operating System"',
            'dmidecode -t system | grep "Product Name"'
        ]
        for command in commands:
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode('utf-8').strip()
            if command.startswith('lscpu'):
                server_info['CPU'] = output.split(':')[1].strip()
            elif command.startswith('free'):
                server_info['RAM'] = output
            elif command.startswith('lsblk'):
                server_info['HDD'] = f"{output} x 2TB"
            elif command.startswith('hostnamectl'):
                server_info['OS'] = output.split(':')[1].strip()
            elif command.startswith('dmidecode'):
                server_info['Type Server'] = output
        for key, value in server_info.items():
            outputRes[-1].append(value)

        # Mendapatkan informasi GPU
        gpu_info = get_gpu_info()
        gpu_output = ', '.join([f"{count} x {name}" for name, count in gpu_info.items()])
        outputRes[-1].append(gpu_output)

        # Mendapatkan serial number server
        serial_number = get_serial_number()
        outputRes[-1].append(serial_number)

        # Menyimpan data ke Google Sheets
        sheet.append_row(outputRes[-1])

    except Exception as err:
        # Menangani kesalahan jika terjadi
        print(f'Error {ip} :', err)

# Menutup koneksi SSH
ssh.close()
