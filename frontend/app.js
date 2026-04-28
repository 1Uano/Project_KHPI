const API_URL = "";

let currentToken = localStorage.getItem('token') || null;
let currentRole = localStorage.getItem('role') || null;

const authStatus    = document.getElementById("authStatus");
const logoutBtn     = document.getElementById("logoutBtn");
const loginSection  = document.getElementById("loginSection");
const adminSection  = document.getElementById("adminSection");
const doctorSection = document.getElementById("doctorSection");
const nurseSection  = document.getElementById("nurseSection");
const patientSection = document.getElementById("patientSection");
const welcomeSection = document.getElementById("welcomeSection");
const welcomeMessage = document.getElementById("welcomeMessage");

function customAlert(message) {
    document.getElementById("customAlertMessage").innerText = message;
    document.getElementById("customAlertModal").style.display = "flex";
}
document.getElementById("customAlertOkBtn")?.addEventListener("click", () => {
    document.getElementById("customAlertModal").style.display = "none";
});

function customConfirm(message, callback, options = {}) {
    const title = options.title || "Підтвердження";
    const okText = options.okText || "Підтвердити";
    const okColor = options.okColor || "#3498db"; // Default primary blue
    const titleColor = options.titleColor || "#2c3e50";

    const titleEl = document.getElementById("customConfirmTitle");
    if (titleEl) {
        titleEl.innerText = title;
        titleEl.style.color = titleColor;
    }

    const okBtn = document.getElementById("customConfirmOkBtn");
    if (okBtn) {
        okBtn.innerText = okText;
        okBtn.style.background = okColor;
    }

    document.getElementById("customConfirmMessage").innerText = message;
    document.getElementById("customConfirmModal").style.display = "flex";
    
    document.getElementById("customConfirmOkBtn").onclick = () => {
        document.getElementById("customConfirmModal").style.display = "none";
        callback();
    };
    document.getElementById("customConfirmCancelBtn").onclick = () => {
        document.getElementById("customConfirmModal").style.display = "none";
    };
}

function parseJwt(token) {
    try {
        const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(decodeURIComponent(atob(base64).split('').map(c =>
            '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
        ).join('')));
    } catch { return null; }
}

function updateUI() {
    document.getElementById("createStatus").innerText = "";

    if (currentToken && currentRole) {
        authStatus.innerText = `${currentRole}`;
        logoutBtn.style.display = "inline-block";
        loginSection.style.display = "none";

        adminSection.style.display  = "none";
        doctorSection.style.display = "none";
        nurseSection.style.display  = "none";
        patientSection.style.display = "none";
        welcomeSection.style.display = "none";
        
        if (currentRole === "ADMIN") {
            adminSection.style.display  = "block";
            if (typeof loadUsersList === 'function') loadUsersList();
        } else if (currentRole === "DOCTOR") {
            doctorSection.style.display = "block";
            if (typeof loadDoctorRecords === 'function') loadDoctorRecords();
        } else if (currentRole === "NURSE") {
            nurseSection.style.display = "block";
            if (typeof loadNurseJobs === 'function') loadNurseJobs();
        } else if (currentRole === "PATIENT") {
            patientSection.style.display = "block";
            if (typeof loadPatientCards === 'function') loadPatientCards();
        } else {
            welcomeSection.style.display = "block";
            welcomeMessage.innerText = `Вітаємо в системі, ${currentRole}!`;
        }
    } else {
        authStatus.innerText = "Не авторизовано";
        logoutBtn.style.display = "none";
        loginSection.style.display = "flex";
        adminSection.style.display  = "none";
        doctorSection.style.display = "none";
        nurseSection.style.display  = "none";
        patientSection.style.display = "none";
        welcomeSection.style.display = "none";
    }
}

logoutBtn.addEventListener("click", () => {
    currentToken = null;
    currentRole  = null;
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    updateUI();
});

