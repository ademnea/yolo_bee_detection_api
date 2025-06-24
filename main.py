import paramiko
import os
import sys

videos = [
    "1_2024-10-30_060006.mp4", "1_2023-04-10_100001.mp4", "1_2024-10-30_120006.mp4",
    "1_2023-04-10_105001.mp4", "1_2024-10-30_145008.mp4", "1-04-10_110001.mp4",
    "1_2024-10-30_180005.mp4", "1_2023-04-10_115001.mp4", "1_2024-10-31_000005.mp4",
    "1_2023-04-10_120001.mp4", "1_2024-10-31_060006.mp4"
]


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
        
        # Download only files in videos list
        downloaded_count = 0
        for file_name in remote_files:
            if file_name in videos:
                remote_file_path = os.path.join(remote_path, file_name).replace('\\', '/')
                local_file_path = os.path.join(local_path, file_name)
                
                print(f"Downloading {file_name}...")
                sftp.get(remote_file_path, local_file_path)
                print(f"Downloaded {file_name} to {local_file_path}")
                downloaded_count += 1
            else:
                print(f"Skipping {file_name} (not in videos list)")
        
        if downloaded_count == 0:
            print("No matching videos found in remote directory")
        else:
            print(f"Successfully downloaded {downloaded_count} video(s)!")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)
    finally:
        # Close SFTP and SSH connections
        if 'sftp' in locals():
            sftp.close()
        if 'ssh' in locals():
            ssh.close()


if __name__ == "__main__":
    # Configuration (use environment variables for sensitive data)
    hostname = os.getenv("SSH_HOST", "196.43.168.57")
    username = os.getenv("SSH_USER", "hivemonitor")
    password = os.getenv("SSH_PASS", "Ad@mnea321")  # WARNING: Hardcoding passwords is insecure
    remote_path = "/var/www/html/ademnea_website/public/hivevideo"
    
    # Set local_path to the script's directory
    local_path = os.path.dirname(os.path.abspath(__file__))

    # Execute download
    ssh_download_files(hostname, username, password, remote_path, local_path)