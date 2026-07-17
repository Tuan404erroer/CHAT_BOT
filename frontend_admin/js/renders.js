/* ========================================================= */
/*  RENDER DASHBOARD                                         */
/* ========================================================= */
function renderDashboard() {
    if (!statsData) return;
    renderGreeting();
    renderStatCards();
    renderRatingChart();
    renderRecentChats();
    renderUsersTable();
    renderHistoryTable();
    renderRatingsTable();
    renderKnowledgeTable();
    renderConsultSection();
    renderPromptSection();
}

/* ========================================================= */
/*  GREETING                                                 */
/* ========================================================= */
function renderGreeting() {
    const hour = statsData.greeting_hour || 8;
    let greeting = "Chào buổi sáng";
    if (hour >= 12 && hour < 18) greeting = "Chào buổi chiều";
    else if (hour >= 18) greeting = "Chào buổi tối";
    document.getElementById("greetingText").textContent = greeting + ", Admin!";
}

/* ========================================================= */
/*  STAT CARDS                                               */
/* ========================================================= */
function renderStatCards() {
    const grid = document.getElementById("statsGrid");
    grid.innerHTML = "";

    const cards = [
        { icon: "💬", label: "Phiên chat", value: statsData.total_sessions },
        { icon: "❓", label: "Tổng số câu hỏi", value: statsData.total_questions },
        { icon: "😊", label: "Tỷ lệ hài lòng", value: statsData.satisfaction_rate + "%" },
        { icon: "👥", label: "Người dùng", value: statsData.total_users }
    ];

    cards.forEach(c => {
        const card = document.createElement("div");
        card.className = "stat-card";
        card.innerHTML = `
            <div class="stat-header">
                <div class="stat-icon">${c.icon}</div>
            </div>
            <div class="stat-label">${c.label}</div>
            <div class="stat-value">${typeof c.value === 'number' ? c.value.toLocaleString() : c.value}</div>
        `;
        grid.appendChild(card);
    });
}

/* ========================================================= */
/*  RATING CHART                                             */
/* ========================================================= */
function renderRatingChart() {
    const ctx = document.getElementById("ratingChart").getContext("2d");

    if (ratingChart) ratingChart.destroy();

    const up = statsData.total_up || 0;
    const down = statsData.total_down || 0;
    const noRate = (statsData.total_questions || 0) - up - down;

    if (up === 0 && down === 0 && noRate === 0) {
        // No data
        const container = document.getElementById("ratingChart").parentElement;
        container.innerHTML = '<div class="empty-table"><div class="empty-icon">📊</div><p>Chưa có dữ liệu đánh giá</p></div>';
        return;
    }

    ratingChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["👍 Tốt", "👎 Chưa tốt", "Chưa đánh giá"],
            datasets: [{
                data: [up, down, noRate > 0 ? noRate : 0],
                backgroundColor: [
                    "rgba(34, 197, 94, 0.85)",
                    "rgba(239, 68, 68, 0.85)",
                    "rgba(148, 163, 184, 0.4)"
                ],
                borderColor: [
                    "rgba(34, 197, 94, 1)",
                    "rgba(239, 68, 68, 1)",
                    "rgba(148, 163, 184, 0.6)"
                ],
                borderWidth: 2,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 10,
                        font: { family: "'Inter', sans-serif", size: 12, weight: 500 }
                    }
                }
            }
        }
    });
}

/* ========================================================= */
/*  RECENT CHATS                                             */
/* ========================================================= */
function renderRecentChats() {
    const container = document.getElementById("recentChats");
    container.innerHTML = "";

    const sessions = (statsData.sessions || []).slice(-6).reverse();
    const avatarClasses = ["a1", "a2", "a3", "a4"];

    if (sessions.length === 0) {
        container.innerHTML = '<div class="empty-table"><div class="empty-icon">💬</div><p>Chưa có phiên chat nào</p></div>';
        return;
    }

    sessions.forEach((s, idx) => {
        const item = document.createElement("div");
        item.className = "recent-chat-item";
        item.onclick = () => openChatModal(s);

        const initials = getInitials(s.user);
        const avatarClass = avatarClasses[idx % avatarClasses.length];

        let ratingBadge = "";
        if (s.thumbs_up > 0) {
            ratingBadge = `<div class="chat-rating-badge good">👍 ${s.thumbs_up}</div>`;
        } else if (s.thumbs_down > 0) {
            ratingBadge = `<div class="chat-rating-badge bad">👎 ${s.thumbs_down}</div>`;
        }

        item.innerHTML = `
            <div class="chat-avatar ${avatarClass}">${initials}</div>
            <div class="chat-info">
                <div class="chat-user">${escapeHtml(s.user)}</div>
                <div class="chat-preview">${escapeHtml(s.title)}</div>
            </div>
            <div class="chat-meta">
                <div class="chat-count">${s.message_count} tin nhắn</div>
                ${ratingBadge}
            </div>
        `;
        container.appendChild(item);
    });
}

