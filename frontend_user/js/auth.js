/* ========================================================= */
/*  AUTH LOGIC                                               */
/* ========================================================= */
// Show/hide login modal
function openLoginModal() {
    loginModal.classList.remove("hidden");
    loginMssv.focus();
}
function closeLoginModal() {
    loginModal.classList.add("hidden");
}

if (headerLoginBtn) headerLoginBtn.addEventListener("click", openLoginModal);
if (sidebarLoginBtn) sidebarLoginBtn.addEventListener("click", openLoginModal);
if (loginCloseBtn) loginCloseBtn.addEventListener("click", closeLoginModal);

// Close modal on backdrop click
if (loginModal) {
    loginModal.addEventListener("click", (e) => {
        if (e.target === loginModal) closeLoginModal();
    });
}

if (loginBtn) {
    loginBtn.addEventListener("click", () => {
        const mssv = loginMssv.value.trim();
        const dob = loginDob.value.trim();
        if (mssv && dob) {
            StreamlitApi.setComponentValue({ action: "login", mssv, dob, timestamp: Date.now() });
            closeLoginModal();
        } else {
            alert("Vui lòng điền đủ MSSV và ngày sinh!");
        }
    });
}

if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
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