function makeEyeToggle(btnId, inputId) {
    document.getElementById(btnId).addEventListener("click", function () {
        const inp = document.getElementById(inputId);
        const isHidden = inp.type === "password";
        inp.type = isHidden ? "text" : "password";
        this.style.color = isHidden ? "#0056b3" : "";
    });
}
makeEyeToggle("toggleLoginPassword", "loginPassword");
makeEyeToggle("togglePassword", "cuPassword");

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("loginError");
    errorEl.innerText = "";

    const body = new URLSearchParams({
        username: document.getElementById("loginEmail").value,
        password: document.getElementById("loginPassword").value,
    });

    try {
        const res  = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body
        });
        const data = await res.json();
        if (res.ok) {
            currentToken = data.access_token;
            currentRole  = parseJwt(currentToken)?.role ?? "UNKNOWN";
            localStorage.setItem('token', currentToken);
            localStorage.setItem('role', currentRole);
            updateUI();
        } else {
            errorEl.innerText = data.detail || "Невірний логін або пароль";
        }
    } catch {
        errorEl.innerText = "Помилка з'єднання з сервером";
    }
});

const cuEmail   = document.getElementById("cuEmail");
const emailHint = document.getElementById("emailHint");
const EMAIL_RE  = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

cuEmail.addEventListener("input", () => {
    const val = cuEmail.value.trim();
    if (!val) {
        setEmailHint("", "");
    } else if (!EMAIL_RE.test(val)) {
        setEmailHint("Невірний формат email (example@domain.com)", "hint-error");
        cuEmail.classList.add("input-error");
        cuEmail.classList.remove("input-ok");
    } else {
        setEmailHint("Формат email коректний", "hint-ok");
        cuEmail.classList.remove("input-error");
        cuEmail.classList.add("input-ok");
    }
});

function setEmailHint(text, cls) {
    emailHint.innerText = text;
    emailHint.className = "field-hint " + cls;
}

const cuPassword      = document.getElementById("cuPassword");
const strengthBarWrap = document.getElementById("strengthBarWrap");
const strengthFill    = document.getElementById("strengthFill");
const strengthLabel   = document.getElementById("strengthLabel");
const pwdRequirements = document.getElementById("pwdRequirements");

const REQS = {
    "req-length": v => v.length >= 8,
    "req-upper":  v => /[A-Z]/.test(v),
    "req-lower":  v => /[a-z]/.test(v),
    "req-digit":  v => /\d/.test(v),
};

function calcStrength(v) {
    const met = Object.values(REQS).filter(fn => fn(v)).length;
    if (!v)        return { pct: 0,   label: "",           color: "" };
    if (met === 1) return { pct: 20,  label: "Слабкий",    color: "#e74c3c" };
    if (met === 2) return { pct: 50,  label: "Задовільний", color: "#f39c12" };
    if (met === 3) return { pct: 75,  label: "Хороший",    color: "#3498db" };
    if (met === 4) return { pct: 100, label: "Надійний",   color: "#27ae60" };
}

cuPassword.addEventListener("input", () => {
    const val = cuPassword.value;
    const show = val.length > 0;

    strengthBarWrap.style.display = show ? "flex" : "none";
    pwdRequirements.style.display = show ? "flex" : "none";

    for (const [id, fn] of Object.entries(REQS)) {
        const li = document.getElementById(id);
        if (fn(val)) {
            li.classList.add("met");
            li.innerHTML = "&#x25CF; " + li.innerText.replace(/^. /, "");
        } else {
            li.classList.remove("met");
            li.innerHTML = "&#x25CB; " + li.innerText.replace(/^. /, "");
        }
    }

    const s = calcStrength(val);
    strengthFill.style.width      = s.pct + "%";
    strengthFill.style.background = s.color;
    strengthLabel.innerText       = s.label;
    strengthLabel.style.color     = s.color;
});

document.getElementById("cuRole").addEventListener("change", function () {
    const specContainer = document.getElementById("cuSpecContainer");
    if (this.value === "DOCTOR") {
        specContainer.style.display = "block";
    } else {
        specContainer.style.display = "none";
        document.getElementById("cuSpecialization").value = "NONE";
    }
});

