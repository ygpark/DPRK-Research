import requests
import os
import json
from datetime import datetime

class PCLOUD:
    def __init__(self):
        #self.token = "u5ws7ZqHXFEmAWBDSZKqE8ykZyxN4oNUtNg49SYA9urDPzVtDQL2k"
        #self.token = "EOyR7ZSu06QWdXYIYZf3kbG7ZFV6p3o4wE3QSqTUC1NWE57c40KIk"
        #self.token = "v2m17ZRTsyGt6W1YbZ42NaykZg3YkJBuCr8Vuj3Vs7fVs07KejPhy"
        self.token = "Poz17Z5rmhrc0S5SSZJIfPykZBBY1K3GcDmXzwM2kSaK1wfoS40zX"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.bot_id = ""

    def create_unique_folder(self, base_path):
        folder_path = base_path
        counter = 1
        while os.path.exists(folder_path):
            folder_path = f"{base_path} ({counter})"
            counter += 1
        os.makedirs(folder_path)
        return folder_path
    
    def get_pcloud_user_info(self):
        try:
            url = "https://api.pcloud.com/userinfo"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
    
    def get_pcloud_file_list(self, folder_id=None):
        try:
            url = "https://api.pcloud.com/listfolder"
            params = {
                "folderid": folder_id if folder_id else 0
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            print(f"get_pcloud_file_list Error: {e}")
            return None
        
    def print_file_list(self, file_list):
        if not file_list:
            print("No files found.")
            return

        print("File List:")
        for item in file_list["metadata"]["contents"]:
            print(f"Name: {item['name']}")
            print(f"FileID: {item['id']}")
            print(f"Is Folder: {item['isfolder']}")
            if item['isfolder'] != False:
                print(f"Folder ID : {item['folderid']}")
            else:
                print(f"File Size: {item['size']}")
            print(f"Create Time: {item['created']}")
            print("---------------")

    def create_pcloud_folder(self, folder_name, parent_folder_id=None):
        try:
            url = "https://api.pcloud.com/createfolder"
            data = {
                "name": folder_name,
                "folderid": parent_folder_id if parent_folder_id else 0
            }
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            data = response.json()
            return data["metadata"]["id"].replace("d","")
        except requests.exceptions.RequestException as e:
            print(f"create_pcloud_folder Error: {e}")
            return None
    
    def upload_to_pcloud(self, local_file_path, remote_folder_id=None):
        try:
            url = "https://api.pcloud.com/uploadfile"
            if self.encrypt_file(local_file_path, local_file_path + ".tmp"):
                local_file_path = local_file_path + ".tmp"
            data = {
                "file": (local_file_path.split("/")[-1], open(local_file_path, "rb"))
            }
            params = {
                "folderid": remote_folder_id if remote_folder_id else 0
            }
            response = requests.post(url, headers=self.headers, files=data, params=params)
            response.raise_for_status()
            data = response.json()
            os.remove(local_file_path)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            os.remove(local_file_path)
            return None
        
   
    # def get_pcloud_oauth2_token(self):
    #     url = f"https://u.pcloud.com/oauth2/authorize?client_id={self.client_id}&response_type=code" # get Code
    #     print(url)
    #     url = f"https://api.pcloud.com/oauth2_token?client_id={self.client_id}&client_secret={self.cliend_secret}&code={self.code}"
    #     print(url)

    def download_pcloud_file(self, file_id, save_path):
        try:
            url = f"https://api.pcloud.com/getfilelink?fileid={file_id}&forcedownload=1"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            print(f"API Response for file {file_id}:")
            #print(json.dumps(data, indent=2))

            if 'error' in data:
                print(f"Error from pCloud API: {data['error']}")
                return

            if 'hosts' not in data or 'path' not in data:
                print("Unexpected API response format")
                return

            download_url = f"https://{data['hosts'][0]}{data['path']}"
            print(f"Download URL: {download_url}")

            download_response = requests.get(download_url)
            download_response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(download_response.content)

            print(f"File downloaded and saved to: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file {file_id}: {e}")
        except Exception as e:
            print(f"Unexpected error for file {file_id}: {e}")


    def download_all_files(self, folder_id=0, local_path=""):
        file_list = self.get_pcloud_file_list(folder_id)
        if not file_list:
            print(f"No files found in folder {folder_id}")
            return

        for item in file_list["metadata"]["contents"]:
            if item['isfolder']:
                new_folder = os.path.join(local_path, item['name'])
                os.makedirs(new_folder, exist_ok=True)
                print(f"Entering folder: {new_folder}")
                self.download_all_files(item['folderid'], new_folder)
            else:
                file_id = item['fileid']
                save_path = os.path.join(local_path, item['name'])
                print(f"Downloading file: {item['name']} (ID: {file_id})")
                self.download_pcloud_file(file_id, save_path)

    def banner(self):
        print("1. File List")
        print("2. Download File")
        print("3. Download All Files")

pcloud = PCLOUD()
print(pcloud.get_pcloud_user_info())

file_list = pcloud.get_pcloud_file_list()
pcloud.print_file_list(file_list)

while True:
    pcloud.banner()
    sel = input("Select > ")
    if sel == "1":
        folder_id = input("Input Folder ID : ")
        folder_id = int(folder_id.replace("d", ""))
        file_list = pcloud.get_pcloud_file_list(folder_id)
        pcloud.print_file_list(file_list)
    elif sel == "2":
        file_id = input("File ID : ")
        save_path = input("Save Path : ")
        pcloud.download_pcloud_file(file_id, save_path)
    elif sel == "3":
        # 현재 날짜와 토큰을 사용하여 폴더 이름 생성
        current_date = datetime.now().strftime("%Y-%m-%d")
        folder_name = f"{current_date} {pcloud.token[:8]}"  # 토큰의 첫 8자만 사용
        base_path = os.path.join(os.getcwd(), folder_name)
        
        # 유니크한 폴더 생성
        local_path = pcloud.create_unique_folder(base_path)
        
        print(f"Downloading all files to: {local_path}")
        pcloud.download_all_files(folder_id=0, local_path=local_path)
    else:
        print("Invalid selection")