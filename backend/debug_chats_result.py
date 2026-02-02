from app.database import supabase
from app.routers.chats import get_chats

def check_asd_chats():
    # User asd ID
    asd_id = "08e77f74-292f-4427-af83-a331d55ec20d"
    print(f"Checking chats for user asd ({asd_id})...")
    
    chats = get_chats(asd_id)
    print(f"Found {len(chats)} chats")
    for c in chats:
        print(f"Chat ID: {c['id']}")
        print(f"  Pet: {c['petName']} (ID: {c['petId']})")
        print(f"  Opponent (Coordinator) Name: {c['coordinatorName']}")
        print(f"  Opponent (Coordinator) Image: {c['coordinatorImage']}")
        print(f"  Unread: {c['unreadCount']}")
        print("-" * 20)

if __name__ == "__main__":
    check_asd_chats()
