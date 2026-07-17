/* ========================================================= */
/*  STATE                                                    */
/* ========================================================= */
let statsData = null;
let ratingChart = null;
let currentRatingFilter = "all";
const loadingStateKey = "admin_ui_loaded_once";
let componentReady = sessionStorage.getItem(loadingStateKey) === "1";

/* ========================================================= */
/*  DOM REFS                                                 */
/* ========================================================= */
const loadingOverlay = document.getElementById("loadingOverlay");
const modalOverlay = document.getElementById("modalOverlay");
const modalClose = document.getElementById("modalClose");
const modalBody = document.getElementById("modalBody");
const modalTitle = document.getElementById("modalTitle");
const headerTitle = document.getElementById("headerTitle");
const globalSearch = document.getElementById("globalSearch");

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

function getInitials(userKey) {
    if (!userKey) return "?";
    const parts = userKey.split("_");
    const mssv = parts[0] || "";
    return mssv.substring(0, 2).toUpperCase();
}

function formatTimestamp(ts) {
    if (!ts) return "—";
    try {
        const d = new Date(ts);
        if (isNaN(d.getTime())) return "—";
        return d.toLocaleString("vi-VN", {
            day: "2-digit", month: "2-digit", year: "numeric",
            hour: "2-digit", minute: "2-digit"
        });
    } catch (e) {
        return "—";
    }
}
