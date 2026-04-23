import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

email = "doctor@test.com"
password = "password123"

print("Creating test doctor account...")
try:
    # 1. Register
    res = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    user_id = res.user.id
    print(f"Created user in Auth: {user_id}")
    
    # 2. Make them a doctor in profiles
    supabase.table("profiles").update({
        "is_doctor": True,
        "doctor_id": 1,
        "name": "Ananya Reddy"
    }).eq("id", user_id).execute()
    
    print("\n✅ Success! You can now log into doctors_page.html with:")
    print(f"Email: {email}")
    print(f"Password: {password}")
except Exception as e:
    print(f"Note: If user already exists, please delete them in Supabase or use a different email.")
    print(f"Error details: {e}")
