// --- SPRINT 3 FUNCTIONALITY (DOCTOR, NURSE, PATIENT) ---

// =======================
// SHARED UTILS
// =======================
async function executePrescription(prescId) {
    customConfirm("Підтвердити виконання призначення?", async () => {
        try {
            const res = await fetch(`${API_URL}/prescriptions/${prescId}/execute`, {
                method: "PATCH",
                headers: { "Authorization": `Bearer ${currentToken}` }
            });
            if (res.ok) {
                customAlert("✓ Призначення успішно виконано!");
                if (currentRole === "NURSE") loadNurseJobs();
                else if (currentRole === "DOCTOR") {
                    if (document.getElementById("doctorJobsView").style.display === "block") {
                        loadDoctorJobs();
                    } else {
                        loadDoctorRecords();
                        document.getElementById("tabDocPrescr").click();
                    }
                }
            } else {
                const data = await res.json();
                customAlert("Помилка: " + (data.detail || ""));
            }
        } catch(e) { customAlert("Помилка з'єднання"); }
    });
}

function renderPrescriptionCard(p, patientName, assignedName) {
    const card = document.createElement("div");
    card.className = "user-card";
    const statusColor = p.status === "COMPLETED" ? "#27ae60" : p.status === "ABORTED" ? "#e74c3c" : "#f39c12";
    let statusText = p.status === "COMPLETED" ? "Виконано" : "Очікує";
    if (p.status === "ABORTED") statusText = "Обірвано";
    
    const currentUserId = parseJwt(currentToken)?.id || parseJwt(currentToken)?.sub;
    const executionHTML = p.status === "COMPLETED" 
        ? `<p><strong>Виконано:</strong> ${new Date(p.completed_at).toLocaleString("uk-UA")}</p>`
        : ((currentRole === "NURSE" || currentRole === "DOCTOR") && p.status === "PENDING" && p.assigned_to === currentUserId
            ? `<button class="btn-primary" style="width: auto; padding: 8px 16px; margin-right: 10px;" onclick="executePrescription('${p._id || p.id}')">Виконати</button>` : "");

    let changeAssigneeHTML = "";
    if (currentRole === "DOCTOR" && p.status === "PENDING") {
        changeAssigneeHTML = `<button class="btn-secondary" style="width: auto; padding: 8px 16px;" onclick="openChangeAssigneeModal('${p._id || p.id}', '${p.type}', '${p.assigned_to}')">Змінити виконавця</button>`;
    }

    const iconTrans = { "MEDICINE": "💊", "PROCEDURE": "💉", "SURGERY": "🔪" };
    const nameTrans = { "MEDICINE": "Медикаментозне лікування", "PROCEDURE": "Медична процедура", "SURGERY": "Хірургічна операція" };
    
    card.innerHTML = `
        <div class="card-header">
            <div class="card-icon" style="background:#e8f4fd;">${iconTrans[p.type] || "📝"}</div>
            <div class="card-info">
                <h3>${patientName}</h3>
                <span class="badge" style="background:${statusColor}; color:#fff">${statusText}</span>
            </div>
        </div>
        <div class="card-body" style="display: flex; flex-direction: column; gap: 8px;">
            <p style="margin: 0;"><strong>Тип медичної допомоги:</strong> ${nameTrans[p.type] || "Інше"}</p>
            <p style="margin: 0;"><strong>Медичний висновок та опис:</strong> ${p.description}</p>
            <p style="margin: 0;"><strong>Час призначення:</strong> ${new Date(p.created_at).toLocaleString("uk-UA")}</p>
            <p style="margin: 0;"><strong>Виконує:</strong> <span style="font-weight:600; color:#2980b9;">${assignedName || "Незазначено"}</span></p>
            ${executionHTML || changeAssigneeHTML ? `<div style="margin-top: 5px;">${executionHTML}${changeAssigneeHTML}</div>` : ""}
        </div>
    `;
    return card;
}

// =======================
// DOCTOR LOGIC
// =======================
let doctorPatientsDict = {};
let currentDocViewRecord = null;
let allDocRecords = [];

