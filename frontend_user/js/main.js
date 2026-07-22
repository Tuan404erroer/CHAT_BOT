/* ========================================================= */
/*  HISTORY LIST RENDER                                      */
/* ========================================================= */
function renderHistoryDOM(historyStr, activeId) {
    if (!historyList) return;
    historyList.innerHTML = "";
    let historyObj = {};
    try { historyObj = JSON.parse(historyStr); } catch (e) { }

    const keys = Object.keys(historyObj).reverse();
    for (let id of keys) {
        const sessionInfo = historyObj[id];
        const btn = document.createElement("button");
        btn.className = "history-item";
        if (id === activeId) btn.classList.add("active");
        btn.textContent = sessionInfo.title || "Đoạn chat";
        btn.onclick = () => {
            StreamlitApi.setComponentValue({ action: "load_session", session_id: id, timestamp: Date.now() });
        };
        historyList.appendChild(btn);
    }
}

if (newChatBtn) {
    newChatBtn.addEventListener("click", () => {
        StreamlitApi.setComponentValue({ action: "new_session", timestamp: Date.now() });
    });
}

/* ========================================================= */
/*  SIDEBAR TOGGLE LOGIC                                     */
/* ========================================================= */
if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed");
    });
}

/* ========================================================= */
/*  STREAMLIT RENDER LISTENER                                */
/* ========================================================= */
window.addEventListener("message", (event) => {
    if (event.data.type === "streamlit:render") {
        const args = event.data.args || {};

        if (args.logged_in === true) {
            updateAuthUI(true, args.name, args.picture);
            currentSessionId = args.current_session_id;
            if (args.history) {
                try {
                    renderHistoryDOM(args.history, currentSessionId);
                } catch (e) { }
            }
        } else {
            updateAuthUI(false, "");
        }

        // Show Auth alerts from backend
        if (args.auth_error) {
            if(typeof showAlert === "function") showAlert(args.auth_error, false);
            else alert(args.auth_error);
        }
        if (args.auth_success) {
            if(typeof showAlert === "function") showAlert(args.auth_success, true);
            else alert(args.auth_success);
            
            // If OTP was sent successfully, transition to step 2 automatically
            if (args.auth_success.includes("OTP")) {
                if(typeof showPanel === "function") showPanel("forgot_step2");
            }
        }
        // Hide loading overlay on first render
        if (!componentReady) {
            componentReady = true;
            sessionStorage.setItem(loadingStateKey, "1");
            if (loadingOverlay) {
                loadingOverlay.classList.add("hidden");
                setTimeout(() => loadingOverlay.remove(), 600);
            }
        }

        // Update messages from backend
        if (args.messages) {
            try {
                const serverMessages = JSON.parse(args.messages);
                messages = serverMessages;
                isProcessing = false;
                renderMessages(false);
                hideTyping();
                enableInput();
            } catch (e) {
                console.error("Failed to parse messages:", e);
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
/*  THEME TOGGLE                                             */
/* ========================================================= */
if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        isDarkMode = !isDarkMode;
        document.documentElement.setAttribute("data-theme", isDarkMode ? "dark" : "light");
        themeIcon.textContent = isDarkMode ? "🌙" : "☀️";
    });
}

/* ========================================================= */
/*  MICROPHONE - SPEECH TO TEXT                               */
/* ========================================================= */
const micBtn = document.getElementById("mic-btn");
let recognition = null;
let isRecording = false;

// Check for Web Speech API support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition && micBtn) {
    let finalTranscript = "";

    function initRecognition() {
        recognition = new SpeechRecognition();
        recognition.lang = "vi-VN";
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event) => {
            let interimTranscript = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + " ";
                } else {
                    interimTranscript += transcript;
                }
            }
            if (userInput) {
                userInput.value = finalTranscript + interimTranscript;
                resizeInput();
            }
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            if (event.error === "not-allowed" || event.error === "service-not-allowed") {
                stopRecording();
                alert("Trình duyệt không cho phép truy cập micro.\n\n" +
                    "Hãy thử:\n1. Cho phép quyền micro trong trình duyệt\n" +
                    "2. Sử dụng Chrome/Edge trên HTTPS\n" +
                    "3. Mở trực tiếp trang web (không trong iframe)");
            } else if (event.error === "no-speech") {
                // Không phát hiện giọng nói - tự restart
            } else if (event.error === "aborted") {
                stopRecording();
            } else if (event.error === "network") {
                stopRecording();
                alert("Lỗi kết nối mạng. Tính năng nhận diện giọng nói cần kết nối internet.");
            }
        };

        recognition.onend = () => {
            if (isRecording) {
                try { recognition.start(); } catch (e) { }
            }
        };
    }

    async function startRecording() {
        // Yêu cầu quyền micro trước (quan trọng cho iframe)
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // Dừng stream ngay - chỉ cần trigger permission prompt
            stream.getTracks().forEach(track => track.stop());
        } catch (err) {
            console.error("Mic permission denied:", err);
            alert("Không thể truy cập micro.\nVui lòng cho phép quyền micro trong trình duyệt và thử lại.");
            return;
        }

        finalTranscript = userInput ? userInput.value : "";
        isRecording = true;
        micBtn.classList.add("recording");
        micBtn.title = "Đang nghe... Nhấn để dừng";

        // Tạo mới recognition mỗi lần để tránh lỗi state
        initRecognition();
        try {
            recognition.start();
        } catch (e) {
            console.error("Cannot start recognition:", e);
            stopRecording();
            alert("Không thể khởi động nhận diện giọng nói.\nVui lòng thử lại hoặc sử dụng trình duyệt Chrome/Edge.");
        }
    }

    function stopRecording() {
        isRecording = false;
        micBtn.classList.remove("recording");
        micBtn.title = "Nhấn để nói";
        try {
            if (recognition) recognition.stop();
        } catch (e) { }
    }

    micBtn.addEventListener("click", () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });
} else if (micBtn) {
    // Speech API not supported
    micBtn.addEventListener("click", () => {
        alert("Trình duyệt của bạn không hỗ trợ nhận diện giọng nói.\nVui lòng sử dụng Google Chrome hoặc Microsoft Edge.");
    });
    micBtn.style.opacity = "0.5";
    micBtn.title = "Trình duyệt không hỗ trợ";
    console.warn("Web Speech API not supported in this browser.");
}

