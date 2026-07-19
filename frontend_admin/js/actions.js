/* ========================================================= */
/*  ACTIONS                                                  */
/* ========================================================= */

// Polling and rendering
let _realtimeIntervalId = null;
function startRealtimePolling(intervalMs = 3000) {
    if (_realtimeIntervalId) return;
    _realtimeIntervalId = setInterval(() => {
        if (!componentReady) return;
        // Send only a timestamp (no action) to request a rerun
        StreamlitApi.setComponentValue({ timestamp: Date.now() });
    }, intervalMs);
}

function stopRealtimePolling() {
    if (_realtimeIntervalId) {
        clearInterval(_realtimeIntervalId);
        _realtimeIntervalId = null;
    }
}

// Start polling after first render
window.addEventListener('message', function onFirstRender(ev) {
    if (ev.data && ev.data.type === 'streamlit:render') {
        startRealtimePolling(3000);
        window.removeEventListener('message', onFirstRender);
    }
});

// Cleanup
window.addEventListener('beforeunload', () => stopRealtimePolling());

/* ========================================================= */
/*  STREAMLIT RENDER                                         */
/* ========================================================= */
window.addEventListener("message", (event) => {
    if (event.data.type === "streamlit:render") {
        const args = event.data.args || {};

        if (!componentReady) {
            componentReady = true;
            sessionStorage.setItem(loadingStateKey, "1");
            loadingOverlay.classList.add("hidden");
            setTimeout(() => loadingOverlay.remove(), 600);
        }

        if (args.stats) {
            try {
                statsData = JSON.parse(args.stats);
                if (typeof renderDashboard === 'function') {
                    renderDashboard();
                }
            } catch (e) {
                console.error("Failed to parse stats:", e);
            }
        }

        StreamlitApi.setFrameHeight(document.documentElement.scrollHeight);
    }
});

/* ========================================================= */
/*  INIT                                                     */
/* ========================================================= */
StreamlitApi.setComponentReady();
StreamlitApi.setFrameHeight(window.innerHeight);

/* ========================================================= */
/*  KNOWLEDGE ACTIONS                                        */
/* ========================================================= */
function toggleKnowledgeFile(filename, enabled) {
    StreamlitApi.setComponentValue({
        action: "update_knowledge_status",
        filename: filename,
        enabled: enabled,
        timestamp: Date.now()
    });
}

function deleteKnowledgeFile(filename) {
    if (confirm("Bạn có chắc chắn muốn XÓA VĨNH VIỄN tệp " + filename + " không? Hành động này không thể hoàn tác.")) {
        StreamlitApi.setComponentValue({
            action: "delete_knowledge_file",
            filename: filename,
            timestamp: Date.now()
        });
    }
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file extension
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'txt' && ext !== 'json') {
        alert("Chỉ hỗ trợ tệp .txt và .json!");
        event.target.value = "";
        return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert("Tệp quá lớn! Kích thước tối đa là 10MB.");
        event.target.value = "";
        return;
    }

    // Read as ArrayBuffer to handle all encodings (UTF-8, UTF-16, ANSI)
    const reader = new FileReader();
    reader.onload = function(e) {
        const buffer = e.target.result;
        const bytes = new Uint8Array(buffer);
        let content = "";

        // Detect BOM and decode accordingly
        if (bytes.length >= 2 && bytes[0] === 0xFF && bytes[1] === 0xFE) {
            // UTF-16 LE BOM
            const decoder = new TextDecoder("utf-16le");
            content = decoder.decode(buffer);
        } else if (bytes.length >= 2 && bytes[0] === 0xFE && bytes[1] === 0xFF) {
            // UTF-16 BE BOM
            const decoder = new TextDecoder("utf-16be");
            content = decoder.decode(buffer);
        } else if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
            // UTF-8 BOM
            const decoder = new TextDecoder("utf-8");
            content = decoder.decode(buffer);
        } else {
            // Try UTF-8 first
            const decoder = new TextDecoder("utf-8", { fatal: true });
            try {
                content = decoder.decode(buffer);
            } catch (err) {
                // Fallback to Windows-1252 (ANSI) for legacy files
                const fallbackDecoder = new TextDecoder("windows-1252");
                content = fallbackDecoder.decode(buffer);
            }
        }

        // Remove BOM character if present at start
        if (content.charCodeAt(0) === 0xFEFF) {
            content = content.substring(1);
        }

        content = content.trim();

        if (!content) {
            alert("Tệp trống hoặc không đọc được nội dung! Vui lòng kiểm tra lại.");
            event.target.value = "";
            return;
        }

        // Validate JSON format if .json file
        if (ext === 'json') {
            try {
                JSON.parse(content);
            } catch (err) {
                alert("Tệp JSON không hợp lệ! Vui lòng kiểm tra cú pháp JSON.\n\nLỗi: " + err.message);
                event.target.value = "";
                return;
            }
        }

        StreamlitApi.setComponentValue({
            action: "upload_knowledge_file",
            filename: file.name,
            content: content,
            timestamp: Date.now()
        });

        alert("✅ Đã tải lên tệp: " + file.name);
        event.target.value = "";
    };

    reader.onerror = function() {
        alert("Lỗi khi đọc tệp! Vui lòng thử lại.");
        event.target.value = "";
    };

    reader.readAsArrayBuffer(file);
}

