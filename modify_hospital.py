import sys

with open('hospital_page.html', 'r') as f:
    content = f.read()

old_html = """      <form class="booking-form" id="bookingForm">
        <div>
          <label class="form-label">Select Specialty</label>
          <select class="form-control" name="specialty" id="specialty">
            <option>Cardiology</option><option>Orthopaedics</option>
            <option>Neurology</option><option>Paediatrics</option>
            <option>Gynaecology</option>
          </select>
        </div>
        <div class="form-row">
          <div>
            <label class="form-label">Preferred Date</label>
            <!-- FIX 1: min is set by JS on page load so users CANNOT pick past dates -->
            <input class="form-control" type="date" name="date" id="aptDate" required/>
            <span class="field-err" id="date-err"></span>
          </div>
          <div>
            <label class="form-label">Preferred Time</label>
            <select class="form-control" name="time_slot" id="timeSlot">
              <option>Morning (10AM - 1PM)</option>
              <option>Evening (4PM - 7PM)</option>
            </select>
          </div>
        </div>
        <div>
          <label class="form-label">Your Name</label>
          <input class="form-control" type="text" name="patient_name" id="patientName" placeholder="e.g. Venkatesh Bonthala"/>
        </div>
        <div>
          <label class="form-label">Mobile Number</label>
          <!-- FIX 2: maxlength=10, inputmode=numeric blocks non-digits on mobile, pattern enforces digits only -->
          <input class="form-control" type="tel" name="patient_phone" id="patientPhone"
            placeholder="10-digit mobile number" maxlength="10" inputmode="numeric" pattern="[0-9]{10}"/>
          <span class="field-err" id="phone-err"></span>
        </div>
        <button class="btn-submit" type="submit" id="bookBtn">Check Availability</button>
        <p class="booking-note" id="bookingMsg">Instant confirmation will be sent to your mobile number.</p>
      </form>"""

new_html = """      <form class="booking-form" id="bookingForm">
        <div>
          <label class="form-label">Step 1: Select Specialty</label>
          <select class="form-control" name="specialty" id="specialty" onchange="fetchDoctorsForSpecialty()">
            <option value="" disabled selected>Choose a department...</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Orthopaedics">Orthopaedics</option>
            <option value="Neurology">Neurology</option>
            <option value="Paediatrics">Paediatrics</option>
            <option value="Gynaecology">Gynaecology</option>
          </select>
        </div>
        <div>
          <label class="form-label">Step 2: Select Doctor</label>
          <select class="form-control" name="doctor_id" id="doctorId" disabled onchange="enableDate()">
            <option value="" disabled selected>Please select specialty first...</option>
          </select>
        </div>
        <div class="form-row">
          <div>
            <label class="form-label">Step 3: Preferred Date</label>
            <input class="form-control" type="date" name="date" id="aptDate" disabled onchange="enableTime()" required/>
            <span class="field-err" id="date-err"></span>
          </div>
          <div>
            <label class="form-label">Step 4: Preferred Time</label>
            <select class="form-control" name="time_slot" id="timeSlot" disabled>
              <option value="" disabled selected>Select date first...</option>
              <option value="Morning (10AM - 1PM)">Morning (10AM - 1PM)</option>
              <option value="Evening (4PM - 7PM)">Evening (4PM - 7PM)</option>
            </select>
          </div>
        </div>
        <button class="btn-submit" type="submit" id="bookBtn">Confirm Booking</button>
        <p class="booking-note" id="bookingMsg">You will be asked to log in if you haven't already.</p>
      </form>"""

content = content.replace(old_html, new_html)

