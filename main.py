import paramiko
import os


def ssh_download_files(hostname, username, password, remote_path, local_path):
    try:
        # Initialize SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the server
        ssh.connect(hostname, username=username, password=password)
        
        # Initialize SFTP session
        sftp = ssh.open_sftp()
        
        # Ensure local directory exists
        os.makedirs(local_path, exist_ok=True)
        
        # List files in remote path
        remote_files = sftp.listdir(remote_path)
        
        if not remote_files:
            print(f"No files found in {remote_path}")
            return
        
        # Download each file
        for file_name in remote_files:
            remote_file_path = os.path.join(remote_path, file_name).replace('\\', '/')
            local_file_path = os.path.join(local_path, file_name)
            
            print(f"Downloading {file_name}...")
            sftp.get(remote_file_path, local_file_path)
            print(f"Downloaded {file_name} to {local_file_path}")
        
        print("All files downloaded successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close SFTP and SSH connections
        if 'sftp' in locals():
            sftp.close()
        if 'ssh' in locals():
            ssh.close()


if __name__ == "__main__":
    # Get user input
    hostname = "196.43.168.57"
    username = "hivemonitor"
    password = "Ad@mnea321"
    remote_path = "/var/www/html/ademnea_website/public/hivevideo/2_2023-06-06_170001.mp4"
    local_path = input("Enter local destination path (e.g., ./downloads): ")
    
    # Execute download
    ssh_download_files(hostname, username, password, remote_path, local_path)