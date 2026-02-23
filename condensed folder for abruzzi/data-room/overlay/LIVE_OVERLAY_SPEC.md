# Created: 2026-01-19
# Live CEO Overlay Specification (Audio-In, Guidance-Out)

## Objective
Provide a live, always-on-top overlay that listens to call audio and surfaces **exact, Steve Jobs-style responses** in real time. The overlay is meant to reduce cognitive load during live meetings and ensure consistent, authoritative answers.

## Core Requirements
- **Live transcription** of call audio (system audio loopback).
- **On-top transparent overlay** that displays response suggestions.
- **Low-latency** (target: <2s end-to-end).
- **Offline-first** option (no external services required).
- **Configurable talk tracks** for consistent messaging.

## MVP Approach (Offline, Low Cost)
1. **Audio capture:** Windows WASAPI loopback using `sounddevice`.
2. **Speech-to-text:** Offline STT via **Vosk** (lightweight, no GPU required).
3. **Routing:** Keyword + intent classification using a rules engine.
4. **Overlay UI:** Transparent always-on-top window with hotkey controls.

### MVP Libraries (Python)
- `sounddevice`
- `vosk`
- `pyside6` or `tkinter` (overlay UI)

## Phase 2 (Smarter Responses)
- Add **LLM response layer** for dynamic prompts.
- Use OpenAI API with strict token caps and approved prompts.
- Still include offline fallback (keyword → talk track).

## Overlay UX
- Top-right overlay (small, minimal).
- 2–4 line response suggestion.
- Hotkeys:
  - `Ctrl+Shift+S` = Start/Stop listening
  - `Ctrl+Shift+H` = Hide/Show overlay
  - `Ctrl+Shift+N` = Next suggestion

## Response Engine
- **Input:** Transcribed sentence or phrase.
- **Routing:** Match to talk-track category (Risk, APY, Competitors, Architecture, etc.).
- **Output:** Short, authoritative response in Steve Jobs cadence.

## Deliverables (Next Build)
- `overlay_app.py` (live overlay MVP)
- `overlay_config.json` (categories + trigger phrases)
- `talk_track_library.md` (responses)
- `README.md` with setup instructions

## Notes
- This MVP is fully local and under $0 in cost.
- LLM integration is optional and can stay below $30/month by limiting tokens.
