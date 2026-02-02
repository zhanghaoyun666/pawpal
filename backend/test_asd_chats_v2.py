from app.database import supabase
from app.routers.chats import get_chats

def verify_fix():
    # User asd ID
    asd_id = "08e77f74-292f-4427-af83-a331d55ec20d"
    print(f"Verifying fix for user asd ({asd_id})...")
    
    chats = get_chats(asd_id)
    print(f"Found {len(chats)} chats")
    for c in chats:
        print(f"Chat ID: {c['id']}")
        print(f"  Pet: {c['petName']}")
        print(f"  Participant: {c['otherParticipantName']}")
        print(f"  Role: {c['otherParticipantRole']}")
        print("-" * 20)

if __name__ == "__main__":
    verify_fix()
 Riverside