const tabDocPatients = document.getElementById("tabDocPatients");
const tabDocArchive = document.getElementById("tabDocArchive");
const tabDocJobs = document.getElementById("tabDocJobs");
const doctorActiveListView = document.getElementById("doctorActiveListView");
const doctorJobsView = document.getElementById("doctorJobsView");
const doctorCardDetailView = document.getElementById("doctorCardDetailView");
const doctorRecordsContainer = document.getElementById("doctorRecordsContainer");
const doctorJobsContainer = document.getElementById("doctorJobsContainer");

let docCurrentTabMode = "ACTIVE";

tabDocPatients?.addEventListener("click", () => {
    tabDocPatients.classList.add("active"); tabDocArchive.classList.remove("active"); tabDocJobs.classList.remove("active");
    doctorActiveListView.style.display = "block"; doctorJobsView.style.display = "none"; doctorCardDetailView.style.display = "none";
    docCurrentTabMode = "ACTIVE";
    document.getElementById("docListTitle").innerText = "Активні пацієнти";
    loadDoctorRecords();
});
tabDocArchive?.addEventListener("click", () => {
    tabDocArchive.classList.add("active"); tabDocPatients.classList.remove("active"); tabDocJobs.classList.remove("active");
    doctorActiveListView.style.display = "block"; doctorJobsView.style.display = "none"; doctorCardDetailView.style.display = "none";
    docCurrentTabMode = "ARCHIVE";
    document.getElementById("docListTitle").innerText = "Архівні картки";
    loadDoctorRecords();
});
tabDocJobs?.addEventListener("click", () => {
    tabDocJobs.classList.add("active"); tabDocPatients.classList.remove("active"); tabDocArchive.classList.remove("active");
    doctorActiveListView.style.display = "none"; doctorJobsView.style.display = "block"; doctorCardDetailView.style.display = "none";
    loadDoctorJobs();
});

document.getElementById("backToDoctorListBtn")?.addEventListener("click", () => {
    doctorCardDetailView.style.display = "none"; doctorActiveListView.style.display = "block";
});

