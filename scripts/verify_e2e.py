import requests
import time
import os

API_URL = "http://localhost:8000/api/v1"

def run_verification():
    print("Waiting for API to be healthy...")
    for _ in range(30):
        try:
            resp = requests.get("http://localhost:8000/")
            if resp.status_code == 200:
                print("API is UP!")
                break
        except:
            time.sleep(2)
            print(".", end="", flush=True)
    else:
        print("\nAPI failed to start.")
        return

    # 1. Create User
    print("\n1. Creating User...")
    user_data = {"email": "test@example.com", "password": "password123", "full_name": "Test User"}
    resp = requests.post(f"{API_URL}/users/", json=user_data)
    if resp.status_code == 200:
        print("User created.")
    elif resp.status_code == 400 and "exists" in resp.text:
        print("User already exists.")
    else:
        print(f"Failed to create user: {resp.text}")
        return

    # 2. Login
    print("\n2. Logging in...")
    resp = requests.post(f"{API_URL}/login/access-token", data={"username": "test@example.com", "password": "password123"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in. Token acquired.")

    # 3. Upload Style PDF (Mock)
    print("\n3. Uploading Style PDF...")
    with open("dummy_style.pdf", "wb") as f:
        f.write(b"%PDF-1.4 mock pdf content")
    
    files = {"files": ("dummy_style.pdf", open("dummy_style.pdf", "rb"), "application/pdf")}
    resp = requests.post(f"{API_URL}/styles/upload", files=files, headers=headers)
    if resp.status_code == 200:
        print(f"Style uploaded: {resp.json()}")
    else:
        print(f"Style upload failed: {resp.text}")

    # 4. Upload Audio (Mock)
    print("\n4. Uploading Meeting Audio...")
    with open("dummy_meeting.mp3", "wb") as f:
        f.write(b"ID3 mock audio content")
    
    files = {"file": ("dummy_meeting.mp3", open("dummy_meeting.mp3", "rb"), "audio/mpeg")}
    resp = requests.post(f"{API_URL}/upload", files=files, headers=headers)
    if resp.status_code == 200:
        meeting = resp.json()
        print(f"Meeting uploaded. ID: {meeting['id']}, Status: {meeting['status']}")
    else:
        print(f"Meeting upload failed: {resp.text}")

    # Cleanup
    os.remove("dummy_style.pdf")
    os.remove("dummy_meeting.mp3")

if __name__ == "__main__":
    run_verification()