document.getElementById("createUserForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const statusEl = document.getElementById("createStatus");
    statusEl.style.color = "#555";
    statusEl.innerText = "Створення...";

    const emailVal = cuEmail.value.trim();
    if (!EMAIL_RE.test(emailVal)) {
        setEmailHint("Введіть коректний email", "hint-error");
        cuEmail.classList.add("input-error");
        statusEl.innerText = "";
        return;
    }

    const pwdVal = cuPassword.value;
    if (!Object.values(REQS).every(fn => fn(pwdVal))) {
        statusEl.style.color = "#e74c3c";
        statusEl.innerText = "Пароль не відповідає вимогам безпеки";
        return;
    }

    const birthDate = document.getElementById("cuBirthDate").value;
    if (!birthDate) {
        statusEl.style.color = "#e74c3c";
        statusEl.innerText = "Введіть дату народження";
        return;
    }

    const payload = {
        email:     emailVal,
        full_name: document.getElementById("cuName").value.trim(),
        role:      document.getElementById("cuRole").value,
        password:  pwdVal,
        is_active: true,
        birth_date: birthDate
    };

    const specContainer = document.getElementById("cuSpecContainer");
    if (specContainer.style.display !== "none") {
        payload.specialization = document.getElementById("cuSpecialization").value;
    }

    try {
        const res  = await fetch(`${API_URL}/admin/users/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${currentToken}`,
            },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (res.ok) {
            statusEl.style.color = "#27ae60";
            statusEl.innerText   = `✓ Користувача створено. ID: ${data.user_id}`;
            e.target.reset();
            document.getElementById("cuSpecContainer").style.display = "none";
            cuEmail.className = "";
            setEmailHint("", "");
            strengthBarWrap.style.display = "none";
            pwdRequirements.style.display = "none";
        } else {
            statusEl.style.color = "#e74c3c";
            if (res.status === 409) {
                setEmailHint("Користувач з таким email вже існує", "hint-error");
                cuEmail.classList.add("input-error");
                statusEl.innerText = "";
            } else {
                statusEl.innerText = "Помилка: " + (data.detail || JSON.stringify(data));
            }
        }
    } catch {
        statusEl.style.color = "#e74c3c";
        statusEl.innerText   = "Помилка з'єднання з сервером";
    }
});

updateUI();

// --- SPRINT 2 ADMIN FUNCTIONALITY ---
let allUsers = [];
let currentPage = 1;
const itemsPerPage = 5;
let currentPatientViewId = null;

const tabCreateUser = document.getElementById("tabCreateUser");
const tabUserList = document.getElementById("tabUserList");
const adminCreateUserView = document.getElementById("adminCreateUserView");
const adminUserListView = document.getElementById("adminUserListView");
const adminUserProfileView = document.getElementById("adminUserProfileView");

// Tabs switching
tabCreateUser.addEventListener("click", () => {
    tabCreateUser.classList.add("active");
    tabUserList.classList.remove("active");
    adminCreateUserView.style.display = "block";
    adminUserListView.style.display = "none";
    adminUserProfileView.style.display = "none";
});

tabUserList.addEventListener("click", () => {
    tabUserList.classList.add("active");
    tabCreateUser.classList.remove("active");
    adminCreateUserView.style.display = "none";
    adminUserListView.style.display = "block";
    adminUserProfileView.style.display = "none";
    loadUsersList();
});

document.getElementById("backToUsersBtn").addEventListener("click", () => {
    adminUserProfileView.style.display = "none";
    adminUserListView.style.display = "block";
});