async function loadDoctorRecords() {
    doctorRecordsContainer.innerHTML = "<p>Завантаження...</p>";
    try {
        const usersRes = await fetch(`${API_URL}/admin/users/`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if (usersRes.ok) {
            const users = await usersRes.json();
            users.forEach(u => doctorPatientsDict[u._id || u.id] = u);
        }
        const recRes = await fetch(`${API_URL}/records/doctor/all`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if (recRes.ok) {
            allDocRecords = await recRes.json();
            renderDoctorRecords();
        } else {
            doctorRecordsContainer.innerHTML = "<p>Помилка завантаження карток.</p>";
        }
    } catch(e) { doctorRecordsContainer.innerHTML = "<p>Помилка з'єднання.</p>"; }
}

function renderDoctorRecords() {
    doctorRecordsContainer.innerHTML = "";
    
    const sorted = [...allDocRecords].sort((a,b) => new Date(b.admission_date) - new Date(a.admission_date));
    const filtered = sorted.filter(r => docCurrentTabMode === "ACTIVE" ? r.status === "ACTIVE" : r.status !== "ACTIVE");
    
    if (filtered.length === 0) return doctorRecordsContainer.innerHTML = "<p>Розділ порожній.</p>";
    
    filtered.forEach(r => {
        const patient = doctorPatientsDict[r.patient_id];
        const pName = patient ? patient.full_name : "Невідомий";
        const admission = new Date(r.admission_date).toLocaleString("uk-UA");
        const bColor = r.status === "ACTIVE" ? "" : "background:#e0e3e9; color:#333;";
        const bText = r.status === "ACTIVE" ? "Лікується" : "Виписано";
        
        let ageStr = "";
        let dobStr = "Не вказано";
        if (patient && patient.birth_date) {
            const dob = new Date(patient.birth_date);
            dobStr = dob.toLocaleDateString("uk-UA");
            const ageDiffMs = Date.now() - dob.getTime();
            const ageDate = new Date(ageDiffMs);
            const age = Math.abs(ageDate.getUTCFullYear() - 1970);
            ageStr = ` (${age} років)`;
        }
        
        const card = document.createElement("div");
        card.className = "user-card";
        card.innerHTML = `
            <div class="card-header">
                <div class="card-icon">🩼</div>
                <div class="card-info">
                    <h3>${pName} (Картка №${(r._id||r.id).slice(-4)})</h3>
                    <span class="badge PATIENT" style="margin-top:2px; ${bColor}">${bText}</span>
                </div>
            </div>
            <div class="card-body">
                <p><strong>Дата народження:</strong> ${dobStr}${ageStr}</p>
                <p><strong>Головний діагноз:</strong> ${r.diagnosis}</p>
                <p><strong>Госпіталізовано:</strong> ${admission}</p>
            </div>
        `;
        card.addEventListener("click", () => openDoctorDetailView(r, patient));
        doctorRecordsContainer.appendChild(card);
    });
}

function openDoctorDetailView(record, patient) {
    doctorActiveListView.style.display = "none";
    doctorCardDetailView.style.display = "block";
    currentDocViewRecord = record;
    currentDischargingRecordId = record._id || record.id;
    
    document.getElementById("tabDocInfo").click();
    
    let ageStr = "";
    let dobStr = "Не вказано";
    if (patient && patient.birth_date) {
        const dob = new Date(patient.birth_date);
        dobStr = dob.toLocaleDateString("uk-UA");
        const ageDiffMs = Date.now() - dob.getTime();
        const ageDate = new Date(ageDiffMs);
        const age = Math.abs(ageDate.getUTCFullYear() - 1970);
        ageStr = ` (${age} років)`;
    }

    document.getElementById("doctorPatientCardHeader").innerHTML = `
        <h2 style="margin-bottom:10px">${patient ? patient.full_name : "Невідомий"} (Картка №${(record._id||record.id).slice(-4)})</h2>
        <span class="badge ${record.status === 'ACTIVE' ? 'PATIENT' : ''}" style="margin-bottom:15px; background:${record.status!=='ACTIVE'?'#ccc':''}">
            Статус: ${record.status === 'ACTIVE' ? "В лікуванні" : "Виписано"}
        </span>
        <div style="font-size:0.9em; margin-bottom:10px;">
            <p><strong>Дата народження:</strong> ${dobStr}${ageStr}</p>
        </div>
    `;
    
    document.getElementById("dischargePatientBtn").style.display = record.status === "ACTIVE" ? "block" : "none";
    document.getElementById("openPrescriptionModalBtn").style.display = record.status === "ACTIVE" ? "inline-block" : "none";
    document.getElementById("addDiagBtn").disabled = record.status !== "ACTIVE";
    document.getElementById("newSecondaryDiag").disabled = record.status !== "ACTIVE";
    
    if (record.status !== "ACTIVE") {
        document.getElementById("docDiagInputGroup").style.display = "none";
    } else {
        document.getElementById("docDiagInputGroup").style.display = "flex";
    }
    
    document.getElementById("dsDiagnosis").value = record.diagnosis;
    
    renderDoctorDiagnoses();
}

const tabDocInfo = document.getElementById("tabDocInfo");
const tabDocPrescr = document.getElementById("tabDocPrescr");
const docDetailedInfoView = document.getElementById("docDetailedInfoView");
const docPrescriptionsView = document.getElementById("docPrescriptionsView");

tabDocInfo?.addEventListener("click", () => {
    tabDocInfo.classList.add("active"); tabDocPrescr.classList.remove("active");
    docDetailedInfoView.style.display = "block"; docPrescriptionsView.style.display = "none";
    renderDoctorDiagnoses();
});
tabDocPrescr?.addEventListener("click", () => {
    tabDocPrescr.classList.add("active"); tabDocInfo.classList.remove("active");
    docDetailedInfoView.style.display = "none"; docPrescriptionsView.style.display = "block";
    loadRecordPrescriptions("docPrescrContainer", currentDocViewRecord._id || currentDocViewRecord.id);
});

function renderDoctorDiagnoses() {
    const container = document.getElementById("doctorDiagnosesList");
    let html = `<div><strong>Основне захворювання:</strong> ${currentDocViewRecord.diagnosis}</div>`;
    const sec = currentDocViewRecord.secondary_diagnoses || [];
    if(sec.length > 0) {
        html += `<div style="margin-top:10px"><strong>Супутні:</strong><ul style="margin-top:5px; padding-left:20px;">`;
        sec.forEach(s => html += `<li>${s}</li>`);
        html += `</ul></div>`;
    }
    container.innerHTML = html;
}

document.getElementById("addDiagBtn")?.addEventListener("click", async () => {
    const val = document.getElementById("newSecondaryDiag").value.trim();
    if(!val) return;
    document.getElementById("addDiagBtn").disabled = true;
    
    const r = currentDocViewRecord;
    const s = r.secondary_diagnoses || [];
    s.push(val);
    
    try {
        const res = await fetch(`${API_URL}/records/${r._id||r.id}/diagnoses`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
            body: JSON.stringify({ diagnosis: r.diagnosis, secondary_diagnoses: s })
        });
        if(res.ok) {
            document.getElementById("newSecondaryDiag").value = "";
            renderDoctorDiagnoses();
        } else customAlert("Помилка оновлення");
    } catch(e) { customAlert("Сервер недоступний"); }
    document.getElementById("addDiagBtn").disabled = false;
});

// PRESCRIPTIONS CREATION
const prescrModal = document.getElementById("createPrescriptionModal");
let hospitalStaff = [];

function populateAssignees() {
    const assigneeSelect = document.getElementById("cpAssignee");
    const pType = document.getElementById("cpType").value;
    assigneeSelect.innerHTML = '<option value="" disabled selected>Оберіть виконавця...</option>';
    
    hospitalStaff.forEach(u => {
        if(u.role === "DOCTOR" || (u.role === "NURSE" && pType !== "SURGERY")) {
            assigneeSelect.innerHTML += `<option value="${u._id||u.id}">${u.full_name} (${u.role})</option>`;
        }
    });
}
document.getElementById("cpType")?.addEventListener("change", populateAssignees);

document.getElementById("openPrescriptionModalBtn")?.addEventListener("click", async () => {
    document.getElementById("cpStatus").innerText = "";
    document.getElementById("createPrescriptionForm").reset();
    
    try {
        const usersRes = await fetch(`${API_URL}/admin/users/`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if (usersRes.ok) hospitalStaff = await usersRes.json();
    } catch {}
    
    populateAssignees();
    prescrModal.style.display = "flex";
});
document.getElementById("closePrescrModal")?.addEventListener("click", () => prescrModal.style.display = "none");

document.getElementById("createPrescriptionForm")?.addEventListener("submit", async(e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    
    const assigned = document.getElementById("cpAssignee").value;
    if (!assigned) {
        document.getElementById("cpStatus").innerText = "Обов'язково оберіть виконавця призначення зі списку!";
        document.getElementById("cpStatus").style.color = "#e74c3c";
        btn.disabled = false;
        return;
    }
    document.getElementById("cpStatus").innerText = "";
    
    const payload = {
        record_id: currentDocViewRecord._id || currentDocViewRecord.id,
        prescribed_by: parseJwt(currentToken)?.sub || "doctor", 
        type: document.getElementById("cpType").value,
        description: document.getElementById("cpDesc").value,
        assigned_to: assigned
    };
    
    try {
        const res = await fetch(`${API_URL}/prescriptions/`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
            body: JSON.stringify(payload)
        });
        if(res.ok) {
            prescrModal.style.display = "none";
            loadRecordPrescriptions("docPrescrContainer", payload.record_id);
        } else document.getElementById("cpStatus").innerText = "Нажаль сталася помилка створення.";
    } catch { document.getElementById("cpStatus").innerText = "Помилка сервера"; }
    btn.disabled = false;
});

async function loadRecordPrescriptions(containerId, recordId) {
    const c = document.getElementById(containerId);
    c.innerHTML = "<p>Завантаження...</p>";
    try {
        const res = await fetch(`${API_URL}/prescriptions/record/${recordId}`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if(res.ok) {
            const data = await res.json();
            c.innerHTML = "";
            if(data.length === 0) return c.innerHTML = "<p>Призначень немає.</p>";
            data.forEach(p => c.appendChild(renderPrescriptionCard(p, "Пацієнт", doctorPatientsDict[p.assigned_to]?.full_name)));
        }
    } catch { c.innerHTML = "<p>Помилка з'єднання</p>";}
}

let docJobsMode = "PENDING";
document.getElementById("tabDocJobsPending")?.addEventListener("click", function() {
   this.classList.add("active"); document.getElementById("tabDocJobsArchive").classList.remove("active");
   docJobsMode = "PENDING"; loadDoctorJobs();
});
document.getElementById("tabDocJobsArchive")?.addEventListener("click", function() {
   this.classList.add("active"); document.getElementById("tabDocJobsPending").classList.remove("active");
   docJobsMode = "ARCHIVE"; loadDoctorJobs();
});

async function loadDoctorJobs() {
    doctorJobsContainer.innerHTML = "<p>Завантаження...</p>";
    try {
        const usersRes = await fetch(`${API_URL}/admin/users/`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        const users = usersRes.ok ? await usersRes.json() : [];
        const uDict = {}; users.forEach(u => uDict[u._id||u.id] = u);

        const res = await fetch(`${API_URL}/prescriptions/assigned/me`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if(res.ok) {
            const data = await res.json();
            const fdata = data.filter(p => docJobsMode === "PENDING" ? p.status === "PENDING" : p.status !== "PENDING");
            doctorJobsContainer.innerHTML = "";
            if(fdata.length === 0) return doctorJobsContainer.innerHTML = "<p>Немає поточних завдань.</p>";
            fdata.forEach(p => doctorJobsContainer.appendChild(renderPrescriptionCard(p, "Для Картки #" + p.record_id.slice(-4), "Ви")));
        }
    } catch { doctorJobsContainer.innerHTML = "<p>Помилка з'єднання</p>"; }
}

// Doctor Discharge Code (from Sprint 2)
const dischargeModal = document.getElementById("dischargeModal");
document.getElementById("dischargePatientBtn")?.addEventListener("click", async () => {
    try {
        const res = await fetch(`${API_URL}/prescriptions/record/${currentDischargingRecordId}`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if(res.ok) {
            const prescs = await res.json();
            const hasPending = prescs.some(p => p.status === "PENDING");
            if (hasPending) {
                customConfirm("Є незакриті процедури. Все одно виписати?", showDischargeModal, {
                    title: "Підтвердження виписки",
                    okText: "Все одно виписати",
                    okColor: "#e74c3c",
                    titleColor: "#e74c3c"
                });
                return;
            }
        }
    } catch {}
    showDischargeModal();
});

function showDischargeModal() {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById("dsDate").value = now.toISOString().slice(0,16);
    document.getElementById("dsStatus").innerText = "";
    dischargeModal.style.display = "flex";
}
document.getElementById("closeDischargeModal")?.addEventListener("click", () => dischargeModal.style.display = "none");
document.getElementById("dischargeForm")?.addEventListener("submit", async(e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const payload = {
        final_diagnosis: document.getElementById("dsDiagnosis").value,
        discharge_date: new Date(document.getElementById("dsDate").value).toISOString()
    };
    try {
        const res = await fetch(`${API_URL}/records/${currentDischargingRecordId}/discharge`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            dischargeModal.style.display = "none";
            document.getElementById("backToDoctorListBtn").click();
            loadDoctorRecords();
        } else {
            const eData = await res.json();
            document.getElementById("dsStatus").innerText = "Помилка: " + (eData.detail || "Невідома помилка");
            document.getElementById("dsStatus").style.color = "#e74c3c";
        }
    } catch(err) {
        document.getElementById("dsStatus").innerText = "Помилка сервера";
        document.getElementById("dsStatus").style.color = "#e74c3c";
    } finally { btn.disabled = false; }
});


// =======================
// NURSE LOGIC
// =======================
const nurseJobsContainer = document.getElementById("nurseJobsContainer");
let nurseJobsMode = "PENDING";
document.getElementById("tabNurseJobsPending")?.addEventListener("click", function() {
   this.classList.add("active"); document.getElementById("tabNurseJobsArchive").classList.remove("active");
   nurseJobsMode = "PENDING"; loadNurseJobs();
});
document.getElementById("tabNurseJobsArchive")?.addEventListener("click", function() {
   this.classList.add("active"); document.getElementById("tabNurseJobsPending").classList.remove("active");
   nurseJobsMode = "ARCHIVE"; loadNurseJobs();
});

async function loadNurseJobs() {
    nurseJobsContainer.innerHTML = "<p>Завантаження...</p>";
    try {
        const res = await fetch(`${API_URL}/prescriptions/assigned/me`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if(res.ok) {
            const data = await res.json();
            const fdata = data.filter(p => nurseJobsMode === "PENDING" ? p.status === "PENDING" : p.status !== "PENDING");
            nurseJobsContainer.innerHTML = "";
            if(fdata.length === 0) return nurseJobsContainer.innerHTML = "<p>Завдань немає.</p>";
            fdata.forEach(p => nurseJobsContainer.appendChild(renderPrescriptionCard(p, "Для Картки #"+p.record_id.slice(-4), "Ви")));
        }
    } catch(e) { nurseJobsContainer.innerHTML = "<p>Помилка.</p>"; }
}

// =======================
// PATIENT LOGIC
// =======================
const patientCardsContainer = document.getElementById("patientCardsContainer");
const patientCardsListView = document.getElementById("patientCardsListView");
const patientCardDetailView = document.getElementById("patientCardDetailView");
let currentPatViewRecord = null;

let patientStaffDict = {};

async function loadPatientCards() {
    patientCardsListView.style.display = "block";
    patientCardDetailView.style.display = "none";
    patientCardsContainer.innerHTML = "<p>Завантаження...</p>";
    
    try {
        const usersRes = await fetch(`${API_URL}/admin/users/`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if (usersRes.ok) {
            const users = await usersRes.json();
            users.forEach(u => patientStaffDict[u._id || u.id] = u);
        }
    } catch(e) {}
    
    try {
        const uId = parseJwt(currentToken)?.id;
        if (!uId) {
             customAlert("Сесія застаріла через оновлення. Будь ласка, авторизуйтесь наново.");
             document.getElementById("logoutBtn").click();
             return;
        }
        const res = await fetch(`${API_URL}/records/patient/${uId}`, { headers: { "Authorization": `Bearer ${currentToken}` } });
        if(res.ok) {
            const data = await res.json();
            patientCardsContainer.innerHTML = "";
            if(data.length === 0) return patientCardsContainer.innerHTML = "<p>У вас поки немає медичних карток.</p>";
            
            const sorted = data.sort((a,b) => {
                if (a.status === "ACTIVE" && b.status !== "ACTIVE") return -1;
                if (b.status === "ACTIVE" && a.status !== "ACTIVE") return 1;
                return new Date(b.admission_date) - new Date(a.admission_date);
            });
            
            sorted.forEach(r => {
                const admission = new Date(r.admission_date).toLocaleString("uk-UA");
                const bColor = r.status === "ACTIVE" ? "background:#3498db;" : "background:#e0e3e9; color:#333;";
                const card = document.createElement("div");
                card.className = "user-card";
                card.innerHTML = `
                    <div class="card-header">
                        <div class="card-icon" style="${bColor}">🏥</div>
                        <div class="card-info">
                            <h3>Картка госпіталізації</h3>
                            <span class="badge" style="margin-top:2px; ${bColor}">${r.status === "ACTIVE" ? "Відкрита" : "Закрита"}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <p><strong>Головний діагноз:</strong> ${r.diagnosis}</p>
                        <p><strong>Час госпіталізації:</strong> ${admission}</p>
                    </div>
                `;
                card.addEventListener("click", () => openPatientDetailView(r));
                patientCardsContainer.appendChild(card);
            });
        } else patientCardsContainer.innerHTML = "<p>Помилка сервера</p>";
    } catch(e) { patientCardsContainer.innerHTML = "<p>Помилка з'єднання</p>"; }
}

const tabPatInfo = document.getElementById("tabPatInfo");
const tabPatPrescr = document.getElementById("tabPatPrescr");
const tabPatDischarge = document.getElementById("tabPatDischarge");
const patDetailedInfoView = document.getElementById("patDetailedInfoView");
const patPrescriptionsView = document.getElementById("patPrescriptionsView");
const patDischargeView = document.getElementById("patDischargeView");

tabPatInfo?.addEventListener("click", () => {
    tabPatInfo.classList.add("active"); tabPatPrescr.classList.remove("active"); tabPatDischarge.classList.remove("active");
    patDetailedInfoView.style.display = "block"; patPrescriptionsView.style.display = "none"; patDischargeView.style.display = "none";
});
tabPatPrescr?.addEventListener("click", () => {
    tabPatPrescr.classList.add("active"); tabPatInfo.classList.remove("active"); tabPatDischarge.classList.remove("active");
    patDetailedInfoView.style.display = "none"; patPrescriptionsView.style.display = "block"; patDischargeView.style.display = "none";
    
            // load prescs
    const pc = document.getElementById("patPrescrContainer");
    pc.innerHTML = "<p>Завантаження...</p>";
    fetch(`${API_URL}/prescriptions/record/${currentPatViewRecord._id||currentPatViewRecord.id}`, { headers: {"Authorization": `Bearer ${currentToken}`}})
        .then(res => res.json()).then(data => {
            pc.innerHTML = "";
            if(data.length === 0) return pc.innerHTML = "<p>Немає процедур або ліків.</p>";
            data.forEach(p => pc.appendChild(renderPrescriptionCard(p, "Призначення", patientStaffDict[p.assigned_to]?.full_name || "Медик")));
        }).catch(()=>pc.innerHTML="Помилка");
});
tabPatDischarge?.addEventListener("click", () => {
    tabPatDischarge.classList.add("active"); tabPatInfo.classList.remove("active"); tabPatPrescr.classList.remove("active");
    patDetailedInfoView.style.display = "none"; patPrescriptionsView.style.display = "none"; patDischargeView.style.display = "block";
    
    if(currentPatViewRecord.status === "ACTIVE") {
        document.getElementById("patDischargeDoc").innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #7f8c8d; background: #f9fbfc; border-radius: 8px; border: 1px dashed #ced4da;">
                <div style="font-size: 3rem; margin-bottom: 15px;">🩺</div>
                <h3 style="margin-bottom: 10px; color: #34495e;">Лікування ще триває</h3>
                <p style="font-size: 1.1em;">Електронний документ виписки буде автоматично згенерований та доступний тут після того, як ваш лікуючий лікар офіційно закриє цю картку.</p>
            </div>
        `;
    } else {
        document.getElementById("patDischargeDoc").innerHTML = `
            <div style="background: white; border: 1px solid #e0e3e9; border-radius: 8px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                <h3 style="margin-bottom: 25px; border-bottom: 2px solid #3498db; padding-bottom: 15px; color: #2c3e50; display:flex; justify-content:space-between; align-items:center;">
                    <span>Виписний Епікриз</span>
                    <span style="font-size:0.6em; background:#ecf0f1; padding:5px 10px; border-radius:4px; color:#7f8c8d;">Офіційний документ</span>
                </h3>
                <div style="display:flex; gap: 40px; margin-bottom: 20px; flex-wrap: wrap;">
                    <p style="margin:0;"><strong>Дата госпіталізації:</strong><br><span style="display:inline-block; margin-top:5px; font-size:1.05em;">${new Date(currentPatViewRecord.admission_date).toLocaleString("uk-UA")}</span></p>
                    <p style="margin:0;"><strong>Дата виписки:</strong><br><span style="display:inline-block; margin-top:5px; font-size:1.05em; color:#27ae60; font-weight:600;">${new Date(currentPatViewRecord.discharge_date).toLocaleString("uk-UA")}</span></p>
                </div>
                <div style="margin-bottom: 20px;">
                    <p style="margin-bottom: 5px;"><strong>Початковий медичний діагноз (при вступі):</strong></p>
                    <div style="background: #f8f9fa; padding: 12px 15px; border-left: 4px solid #bdc3c7; border-radius: 4px;">
                        ${currentPatViewRecord.diagnosis}
                    </div>
                </div>
                <div style="margin-top: 20px;">
                    <p style="font-size:1.1em; color:#0056b3; margin-bottom: 5px;"><strong>Заключний клінічний діагноз (при виписці):</strong></p>
                    <div style="background: #e8f4fd; padding: 15px; border-left: 4px solid #3498db; border-radius: 4px; font-weight: bold; font-size: 1.15em; color: #2c3e50;">
                        ${currentPatViewRecord.final_diagnosis || currentPatViewRecord.diagnosis}
                    </div>
                </div>
            </div>
        `;
    }
});

document.getElementById("backToPatientCardsBtn")?.addEventListener("click", () => {
    patientCardsListView.style.display = "block"; patientCardDetailView.style.display = "none";
});

async function openPatientDetailView(r) {
    patientCardsListView.style.display = "none"; patientCardDetailView.style.display = "block";
    currentPatViewRecord = r;
    document.getElementById("tabPatInfo").click();
    
    document.getElementById("patCardHeader").innerHTML = `
        <h2 style="margin-bottom:10px">Медична Картка #${(r._id||r.id).slice(-6)}</h2>
        <span class="badge" style="margin-bottom:15px; ${r.status !== 'ACTIVE'?'background:#e0e3e9; color:#333':''}">${r.status==="ACTIVE"?"В лікуванні":"Виписано"}</span>
    `;
    
    let dHTML = `
        <div style="margin-bottom:10px;"><strong>Лікар:</strong> ${patientStaffDict[r.doctor_id]?.full_name || "Невідомо"}</div>
        <div><strong>Основне захворювання:</strong> ${r.diagnosis}</div>
    `;
    if(r.secondary_diagnoses && r.secondary_diagnoses.length) {
        dHTML += `<div style="margin-top:10px"><strong>Супутні:</strong><ul style="padding-left:20px;">`;
        r.secondary_diagnoses.forEach(s => dHTML += `<li>${s}</li>`);
        dHTML += `</ul></div>`;
    }
    document.getElementById("patDiagnosesList").innerHTML = dHTML;
    
    if(r.status !== "ACTIVE") {
        // Patient discharge is generated on demand in the click handler now
    }
}

// Initial Data Load (Since updateUI in app.js fires before sprint3.js is parsed)
if (currentRole === "DOCTOR") loadDoctorRecords();
if (currentRole === "NURSE") loadNurseJobs();
if (currentRole === "PATIENT") loadPatientCards();

// CHANGE ASSIGNEE LOGIC
let currentChangeAssigneePrescriptionId = null;

async function openChangeAssigneeModal(prescId, type, currentAssignee) {
    currentChangeAssigneePrescriptionId = prescId;
    const select = document.getElementById("caAssigneeSelect");
    select.innerHTML = '<option value="" disabled>Оберіть нового виконавця...</option>';
    
    if (hospitalStaff.length === 0) {
        try {
            const usersRes = await fetch(`${API_URL}/admin/users/`, { headers: { "Authorization": `Bearer ${currentToken}` } });
            if (usersRes.ok) hospitalStaff = await usersRes.json();
        } catch {}
    }
    
    hospitalStaff.forEach(u => {
        if(u.role === "DOCTOR" || (u.role === "NURSE" && type !== "SURGERY")) {
            const selArg = (u._id||u.id) === currentAssignee ? "selected" : "";
            select.innerHTML += `<option value="${u._id||u.id}" ${selArg}>${u.full_name} (${u.role})</option>`;
        }
    });
    document.getElementById("caStatus").innerText = "";
    document.getElementById("changeAssigneeModal").style.display = "flex";
}

document.getElementById("closeChangeAssigneeModal")?.addEventListener("click", () => {
    document.getElementById("changeAssigneeModal").style.display = "none";
});

document.getElementById("changeAssigneeForm")?.addEventListener("submit", async(e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    const assigned = document.getElementById("caAssigneeSelect").value;
    
    try {
        const res = await fetch(`${API_URL}/prescriptions/${currentChangeAssigneePrescriptionId}/assignee`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${currentToken}` },
            body: JSON.stringify({ new_assignee: assigned })
        });
        if(res.ok) {
            document.getElementById("changeAssigneeModal").style.display = "none";
            if (document.getElementById("doctorJobsView").style.display === "block") loadDoctorJobs();
            else if (docPrescriptionsView.style.display === "block") loadRecordPrescriptions("docPrescrContainer", currentDocViewRecord._id || currentDocViewRecord.id);
        } else {
            document.getElementById("caStatus").innerText = "Нажаль сталася помилка.";
        }
    } catch { document.getElementById("caStatus").innerText = "Помилка сервера"; }
    btn.disabled = false;
});