/* ========================================================= */
/*  USERS TABLE                                              */
/* ========================================================= */
function renderUsersTable() {
    const tbody = document.getElementById("usersTableBody");
    tbody.innerHTML = "";

    const users = statsData.users || [];
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty-table"><div class="empty-icon">👥</div>Chưa có người dùng</td></tr>';
        return;
    }

    users.forEach(u => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${escapeHtml(u.user_key)}</strong></td>
            <td><span class="badge badge-info">${u.session_count} phiên</span></td>
            <td><span class="badge badge-muted">${u.question_count} câu hỏi</span></td>
        `;
        tbody.appendChild(tr);
    });
}

/* ========================================================= */
/*  HISTORY TABLE                                            */
/* ========================================================= */
function renderHistoryTable() {
    const tbody = document.getElementById("historyTableBody");
    tbody.innerHTML = "";

    const sessions = statsData.sessions || [];
    if (sessions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-table"><div class="empty-icon">💬</div>Chưa có lịch sử chat</td></tr>';
        return;
    }

    sessions.forEach((s, idx) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${escapeHtml(s.user)}</strong></td>
            <td>${escapeHtml(s.title)}</td>
            <td>${s.message_count}</td>
            <td>${s.thumbs_up > 0 ? '<span class="badge badge-success">👍 ' + s.thumbs_up + '</span>' : '<span class="badge badge-muted">0</span>'}</td>
            <td>${s.thumbs_down > 0 ? '<span class="badge badge-danger">👎 ' + s.thumbs_down + '</span>' : '<span class="badge badge-muted">0</span>'}</td>
            <td><button class="filter-tab" style="padding:6px 14px" onclick="openChatModalByIndex(${idx})">Xem</button></td>
        `;
        tbody.appendChild(tr);
    });
}

