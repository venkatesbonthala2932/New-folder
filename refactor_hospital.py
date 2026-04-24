import re

with open('hospital_page.html', 'r') as f:
    html = f.read()

# 1. Update Navigation Links
nav_links_pattern = r'<nav class="nav-links">.*?</nav>'
new_nav_links = """<nav class="nav-links">
      <a href="/public_doctors.html" class="nav-link">Doctors</a>
      <a href="/public_appointment.html" class="nav-link">Specialties</a>
      <a href="/#services" class="nav-link">Services</a>
      <a href="/#about" class="nav-link">About Us</a>
      <a href="/public_appointment.html" class="nav-link">Appointment</a>
    </nav>"""
html = re.sub(nav_links_pattern, new_nav_links, html, flags=re.DOTALL)

# 2. Hide Guest Login/Register Buttons
nav_guest_pattern = r'<div id="navGuest" class="nav-user-area">.*?</div>'
new_nav_guest = """<div id="navGuest" class="nav-user-area" style="display:none;"></div>"""
# Since there are nested divs, regex might fail. Let's use exact replace if possible.
html = re.sub(r'<div id="navGuest" class="nav-user-area">[\s\S]*?</div>[\s\S]*?<!-- Shown when logged in -->', '<div id="navGuest" class="nav-user-area" style="display:none;"></div>\n      <!-- Shown when logged in -->', html)

# 3. Modify Hero Section
# Remove booking widget and add a primary button.
hero_pattern = r'<!-- Booking Widget -->.*?</div>\s*</div>\s*</section>'
new_hero_end = """<!-- Booking Widget Removed -->
    <div style="margin-top: 30px;">
      <a href="/public_appointment.html" class="btn-primary" style="padding: 15px 30px; font-size: 18px; border-radius: 8px; text-decoration: none;">Book Appointment</a>
    </div>
  </div>
</section>"""
html = re.sub(hero_pattern, new_hero_end, html, flags=re.DOTALL)

# Also remove the specific booking JS logic since it's no longer here.
js_pattern = r'// ── Multi-Step Booking Form ─────────────────────────────────────────.*?(?=\n// ── Utility ────────────────────────────────────────────────)'
html = re.sub(js_pattern, '', html, flags=re.DOTALL)

with open('hospital_page.html', 'w') as f:
    f.write(html)

print("hospital_page.html updated successfully!")
