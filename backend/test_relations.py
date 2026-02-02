from app.database import supabase

def test_relations():
    print("Test 1: pet:pet_id(*)")
    try:
        res = supabase.table("applications").select("*, pet:pet_id(*)").limit(1).execute()
        print("Success 1!")
        print(f"Data: {res.data[0].get('pet')}")
    except Exception as e:
        print(f"Fail 1: {e}")

    print("\nTest 2: pets(*)")
    try:
        res = supabase.table("applications").select("*, pets(*)").limit(1).execute()
        print("Success 2!")
    except Exception as e:
        print(f"Fail 2: {e}")

if __name__ == "__main__":
    test_relations()