/* ========================================================= */
/*  CONSULT ACTIONS                                          */
/* ========================================================= */
function openConsultDetail(idx) {
    const regs = statsData.consult_registrations || [];
    const r = regs[idx];
    if (!r) return;

    const status = r.status || "new";
    const statusLabels = {
        new: { label: "🆕 Mới", cls: "status-new" },
        contacted: { label: "📞 Đã liên hệ", cls: "status-contacted" },
        done: { label: "✅ Đã trả lời", cls: "status-done" }
    };
    const statusInfo = statusLabels[status] || statusLabels.new;

    modalTitle.textContent = "Chi tiết yêu cầu tư vấn #" + (idx + 1);
    modalBody.innerHTML = `
        <div class="consult-detail">
            <div class="consult-detail-row">
                <div class="consult-detail-label">Họ và tên</div>
                <div class="consult-detail-value"><strong>${escapeHtml(r.name)}</strong></div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Số điện thoại</div>
                <div class="consult-detail-value">${escapeHtml(r.phone)}</div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Email</div>
                <div class="consult-detail-value">${escapeHtml(r.email || "Không cung cấp")}</div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Ngành quan tâm</div>
                <div class="consult-detail-value">${escapeHtml(r.major || "Không chọn")}</div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Nội dung</div>
                <div class="consult-detail-value">${escapeHtml(r.message || "Không có nội dung")}</div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Tài khoản gửi</div>
                <div class="consult-detail-value"><span class="badge badge-info">${escapeHtml(r.user_key || "guest")}</span></div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Thời gian gửi</div>
                <div class="consult-detail-value">${formatTimestamp(r.timestamp)}</div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Trạng thái</div>
                <div class="consult-detail-value">
                    <select class="status-select" id="modalStatusSelect" onchange="changeStatusFromModal(${idx}, this.value)">
                        <option value="new" ${status === 'new' ? 'selected' : ''}>🆕 Mới</option>
                        <option value="contacted" ${status === 'contacted' ? 'selected' : ''}>📞 Đã liên hệ</option>
                        <option value="done" ${status === 'done' ? 'selected' : ''}>✅ Đã trả lời</option>
                    </select>
                </div>
            </div>
            <div class="consult-detail-row">
                <div class="consult-detail-label">Ghi chú Admin</div>
                <div class="consult-detail-value">
                    <textarea class="admin-note-area" id="adminNoteArea" placeholder="Thêm ghi chú cho yêu cầu này...">${escapeHtml(r.admin_note || "")}</textarea>
                    <button class="save-note-btn" onclick="saveAdminNote(${idx})">💾 Lưu ghi chú</button>
                </div>
            </div>
            <div class="consult-detail-actions">
                <button class="action-btn btn-delete" onclick="deleteConsult(${idx}); modalOverlay.classList.remove('open');">🗑 Xóa yêu cầu</button>
            </div>
        </div>
    `;
    modalOverlay.classList.add("open");
}

function cycleConsultStatus(idx) {
    const regs = statsData.consult_registrations || [];
    const r = regs[idx];
    if (!r) return;

    const statusCycle = ["new", "contacted", "done"];
    const current = r.status || "new";
    const nextIdx = (statusCycle.indexOf(current) + 1) % statusCycle.length;
    const nextStatus = statusCycle[nextIdx];

    StreamlitApi.setComponentValue({
        action: "update_consult_status",
        index: idx,
        status: nextStatus,
        timestamp: Date.now()
    });
}

function changeStatusFromModal(idx, status) {
    StreamlitApi.setComponentValue({
        action: "update_consult_status",
        index: idx,
        status: status,
        timestamp: Date.now()
    });
}

function deleteConsult(idx) {
    if (!confirm("Bạn có chắc muốn xóa yêu cầu tư vấn này?")) return;
    StreamlitApi.setComponentValue({
        action: "delete_consult",
        index: idx,
        timestamp: Date.now()
    });
}

function saveAdminNote(idx) {
    const note = document.getElementById("adminNoteArea").value.trim();
    StreamlitApi.setComponentValue({
        action: "update_consult_note",
        index: idx,
        note: note,
        timestamp: Date.now()
    });
}

/* ========================================================= */
/*  PROMPT ACTIONS                                           */
/* ========================================================= */
function openPromptEdit(key) {
    const promptObj = localPrompts[key];
    if (!promptObj) return;

    modalTitle.textContent = "Sửa Prompt: " + promptObj.name;
    modalBody.innerHTML = `
        <div class="consult-detail">
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 12px;">Lưu ý: Không thay đổi các biến <code>{context}</code>, <code>{question}</code>, <code>{current_date}</code> vì hệ thống cần chúng để điền dữ liệu động.</p>
            <div class="consult-detail-row" style="display:flex; flex-direction:column; align-items:flex-start;">
                <div class="consult-detail-label" style="margin-bottom:8px;">Nội dung kịch bản</div>
                <div class="consult-detail-value" style="width:100%;">
                    <textarea id="modalPromptContent" style="width: 100%; height: 350px; padding: 12px; border: 1px solid var(--border); border-radius: 8px; font-family: monospace; font-size: 14px; line-height: 1.5; resize: vertical;">${escapeHtml(promptObj.content)}</textarea>
                </div>
            </div>
            <div class="consult-detail-actions">
                <button class="action-btn" style="background: #000080; color: white;" onclick="savePromptFromModal('${key}')">💾 Lưu thay đổi</button>
            </div>
        </div>
    `;
    modalOverlay.classList.add("open");
}

function savePromptFromModal(key) {
    const newContent = document.getElementById("modalPromptContent").value;
    if (!newContent.trim()) {
        alert("Nội dung prompt không được để trống!");
        return;
    }
    
    localPrompts[key].content = newContent;
    
    StreamlitApi.setComponentValue({
        action: "update_system_prompt",
        prompts: localPrompts,
        timestamp: Date.now()
    });
    modalOverlay.classList.remove("open");
}
