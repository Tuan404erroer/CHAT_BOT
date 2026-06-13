import re

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# ADD CSS FOR SIDEBAR & LOGIN
added_css = \"\"\"
        /* OVERLAY LOGIN */
        .login-overlay {
            position: fixed;
            inset: 0;
            background: var(--bg-primary);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            padding: 20px;
        }
        .login-overlay[hidden] {
            display: none !important;
        }
        .login-box {
            background: var(--bg-secondary);
            padding: 40px;
            border-radius: 20px;
            border: 1px solid var(--divider);
            box-shadow: var(--shadow-lg);
            width: 100%;
            max-width: 420px;
        }
        .login-box h2 {
            margin-bottom: 8px;
            text-align: center;
            color: var(--text-primary);
        }
        .login-box p {
            margin-bottom: 24px;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.95rem;
        }
        .login-box input {
            width: 100%;
            padding: 14px;
            margin-bottom: 16px;
            background: var(--input-bg);
            border: 1px solid var(--input-border);
            border-radius: 12px;
            color: var(--text-primary);
            font-family: inherit;
        }
        .login-box button {
            width: 100%;
            padding: 14px;
            background: var(--accent);
            color: #fff;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .login-box button:hover {
            opacity: 0.9;
        }
        
        /* APP LAYOUT */
        .main-wrapper {
            display: flex;
            height: 100vh;
            width: 100vw;
        }
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--divider);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            transition: transform 0.3s ease;
        }
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--divider);
        }
        .sidebar-header .user-info {
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--accent);
        }
        .new-chat-btn {
            width: 100%;
            padding: 10px;
            background: var(--bg-surface-hover);
            border: 1px dashed var(--accent-border);
            border-radius: 8px;
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-weight: 500;
        }
        .new-chat-btn:hover {
            background: var(--accent-dim);
            border-color: var(--accent);
        }
        .history-list {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .history-item {
            padding: 12px;
            border-radius: 8px;
            cursor: pointer;
            color: var(--text-primary);
            background: transparent;
            border: 1px solid transparent;
            text-align: left;
            font-size: 0.9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .history-item:hover {
            background: var(--bg-surface);
        }
        .history-item.active {
            background: var(--accent-dim);
            border: 1px solid var(--accent-border);
            color: var(--accent);
        }
        .sidebar-footer {
            padding: 20px;
            border-top: 1px solid var(--divider);
        }
        .logout-btn {
            width: 100%;
            padding: 10px;
            background: transparent;
            border: 1px solid var(--divider);
            border-radius: 8px;
            color: var(--text-secondary);
            cursor: pointer;
        }
        .logout-btn:hover {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border-color: rgba(239, 68, 68, 0.3);
        }
        .app-container {
            flex: 1;
            width: auto;
        }
\"\"\"

text = text.replace('/* ============================================= */\\n        /*  RESET & BASE                                 */', added_css + '\\n        /* ============================================= */\\n        /*  RESET & BASE                                 */')


# INJECT DOM
old_app_container = '<div class=\"app-container\">'
new_dom = \"\"\"
    <!-- LOGIN SCREEN -->
    <div id=\"loginScreen\" class=\"login-overlay\">
        <div class=\"login-box\">
            <h2>?? C?ng Tu V?n AI</h2>
            <p>Vui lòng dang nh?p d? ti?p t?c</p>
            <input type=\"text\" id=\"loginMssv\" placeholder=\"Mã s? sinh viên (MSSV) / SÐT\">
            <input type=\"text\" id=\"loginDob\" placeholder=\"Ngày sinh (VD: 01/01/2005)\">
            <button id=\"loginBtn\">Ðang nh?p</button>
        </div>
    </div>

    <div class=\"main-wrapper\" id=\"mainWrapper\" hidden>
        <!-- SIDEBAR -->
        <div class=\"sidebar\">
            <div class=\"sidebar-header\">
                <div class=\"user-info\" id=\"userInfoDisplay\">Chào b?n: ...</div>
                <button class=\"new-chat-btn\" id=\"newChatBtn\">? Cu?c trò chuy?n m?i</button>
            </div>
            <div class=\"history-list\" id=\"historyList\">
                <!-- History injected via JS -->
            </div>
            <div class=\"sidebar-footer\">
                <button class=\"logout-btn\" id=\"logoutBtn\">Ðang xu?t</button>
            </div>
        </div>

        <div class=\"app-container\">
\"\"\"

text = text.replace(old_app_container, new_dom)

# Close the .main-wrapper at the end of the body
text = text.replace('</div>\\n    <!-- ========================================== -->\\n    <!--  JS SCRIPT                                 -->', '</div>\\n    </div>\\n    <!-- ========================================== -->\\n    <!--  JS SCRIPT                                 -->')


# UPDATE JS
js_injection = \"\"\"
        // --- ADDED STATE REFS ---
        const loginScreen = document.getElementById("loginScreen");
        const mainWrapper = document.getElementById("mainWrapper");
        const loginBtn = document.getElementById("loginBtn");
        const loginMssv = document.getElementById("loginMssv");
        const loginDob = document.getElementById("loginDob");
        const userInfoDisplay = document.getElementById("userInfoDisplay");
        const newChatBtn = document.getElementById("newChatBtn");
        const logoutBtn = document.getElementById("logoutBtn");
        const historyList = document.getElementById("historyList");

        let currentSessionId = null;

        loginBtn.addEventListener("click", () => {
            const mssv = loginMssv.value.trim();
            const dob = loginDob.value.trim();
            if (mssv && dob) {
                StreamlitApi.setComponentValue({ action: "login", mssv, dob, timestamp: Date.now() });
            } else {
                alert("Vui lòng di?n d? MSSV và ngày sinh!");
            }
        });

        logoutBtn.addEventListener("click", () => {
            StreamlitApi.setComponentValue({ action: "logout", timestamp: Date.now() });
        });

        newChatBtn.addEventListener("click", () => {
            StreamlitApi.setComponentValue({ action: "new_session", timestamp: Date.now() });
        });

        function renderHistory(historyStr, activeId) {
            historyList.innerHTML = "";
            let historyObj = {};
            try {
                historyObj = JSON.parse(historyStr);
            } catch (e) {}
            
            // reverse iterate
            const keys = Object.keys(historyObj).reverse();
            for (let id of keys) {
                const sessionInfo = historyObj[id];
                const btn = document.createElement("button");
                btn.className = "history-item";
                if (id === activeId) btn.classList.add("active");
                btn.textContent = sessionInfo.title || "Ðo?n chat";
                btn.onclick = () => {
                    StreamlitApi.setComponentValue({ action: "load_session", session_id: id, timestamp: Date.now() });
                };
                historyList.appendChild(btn);
            }
        }
\"\"\"

text = text.replace('const sendBtn = document.getElementById("sendBtn");', 'const sendBtn = document.getElementById("sendBtn");\\n' + js_injection)

# IN RENDER UPDATE
old_js_render_check = 'if (!args) return;'
new_js_render_check = \"\"\"if (!args) return;
            
            if (args.logged_in) {
                loginScreen.hidden = true;
                mainWrapper.hidden = false;
                userInfoDisplay.textContent = "Chào b?n: " + args.mssv;
                currentSessionId = args.current_session_id;
                if (args.history) {
                    renderHistory(args.history, currentSessionId);
                }
            } else {
                loginScreen.hidden = false;
                mainWrapper.hidden = true;
            }
\"\"\"
text = text.replace(old_js_render_check, new_js_render_check)

# IN SEND MESSAGE logic
text = text.replace('StreamlitApi.setComponentValue({ message: text, timestamp: Date.now() });', 'StreamlitApi.setComponentValue({ action: "chat", message: text, timestamp: Date.now() });')


with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
