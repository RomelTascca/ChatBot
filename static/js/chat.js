(() => {
  "use strict";

  const app = document.getElementById("chat-app");
  if (!app) return;

  const sendUrl = app.dataset.sendUrl;
  const resetUrl = app.dataset.resetUrl;
  const box = document.getElementById("chat-messages");
  const input = document.getElementById("chat-text");
  const sendBtn = document.getElementById("chat-send");
  const resetBtn = document.getElementById("chat-reset");
  const suggestions = document.getElementById("chat-suggestions");
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  let busy = false;

  // ---------- render seguro: escapa HTML y soporta **negrita** y listas con guion ----------
  const escapeHtml = (s) =>
    s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const inline = (s) => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  function formatBot(text) {
    let html = "", inList = false;
    for (const raw of escapeHtml(text).split("\n")) {
      const line = raw.trim();
      const m = line.match(/^[-*•]\s+(.*)$/);
      if (m) {
        if (!inList) { html += "<ul>"; inList = true; }
        html += `<li>${inline(m[1])}</li>`;
      } else {
        if (inList) { html += "</ul>"; inList = false; }
        if (line) html += `<p>${inline(line)}</p>`;
      }
    }
    return inList ? html + "</ul>" : html;
  }

  function addMessage(role, text, extraClass = "") {
    const el = document.createElement("div");
    el.className = `msg msg-${role === "user" ? "user" : "bot"} ${extraClass}`.trim();
    if (role === "user") el.textContent = text;          // texto del usuario: nunca como HTML
    else el.innerHTML = formatBot(text);
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
    return el;
  }

  function showTyping() {
    const el = document.createElement("div");
    el.className = "msg msg-bot typing";
    el.innerHTML = "<span></span><span></span><span></span>";
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
    return el;
  }

  function setBusy(state) {
    busy = state;
    sendBtn.disabled = state;
    input.disabled = state;
    if (!state) input.focus();
  }

  async function send(text) {
    text = text.trim();
    if (!text || busy) return;
    suggestions.hidden = true;
    addMessage("user", text);
    input.value = "";
    autoresize();
    setBusy(true);
    const typing = showTyping();

    try {
      const res = await fetch(sendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        credentials: "same-origin",
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json().catch(() => ({}));
      typing.remove();
      if (!res.ok) addMessage("bot", data.error || "Ocurrió un error. Inténtalo de nuevo.", "msg-error");
      else addMessage("bot", data.reply, data.source === "fallback" ? "msg-error" : "");
    } catch (err) {
      typing.remove();
      addMessage("bot", "No pude conectarme con el servidor. Revisa tu conexión.", "msg-error");
    } finally {
      setBusy(false);
    }
  }

  function autoresize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
  }

  // ---------- eventos ----------
  sendBtn.addEventListener("click", () => send(input.value));
  input.addEventListener("input", autoresize);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  suggestions.addEventListener("click", (e) => {
    if (e.target.classList.contains("chip")) send(e.target.textContent);
  });
  resetBtn.addEventListener("click", async () => {
    if (busy) return;
    await fetch(resetUrl, { method: "POST", headers: { "X-CSRFToken": csrf }, credentials: "same-origin" });
    box.innerHTML = "";
    suggestions.hidden = false;
    greet();
  });

  // ---------- carga inicial ----------
  function greet() {
    addMessage("bot", "¡Hola! 👋 Soy el asistente virtual. Puedo ayudarte con productos, precios, envíos y cambios. ¿Qué necesitas?");
  }

  const initial = JSON.parse(document.getElementById("initial-messages").textContent || "[]");
  if (initial.length) {
    suggestions.hidden = true;
    initial.forEach((m) => addMessage(m.role, m.content, m.source === "fallback" ? "msg-error" : ""));
  } else {
    greet();
  }
  input.focus();
})();
