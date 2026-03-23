const chatContainer = document.getElementById("chat-container");
const promptInput = document.getElementById("prompt-input");
const sendBtn = document.getElementById("send-btn");
const imageBtn = document.getElementById("image-btn");
const imageInput = document.getElementById("image-input");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const userInfo = document.getElementById("user-info");
const userAvatar = document.getElementById("user-avatar");
const userName = document.getElementById("user-name");
const inputContainer = document.getElementById("input-container");
const authPrompt = document.getElementById("auth-prompt");
const sessionSelector = document.getElementById("session-selector");
const newSessionBtn = document.getElementById("new-session-btn");
const deleteSessionBtn = document.getElementById("delete-session-btn");
const attachedImagesContainer = document.getElementById(
    "attached-images-container",
);
const authLoginBtn = document.getElementById("auth-login-btn");

let isAuthenticated = false;
let currentSessionId = null;

async function resetUI() {
    userInfo.style.display = "none";
    loginBtn.style.display = "block";
    logoutBtn.style.display = "none";
    sessionSelector.style.display = "none";
    newSessionBtn.style.display = "none";
    chatContainer.classList.add("hidden");
    inputContainer.classList.add("hidden");
    authPrompt.classList.remove("hidden");
}

async function checkAuth() {
    try {
        const response = await fetch("/api/v1/auth/me");
        const data = await response.json();
        if (data.authenticated) {
            isAuthenticated = true;
            userInfo.style.display = "flex";
            loginBtn.style.display = "none";
            logoutBtn.style.display = "block";
            sessionSelector.style.display = "block";
            newSessionBtn.style.display = "block";
            userAvatar.src = data.user.avatar_url || "";
            userName.textContent = data.user.name || data.user.email;
            chatContainer.classList.remove("hidden");
            inputContainer.classList.remove("hidden");
            authPrompt.classList.add("hidden");
            loadSessions();
        } else {
            resetUI();
        }
    } catch (e) {
        isAuthenticated = false;
        resetUI();
    }
}

loginBtn.addEventListener("click", () => {
    window.location.href = "/api/v1/auth/google/login";
});

authLoginBtn.addEventListener("click", () => {
    window.location.href = "/api/v1/auth/google/login";
});

logoutBtn.addEventListener("click", async () => {
    await fetch("/api/v1/auth/logout", { method: "POST" });
    window.location.reload();
});

async function loadSessions() {
    try {
        const response = await fetch("/api/v1/sessions/");
        if (!response.ok) {
            throw new Error("Failed to load sessions");
        }

        const sessions = await response.json();
        sessionSelector.innerHTML = '<option value="">New Session</option>';
        sessions.forEach((session) => {
            const option = document.createElement("option");
            option.value = session.id;
            const date = new Date(session.created_at).toLocaleDateString();
            option.textContent = `Session ${session.id} - ${date}`;
            sessionSelector.appendChild(option);
        });
        if (currentSessionId) {
            sessionSelector.value = currentSessionId;
        }
    } catch (e) {
        console.error("Failed to load sessions:", e);
    }
}

