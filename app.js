const logEl = document.getElementById("log");
const formEl = document.getElementById("input-form");
const inputEl = document.getElementById("command-input");
const NOTES_KEY = "jarvis_web_notes";
const siteUrlEl = document.getElementById("site-url");

const commands = {
  help: () => `사용 가능한 명령:\n- help\n- time\n- date\n- calc <expr>\n- note <text>\n- notes\n- search <query>\n- clear\n- exit`,
  time: () => `현재 UTC 시각은 ${new Date().toISOString().slice(11, 19)} 입니다.`,
  date: () => `오늘 날짜(UTC)는 ${new Date().toISOString().slice(0, 10)} 입니다.`,
  calc: (args) => {
    if (!args.length) return "예시: jarvis calc 12 * (8 + 2)";
    const expr = args.join(" ");
    if (!/^[0-9+\-*/().\s%]+$/.test(expr)) {
      return "숫자/연산자만 허용됩니다.";
    }
    try {
      // eslint-disable-next-line no-new-func
      const result = Function(`'use strict'; return (${expr})`)();
      return `계산 결과: ${result}`;
    } catch {
      return "수식을 계산할 수 없습니다.";
    }
  },
  note: (args) => {
    if (!args.length) return "예시: jarvis note 아크 리액터 점검";
    const notes = loadNotes();
    notes.push({ timestamp: new Date().toISOString(), text: args.join(" ") });
    localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
    return "메모를 저장했습니다.";
  },
  notes: () => {
    const notes = loadNotes();
    if (!notes.length) return "저장된 메모가 없습니다.";
    return "저장된 메모 목록:\n" + notes.map((n, i) => `${i + 1}. [${n.timestamp}] ${n.text}`).join("\n");
  },
  search: (args) => {
    if (!args.length) return "예시: jarvis search iron man suit ai";
    const q = encodeURIComponent(args.join(" "));
    const url = `https://duckduckgo.com/?q=${q}`;
    window.open(url, "_blank", "noopener");
    return `검색을 새 탭에서 열었습니다: ${url}`;
  },
  clear: () => {
    logEl.innerHTML = "";
    return "로그를 지웠습니다.";
  },
  exit: () => "웹 버전에서는 창을 닫거나 탭을 종료하면 됩니다.",
};

function loadNotes() {
  try {
    return JSON.parse(localStorage.getItem(NOTES_KEY) || "[]");
  } catch {
    return [];
  }
}

function pushLog(role, text) {
  const row = document.createElement("div");
  row.className = `msg ${role}`;
  row.textContent = `${role === "user" ? "You" : "JARVIS"} > ${text}`;
  logEl.appendChild(row);
  logEl.scrollTop = logEl.scrollHeight;
}

function handleInput(raw) {
  const text = raw.trim();
  if (!text) return;

  pushLog("user", text);

  if (!text.toLowerCase().startsWith("jarvis")) {
    pushLog("bot", "대기 중입니다. 'jarvis <명령>' 형태로 호출하세요.");
    return;
  }

  const parts = text.slice(6).trim().split(/\s+/).filter(Boolean);
  if (!parts.length) {
    pushLog("bot", "명령을 말씀해주세요. 예: jarvis help");
    return;
  }

  const [name, ...args] = parts;
  const handler = commands[name.toLowerCase()];
  if (!handler) {
    pushLog("bot", `'${name}' 명령은 아직 없습니다. jarvis help를 확인하세요.`);
    return;
  }

  const response = handler(args);
  pushLog("bot", response);
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  handleInput(inputEl.value);
  inputEl.value = "";
  inputEl.focus();
});

pushLog("bot", "온라인 상태입니다, 보스. 웹에서 'jarvis ...'로 호출하세요.");


if (siteUrlEl) {
  siteUrlEl.textContent = `현재 실행 URL: ${window.location.href}`;
}
