#!/usr/bin/env python3
"""A lightweight terminal JARVIS-style assistant.

Features
- wake word style interaction (`jarvis ...`)
- built-in utilities: time, date, calc, note, open web search links
- plugin-like command routing structure for easy extension
"""

from __future__ import annotations

import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

APP_DIR = Path.home() / ".jarvis"
NOTES_FILE = APP_DIR / "notes.json"


@dataclass
class Command:
    name: str
    help_text: str
    handler: Callable[[list[str]], str]


class Jarvis:
    def __init__(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self.commands: dict[str, Command] = {}
        self._register_defaults()

    def _register(self, name: str, help_text: str, handler: Callable[[list[str]], str]) -> None:
        self.commands[name] = Command(name, help_text, handler)

    def _register_defaults(self) -> None:
        self._register("help", "사용 가능한 명령 보기", self._cmd_help)
        self._register("time", "현재 UTC 시간 확인", self._cmd_time)
        self._register("date", "오늘 날짜 확인", self._cmd_date)
        self._register("calc", "수식 계산: calc 12 * (8 + 2)", self._cmd_calc)
        self._register("note", "메모 저장: note buy arc reactor", self._cmd_note)
        self._register("notes", "저장한 메모 보기", self._cmd_notes)
        self._register("search", "웹 검색 열기: search latest suit upgrades", self._cmd_search)
        self._register("shell", "쉘 명령 실행(주의): shell echo hi", self._cmd_shell)
        self._register("exit", "자비스 종료", self._cmd_exit)

    def run(self) -> None:
        self._speak("온라인 상태입니다, 보스. 호출하려면 'jarvis ...' 형태로 입력하세요.")
        while True:
            try:
                raw = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self._speak("오프라인으로 전환합니다.")
                return

            if not raw:
                continue

            if raw.lower() in {"exit", "quit"}:
                self._speak("오프라인으로 전환합니다.")
                return

            if raw.lower().startswith("jarvis"):
                message = raw[6:].strip()
                if not message:
                    self._speak("명령을 말씀해주세요. 예: jarvis help")
                    continue
                self._dispatch(message)
            else:
                self._speak("대기 중입니다. 'jarvis <명령>' 형태로 불러주세요.")

    def _dispatch(self, message: str) -> None:
        parts = shlex.split(message)
        if not parts:
            self._speak("명령을 이해하지 못했습니다.")
            return

        name, args = parts[0].lower(), parts[1:]
        command = self.commands.get(name)
        if not command:
            self._speak(f"'{name}' 명령은 아직 없습니다. 'jarvis help'를 확인하세요.")
            return

        try:
            result = command.handler(args)
        except Exception as exc:  # pragma: no cover - interactive guard
            result = f"실행 중 오류 발생: {exc}"

        self._speak(result)

    def _speak(self, text: str) -> None:
        print(f"JARVIS > {text}")

    def _cmd_help(self, _: list[str]) -> str:
        items = [f"- {c.name}: {c.help_text}" for c in self.commands.values()]
        return "사용 가능한 명령:\n" + "\n".join(items)

    def _cmd_time(self, _: list[str]) -> str:
        now = dt.datetime.now(dt.timezone.utc)
        return f"현재 UTC 시각은 {now.strftime('%H:%M:%S')} 입니다."

    def _cmd_date(self, _: list[str]) -> str:
        today = dt.datetime.now(dt.timezone.utc).date()
        return f"오늘 날짜는 {today.isoformat()} 입니다."

    def _cmd_calc(self, args: list[str]) -> str:
        if not args:
            return "예시: jarvis calc 7 * (9 + 3)"
        expr = " ".join(args)
        allowed = {"__builtins__": {}}
        value = eval(expr, allowed, {})
        return f"계산 결과: {value}"

    def _load_notes(self) -> list[dict[str, str]]:
        if not NOTES_FILE.exists():
            return []
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))

    def _save_notes(self, notes: list[dict[str, str]]) -> None:
        NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cmd_note(self, args: list[str]) -> str:
        if not args:
            return "예시: jarvis note Mark 43 배터리 점검"
        note = " ".join(args)
        notes = self._load_notes()
        notes.append({"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "text": note})
        self._save_notes(notes)
        return "메모를 저장했습니다."

    def _cmd_notes(self, _: list[str]) -> str:
        notes = self._load_notes()
        if not notes:
            return "저장된 메모가 없습니다."
        lines = [f"{idx+1}. [{n['timestamp']}] {n['text']}" for idx, n in enumerate(notes)]
        return "저장된 메모 목록:\n" + "\n".join(lines)

    def _cmd_search(self, args: list[str]) -> str:
        if not args:
            return "예시: jarvis search new AI assistant ideas"
        query = "+".join(args)
        url = f"https://duckduckgo.com/?q={query}"
        webbrowser.open(url)
        return f"브라우저에서 검색을 열었습니다: {url}"

    def _cmd_shell(self, args: list[str]) -> str:
        if not args:
            return "예시: jarvis shell echo Hello"
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            return f"명령 실패({result.returncode}):\n{result.stderr.strip()}"
        return result.stdout.strip() or "명령 실행 완료"

    def _cmd_exit(self, _: list[str]) -> str:
        self._speak("오프라인으로 전환합니다.")
        raise SystemExit(0)


if __name__ == "__main__":
    Jarvis().run()
