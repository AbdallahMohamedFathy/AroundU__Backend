from src.models.user import User

def test_attr():
    u = User()
    try:
        u.hashed_refresh_token = "test"
        print("Set successfully")
    except AttributeError as e:
        print(f"AttributeError: {e}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_attr()