/* ========================================================= */
/*  CONSULTATION FORM                                        */
/* ========================================================= */
const consultModal = document.getElementById("consultModal");
const consultRegisterBtn = document.getElementById("consultRegisterBtn");
const consultCloseBtn = document.getElementById("consultCloseBtn");
const consultSubmitBtn = document.getElementById("consultSubmitBtn");
const consultFormContent = document.getElementById("consultFormContent");

function openConsultModal() {
    consultModal.classList.remove("hidden");
    // Reset to form state (in case it was showing success)
    resetConsultForm();
}

function closeConsultModal() {
    consultModal.classList.add("hidden");
}

function resetConsultForm() {
    if (!consultFormContent) return;
    consultFormContent.innerHTML = `
        <div class="consult-header">
            <span class="consult-header-icon">📋</span>
            <h2>Đăng ký tư vấn tuyển sinh</h2>
            <p>Điền thông tin bên dưới, bộ phận tuyển sinh sẽ liên hệ bạn trong thời gian sớm nhất.</p>
        </div>
        <div class="consult-form-row">
            <div class="consult-form-group">
                <label>Họ và tên <span class="required">*</span></label>
                <input type="text" id="consultName" placeholder="Nguyễn Văn A">
            </div>
            <div class="consult-form-group">
                <label>Số điện thoại</label>
                <input type="tel" id="consultPhone" placeholder="0901 234 567">
            </div>
        </div>
        <div class="consult-form-group">
            <label>Email <span class="required">*</span></label>
            <input type="email" id="consultEmail" placeholder="email@example.com">
        </div>
        <div class="consult-form-group">
            <label>Ngành quan tâm</label>
            <select id="consultMajor">
                <option value="">-- Chọn ngành --</option>
                <optgroup label="⚡ Nhóm ngành Điện - Điện tử">
                    <option value="Công nghệ Kỹ thuật Điện, Điện tử">Công nghệ KT Điện, Điện tử (ABET)</option>
                    <option value="Công nghệ Kỹ thuật Điện và Năng lượng tái tạo">Công nghệ KT Điện và Năng lượng tái tạo</option>
                    <option value="Công nghệ Kỹ thuật Điện tử - Viễn thông">Công nghệ KT Điện tử - Viễn thông</option>
                    <option value="Công nghệ Kỹ thuật Bán dẫn và Vi mạch">Công nghệ KT Bán dẫn và Vi mạch</option>
                    <option value="Điện công nghiệp">Điện công nghiệp</option>
                    <option value="Điện tử công nghiệp">Điện tử công nghiệp</option>
                </optgroup>
                <optgroup label="🔧 Nhóm ngành Cơ khí - Ô tô">
                    <option value="Công nghệ Kỹ thuật Cơ khí">Công nghệ KT Cơ khí (ABET)</option>
                    <option value="Công nghệ Kỹ thuật Bảo trì thiết bị công nghiệp">Công nghệ KT Bảo trì thiết bị công nghiệp</option>
                    <option value="Công nghệ Kỹ thuật Ô tô">Công nghệ KT Ô tô (ABET)</option>
                    <option value="Công nghệ Kỹ thuật Nhiệt (Cơ điện lạnh)">Công nghệ KT Nhiệt - Cơ điện lạnh (ABET)</option>
                    <option value="Bảo trì, sửa chữa Ô tô">Bảo trì, sửa chữa Ô tô (Công nghệ Ô tô)</option>
                    <option value="Cơ khí chế tạo (Cắt gọt kim loại)">Cơ khí chế tạo (Cắt gọt kim loại)</option>
                    <option value="Sửa chữa cơ khí (Nguội sửa chữa máy công cụ)">Sửa chữa cơ khí (Nguội sửa chữa máy công cụ)</option>
                    <option value="Hàn (Công nghệ cao)">Hàn (Công nghệ cao)</option>
                    <option value="Kỹ thuật máy lạnh và điều hòa không khí">KT máy lạnh và điều hòa không khí</option>
                </optgroup>
                <optgroup label="💻 Nhóm ngành Công nghệ thông tin">
                    <option value="Công nghệ Thông tin">Công nghệ Thông tin</option>
                    <option value="Quản trị mạng máy tính">Quản trị mạng máy tính</option>
                    <option value="Kỹ thuật sửa chữa, lắp ráp máy tính">KT sửa chữa, lắp ráp máy tính</option>
                </optgroup>
                <optgroup label="🤖 Nhóm ngành Tự động hóa - Cơ điện tử">
                    <option value="Công nghệ Kỹ thuật Điều khiển và Tự động hóa">Công nghệ KT Điều khiển và Tự động hóa</option>
                    <option value="Công nghệ Kỹ thuật Tự động hóa trong nông nghiệp">Công nghệ KT Tự động hóa trong nông nghiệp</option>
                    <option value="Công nghệ Kỹ thuật Cơ điện tử">Công nghệ KT Cơ điện tử (KOSEN-Nhật Bản)</option>
                </optgroup>
                <optgroup label="📊 Nhóm ngành Kinh tế - Tài chính">
                    <option value="Kế toán tin học (Kế toán doanh nghiệp)">Kế toán tin học (Kế toán doanh nghiệp)</option>
                    <option value="Công nghệ Tài chính và Kinh doanh số">Công nghệ Tài chính và Kinh doanh số</option>
                </optgroup>
            </select>
        </div>
        <div class="consult-form-group">
            <label>Nội dung cần tư vấn</label>
            <textarea id="consultMessage" placeholder="Nhập nội dung bạn muốn được tư vấn..."></textarea>
        </div>
        <button class="consult-submit-btn" id="consultSubmitBtn">📨 Gửi đăng ký tư vấn</button>
        <button class="consult-close-btn" id="consultCloseBtn">Đóng</button>
    `;

    // Re-wire event listeners after DOM reset
    const newSubmitBtn = document.getElementById("consultSubmitBtn");
    const newCloseBtn = document.getElementById("consultCloseBtn");
    if (newSubmitBtn) newSubmitBtn.addEventListener("click", submitConsultForm);
    if (newCloseBtn) newCloseBtn.addEventListener("click", closeConsultModal);
}

