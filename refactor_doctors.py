import re

with open('public_doctors.html', 'r') as f:
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
html = re.sub(r'<div id="navGuest" class="nav-user-area">[\s\S]*?</div>[\s\S]*?<!-- Shown when logged in -->', '<div id="navGuest" class="nav-user-area" style="display:none;"></div>\n      <!-- Shown when logged in -->', html)

# 3. Replace all sections between HERO and CONTACT with our new Doctors Directory
sections_pattern = r'<!-- HERO -->.*?<!-- CONTACT -->'
new_sections = """<!-- DOCTORS DIRECTORY -->
<section class="doctors-section" style="padding: 6rem 0; min-height: 70vh;">
  <div class="doctors-inner">
    <div class="section-center" style="margin-bottom: 4rem;">
      <h2 class="section-title">Meet Our Distinguished Experts</h2>
      <p class="section-desc">Consult with top-tier physicians recognized for their expertise and patient care.</p>
    </div>
    <div class="doctors-grid" id="publicDoctorsGrid">
      <p style="text-align: center; color: var(--on-surface-variant); grid-column: 1/-1;">Loading doctors...</p>
    </div>
  </div>
</section>
<!-- CONTACT -->"""
html = re.sub(sections_pattern, new_sections, html, flags=re.DOTALL)

# 4. Replace JS booking logic with public doctors fetch logic
js_pattern = r'// ── Multi-Step Booking Form ─────────────────────────────────────────.*?(?=\n// ── Utility ────────────────────────────────────────────────)'
new_js = """// ── Public Doctors Directory ─────────────────────────────────────────
async function loadPublicDoctors() {
  const grid = document.getElementById('publicDoctorsGrid');
  const res = await fetch(`${API}/api/doctors`).catch(() => null);
  if (!res) {
    grid.innerHTML = '<p style="text-align:center;color:var(--error);grid-column:1/-1;">Could not load doctors.</p>';
    return;
  }
  const data = await res.json();
  if (data.doctors.length === 0) {
    grid.innerHTML = '<p style="text-align:center;color:var(--on-surface-variant);grid-column:1/-1;">No doctors found.</p>';
    return;
  }

  // Define some placeholder avatars if real photos aren't available in DB
  const avatars = [
    "https://lh3.googleusercontent.com/aida-public/AB6AXuB63fIZNdWvjBTVdZrZyuYqVykk7RKt4MEuC3I1VsfnTOY-ZiAMj4dK_kETDpzOtV8SUK5iLY2CM4jygTSEl_97O6swwFCGAwunpFU87lWtZbGotC3ZzeQMS682mIOpj1xezakVWWDJFM04YaDcPFdRBb4WgfoENeg6Ch4WjouH541kBA8gKRshwTu7u6pH7gcbLXwsiOxvbSSooGtHdaWt9KHN7EZQps-nt-0uLrWP6YpEm-nnJl5Onp7WlfovmwkClL4PIFpo3MIb",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuASF1i1fc8aA-YcxvX4fx-zTXLG2SHzDb7veeVFqEvhhy-POQayVEGoBiiON6TLgXU0m-3V6Ts-ol-g7MohlakLEvkwm5B6c8Y9o1pT2AlWJyb0ja0T8HNOxeDsUDk2TYPmbsNlenmHBHeIAlN3ZuMRSEcp9v_AZskGsRTstOHUjv2FhSBuNTFZ8rpz0G_23FaZ4zrJL2Bqx7ijSHS7g3RrirhtpUK22p5vd2pXPw-fFTGXrPVtEVSW5qVWgsQ02Ai9s0EPvbTdv1J2",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuCb35r8S6l1bJITzgUjBdwohONu7BILq_0OPVgA-P0XRWP3OCYVhkTcjM6BEyk6DUcjYge7NAaoJJONN8yFK0Tlarp0i2ApW34dh1ZOUo4r90m6kelrppI6ljMRu3J8gQ6icW6Av7hHw3OleGUC9XCk7jSNEBUkT9M68WeeiueFg_DqVRZv1oN_ZVfGblBF5JnizAZdZWMRmyfOe2I12caI6qZY_X1CmqH6JelnYbWLVX5SdFyCLrBoFp_X-zYNBEhIPmaauSSb-2DN"
  ];

  grid.innerHTML = data.doctors.map((d, index) => {
    const avatar = avatars[index % avatars.length];
    return `
      <div class="doctor-card" style="display:flex;flex-direction:column;height:100%;">
        <div class="doctor-avatar-wrap">
          <div class="doctor-avatar">
            <img src="${avatar}" alt="${d.name}"/>
          </div>
        </div>
        <div class="doctor-info" style="flex:1;display:flex;flex-direction:column;">
          <span class="doctor-specialty">${d.specialty}</span>
          <h3 class="doctor-name">${d.name}</h3>
          <p class="doctor-desc" style="flex:1;">${d.qualification} | ${d.experience} Exp.<br/>Consultation Fee: ₹${d.fees}</p>
          <div class="doctor-actions" style="margin-top:1rem;">
            <button class="btn-outline" onclick="alert('Profile details coming soon')">View Profile</button>
            <a href="/public_appointment.html?doctor_id=${d.id}&specialty=${encodeURIComponent(d.specialty)}" class="btn-primary" style="text-decoration:none;display:flex;align-items:center;justify-content:center;">Book Now</a>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Call it on load
document.addEventListener('DOMContentLoaded', loadPublicDoctors);
"""
html = re.sub(js_pattern, new_js, html, flags=re.DOTALL)

with open('public_doctors.html', 'w') as f:
    f.write(html)

print("public_doctors.html generated successfully!")
