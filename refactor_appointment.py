import re

with open('public_appointment.html', 'r') as f:
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

# 3. Replace all sections between HERO and CONTACT with our new Appointment Portal
sections_pattern = r'<!-- HERO -->.*?<!-- CONTACT -->'
new_sections = """<!-- APPOINTMENT PORTAL -->
<section class="appointment-portal" style="padding: 4rem 1.5rem; min-height: 80vh; background: var(--surface2);">
  <div style="max-width: 800px; margin: 0 auto; background: var(--surface); border-radius: 16px; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid var(--border);">
    
    <div style="text-align: center; margin-bottom: 2rem;">
      <h2 style="font-family: 'Manrope', sans-serif; font-size: 1.8rem; color: var(--primary);">Book an Appointment</h2>
      <p style="color: var(--on-surface-variant); font-size: 0.9rem; margin-top: 0.5rem;">Follow the steps below to schedule your consultation.</p>
    </div>

    <!-- Progress Indicator -->
    <div style="display: flex; justify-content: space-between; margin-bottom: 3rem; position: relative;">
      <div style="position: absolute; top: 12px; left: 0; right: 0; height: 2px; background: var(--border); z-index: 1;"></div>
      <div id="prog-1" style="position: relative; z-index: 2; background: var(--primary); color: white; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 4px solid var(--surface);">1</div>
      <div id="prog-2" style="position: relative; z-index: 2; background: var(--border); color: var(--muted); width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 4px solid var(--surface);">2</div>
      <div id="prog-3" style="position: relative; z-index: 2; background: var(--border); color: var(--muted); width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 4px solid var(--surface);">3</div>
    </div>

    <!-- Step 1: Specialty -->
    <div id="step1">
      <h3 style="font-size: 1.1rem; margin-bottom: 1rem;">Select a Specialty</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem;">
        <button onclick="selectSpecialty('Cardiology')" style="padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: white; text-align: center; transition: all 0.2s; cursor: pointer;">
          <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;">cardiology</span>
          <div style="font-weight: 600; font-size: 0.9rem;">Cardiology</div>
        </button>
        <button onclick="selectSpecialty('Orthopaedics')" style="padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: white; text-align: center; transition: all 0.2s; cursor: pointer;">
          <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;">bone</span>
          <div style="font-weight: 600; font-size: 0.9rem;">Orthopaedics</div>
        </button>
        <button onclick="selectSpecialty('Neurology')" style="padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: white; text-align: center; transition: all 0.2s; cursor: pointer;">
          <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;">psychology</span>
          <div style="font-weight: 600; font-size: 0.9rem;">Neurology</div>
        </button>
        <button onclick="selectSpecialty('Paediatrics')" style="padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: white; text-align: center; transition: all 0.2s; cursor: pointer;">
          <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;">child_care</span>
          <div style="font-weight: 600; font-size: 0.9rem;">Paediatrics</div>
        </button>
        <button onclick="selectSpecialty('Gynaecology')" style="padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: white; text-align: center; transition: all 0.2s; cursor: pointer;">
          <span class="material-symbols-outlined" style="font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem;">female</span>
          <div style="font-weight: 600; font-size: 0.9rem;">Gynaecology</div>
        </button>
      </div>
    </div>

    <!-- Step 2: Doctor -->
    <div id="step2" style="display: none;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
        <h3 style="font-size: 1.1rem;">Select a Doctor</h3>
        <button onclick="goBack(1)" style="background: none; color: var(--info); font-size: 0.8rem; font-weight: 600;">← Back</button>
      </div>
      <div id="doctorList" style="display: flex; flex-direction: column; gap: 1rem;">
        <!-- Filled by JS -->
      </div>
    </div>

    <!-- Step 3: Date & Time -->
    <div id="step3" style="display: none;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <h3 style="font-size: 1.1rem;">Select Date & Time</h3>
        <button onclick="goBack(2)" style="background: none; color: var(--info); font-size: 0.8rem; font-weight: 600;">← Back</button>
      </div>
      
      <div style="background: var(--surface2); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem;">
        <div style="width: 40px; height: 40px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;" id="selectedDocAvatar"></div>
        <div>
          <div style="font-weight: 700; font-size: 1rem;" id="selectedDocName"></div>
          <div style="font-size: 0.8rem; color: var(--muted);" id="selectedDocSpec"></div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 700; color: var(--secondary); text-transform: uppercase; margin-bottom: 0.5rem;">Date</label>
          <input type="date" id="bookDate" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border); border-radius: 8px; font-family: inherit;" required />
          <span id="bookDateErr" style="color: var(--error); font-size: 0.75rem; font-weight: 600; display: block; margin-top: 4px;"></span>
        </div>
        <div>
          <label style="display: block; font-size: 0.85rem; font-weight: 700; color: var(--secondary); text-transform: uppercase; margin-bottom: 0.5rem;">Time Slot</label>
          <select id="bookTime" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border); border-radius: 8px; font-family: inherit;">
            <option value="Morning (10AM - 1PM)">Morning (10AM - 1PM)</option>
            <option value="Evening (4PM - 7PM)">Evening (4PM - 7PM)</option>
          </select>
        </div>
      </div>

      <button id="finalBookBtn" onclick="confirmBooking()" style="width: 100%; background: var(--primary); color: white; padding: 1rem; border-radius: 8px; font-size: 1rem; font-weight: 700; transition: 0.2s;">Confirm Appointment</button>
      <p id="bookingMsg" style="text-align: center; margin-top: 1rem; font-size: 0.85rem; color: var(--on-surface-variant);"></p>
    </div>

  </div>
</section>
<!-- CONTACT -->"""
html = re.sub(sections_pattern, new_sections, html, flags=re.DOTALL)

