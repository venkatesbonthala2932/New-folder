import re
import glob

files = ['hospital_page.html', 'public_doctors.html', 'public_appointment.html']

for file in files:
    with open(file, 'r') as f:
        html = f.read()
    
    # Restore the Login / Register buttons cleanly in the navbar
    old_guest = '<div id="navGuest" class="nav-user-area" style="display:none;"></div>'
    new_guest = """<div id="navGuest" class="nav-user-area">
        <button class="btn-book" onclick="openModal('loginModal')" style="background:transparent;color:var(--primary);border:none;font-weight:700;">Login</button>
        <button class="btn-book" onclick="openModal('registerModal')" style="background:var(--primary);color:#fff;border-radius:6px;padding:8px 16px;">Register</button>
      </div>"""
    
    html = html.replace(old_guest, new_guest)
    
    with open(file, 'w') as f:
        f.write(html)

print("Restored Login/Register buttons in the navigation bar successfully!")