old_js = """// ── Booking Form (with FIX 1 date  + FIX 2 phone validation) ────────
document.getElementById('bookingForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn     = document.getElementById('bookBtn');
  const msgEl   = document.getElementById('bookingMsg');
  const dateEl  = document.getElementById('aptDate');
  const phoneEl = document.getElementById('patientPhone');
  const dateErr = document.getElementById('date-err');
  const phoneErr= document.getElementById('phone-err');

  // Reset previous error highlights
  dateErr.textContent = ''; phoneErr.textContent = '';
  dateEl.classList.remove('input-invalid');
  phoneEl.classList.remove('input-invalid');

  // FIX 1: Reject past dates
  const today    = new Date(); today.setHours(0,0,0,0);
  const chosenRaw= dateEl.value;   // "YYYY-MM-DD"
  const chosen   = chosenRaw ? new Date(chosenRaw + 'T00:00:00') : null;
  if (!chosenRaw) {
    dateErr.textContent = '⚠️ Please select an appointment date.';
    dateEl.classList.add('input-invalid'); dateEl.focus(); return;
  }
  if (chosen < today) {
    dateErr.textContent = '❌ Past dates are not allowed. Please pick today or a future date.';
    dateEl.classList.add('input-invalid'); dateEl.focus(); return;
  }

  // FIX 2: Reject non-10-digit phone
  const phone = phoneEl.value.replace(/\D/g, '');
  if (!phone) {
    phoneErr.textContent = '⚠️ Mobile number is required.';
    phoneEl.classList.add('input-invalid'); phoneEl.focus(); return;
  }
  if (phone.length !== 10) {
    phoneErr.textContent = `❌ Must be exactly 10 digits (you entered ${phone.length}).`;
    phoneEl.classList.add('input-invalid'); phoneEl.focus(); return;
  }

  // Auth check
  if (!currentUser && !getToken()) {
    msgEl.style.color = 'var(--error)';
    msgEl.textContent = '❌ Please login first to book an appointment.';
    setTimeout(() => openModal('loginModal'), 800);
    return;
  }

  btn.textContent = '⏳ Booking...'; btn.disabled = true;
  msgEl.style.color = 'var(--secondary)'; msgEl.textContent = 'Please wait...';

  const res = await fetch(`${API}/api/book`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      specialty: document.getElementById('specialty').value,
      date:      chosenRaw,
      time_slot: document.getElementById('timeSlot').value,
      notes:     ''
    })
  }).catch(() => null);

  btn.textContent = 'Check Availability'; btn.disabled = false;

  if (!res) { msgEl.style.color='var(--error)'; msgEl.textContent='❌ Server not reachable.'; return; }
  const data = await res.json();
  if (data.success) {
    msgEl.style.color = '#00483c';
    msgEl.textContent = '✅ ' + data.message;
    document.getElementById('bookingForm').reset();
    dateEl.min = new Date().toISOString().split('T')[0]; // re-apply min after reset
  } else {
    msgEl.style.color = 'var(--error)';
    msgEl.textContent = '❌ ' + data.message;
  }
});"""

