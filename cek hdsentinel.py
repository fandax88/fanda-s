import paramiko

# Fungsi untuk mendeteksi model HDD berdasarkan Model ID
def identify_hdd_model(model_id):
    if model_id == "ST2000LX001-1RG174" or model_id == "ST2000DX002-2DV164":
        return "HDD Firecuda"
    elif model_id == "ST2000LM015-2E8174":
        return "HDD Baracuda"
    elif model_id == "ST2000NM000B-2TD100":
        return "HDD Exos"
    elif model_id == "CT2000MX500SSD1":
        return "SSD Crucial"
    elif model_id == "ST2000DM006-2DM164":
        return "HDD Baracuda"
    elif model_id == "WDC WD2003FZEX-00SRLA0":
        return "HDD WD"
    else:
        return "Tidak Dikenal"

def transfer_and_run_hdsentinel(ip, password, local_path, remote_path):
    # Membuat koneksi SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(hostname=ip, username="root", password=password)

        # Menggunakan SCP untuk mentransfer file HDSentinel
        scp_client = paramiko.SFTPClient.from_transport(ssh_client.get_transport())
        scp_client.put(local_path, f"{remote_path}/hdsentinel-017-x64")

        # Mengubah izin file HDSentinel
        ssh_client.exec_command(f"chmod +x {remote_path}/hdsentinel-017-x64")

        # Menjalankan HDSentinel
        stdin, stdout, stderr = ssh_client.exec_command(f"{remote_path}/hdsentinel-017-x64")
        output = stdout.read().decode("utf-8")

        print("Output dari HDSentinel:")
        print(output)

        # Mendapatkan Model ID dari output HDSentinel
        model_id = None
        lines = output.split('\n')
        for line in lines:
            if "HDD Model ID" in line:  # Menemukan baris yang mencantumkan Model ID
                model_id = line.split(":")[-1].strip()
                break

        # Mengidentifikasi model HDD berdasarkan Model ID
        if model_id:
            model_name = identify_hdd_model(model_id)
            print(f"\nModel HDD/SSD: {model_name}")
        else:
            print("\nModel HDD/SSD tidak ditemukan.")

        # Menjalankan perintah lshw untuk mendapatkan informasi perangkat keras
        stdin, stdout, stderr = ssh_client.exec_command("lshw -class disk")
        disk_info = stdout.read().decode("utf-8")
        print("\nInformasi Disk (lshw):")
        print(disk_info)

        # Menjalankan perintah lsblk untuk mendapatkan informasi block devices
        stdin, stdout, stderr = ssh_client.exec_command("lsblk")
        lsblk_output = stdout.read().decode("utf-8")
        print("\nInformasi Block Devices (lsblk):")
        print(lsblk_output)

    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")
    finally:
        ssh_client.close()

if __name__ == "__main__":
    # Meminta input IP dan password dari pengguna
    ip = input("Masukkan IP server tujuan: ")
    password = input("Masukkan password: ")

    # Lokasi file HDSentinel di lokal dan di server tujuan
    local_path = "/opt/hdsentinel-017-x64"
    remote_path = "/opt"

    # Memanggil fungsi untuk mentransfer file HDSentinel dan menjalankannya di server tujuan
    transfer_and_run_hdsentinel(ip, password, local_path, remote_path)
