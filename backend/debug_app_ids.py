from app.database import supabase

def check_everything():
    print("--- USERS ---")
    users = supabase.table("users").select("id, name, role").execute().data
    for u in users:
        print(f"User: {u['name']} (ID: {u['id']}) Role: {u['role']}")
        
    print("\n--- PETS ---")
    pets = supabase.table("pets").select("id, name, owner_id").execute().data
    for p in pets:
        print(f"Pet: {p['name']} (ID: {p['id']}) OwnerID: {p['owner_id']}")
        
    print("\n--- APPLICATIONS ---")
    apps = supabase.table("applications").select("*").execute().data
    for a in apps:
        print(f"App: {a['id']} PetID: {a['pet_id']} UserID: {a['user_id']} Name: {a['full_name']}")

    print("\n--- CONVERSATIONS ---")
    convs = supabase.table("conversations").select("*").execute().data
    for c in convs:
         print(f"Conv: {c['id']} PetID: {c['pet_id']} UserID: {c['user_id']}")

if __name__ == "__main__":
    check_everything()
