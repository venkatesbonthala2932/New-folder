import os
from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.environ.get('https://adxylnurovyjsfccofhd.supabase.co')
SUPABASE_SERVICE_KEY = os.environ.get('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFkeHlsbnVyb3Z5anNmY2NvZmhkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQ4MjEwMCwiZXhwIjoyMDkxMDU4MTAwfQ.1Xi-C-oCMQxmDVoEvDoswOcHCAjJMZpy93OnBrI0TaU')

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Missing Supabase credentials in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Check existing doctors
try:
    res = supabase.table('doctors').select('*').execute()
    if res.data and len(res.data) > 0:
        print(f"Found {len(res.data)} existing doctors. Adding a few more just in case.")
    
    # Insert dummy doctors
    doctors = [
        {
            "name": "Dr. Ananya Reddy",
            "specialty": "Cardiology",
            "qualification": "MBBS, MD - Cardiology",
            "experience": "15+ Years",
            "fees": 1500,
            "available_days": "Mon,Tue,Wed,Thu,Fri",
            "slots": "Morning (10AM-1PM),Evening (4PM-7PM)"
        },
        {
            "name": "Dr. Vikram Rao",
            "specialty": "Orthopaedics",
            "qualification": "MS Ortho, MCh (Ortho)",
            "experience": "20+ Years",
            "fees": 1200,
            "available_days": "Mon,Wed,Fri",
            "slots": "Morning (10AM-1PM)"
        },
        {
            "name": "Dr. Sai Pallavi",
            "specialty": "Paediatrics",
            "qualification": "MD Paediatrics",
            "experience": "12+ Years",
            "fees": 1000,
            "available_days": "Tue,Thu,Sat",
            "slots": "Evening (4PM-7PM)"
        },
        {
            "name": "Dr. Ramesh Babu",
            "specialty": "Neurology",
            "qualification": "DM Neurology",
            "experience": "18+ Years",
            "fees": 2000,
            "available_days": "Mon,Tue,Wed,Thu,Fri,Sat",
            "slots": "Morning (10AM-1PM),Evening (4PM-7PM)"
        },
        {
            "name": "Dr. Kavitha Kumari",
            "specialty": "Gynaecology",
            "qualification": "MD OBG",
            "experience": "14+ Years",
            "fees": 1100,
            "available_days": "Mon,Tue,Wed,Thu,Fri",
            "slots": "Morning (10AM-1PM),Evening (4PM-7PM)"
        }
    ]
    
    supabase.table('doctors').insert(doctors).execute()
    print("✅ Successfully inserted example doctors into the database!")
    
except Exception as e:
    print(f"❌ Error inserting doctors: {e}")
