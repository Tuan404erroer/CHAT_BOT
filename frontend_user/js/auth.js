/* ========================================================= */
/*  AUTH LOGIC                                               */
/* ========================================================= */
// Panels
const panelLogin = document.getElementById("panelLogin");
const panelRegister = document.getElementById("panelRegister");
const panelForgot = document.getElementById("panelForgot");
const forgotStep1 = document.getElementById("forgotStep1");
const forgotStep2 = document.getElementById("forgotStep2");
const authAlert = document.getElementById("authAlert");
const authModalTitle = document.getElementById("authModalTitle");
const authModalDesc = document.getElementById("authModalDesc");

// Links
const linkToForgot = document.getElementById("linkToForgot");
const linkToRegister = document.getElementById("linkToRegister");
const linkToLoginFromReg = document.getElementById("linkToLoginFromReg");
const linkToLoginFromForgot = document.getElementById("linkToLoginFromForgot");

// Show/hide login modal
function openLoginModal() {
    loginModal.classList.remove("hidden");
    showPanel("login");
}
function closeLoginModal() {
    loginModal.classList.add("hidden");
    hideAlert();
}

if (sidebarLoginBtn) sidebarLoginBtn.addEventListener("click", openLoginModal);
if (loginCloseBtn) loginCloseBtn.addEventListener("click", closeLoginModal);

// Close modal on backdrop click
if (loginModal) {
    loginModal.addEventListener("click", (e) => {
        if (e.target === loginModal) closeLoginModal();
    });
}

function hideAlert() {
    authAlert.style.display = "none";
}
function showAlert(msg, isSuccess=false) {
    authAlert.style.display = "block";
    authAlert.style.backgroundColor = isSuccess ? "#e8f5e9" : "#ffebee";
    authAlert.style.color = isSuccess ? "#2e7d32" : "#c62828";
    authAlert.textContent = msg;
}

// Switching panels
function showPanel(panelName) {
    hideAlert();
    panelLogin.style.display = "none";
    panelRegister.style.display = "none";
    panelForgot.style.display = "none";
    forgotStep1.style.display = "none";
    forgotStep2.style.display = "none";

    if (panelName === "login") {
        panelLogin.style.display = "block";
        authModalTitle.innerText = "🎓 Cổng Tư Vấn AI";
        authModalDesc.innerText = "Đăng nhập để lưu và xem lại lịch sử trò chuyện";
        document.getElementById("loginMssv").focus();
    } else if (panelName === "register") {
        panelRegister.style.display = "block";
        authModalTitle.innerText = "📝 Đăng ký tài khoản";
        authModalDesc.innerText = "Tạo tài khoản mới để trải nghiệm đầy đủ tính năng";
        document.getElementById("regName").focus();
    } else if (panelName === "forgot_step1") {
        panelForgot.style.display = "block";
        forgotStep1.style.display = "block";
        authModalTitle.innerText = "🔑 Quên mật khẩu";
        authModalDesc.innerText = "Nhập email của bạn để nhận mã khôi phục";
        document.getElementById("forgotEmail").focus();
    } else if (panelName === "forgot_step2") {
        panelForgot.style.display = "block";
        forgotStep2.style.display = "block";
        authModalTitle.innerText = "🔑 Xác thực OTP";
        authModalDesc.innerText = "Nhập mã OTP và mật khẩu mới";
        document.getElementById("forgotOtp").focus();
    }
}

if(linkToRegister) linkToRegister.addEventListener("click", (e) => { e.preventDefault(); showPanel("register"); });
if(linkToLoginFromReg) linkToLoginFromReg.addEventListener("click", (e) => { e.preventDefault(); showPanel("login"); });
if(linkToForgot) linkToForgot.addEventListener("click", (e) => { e.preventDefault(); showPanel("forgot_step1"); });
if(linkToLoginFromForgot) linkToLoginFromForgot.addEventListener("click", (e) => { e.preventDefault(); showPanel("login"); });

// Actions
document.getElementById("btnLoginSubmit").addEventListener("click", () => {
    const mssv = document.getElementById("loginMssv").value.trim();
    const password = document.getElementById("loginPassword").value.trim();
    if (mssv && password) {
        StreamlitApi.setComponentValue({ action: "login", mssv, password, timestamp: Date.now() });
    } else {
        showAlert("Vui lòng nhập đủ thông tin đăng nhập!");
    }
});

document.getElementById("btnRegisterSubmit").addEventListener("click", () => {
    const name = document.getElementById("regName").value.trim();
    const mssv = document.getElementById("regMssv").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value.trim();
    const confirm = document.getElementById("regConfirmPassword").value.trim();
    
    if(!name || !mssv || !email || !password || !confirm) {
        showAlert("Vui lòng điền đủ tất cả các trường!");
        return;
    }
    if(password !== confirm) {
        showAlert("Mật khẩu xác nhận không khớp!");
        return;
    }
    StreamlitApi.setComponentValue({ action: "register", name, mssv, email, password, timestamp: Date.now() });
});

