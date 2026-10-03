(() => {
  "use strict";

  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const resetBtn = document.getElementById("reset-btn");
  const errorEl = document.getElementById("error-banner");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

  const GREETING = "¡Hola! 👋 Soy tu asistente virtual. ¿En qué puedo ayudarte?";

  // textContent (nunca innerHTML): evita XSS aunque el texto venga de la BD o del usuario
  function addMessage(role, text, extraClass = "") {
    const div = document.createElement("div");
    div.className = `msg msg--${role} ${extraClass}`.trim();
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function showError(text) {
    errorEl.textContent = text;
    errorEl.hidden = !text;
  }

  async function post(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
    let data = {};
    try { data = await response.json(); } catch (_) { /* respuesta no JSON */ }
    if (!response.ok) throw new Error(data.error || `Error del servidor (${response.status})`);
    return data;
  }

  function renderInitialHistory() {
    const history = JSON.parse(document.getElementById("initial-history").textContent);
    if (history.length === 0) addMessage("bot", GREETING);
    history.forEach((m) => addMessage(m.role, m.content));
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    showError("");
    addMessage("user", text);
    input.value = "";
    input.disabled = sendBtn.disabled = true;
    const typing = addMessage("bot", "Escribiendo…", "msg--typing");

    try {
      const data = await post("/api/chat/", { message: text });
      typing.remove();
      addMessage("bot", data.reply);
    } catch (err) {
      typing.remove();
      showError(err.message || "No se pudo conectar con el servidor.");
    } finally {
      input.disabled = sendBtn.disabled = false;
      input.focus();
    }
  });

  resetBtn.addEventListener("click", async () => {
    try {
      await post("/api/reset/");
      messagesEl.replaceChildren();
      addMessage("bot", GREETING);
      showError("");
    } catch (err) {
      showError(err.message);
    }
  });

  renderInitialHistory();
  input.focus();
})();
