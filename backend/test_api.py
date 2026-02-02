import requests
import json

def test_api():
    print("Testing /api/pets ...")
    try:
        r = requests.get("http://localhost:8000/api/pets")
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Error detail: {r.text}")
        else:
            data = r.json()
            print(f"Success! Found {len(data)} pets")
    except Exception as e:
        print(f"Failed to connect to /api/pets: {e}")

    print("\nTesting /api/users/favorites ...")
    try:
        r = requests.get("http://localhost:8000/api/users/favorites")
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Error detail: {r.text}")
        else:
            data = r.json()
            print(f"Success! Found {len(data)} favorites")
    except Exception as e:
        print(f"Failed to connect to /api/users/favorites: {e}")

if __name__ == "__main__":
    test_api()
