from app.database import supabase
import json

def check_auto_reply():
    print("Checking Conversations...")
    convs = supabase.table("conversations").select("*").execute()
    print(f"Total Conversations: {len(convs.data)}")
    for c in convs.data:
        print(f"Conv ID: {c['id']}, User ID: {c['user_id']}, Pet ID: {c['pet_id']}")
    
    print("\nChecking Messages...")
    msgs = supabase.table("messages").select("*").execute()
    print(f"Total Messages: {len(msgs.data)}")
    for m in msgs.data:
        print(f"Msg ID: {m['id']}, Conv ID: {m['conversation_id']}, Sender ID: {m['sender_id']}, Content: {m['content']}")

if __name__ == "__main__":
    check_auto_reply()
