import os

with open("frontend/index.html", "r", encoding="utf-8") as f:
    text = f.read()

# ADD CSS
added_css = """
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
        .login-overlay[hidden] { display: none !important; }
        .login-box {
            background: var(--bg-secondary);
            padding: 40px;
            border-radius: 20px;
            border: 1px solid var(--divider);
            box-shadow: var(--shadow-lg);
            width: 100%;
            max-width: 420px;
            text-align: center;
        }
        .login-box h2 {
            margin-bottom: 8px;
            color: var(--text-primary);
        }
        .login-box p {
            margin-bottom: 24px;
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
        .login-box button:hover { opacity: 0.9; }
        
        /* APP LAYOUT */
        .main-wrapper {
            display: flex;
            height: 100vh;
            width: 100vw;
        }
        .main-wrapper[hidden] { display: none !important; }

        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--divider);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--divider);
        }
        .sidebar-header .user-info {
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--accent);
            text-align: left;
        }
        .new-chat-btn {
            width: 100%;
            padding: 12px;
            background: var(--bg-surface-hover);
            border: 1px dashed var(--accent-border);
            border-radius: 8px;
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 500;
            transition: 0.2s;
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
        .history-item:hover { background: var(--bg-surface); }
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
"""
text = text.replace('/*  RESET & BASE                                 */', added_css + '\n        /*  RESET & BASE                                 */')


dom_head = """
    <!-- LOGIN SCREEN -->
    <div id="loginScreen" class="login-overlay">
        <div class="login-box">
            <h2>🎓 Cổng Tư Vấn AI</h2>
            <p>Vui lòng đăng nhập để tiếp tục</p>
            <input type="text" id="loginMssv" placeholder="Mã số sinh viên (MSSV) / SĐT">
            <input type="text" id="loginDob" placeholder="Ngày sinh (VD: 01/01/2005)">
            <button id="loginBtn">Đăng nhập</button>
        </div>
    </div>

    <div class="main-wrapper" id="mainWrapper" hidden>
        <!-- SIDEBAR -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="user-info" id="userInfoDisplay">Chào bạn: ...</div>
                <button class="new-chat-btn" id="newChatBtn">➕ Cuộc trò chuyện mới</button>
            </div>
            <div class="history-list" id="historyList">
                <!-- History injected via JS -->
            </div>
            <div class="sidebar-footer">
                <button class="logout-btn" id="logoutBtn">Đăng xuất</button>
            </div>
        </div>
"""
text = text.replace('<body>', '<body>\n\n' + dom_head)
text = text.replace('</body>', '\n    </div>\n</body>')

js_added = """
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
                alert("Vui lòng điền đủ MSSV và ngày sinh!");
            }
        });

        logoutBtn.addEventListener("click", () => {
            StreamlitApi.setComponentValue({ action: "logout", timestamp: Date.now() });
        });

        newChatBtn.addEventListener("click", () => {
            StreamlitApi.setComponentValue({ action: "new_session", timestamp: Date.now() });
        });

        function renderHistoryDOM(historyStr, activeId) {
            historyList.innerHTML = "";
            let historyObj = {};
            try { historyObj = JSON.parse(historyStr); } catch (e) {}
            
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
"""
text = text.replace('let componentReady = false;', 'let componentReady = false;\n' + js_added)

js_render = """
                if (args.logged_in === true) {
                    loginScreen.hidden = true;
                    mainWrapper.hidden = false;
                    userInfoDisplay.textContent = "Chào bạn: " + args.mssv;
                    currentSessionId = args.current_session_id;
                    if (args.history) {
                        try {
                            renderHistoryDOM(args.history, currentSessionId);
                        } catch(e) {}
                    }
                } else if (args.logged_in === false) {
                    loginScreen.hidden = false;
                    mainWrapper.hidden = true;
                }
"""
text = text.replace('const args = event.data.args || {};', 'const args = event.data.args || {};\n' + js_render)

text = text.replace('StreamlitApi.setComponentValue({ message: text, timestamp: Date.now() });', 'StreamlitApi.setComponentValue({ action: "chat", message: text, timestamp: Date.now() });')

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(text)
