// assistant.js - the page behaviour: microphone, sending commands, speaking replies.
const logBox = document.getElementById("log");
const textInput = document.getElementById("textInput");
const micBtn = document.getElementById("micBtn");
const statusLine = document.getElementById("statusLine");
const langSel = document.getElementById("langSel");
const engineSel = document.getElementById("engineSel");
const speakChk = document.getElementById("speakChk");
let serverStatus = { whisper: false, coqui: false };

function addBubble(text, cls, small) {
  const d = document.createElement("div");
  d.className = "bubble " + cls;
  d.textContent = text;
  if (small) { const s = document.createElement("small"); s.textContent = small; d.appendChild(s); }
  logBox.appendChild(d);
  logBox.scrollTop = logBox.scrollHeight;
}

async function speak(text) {
  if (!speakChk.checked) return;
  if (serverStatus.coqui) {                      // Coqui TTS (server)
    try {
      const r = await fetch("/api/tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      if (r.ok) { new Audio(URL.createObjectURL(await r.blob())).play(); return; }
    } catch (e) { /* fall through to the browser voice */ }
  }
  if ("speechSynthesis" in window) {             // browser voice
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-GB";
    window.speechSynthesis.speak(u);
  }
}

async function sendCommand(text) {
  text = (text || "").trim();
  if (!text) return;
  addBubble(text, "user");
  textInput.value = "";
  try {
    const r = await fetch("/api/command", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
    const data = await r.json();
    addBubble(data.reply, data.ok ? "bot" : "err", (data.language_name || "") + (data.intent ? " | " + data.intent : ""));
    speak(data.reply);
  } catch (e) {
    addBubble("Could not reach the server. Is it running?", "err");
  }
}

// ---------- microphone: Whisper (server) ----------
let recorder = null, chunks = [];
async function startWhisper() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  recorder = new MediaRecorder(stream);
  chunks = [];
  recorder.ondataavailable = e => chunks.push(e.data);
  recorder.onstop = async () => {
    stream.getTracks().forEach(t => t.stop());
    micBtn.classList.remove("listening");
    statusLine.textContent = "Whisper is converting your voice to text...";
    const form = new FormData();
    form.append("audio", new Blob(chunks, { type: "audio/webm" }), "voice.webm");
    form.append("language", langSel.value);
    const r = await fetch("/api/transcribe", { method: "POST", body: form });
    const data = await r.json();
    statusLine.textContent = "Ready.";
    if (data.ok) sendCommand(data.text); else addBubble("Voice error: " + (data.error || "unknown"), "err");
  };
  recorder.start();
  micBtn.classList.add("listening");
  statusLine.textContent = "Listening... press the microphone again to stop.";
}

// ---------- microphone: browser (Chrome / Edge) ----------
let recognition = null;
function startBrowser() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { addBubble("This browser cannot listen. Use Chrome or Edge, or type your command.", "err"); return; }
  recognition = new SR();
  recognition.lang = (langSel.value === "en-GB" || langSel.value === "auto" || langSel.value === "kri") ? "en-GB" : "en-GB";
  recognition.onresult = e => sendCommand(e.results[0][0].transcript);
  recognition.onend = () => { micBtn.classList.remove("listening"); statusLine.textContent = "Ready."; };
  recognition.onerror = e => addBubble("Microphone error: " + e.error, "err");
  recognition.start();
  micBtn.classList.add("listening");
  statusLine.textContent = "Listening...";
}

micBtn.addEventListener("click", async () => {
  if (recorder && recorder.state === "recording") { recorder.stop(); return; }
  if (recognition && micBtn.classList.contains("listening")) { recognition.stop(); return; }
  let engine = engineSel.value;
  if (engine === "auto") engine = serverStatus.whisper ? "whisper" : "browser";
  try {
    if (engine === "whisper") await startWhisper(); else startBrowser();
  } catch (e) {
    addBubble("Cannot use the microphone: " + e.message, "err");
  }
});

document.getElementById("sendBtn").addEventListener("click", () => sendCommand(textInput.value));
textInput.addEventListener("keydown", e => { if (e.key === "Enter") sendCommand(textInput.value); });
document.querySelectorAll(".chips li").forEach(li => li.addEventListener("click", () => sendCommand(li.dataset.say)));

fetch("/api/status").then(r => r.json()).then(s => {
  serverStatus = s;
  statusLine.textContent = "Speech-to-text: " + (s.whisper ? "Whisper ready" : "browser microphone (Whisper not installed)") +
    " | Voice reply: " + (s.coqui ? "Coqui TTS ready" : "browser voice (Coqui not installed)");
});
