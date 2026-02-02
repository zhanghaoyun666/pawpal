from dotenv import load_dotenv
import os

# Explicitly point to the .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"SUPABASE_URL found: '{url}'")
print(f"SUPABASE_KEY found length: {len(key) if key else 0}")

if url == "your_supabase_url":
    print("ERROR: Still seeing placeholder value!")
else:
    print("SUCCESS: Values seem updated.")