new_js = """// ── Multi-Step Booking Form ─────────────────────────────────────────

// Hold booking data if login is required
let pendingBooking = null;

async function fetchDoctorsForSpecialty() {
  const specialty = document.getElementById('specialty').value;
  const docSelect = document.getElementById('doctorId');
  const dateInput = document.getElementById('aptDate');
  const timeSelect = document.getElementById('timeSlot');
  
  docSelect.disabled = true;
  docSelect.innerHTML = '<option value="" disabled selected>Loading doctors...</option>';
  dateInput.disabled = true; dateInput.value = '';
  timeSelect.disabled = true; timeSelect.value = '';

  const res = await fetch(`${API}/api/doctors`).catch(() => null);
  if (!res) { docSelect.innerHTML = '<option value="" disabled>Error loading</option>'; return; }
  
  const data = await res.json();
  const filtered = data.doctors.filter(d => d.specialty.toLowerCase().includes(specialty.toLowerCase()));
  
  if (filtered.length === 0) {
    docSelect.innerHTML = '<option value="" disabled selected>No doctors available</option>';
  } else {
    docSelect.innerHTML = '<option value="" disabled selected>Choose a doctor...</option>' + 
      filtered.map(d => `<option value="${d.id}">${d.name} (${d.qualification})</option>`).join('');
    docSelect.disabled = false;
  }
}

function enableDate() {
  const dateInput = document.getElementById('aptDate');
  dateInput.disabled = false;
  // min date is already set by JS on page load
}

function enableTime() {
  document.getElementById('timeSlot').disabled = false;
}

document.getElementById('bookingForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn     = document.getElementById('bookBtn');
  const msgEl   = document.getElementById('bookingMsg');
  const dateEl  = document.getElementById('aptDate');
  const dateErr = document.getElementById('date-err');

  dateErr.textContent = '';
  dateEl.classList.remove('input-invalid');

  const specialty = document.getElementById('specialty').value;
  const doctorId  = document.getElementById('doctorId').value;
  const chosenRaw = dateEl.value;
  const timeSlot  = document.getElementById('timeSlot').value;

  if (!specialty || !doctorId || !chosenRaw || !timeSlot) {
    msgEl.style.color = 'var(--error)';
    msgEl.textContent = '⚠️ Please complete all steps before confirming.';
    return;
  }

  const today = new Date(); today.setHours(0,0,0,0);
  const chosen = new Date(chosenRaw + 'T00:00:00');
  if (chosen < today) {
    dateErr.textContent = '❌ Past dates are not allowed.';
    dateEl.classList.add('input-invalid'); dateEl.focus(); return;
  }

  const payload = {
    specialty: specialty,
    doctor_id: doctorId,
    date:      chosenRaw,
    time_slot: timeSlot,
    notes:     ''
  };

  // Auth check - Just In Time!
  if (!currentUser && !getToken()) {
    msgEl.style.color = 'var(--secondary)';
    msgEl.textContent = 'Please log in to finalize your booking...';
    pendingBooking = payload; // save payload to submit after login
    openModal('loginModal');
    return;
  }

  await submitBooking(payload);
});

async function submitBooking(payload) {
  const btn = document.getElementById('bookBtn');
  const msgEl = document.getElementById('bookingMsg');
  
  btn.textContent = '⏳ Booking...'; btn.disabled = true;
  msgEl.style.color = 'var(--secondary)'; msgEl.textContent = 'Please wait...';

  const res = await fetch(`${API}/api/book`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload)
  }).catch(() => null);

  btn.textContent = 'Confirm Booking'; btn.disabled = false;

  if (!res) { msgEl.style.color='var(--error)'; msgEl.textContent='❌ Server not reachable.'; return; }
  const data = await res.json();
  if (data.success) {
    msgEl.style.color = '#00483c';
    msgEl.textContent = '✅ ' + data.message;
    document.getElementById('bookingForm').reset();
    document.getElementById('doctorId').disabled = true;
    document.getElementById('aptDate').disabled = true;
    document.getElementById('timeSlot').disabled = true;
  } else {
    msgEl.style.color = 'var(--error)';
    msgEl.textContent = '❌ ' + data.message;
  }
}

// Intercept setLoggedIn to process pending booking
const originalSetLoggedIn = setLoggedIn;
setLoggedIn = function(user) {
  originalSetLoggedIn(user);
  if (pendingBooking) {
    closeModal('loginModal');
    submitBooking(pendingBooking);
    pendingBooking = null;
  }
};
"""

content = content.replace(old_js, new_js)

# Also remove patient name/phone from being reset in setLoggedIn/Out
content = content.replace("document.getElementById('patientName').value  = user.name;", "")
content = content.replace("document.getElementById('patientPhone').value = user.phone;", "")
content = content.replace("document.getElementById('patientName').value  = '';", "")
content = content.replace("document.getElementById('patientPhone').value = '';", "")

with open('hospital_page.html', 'w') as f:
    f.write(content)

print("Applied multi-step booking form successfully.")
