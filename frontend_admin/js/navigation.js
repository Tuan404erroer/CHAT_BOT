/* ========================================================= */
/*  NAVIGATION                                               */
/* ========================================================= */
const navItems = document.querySelectorAll(".nav-item[data-page]");
const pageSections = document.querySelectorAll(".page-section");

const pageTitles = {
    overview: "Tổng quan hệ thống",
    history: "Lịch sử Chat",
    ratings: "Đánh giá câu trả lời",
    knowledge: "Dữ liệu Tuyển sinh",
    consult: "Yêu cầu tư vấn",
    prompt: "Quản lý Prompt"
};

navItems.forEach(item => {
    item.addEventListener("click", () => {
        const page = item.dataset.page;
        navItems.forEach(n => n.classList.remove("active"));
        item.classList.add("active");
        pageSections.forEach(s => s.classList.remove("active"));
        document.getElementById("page-" + page).classList.add("active");
        headerTitle.textContent = pageTitles[page] || "Admin";
    });
});

/* ========================================================= */
/*  MODAL                                                    */
/* ========================================================= */
modalClose.addEventListener("click", () => {
    modalOverlay.classList.remove("open");
});
modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) modalOverlay.classList.remove("open");
});

function openChatModal(session) {
    modalTitle.textContent = session.title || "Chi tiết phiên chat";
    modalBody.innerHTML = "";

    const info = document.createElement("div");
    info.style.cssText = "margin-bottom:16px;padding:10px 14px;background:var(--bg-page);border-radius:10px;font-size:0.82rem;color:var(--text-secondary);";
    info.innerHTML = `<strong>Người dùng:</strong> ${escapeHtml(session.user)} &nbsp;|&nbsp; <strong>Tin nhắn:</strong> ${session.message_count}`;
    modalBody.appendChild(info);

    (session.messages || []).forEach(msg => {
        const row = document.createElement("div");
        row.className = "modal-message " + msg.role;

        const avatar = document.createElement("div");
        avatar.className = "msg-avatar";
        avatar.textContent = msg.role === "user" ? "👤" : "🤖";

        const bubble = document.createElement("div");
        bubble.className = "msg-bubble";
        bubble.textContent = msg.content || "";

        if (msg.role === "assistant" && msg.rating) {
            const tag = document.createElement("div");
            tag.className = "msg-rating-tag " + msg.rating;
            tag.textContent = msg.rating === "up" ? "👍 Tốt" : "👎 Chưa tốt";
            bubble.appendChild(tag);
        }

        row.appendChild(avatar);
        row.appendChild(bubble);
        modalBody.appendChild(row);
    });

    modalOverlay.classList.add("open");
}

function openChatModalByIndex(idx) {
    const session = statsData.sessions[idx];
    if (session) openChatModal(session);
}

/* ========================================================= */
/*  SEARCH                                                   */
/* ========================================================= */
globalSearch.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    if (!query) {
        if (typeof renderHistoryTable === 'function') renderHistoryTable();
        if (typeof renderRatingsTable === 'function') renderRatingsTable();
        if (typeof renderConsultTable === 'function') renderConsultTable();
        return;
    }

    // Filter history
    const historyTbody = document.getElementById("historyTableBody");
    const historyRows = historyTbody.querySelectorAll("tr");
    historyRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
    });

    // Filter ratings
    const ratingsTbody = document.getElementById("ratingsTableBody");
    const ratingsRows = ratingsTbody.querySelectorAll("tr");
    ratingsRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
    });

    // Filter consult
    const consultTbody = document.getElementById("consultTableBody");
    const consultRows = consultTbody.querySelectorAll("tr");
    consultRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
    });
});
