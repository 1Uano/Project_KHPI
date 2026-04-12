const API_URL = "";

let currentToken = null;
let currentRole = null;

const authStatus    = document.getElementById("authStatus");
const logoutBtn     = document.getElementById("logoutBtn");
const loginSection  = document.getElementById("loginSection");
const adminSection  = document.getElementById("adminSection");
const welcomeSection = document.getElementById("welcomeSection");
const welcomeMessage = document.getElementById("welcomeMessage");

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

        if (currentRole === "ADMIN") {
            adminSection.style.display  = "block";
            welcomeSection.style.display = "none";
        } else {
            adminSection.style.display  = "none";
            welcomeSection.style.display = "block";
            welcomeMessage.innerText = `Вітаємо в системі, ${currentRole}!`;
        }
    } else {
        authStatus.innerText = "Не авторизовано";
        logoutBtn.style.display = "none";
        loginSection.style.display = "block";
        adminSection.style.display  = "none";
        welcomeSection.style.display = "none";
    }
}

logoutBtn.addEventListener("click", () => {
    currentToken = null;
    currentRole  = null;
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

    const payload = {
        email:     emailVal,
        full_name: document.getElementById("cuName").value.trim(),
        role:      document.getElementById("cuRole").value,
        password:  pwdVal,
        is_active: true,
    };

    const birthDate = document.getElementById("cuBirthDate").value;
    if (birthDate) payload.birth_date = birthDate;

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
