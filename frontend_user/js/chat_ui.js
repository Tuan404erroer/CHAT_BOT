/* ========================================================= */
/*  RENDER CHAT UI                                           */
/* ========================================================= */
function renderMessages(animateLast = true) {
    messagesArea.innerHTML = "";

    if (messages.length === 0) {
        renderEmptyState();
        return;
    }

    messages.forEach((msg, idx) => {
        const shouldAnimate = animateLast && idx === messages.length - 1;
        appendMessageDOM(msg, shouldAnimate, idx);
    });

    scrollToBottom();
}

function appendMessageDOM(msg, animate, msgIndex) {
    const row = document.createElement("div");
    row.className = "message " + msg.role;
    if (animate) row.style.animationDelay = "0.05s";

    // Avatar
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = msg.role === "user" ? "👤" : "🤖";

    // Bubble
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    // Content
    const content = document.createElement("div");
    content.className = "message-content";
    if (msg.role === "assistant") {
        content.innerHTML = renderMarkdown(msg.content);
    } else {
        content.textContent = msg.content;
    }
    bubble.appendChild(content);

    // Sources (assistant only)
    if (msg.role === "assistant" && msg.sources && msg.sources.length > 0) {
        bubble.appendChild(createSourcesSection(msg.sources));
    }

    // Rating Buttons (assistant only)
    if (msg.role === "assistant" && typeof msgIndex !== "undefined") {
        const ratingContainer = document.createElement("div");
        ratingContainer.className = "rating-container";

        const btnUp = document.createElement("button");
        btnUp.className = "rating-btn up" + (msg.rating === "up" ? " active" : "");
        btnUp.textContent = "👍";
        btnUp.title = "Câu trả lời tốt";
        btnUp.onclick = () => {
            StreamlitApi.setComponentValue({ action: "rate", rating: "up", message_index: msgIndex, timestamp: Date.now() });
        };

        const btnDown = document.createElement("button");
        btnDown.className = "rating-btn down" + (msg.rating === "down" ? " active" : "");
        btnDown.textContent = "👎";
        btnDown.title = "Câu trả lời chưa tốt";
        btnDown.onclick = () => {
            StreamlitApi.setComponentValue({ action: "rate", rating: "down", message_index: msgIndex, timestamp: Date.now() });
        };

        ratingContainer.appendChild(btnUp);
        ratingContainer.appendChild(btnDown);
        bubble.appendChild(ratingContainer);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesArea.appendChild(row);
}

/* ========================================================= */
/*  MARKDOWN RENDERING                                       */
/* ========================================================= */
function renderMarkdown(text) {
    if (typeof marked !== "undefined") {
        marked.setOptions({ breaks: true, gfm: true });
        return marked.parse(text || "");
    }
    // Fallback: basic escaping + line breaks
    return escapeHtml(text).replace(/\n/g, "<br>");
}

/* ========================================================= */
/*  SOURCES SECTION                                          */
/* ========================================================= */
function createSourcesSection(sources) {
    const section = document.createElement("div");
    section.className = "sources-section";

    const toggle = document.createElement("div");
    toggle.className = "sources-toggle";
    toggle.innerHTML = '📚 Nguồn tài liệu tham khảo <span class="chevron">▼</span>';

    const contentWrap = document.createElement("div");
    contentWrap.className = "sources-content";

    const list = document.createElement("ul");
    list.className = "sources-list";

    sources.forEach((src) => {
        const li = document.createElement("li");
        li.style.whiteSpace = "pre-wrap";
        li.style.fontFamily = "monospace";
        li.textContent = typeof src === "string" ? src : (src.content || JSON.stringify(src, null, 2));
        list.appendChild(li);
    });

    contentWrap.appendChild(list);

    toggle.addEventListener("click", () => {
        toggle.classList.toggle("open");
        contentWrap.classList.toggle("open");
    });

    section.appendChild(toggle);
    section.appendChild(contentWrap);
    return section;
}

/* ========================================================= */
/*  EMPTY STATE                                              */
/* ========================================================= */
function renderEmptyState() {
    messagesArea.innerHTML = `
<div class="empty-state">
    <div class="empty-icon">🎓</div>
    <h2>Chào mừng đến với AI Tư Vấn Tuyển Sinh</h2>
    <p>Hãy đặt câu hỏi về tuyển sinh, ngành đào tạo, điểm chuẩn, học phí và nhiều hơn nữa.</p>
    <div class="suggestion-chips">
        <button class="chip" onclick="askSuggestion('Điểm chuẩn các ngành năm nay là bao nhiêu?')">📊 Điểm chuẩn các ngành</button>
        <button class="chip" onclick="askSuggestion('Trường sử dụng phương thức xét tuyển nào?')">📋 Phương thức xét tuyển</button>
        <button class="chip" onclick="askSuggestion('Học phí các ngành bao nhiêu?')">💰 Học phí các ngành</button>
        <button class="chip" onclick="askSuggestion('Chuẩn đầu ra ngoại ngữ là gì?')">🌍 Chuẩn đầu ra ngoại ngữ</button>
    </div>
    <div class="empty-powered">Được hỗ trợ bởi Google Gemini &amp; Hybrid RAG Search</div>
</div>`;
}

function askSuggestion(text) {
    userInput.value = text;
    sendMessage();
}

/* ========================================================= */
/*  SEND MESSAGE                                             */
/* ========================================================= */
function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isProcessing) return;

    isProcessing = true;
    userInput.value = "";
    resizeInput();
    disableInput();

    // Show user message locally
    messages.push({ role: "user", content: text });
    renderMessages(true);

    // Show typing indicator
    showTyping();
    scrollToBottom();

    // Send to Streamlit backend
    StreamlitApi.setComponentValue({ action: "chat", message: text, timestamp: Date.now() });
}

/* ========================================================= */
/*  TYPING INDICATOR                                         */
/* ========================================================= */
function showTyping() { typingIndicator.classList.add("visible"); }
function hideTyping() { typingIndicator.classList.remove("visible"); }

/* ========================================================= */
/*  INPUT CONTROLS                                           */
/* ========================================================= */
function disableInput() { sendBtn.disabled = true; }
function enableInput() { sendBtn.disabled = false; }

function resizeInput() {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 150) + "px";
}

if (userInput) {
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    userInput.addEventListener("input", resizeInput);
}

if (sendBtn) sendBtn.addEventListener("click", sendMessage);

/* ========================================================= */
/*  SCROLL                                                   */
/* ========================================================= */
function scrollToBottom() {
    requestAnimationFrame(() => {
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    });
}