async function loadUsersList() {
    try {
        const res = await fetch(`${API_URL}/admin/users/`, {
            headers: { "Authorization": `Bearer ${currentToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            const payload = parseJwt(currentToken);
            const adminEmail = payload?.sub || "admin@hospital.com";
            allUsers = data.filter(u => u.email !== adminEmail);
            currentPage = 1;
            renderUsers();
        }
    } catch (e) {
        console.error("Failed to load users", e);
    }
}

// User List Rendering, Filtering, Pagination
const filterRole = document.getElementById("filterRole");
const searchUser = document.getElementById("searchUser");
const userListContainer = document.getElementById("userListContainer");
const prevPageBtn = document.getElementById("prevPage");
const nextPageBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

filterRole.addEventListener("change", () => { currentPage = 1; renderUsers(); });
searchUser.addEventListener("input", () => { currentPage = 1; renderUsers(); });
prevPageBtn.addEventListener("click", () => { if(currentPage > 1) { currentPage--; renderUsers(); } });
nextPageBtn.addEventListener("click", () => { currentPage++; renderUsers(); });

function renderUsers() {
    const role = filterRole.value;
    const query = searchUser.value.toLowerCase();
    
    let filtered = allUsers.filter(u => {
        const matchesRole = role === "ALL" || u.role === role;
        const matchesQuery = u.full_name.toLowerCase().includes(query);
        return matchesRole && matchesQuery;
    });
    
    const totalPages = Math.ceil(filtered.length / itemsPerPage) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage >= totalPages;
    pageInfo.innerText = `${currentPage} / ${totalPages}`;
    
    userListContainer.innerHTML = "";
    
    const start = (currentPage - 1) * itemsPerPage;
    const pageData = filtered.slice(start, start + itemsPerPage);
    
    if (pageData.length === 0) {
        userListContainer.innerHTML = "<p>Користувачів не знайдено.</p>";
        return;
    }
    
    pageData.forEach(u => {
        const dIcon = u.role === "DOCTOR" ? "🩺" : u.role === "NURSE" ? "💉" : u.role === "PATIENT" ? "🩼" : "🛡️";
        const roleNames = { "ADMIN":"Адміністратор", "DOCTOR":"Лікар", "NURSE":"Медсестра", "PATIENT":"Пацієнт" };
        const specName = u.role === "DOCTOR" && u.specialization !== "NONE" ? ` / ${u.specialization}` : "";

        let ageStr = "";
        if (u.birth_date && u.role !== "PATIENT") {
            const dob = new Date(u.birth_date);
            const ageDiffMs = Date.now() - dob.getTime();
            const ageDate = new Date(ageDiffMs);
            const age = Math.abs(ageDate.getUTCFullYear() - 1970);
            ageStr = ` (Років: ${age})`;
        }
        
        const card = document.createElement("div");
        card.className = "user-card";
        card.innerHTML = `
            <div class="card-header">
                <div class="card-icon">${dIcon}</div>
                <div class="card-info">
                    <h3>${u.full_name}</h3>
                    <span class="badge ${u.role}">${roleNames[u.role] || u.role}${specName}</span>
                </div>
            </div>
            <div class="card-body">
                <p><strong>Email:</strong> ${u.email}</p>
                <p><strong>Дата народження:</strong> ${u.birth_date ? new Date(u.birth_date).toLocaleDateString("uk-UA") : "Не вказано"}${ageStr}</p>
            </div>
        `;
        card.addEventListener("click", () => openProfile(u));
        userListContainer.appendChild(card);
    });
}

function openProfile(u) {
    adminUserListView.style.display = "none";
    adminUserProfileView.style.display = "block";
    
    const uid = u._id || u.id;
    const roleNames = { "ADMIN":"Адміністратор", "DOCTOR":"Лікар", "NURSE":"Медсестра", "PATIENT":"Пацієнт" };
    const specName = u.role === "DOCTOR" && u.specialization !== "NONE" ? ` / ${u.specialization}` : "";
    
    let ageStr = "";
    if (u.birth_date && u.role !== "PATIENT") {
        const dob = new Date(u.birth_date);
        const ageDiffMs = Date.now() - dob.getTime();
        const ageDate = new Date(ageDiffMs);
        const age = Math.abs(ageDate.getUTCFullYear() - 1970);
        ageStr = ` (${age} років)`;
    }

    document.getElementById("userProfileHeader").innerHTML = `
        <h2 style="margin-bottom:10px">${u.full_name}</h2>
        <span class="badge ${u.role}" style="margin-bottom:15px">${roleNames[u.role] || u.role}${specName}</span>
        <div style="display:flex; gap:20px; font-size:0.9em; flex-wrap:wrap">
            <p><strong>Email:</strong> ${u.email}</p>
            <p><strong>Р.Н.:</strong> ${u.birth_date ? new Date(u.birth_date).toLocaleDateString("uk-UA") : "Не вказано"}${ageStr}</p>
        </div>
    `;
    
    const section = document.getElementById("patientRecordsSection");
    if(u.role === "PATIENT") {
        currentPatientViewId = uid;
        document.getElementById("mrPatientName").value = u.full_name;
        document.getElementById("mrPatientDob").value = u.birth_date || "";
        
        const btn = document.getElementById("openMedicalCardModalBtn");
        btn.disabled = true;
        btn.innerText = "+ Госпіталізувати";
        btn.style.opacity = "0.5";
        btn.style.cursor = "not-allowed";
        
        section.style.display = "block";
        loadPatientRecords(uid);
    } else {
        currentPatientViewId = null;
        section.style.display = "none";
    }
}

async function loadPatientRecords(patientId) {
    const container = document.getElementById("patientRecordsContainer");
    const btn = document.getElementById("openMedicalCardModalBtn");
    
    container.innerHTML = "<p>Завантаження...</p>";
    try {
        const res = await fetch(`${API_URL}/records/patient/${patientId}`, {
            headers: { "Authorization": `Bearer ${currentToken}` }
        });
        if(res.ok) {
            const records = await res.json();
            
            const hasActive = records.some(r => r.status === 'ACTIVE');
            if (hasActive) {
                btn.disabled = true;
                btn.innerText = "Пацієнт лікується";
                btn.style.opacity = "0.5";
                btn.style.cursor = "not-allowed";
            } else {
                btn.disabled = false;
                btn.innerText = "+ Госпіталізувати";
                btn.style.opacity = "1";
                btn.style.cursor = "pointer";
            }

            if(records.length === 0) {
                container.innerHTML = "<p>У пацієнта ще немає госпіталізацій.</p>";
            } else {
                container.innerHTML = "";
                records.forEach(r => {
                    const admission = new Date(r.admission_date).toLocaleString("uk-UA");
                    const discharge = r.discharge_date ? new Date(r.discharge_date).toLocaleString("uk-UA") : "Не призначено";
                    
                    const docInfo = allUsers.find(du => (du._id || du.id) === r.doctor_id);
                    const docName = docInfo ? docInfo.full_name : "Невідомий лікар";

                    const card = document.createElement("div");
                    card.className = "block-card";
                    card.innerHTML = `
                       <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                           <strong>Діагноз: ${r.diagnosis}</strong>
                           <span class="badge ${r.status === 'ACTIVE' ? 'DOCTOR' : 'NURSE'}">${r.status === 'ACTIVE' ? 'Відкритий' : 'Виписано'}</span>
                       </div>
                       <div class="card-body" style="background:#f4f5f8;">
                           <p><strong>Госпіталізовано:</strong> ${admission}</p>
                           <p><strong>Виписано:</strong> ${discharge}</p>
                           <p><strong>Лікуючий лікар:</strong> ${docName}</p>
                       </div>
                    `;
                    container.appendChild(card);
                });
            }
        } else {
            container.innerHTML = "<p>Помилка завантаження карток.</p>";
        }
    } catch(e) {
        container.innerHTML = "<p>Помилка з'єднання.</p>";
    }
}

// Medical Record Modal Logic
const modal = document.getElementById("medicalRecordModal");
document.getElementById("openMedicalCardModalBtn").addEventListener("click", () => {
    // Populate Doctors
    const docSelect = document.getElementById("mrDoctorSelect");
    docSelect.innerHTML = '<option value="">Оберіть лікаря...</option>';
    allUsers.filter(u => u.role === "DOCTOR").forEach(doc => {
        const opt = document.createElement("option");
        opt.value = doc._id || doc.id;
        opt.innerText = `${doc.full_name} (${doc.specialization !== "NONE" ? doc.specialization : "Лікар"})`;
        docSelect.appendChild(opt);
    });
    
    // Set admission time to now
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById("mrAdmissionDate").value = now.toISOString().slice(0,16);
    
    document.getElementById("mrDiagnosis").value = "";
    document.getElementById("mrStatus").innerText = "";
    
    modal.style.display = "flex";
});

document.getElementById("closeMedRecordModal").addEventListener("click", () => modal.style.display = "none");

document.getElementById("medicalRecordForm").addEventListener("submit", async(e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    
    const payload = {
        patient_id: currentPatientViewId,
        doctor_id: document.getElementById("mrDoctorSelect").value,
        diagnosis: document.getElementById("mrDiagnosis").value,
        status: "ACTIVE",
        admission_date: new Date(document.getElementById("mrAdmissionDate").value).toISOString()
    };
    
    try {
        const res = await fetch(`${API_URL}/records/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${currentToken}`
            },
            body: JSON.stringify(payload)
        });
        if(res.ok) {
            modal.style.display = "none";
            loadPatientRecords(currentPatientViewId);
        } else {
            const eData = await res.json();
            document.getElementById("mrStatus").innerText = "Помилка: " + (eData.detail || "Невідома помилка");
            document.getElementById("mrStatus").style.color = "#e74c3c";
        }
    } catch(err) {
        document.getElementById("mrStatus").innerText = "Помилка сервера";
        document.getElementById("mrStatus").style.color = "#e74c3c";
    } finally {
        btn.disabled = false;
    }
});