/* ========================================================= */
/*  RATINGS TABLE                                            */
/* ========================================================= */
function renderRatingsTable() {
    const tbody = document.getElementById("ratingsTableBody");
    tbody.innerHTML = "";

    let rated = statsData.rated_messages || [];

    if (currentRatingFilter !== "all") {
        rated = rated.filter(r => r.rating === currentRatingFilter);
    }

    if (rated.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-table"><div class="empty-icon">⭐</div>Chưa có đánh giá nào</td></tr>';
        return;
    }

    rated.forEach(r => {
        const tr = document.createElement("tr");
        const badgeClass = r.rating === "up" ? "badge-success" : "badge-danger";
        const badgeText = r.rating === "up" ? "👍 Tốt" : "👎 Chưa tốt";
        tr.innerHTML = `
            <td><strong>${escapeHtml(r.user)}</strong></td>
            <td>${escapeHtml(r.question)}</td>
            <td style="max-width:300px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(r.answer)}</td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// Filter tabs for ratings
document.getElementById("ratingFilter").addEventListener("click", (e) => {
    const tab = e.target.closest(".filter-tab");
    if (!tab) return;
    document.querySelectorAll("#ratingFilter .filter-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentRatingFilter = tab.dataset.filter;
    renderRatingsTable();
});

/* ========================================================= */
/*  KNOWLEDGE MANAGEMENT                                     */
/* ========================================================= */
function renderKnowledgeTable() {
    const tbody = document.getElementById("knowledgeTableBody");
    tbody.innerHTML = "";

    const files = statsData.knowledge_files || [];
    
    // Tính tổng dung lượng
    const totalKb = files.reduce((sum, f) => sum + (f.size_kb || 0), 0);
    const mb = (totalKb / 1024).toFixed(1);
    const storageDisplay = document.getElementById("totalStorageDisplay");
    if (storageDisplay) storageDisplay.textContent = mb + " MB";

    if (files.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-table"><div class="empty-icon">📚</div>Chưa có tệp dữ liệu nào</td></tr>';
        return;
    }

    files.forEach((f, idx) => {
        const tr = document.createElement("tr");
        const isEnabled = f.enabled !== false;
        
        const statusBadge = isEnabled 
            ? '<span class="badge badge-success" style="background:#dcfce7; color:#16a34a;">● Đang sử dụng</span>'
            : '<span class="badge badge-muted">● Đã ẩn</span>';
            
        const dateStr = f.uploaded_at ? new Date(f.uploaded_at).toLocaleDateString("vi-VN") : "—";
        
        const icon = f.name.toLowerCase().endsWith(".json") ? "{ }" : "📄";
        const iconColor = f.name.toLowerCase().endsWith(".json") ? "#3b82f6" : "#f59e0b";

        tr.innerHTML = `
            <td>${(idx + 1).toString().padStart(2, '0')}</td>
            <td><strong style="color: ${iconColor}; margin-right: 5px;">${icon}</strong> <strong>${escapeHtml(f.name)}</strong></td>
            <td>${dateStr}</td>
            <td>${f.size_kb} KB</td>
            <td>
                <div style="cursor: pointer;" onclick="toggleKnowledgeFile('${escapeHtml(f.name)}', ${!isEnabled})">
                    ${statusBadge}
                </div>
            </td>
            <td>
                <button class="action-btn btn-delete" onclick="deleteKnowledgeFile('${escapeHtml(f.name)}')" title="Xóa">🗑</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

/* ========================================================= */
/*  CONSULT MANAGEMENT                                       */
/* ========================================================= */
let currentConsultFilter = "all";

function renderConsultSection() {
    renderConsultStats();
    renderConsultTable();
    updateConsultNavBadge();
}

function updateConsultNavBadge() {
    const badge = document.getElementById("consultNavBadge");
    const regs = statsData.consult_registrations || [];
    const newCount = regs.filter(r => !r.status || r.status === "new").length;
    if (newCount > 0) {
        badge.textContent = newCount;
        badge.style.display = "inline-block";
    } else {
        badge.style.display = "none";
    }
}

function renderConsultStats() {
    const grid = document.getElementById("consultStatsGrid");
    grid.innerHTML = "";

    const regs = statsData.consult_registrations || [];
    const totalCount = regs.length;
    const newCount = regs.filter(r => !r.status || r.status === "new").length;
    const contactedCount = regs.filter(r => r.status === "contacted").length;
    const doneCount = regs.filter(r => r.status === "done").length;

    const cards = [
        { icon: "📋", label: "Tổng yêu cầu", value: totalCount },
        { icon: "🆕", label: "Chờ xử lý", value: newCount },
        { icon: "📞", label: "Đã liên hệ", value: contactedCount },
        { icon: "✅", label: "Đã trả lời", value: doneCount }
    ];

    cards.forEach(c => {
        const card = document.createElement("div");
        card.className = "stat-card";
        card.innerHTML = `
            <div class="stat-header">
                <div class="stat-icon">${c.icon}</div>
            </div>
            <div class="stat-label">${c.label}</div>
            <div class="stat-value">${c.value}</div>
        `;
        grid.appendChild(card);
    });
}

function renderConsultTable() {
    const tbody = document.getElementById("consultTableBody");
    tbody.innerHTML = "";

    let regs = statsData.consult_registrations || [];

    if (currentConsultFilter !== "all") {
        regs = regs.filter(r => {
            const status = r.status || "new";
            return status === currentConsultFilter;
        });
    }

    if (regs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-table"><div class="empty-icon">📋</div>Chưa có yêu cầu tư vấn nào</td></tr>';
        return;
    }

    // We need original indexes for actions
    const allRegs = statsData.consult_registrations || [];

    regs.forEach(r => {
        const originalIdx = allRegs.indexOf(r);
        const tr = document.createElement("tr");
        const status = r.status || "new";
        const statusLabels = {
            new: { label: "🆕 Mới", cls: "status-new" },
            contacted: { label: "📞 Đã liên hệ", cls: "status-contacted" },
            done: { label: "✅ Đã trả lời", cls: "status-done" }
        };
        const statusInfo = statusLabels[status] || statusLabels.new;
        const userKey = r.user_key || "guest";

        tr.innerHTML = `
            <td>${originalIdx + 1}</td>
            <td><strong>${escapeHtml(r.name)}</strong></td>
            <td>${escapeHtml(r.phone)}</td>
            <td>${escapeHtml(r.email || "—")}</td>
            <td>${escapeHtml(r.major || "—")}</td>
            <td><span class="badge badge-info">${escapeHtml(userKey)}</span></td>
            <td><span class="consult-status-badge ${statusInfo.cls}">${statusInfo.label}</span></td>
            <td>
                <div class="action-btn-group">
                    <button class="action-btn btn-view" onclick="openConsultDetail(${originalIdx})" title="Xem chi tiết">👁 Xem</button>
                    <button class="action-btn btn-status" onclick="cycleConsultStatus(${originalIdx})" title="Đổi trạng thái">🔄</button>
                    <button class="action-btn btn-delete" onclick="deleteConsult(${originalIdx})" title="Xóa">🗑</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Filter tabs for consult
document.getElementById("consultFilter").addEventListener("click", (e) => {
    const tab = e.target.closest(".filter-tab");
    if (!tab) return;
    document.querySelectorAll("#consultFilter .filter-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentConsultFilter = tab.dataset.filter;
    renderConsultTable();
});

/* ========================================================= */
/*  PROMPT MANAGEMENT                                        */
/* ========================================================= */
let localPrompts = {};

function renderPromptSection() {
    const tbody = document.getElementById("promptTableBody");
    if (!tbody || !statsData.system_prompts) return;
    
    localPrompts = JSON.parse(JSON.stringify(statsData.system_prompts)); // clone
    tbody.innerHTML = "";
    
    for (const [key, promptObj] of Object.entries(localPrompts)) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="text-align: center;"><strong>${escapeHtml(key)}</strong></td>
            <td style="text-align: center;">${escapeHtml(promptObj.name)}</td>
            <td style="text-align: center;">${escapeHtml(promptObj.description)}</td>
            <td style="text-align: center;">
                <button class="action-btn btn-view" onclick="openPromptEdit('${key}')" title="Sửa kịch bản">✏️ Sửa</button>
            </td>
        `;
        tbody.appendChild(tr);
    }
}
