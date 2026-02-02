from app.database import supabase

def check_data():
    apps = supabase.table("applications").select("*").execute()
    print("--- Applications ---")
    for app in apps.data:
        print(app)
        
    convs = supabase.table("conversations").select("*").execute()
    print("\n--- Conversations ---")
    for conv in convs.data:
        print(conv)
        
    msgs = supabase.table("messages").select("*").execute()
    print("\n--- Messages ---")
    for msg in msgs.data:
        print(msg)

if __name__ == "__main__":
    check_data()
