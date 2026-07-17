/* ========================================================= */
/*  STATE                                                    */
/* ========================================================= */
let messages = [];
let isProcessing = false;
let isDarkMode = true;
const loadingStateKey = "chat_ui_loaded_once";
let componentReady = sessionStorage.getItem(loadingStateKey) === "1";

let currentSessionId = null;
let isLoggedIn = false;

/* ========================================================= */
/*  DOM REFS                                                 */
/* ========================================================= */
const loginModal = document.getElementById("loginModal");
const loginBtn = document.getElementById("loginBtn");
const loginCloseBtn = document.getElementById("loginCloseBtn");
const loginMssv = document.getElementById("loginMssv");
const loginDob = document.getElementById("loginDob");
const headerLoginBtn = document.getElementById("headerLoginBtn");
const headerAuthArea = document.getElementById("headerAuthArea");
const sidebarLoginBtn = document.getElementById("sidebarLoginBtn");
const sidebarLoggedIn = document.getElementById("sidebarLoggedIn");
const sidebarGuest = document.getElementById("sidebarGuest");
const userInfoDisplay = document.getElementById("userInfoDisplay");
const newChatBtn = document.getElementById("newChatBtn");
const logoutBtn = document.getElementById("logoutBtn");
const historyList = document.getElementById("historyList");

const messagesArea = document.getElementById("messages-area");
const chatContainer = document.getElementById("chat-container");
const typingIndicator = document.getElementById("typing-indicator");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const themeToggle = document.getElementById("theme-toggle");
const themeIcon = document.getElementById("theme-icon");
const loadingOverlay = document.getElementById("loading-overlay");
const sidebar = document.querySelector(".sidebar");
const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");

if (componentReady && loadingOverlay) {
    loadingOverlay.classList.add("hidden");
    loadingOverlay.style.display = "none";
}

/* ========================================================= */
/*  UTILITIES                                                */
/* ========================================================= */
function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}