# 4. Replace JS booking logic with new step-by-step logic
js_pattern = r'// ── Multi-Step Booking Form ─────────────────────────────────────────.*?(?=\n// ── Utility ────────────────────────────────────────────────)'
new_js = """// ── Booking Portal Logic ─────────────────────────────────────────

let bookingState = {
  specialty: null,
  doctorId: null,
  doctorName: null,
  date: null,
  timeSlot: null
};

// Check if URL has pre-selected doctor
document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const docId = urlParams.get('doctor_id');
  const spec = urlParams.get('specialty');
  
  // Set min date
  const dateInput = document.getElementById('bookDate');
  if (dateInput) {
    dateInput.min = new Date().toISOString().split('T')[0];
  }

  if (docId && spec) {
    // Fast track to Step 3
    bookingState.specialty = spec;
    
    // We need to fetch the doctor's name to display it nicely
    const res = await fetch(`${API}/api/doctors`);
    if (res.ok) {
      const data = await res.json();
      const doc = data.doctors.find(d => d.id == docId);
      if (doc) {
        selectDoctor(doc.id, doc.name, doc.specialty);
      }
    }
  }
});

function setProgress(step) {
  for (let i = 1; i <= 3; i++) {
    const el = document.getElementById(`prog-${i}`);
    if (i <= step) {
      el.style.background = 'var(--primary)';
      el.style.color = 'white';
    } else {
      el.style.background = 'var(--border)';
      el.style.color = 'var(--muted)';
    }
  }
}

function goBack(step) {
  document.getElementById('step1').style.display = 'none';
  document.getElementById('step2').style.display = 'none';
  document.getElementById('step3').style.display = 'none';
  
  document.getElementById(`step${step}`).style.display = 'block';
  setProgress(step);
}

async function selectSpecialty(spec) {
  bookingState.specialty = spec;
  
  document.getElementById('step1').style.display = 'none';
  document.getElementById('step2').style.display = 'block';
  setProgress(2);
  
  const list = document.getElementById('doctorList');
  list.innerHTML = '<p style="text-align:center;color:var(--muted);">Finding doctors...</p>';
  
  const res = await fetch(`${API}/api/doctors`).catch(() => null);
  if (!res) { list.innerHTML = '<p style="color:var(--error);">Error fetching doctors.</p>'; return; }
  
  const data = await res.json();
  const doctors = data.doctors.filter(d => d.specialty.toLowerCase().includes(spec.toLowerCase()));
  
  if (doctors.length === 0) {
    list.innerHTML = `<p style="text-align:center;color:var(--muted);">No doctors available for ${spec} right now.</p>`;
    return;
  }
  
  list.innerHTML = doctors.map(d => `
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 1rem; border: 1px solid var(--border); border-radius: 8px; background: white; transition: 0.2s;" onmouseover="this.style.borderColor='var(--primary)'" onmouseout="this.style.borderColor='var(--border)'">
      <div style="display: flex; align-items: center; gap: 1rem;">
        <div style="width: 48px; height: 48px; background: var(--secondary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;">${d.name[4] || d.name[0]}</div>
        <div>
          <div style="font-weight: 700; font-size: 1.05rem; color: var(--on-surface);">${d.name}</div>
          <div style="font-size: 0.8rem; color: var(--muted);">${d.qualification} | ₹${d.fees}</div>
        </div>
      </div>
      <button onclick="selectDoctor(${d.id}, '${d.name}', '${d.specialty}')" style="background: var(--surface2); color: var(--primary); padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; font-size: 0.85rem;">Select</button>
    </div>
  `).join('');
}

function selectDoctor(id, name, spec) {
  bookingState.doctorId = id;
  bookingState.doctorName = name;
  
  document.getElementById('step1').style.display = 'none';
  document.getElementById('step2').style.display = 'none';
  document.getElementById('step3').style.display = 'block';
  setProgress(3);
  
  document.getElementById('selectedDocName').textContent = name;
  document.getElementById('selectedDocSpec').textContent = spec;
  document.getElementById('selectedDocAvatar').textContent = name[4] || name[0];
}

async function confirmBooking() {
  const dateEl = document.getElementById('bookDate');
  const dateErr = document.getElementById('bookDateErr');
  const msgEl = document.getElementById('bookingMsg');
  
  dateErr.textContent = '';
  dateEl.style.borderColor = 'var(--border)';
  
  const chosenRaw = dateEl.value;
  const timeSlot = document.getElementById('bookTime').value;
  
  if (!chosenRaw) {
    dateErr.textContent = 'Please select a date.';
    dateEl.style.borderColor = 'var(--error)';
    return;
  }
  
  const today = new Date(); today.setHours(0,0,0,0);
  const chosen = new Date(chosenRaw + 'T00:00:00');
  if (chosen < today) {
    dateErr.textContent = 'Past dates are not allowed.';
    dateEl.style.borderColor = 'var(--error)';
    return;
  }
  
  bookingState.date = chosenRaw;
  bookingState.timeSlot = timeSlot;
  
  const payload = {
    specialty: bookingState.specialty,
    doctor_id: bookingState.doctorId,
    date: bookingState.date,
    time_slot: bookingState.timeSlot,
    notes: ''
  };

  // Just-In-Time Login Check
  if (!currentUser && !getToken()) {
    msgEl.style.color = 'var(--secondary)';
    msgEl.textContent = 'Please log in or register to finalize your booking...';
    pendingBooking = payload; // save globally
    openModal('loginModal');
    return;
  }

  await executeBooking(payload);
}

let pendingBooking = null;

async function executeBooking(payload) {
  const btn = document.getElementById('finalBookBtn');
  const msgEl = document.getElementById('bookingMsg');
  
  btn.textContent = '⏳ Booking...'; btn.disabled = true;
  msgEl.style.color = 'var(--secondary)'; msgEl.textContent = 'Please wait...';

  const res = await fetch(`${API}/api/book`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload)
  }).catch(() => null);

  btn.textContent = 'Confirm Appointment'; btn.disabled = false;

  if (!res) { msgEl.style.color='var(--error)'; msgEl.textContent='❌ Server not reachable.'; return; }
  const data = await res.json();
  if (data.success) {
    msgEl.style.color = 'var(--primary)';
    msgEl.textContent = '✅ ' + data.message;
    // Hide form and show massive success
    document.getElementById('step3').innerHTML = `
      <div style="text-align:center; padding: 2rem 0;">
        <div style="width: 80px; height: 80px; background: rgba(0, 196, 140, 0.1); color: var(--secondary); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 3rem; margin: 0 auto 1.5rem;">
          <span class="material-symbols-outlined" style="font-size: 2.5rem;">check_circle</span>
        </div>
        <h3 style="font-size: 1.5rem; color: var(--primary); margin-bottom: 0.5rem;">Appointment Confirmed!</h3>
        <p style="color: var(--on-surface-variant); font-size: 0.95rem; margin-bottom: 2rem;">Your appointment with <strong>${bookingState.doctorName}</strong> is scheduled for <strong>${bookingState.date}</strong> at <strong>${bookingState.timeSlot}</strong>.</p>
        <button class="btn-primary" onclick="window.location.href='/'">Return to Home</button>
      </div>
    `;
  } else {
    msgEl.style.color = 'var(--error)';
    msgEl.textContent = '❌ ' + data.message;
  }
}

// Hook into login success to process pending booking
const originalSetLoggedInAppt = setLoggedIn;
setLoggedIn = function(user) {
  originalSetLoggedInAppt(user);
  if (pendingBooking) {
    closeModal('loginModal');
    closeModal('registerModal');
    executeBooking(pendingBooking);
    pendingBooking = null;
  }
};
"""
html = re.sub(js_pattern, new_js, html, flags=re.DOTALL)

with open('public_appointment.html', 'w') as f:
    f.write(html)

print("public_appointment.html generated successfully!")