function submitConsultForm() {
    const name = document.getElementById("consultName").value.trim();
    const phone = document.getElementById("consultPhone").value.trim();
    const email = document.getElementById("consultEmail").value.trim();
    const major = document.getElementById("consultMajor").value;
    const message = document.getElementById("consultMessage").value.trim();

    // Validation
    if (!name) {
        alert("Vui lòng nhập họ và tên!");
        document.getElementById("consultName").focus();
        return;
    }
    if (!email) {
        alert("Vui lòng nhập email!");
        document.getElementById("consultEmail").focus();
        return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert("Email không hợp lệ!");
        document.getElementById("consultEmail").focus();
        return;
    }

    // Phone validation (optional but if provided, must be valid)
    if (phone) {
        const phoneRegex = /^[0-9\s\-\+]{8,15}$/;
        if (!phoneRegex.test(phone)) {
            alert("Số điện thoại không hợp lệ!");
            document.getElementById("consultPhone").focus();
            return;
        }
    }

    // Send to backend via Streamlit
    StreamlitApi.setComponentValue({
        action: "consult_register",
        name: name,
        phone: phone,
        email: email,
        major: major,
        message: message,
        timestamp: Date.now()
    });

    // Show success state
    consultFormContent.innerHTML = `
        <div class="consult-success">
            <span class="success-icon">✅</span>
            <h3>Đăng ký thành công!</h3>
            <p>Cảm ơn bạn <strong>${escapeHtml(name)}</strong> đã đăng ký tư vấn.<br>Bộ phận tuyển sinh sẽ liên hệ bạn qua SĐT <strong>${escapeHtml(phone)}</strong> trong thời gian sớm nhất.</p>
        </div>
        <button class="consult-close-btn" id="consultSuccessClose">Đóng</button>
    `;
    document.getElementById("consultSuccessClose").addEventListener("click", closeConsultModal);
}

if (consultRegisterBtn) consultRegisterBtn.addEventListener("click", openConsultModal);
if (consultCloseBtn) consultCloseBtn.addEventListener("click", closeConsultModal);
if (consultSubmitBtn) consultSubmitBtn.addEventListener("click", submitConsultForm);

// Close modal on backdrop click
if (consultModal) {
    consultModal.addEventListener("click", (e) => {
        if (e.target === consultModal) closeConsultModal();
    });
}

/* ========================================================= */
/*  INITIAL RENDER                                           */
/* ========================================================= */
renderMessages(false);