document.getElementById("btnForgotSubmit").addEventListener("click", () => {
    const email = document.getElementById("forgotEmail").value.trim();
    if(email) {
        StreamlitApi.setComponentValue({ action: "request_otp", email, timestamp: Date.now() });
    } else {
        showAlert("Vui lòng nhập Email!");
    }
});

document.getElementById("btnResetSubmit").addEventListener("click", () => {
    const otp = document.getElementById("forgotOtp").value.trim();
    const new_password = document.getElementById("forgotNewPassword").value.trim();
    if(otp && new_password) {
        StreamlitApi.setComponentValue({ action: "reset_password", otp, new_password, timestamp: Date.now() });
    } else {
        showAlert("Vui lòng nhập mã OTP và mật khẩu mới!");
    }
});

if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("user_mssv");
        localStorage.removeItem("user_dob");
        StreamlitApi.setComponentValue({ action: "logout", timestamp: Date.now() });
    });
}


// Dropdown toggle logic
const authDropdown = document.getElementById("authDropdown");
let dropdownOpen = false;

function toggleDropdown() {
    dropdownOpen = !dropdownOpen;
    if (authDropdown) authDropdown.classList.toggle("open", dropdownOpen);
}
function closeDropdown() {
    dropdownOpen = false;
    if (authDropdown) authDropdown.classList.remove("open");
}

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
    if (headerAuthArea && !headerAuthArea.contains(e.target)) closeDropdown();
});

// Initial wiring for guest state
if (headerLoginBtn) headerLoginBtn.addEventListener("click", toggleDropdown);
const ddLoginUser = document.getElementById("ddLoginUser");
if (ddLoginUser) {
    ddLoginUser.addEventListener("click", () => {
        closeDropdown();
        openLoginModal();
    });
}

function updateAuthUI(loggedIn, mssv) {
    isLoggedIn = loggedIn;
    closeDropdown();
    if (loggedIn) {
        // Hide modal if it's open upon successful login
        closeLoginModal();
        
        // Header: show user badge with dropdown
        headerAuthArea.innerHTML = `
            <button class="header-user-badge" id="headerUserBtn" style="cursor:pointer;">
                👤 ${mssv} ▾
            </button>
            <div class="auth-dropdown" id="authDropdown">
                <a href="/?page=admin" target="_blank" class="auth-dropdown-item">
                    <span class="item-icon">⚙️</span>
                    <span class="item-label">Trang Admin</span>
                </a>
                <div class="auth-dropdown-divider"></div>
                <button class="auth-dropdown-item danger" id="ddLogout">
                    <span class="item-icon">🚪</span>
                    <span class="item-label">Đăng xuất</span>
                </button>
            </div>
        `;
        // Re-wire dropdown
        const newDropdown = document.getElementById("authDropdown");
        document.getElementById("headerUserBtn").addEventListener("click", () => {
            dropdownOpen = !dropdownOpen;
            newDropdown.classList.toggle("open", dropdownOpen);
        });
        document.getElementById("ddLogout").addEventListener("click", () => {
            localStorage.removeItem("user_mssv");
            localStorage.removeItem("user_dob");
            StreamlitApi.setComponentValue({ action: "logout", timestamp: Date.now() });
        });
        // Sidebar: show logged-in content
        userInfoDisplay.textContent = "Chào bạn: " + mssv;
        sidebarLoggedIn.style.display = "flex";
        sidebarGuest.style.display = "none";
    } else {
        // Header: show login button with dropdown
        headerAuthArea.innerHTML = `
            <button class="header-login-btn" id="headerLoginBtn" title="Đăng nhập">
                🔑 Đăng nhập
            </button>
            <div class="auth-dropdown" id="authDropdown">
                <button class="auth-dropdown-item" id="ddLoginUser">
                    <span class="item-icon">👤</span>
                    <span class="item-label">Đăng nhập Người dùng</span>
                </button>
                <div class="auth-dropdown-divider"></div>
                <a href="/?page=admin" target="_blank" class="auth-dropdown-item" id="ddLoginAdmin">
                    <span class="item-icon">⚙️</span>
                    <span class="item-label">Đăng nhập Admin</span>
                </a>
            </div>
        `;
        const newDropdown = document.getElementById("authDropdown");
        document.getElementById("headerLoginBtn").addEventListener("click", () => {
            dropdownOpen = !dropdownOpen;
            newDropdown.classList.toggle("open", dropdownOpen);
        });
        document.getElementById("ddLoginUser").addEventListener("click", () => {
            closeDropdown();
            openLoginModal();
        });
        // Sidebar: show guest prompt
        sidebarLoggedIn.style.display = "none";
        sidebarGuest.style.display = "flex";
    }
}
