from app.database import supabase
from app.routers.chats import get_chats
import json

def debug_api_chats():
    # Test for Sarah (coordinator)
    sarah_id = '11111111-1111-1111-1111-111111111111'
    print(f"Chats for Sarah ({sarah_id}):")
    chats_sarah = get_chats(sarah_id)
    print(json.dumps(chats_sarah, indent=2, ensure_ascii=False))
    
    # Test for Test User (applicant)
    test_user_id = '00000000-0000-0000-0000-000000000000'
    print(f"\nChats for Test User ({test_user_id}):")
    chats_test = get_chats(test_user_id)
    print(json.dumps(chats_test, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    debug_api_chats()