async function createNewSession() {
    try {
        const response = await fetch("/api/v1/sessions/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });
        if (!response.ok) {
            throw new Error("Failed to load sessions");
        }

        const session = await response.json();
        currentSessionId = session.id;
        chatContainer.innerHTML = "";
        deleteSessionBtn.style.display = "block";
        await loadSessions();
        sessionSelector.value = currentSessionId;
    } catch (e) {
        console.error("Failed to create session:", e);
    }
}

sessionSelector.addEventListener("change", (e) => {
    currentSessionId = e.target.value ? parseInt(e.target.value, 10) : null;
    chatContainer.innerHTML = "";
    deleteSessionBtn.style.display = currentSessionId ? "block" : "none";
    if (currentSessionId) {
        loadSessionMessages(currentSessionId);
    }
});

deleteSessionBtn.addEventListener("click", async () => {
    if (!currentSessionId) return;
    if (!confirm("Are you sure you want to delete this session? This cannot be undone.")) return;

    try {
        const response = await fetch(`/api/v1/sessions/${currentSessionId}`, {
            method: "DELETE",
        });
        if (!response.ok) {
            throw new Error("Failed to delete session");
        }
        currentSessionId = null;
        chatContainer.innerHTML = "";
        deleteSessionBtn.style.display = "none";
        sessionSelector.value = "";
        await loadSessions();
    } catch (e) {
        console.error("Failed to delete session:", e);
    }
});

async function loadSessionMessages(sessionId) {
    try {
        const response = await fetch(`/api/v1/sessions/${sessionId}`);
        if (!response.ok) {
            throw new Error("Failed to load session messages");
        }

        const session = await response.json();
        for (const item of session.items) {
            const userImages = item.images
                .filter((img) => img.source === "USER")
                .map((img) => ({ src: img.file_path }));
            addMessage(item.text, "user", null, userImages);

            if (item.images && item.images.length > 0) {
                for (const img of item.images) {
                    if (img.source === "OPENROUTER") {
                        addMessage("Generated image:", "assistant", img.file_path);
                    }
                }
            }
        }
    } catch (e) {
        console.error("Failed to load session messages:", e);
    }
}

newSessionBtn.addEventListener("click", createNewSession);

checkAuth();

let attachedImages = [];

function addMessage(content, type, imageData = null, userImages = null) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}`;

    if (type === "loading") {
        messageDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div><span>Creating...</span>';
    } else if (type === "error") {
        messageDiv.textContent = content;
    } else {
        const imagesToShow = userImages || (type === "user" ? attachedImages : null);
        if (imagesToShow && imagesToShow.length > 0) {
            const imgContainer = document.createElement("div");
            imgContainer.className = "attached-images";
            imagesToShow.forEach((img) => {
                const imgEl = document.createElement("img");
                imgEl.src = img.src || img.preview;
                imgEl.style.width = "60px";
                imgEl.style.height = "60px";
                imgEl.style.objectFit = "cover";
                imgEl.style.borderRadius = "0.25rem";
                imgContainer.appendChild(imgEl);
            });
            messageDiv.appendChild(imgContainer);
        }

        const textSpan = document.createElement("span");
        textSpan.textContent = content;
        messageDiv.appendChild(textSpan);

        if (imageData) {
            const imgContainer = document.createElement("div");
            imgContainer.className = "image-container";
            const img = document.createElement("img");
            img.src = imageData;
            img.alt = "Generated image";
            imgContainer.appendChild(img);
            messageDiv.appendChild(imgContainer);
        }
    }

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function renderAttachedImages() {
    attachedImagesContainer.innerHTML = "";
    attachedImages.forEach((img, idx) => {
        const wrapper = document.createElement("div");
        wrapper.className = "attached-image";
        const imgEl = document.createElement("img");
        imgEl.src = img.preview;
        const removeBtn = document.createElement("button");
        removeBtn.className = "remove-btn";
        removeBtn.textContent = "×";
        removeBtn.onclick = () => {
            attachedImages.splice(idx, 1);
            renderAttachedImages();
        };
        wrapper.appendChild(imgEl);
        wrapper.appendChild(removeBtn);
        attachedImagesContainer.appendChild(wrapper);
    });
}

imageBtn.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", async (e) => {
    const files = Array.from(e.target.files);
    for (const file of files) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            const base64 = ev.target.result.split(",")[1];
            attachedImages.push({ base64, preview: ev.target.result });
            renderAttachedImages();
        };
        reader.readAsDataURL(file);
    }
    imageInput.value = "";
});

async function sendPrompt() {
    if (!isAuthenticated) {
        addMessage("Please login to generate images", "error");
        return;
    }

    const prompt = promptInput.value.trim();
    if (!prompt && attachedImages.length === 0) return;

    promptInput.value = "";
    promptInput.style.height = "auto";
    promptInput.disabled = true;
    sendBtn.disabled = true;
    imageBtn.disabled = true;

    if (!currentSessionId) {
        addMessage("Please select or create a session first", "error");
        promptInput.disabled = false;
        sendBtn.disabled = false;
        imageBtn.disabled = false;
        return;
    }

    const imagesToSend = attachedImages.map((img) => img.base64);

    addMessage(prompt, "user");

    attachedImages = [];
    renderAttachedImages();

    addMessage("", "loading");

    try {
        let url = currentSessionId
            ? `/api/v1/image/${currentSessionId}`
            : "/api/v1/image";
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt,
                images: imagesToSend.length > 0 ? imagesToSend : null,
            }),
        });

        const lastMessage = chatContainer.lastElementChild;
        lastMessage.remove();

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to generate image");
        }

        const data = await response.json();
        if (!Array.isArray(data.images) || data.images.length === 0) {
            console.error("Unexpected API response:", data);
            addMessage("No images returned from API", "error");
            return;
        }
        addMessage(
            "Here is your generated image:",
            "assistant",
            data.images[0],
        );
    } catch (error) {
        const lastMessage = chatContainer.lastElementChild;
        if (lastMessage && lastMessage.classList.contains("loading")) {
            lastMessage.remove();
        }
        addMessage(error.message, "error");
    } finally {
        promptInput.disabled = false;
        sendBtn.disabled = false;
        imageBtn.disabled = false;
        promptInput.focus();
    }
}

sendBtn.addEventListener("click", sendPrompt);

promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendPrompt();
    }
});

promptInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 150) + "px";
});
