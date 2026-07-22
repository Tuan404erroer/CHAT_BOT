/* ========================================================= */
/*  AUTH LOGIC (GOOGLE SSO)                                  */
/* ========================================================= */
const authAlert = document.getElementById("authAlert");
const authModalTitle = document.getElementById("authModalTitle");
const authModalDesc = document.getElementById("authModalDesc");
const panelLogin = document.getElementById("panelLogin");

// Show/hide login modal
function openLoginModal() {
    loginModal.classList.remove("hidden");
    showPanel("login");
    renderGoogleButton();
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
    if(authAlert) authAlert.style.display = "none";
}
function showAlert(msg, isSuccess=false) {
    if(authAlert) {
        authAlert.style.display = "block";
        authAlert.style.backgroundColor = isSuccess ? "#e8f5e9" : "#ffebee";
        authAlert.style.color = isSuccess ? "#2e7d32" : "#c62828";
        authAlert.textContent = msg;
    }
}

function showPanel(panelName) {
    hideAlert();
    if(panelLogin) panelLogin.style.display = "flex";
    if(authModalTitle) authModalTitle.innerText = "🎓 Cổng Tư Vấn AI";
    if(authModalDesc) authModalDesc.innerText = "Đăng nhập để lưu và xem lại lịch sử trò chuyện";
}

// ---------------------------------------------------------
// GOOGLE SSO LOGIC
// ---------------------------------------------------------
const GOOGLE_CLIENT_ID = "771099693125-6kplha8s30akkd61enumes5p93mq2nb5.apps.googleusercontent.com";

function decodeJwtResponse(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
}

function handleGoogleResponse(response) {
    // Decode JWT token to get user info
    const responsePayload = decodeJwtResponse(response.credential);
    const email = responsePayload.email;
    const name = responsePayload.name;
    const picture = responsePayload.picture;

    // Gửi dữ liệu về Backend qua Streamlit Component
    StreamlitApi.setComponentValue({ 
        action: "google_login", 
        email: email,
        name: name,
        picture: picture,
        timestamp: Date.now() 
    });
}

function renderGoogleButton() {
    const btnContainer = document.getElementById("googleBtnContainer");
    if (!btnContainer) return;
    
    // Khởi tạo Google Identity Services
    google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleResponse
    });
    
    // Render nút bấm
    google.accounts.id.renderButton(
        btnContainer,
        { theme: "outline", size: "large", width: 280, text: "continue_with" }
    );
}

// ---------------------------------------------------------
// UI UPDATES & DROPDOWN LOGIC
// ---------------------------------------------------------
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
const ddLoginUser = document.getElementById("ddLoginUser");
if (ddLoginUser) {
    ddLoginUser.addEventListener("click", () => {
        closeDropdown();
        openLoginModal();
    });
}

function updateAuthUI(loggedIn, name, picture) {
    isLoggedIn = loggedIn;
    closeDropdown();
    if (loggedIn) {
        closeLoginModal();
        
        // Header: show user badge with picture or name
        const displayAvatar = picture ? `<img src="${picture}" alt="Avatar" style="width:24px; height:24px; border-radius:50%; margin-right:5px; vertical-align:middle;">` : `👤`;
        const displayName = name || "Sinh viên";
        
        headerAuthArea.innerHTML = `
            <button class="header-user-badge" id="headerUserBtn" style="cursor:pointer; display:flex; align-items:center; border: 1px solid var(--border); background: var(--bg-surface); padding: 5px 10px; border-radius: 20px;">
                ${displayAvatar} 
                <span style="font-size:13px; font-weight:500;">${displayName} ▾</span>
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
            StreamlitApi.setComponentValue({ action: "logout", timestamp: Date.now() });
        });
        // Sidebar: show logged-in content
        if (userInfoDisplay) userInfoDisplay.innerHTML = `<div style="display:flex;align-items:center;gap:8px;">${displayAvatar} <span>${displayName}</span></div>`;
        if (sidebarLoggedIn) sidebarLoggedIn.style.display = "flex";
        if (sidebarGuest) sidebarGuest.style.display = "none";
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
        if (sidebarLoggedIn) sidebarLoggedIn.style.display = "none";
        if (sidebarGuest) sidebarGuest.style.display = "flex";
    }
}
