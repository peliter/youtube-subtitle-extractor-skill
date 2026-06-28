# YouTube Subtitle Extractor (AI Agent Skill)

A robust Python tool and AI Agent skill designed to automatically extract Traditional Chinese (`zh-TW`) subtitles from YouTube videos. If no native subtitles exist, it automatically falls back to downloading the audio and transcribing it locally using Whisper AI.

## 🌟 Features
* **Priority-based Extraction**: Automatically hunts for Traditional Chinese subtitles first.
* **Smart Conversion**: If only Simplified Chinese (`zh-CN`) is available, it translates them to Traditional Chinese using `opencc`.
* **Whisper AI Fallback**: If the video has NO subtitles at all, the script uses `yt-dlp` to download the audio track and `faster-whisper` to transcribe the audio into a highly accurate Traditional Chinese `.srt` file.
* **AI Agent Ready**: Designed to be plugged directly into AI coding assistants (like Opencode, Cursor, Claude Code) as a "Skill".

## 🚀 Setup & Installation

### 1. Prerequisites
You must have **`ffmpeg`** installed on your system and added to your system's `PATH`.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 💻 CLI Usage

You can use the python script directly from your terminal:

```bash
python yt_sub_extractor.py "https://www.youtube.com/watch?v=YOUR_VIDEO_ID" --output "./downloads"
```

## 🤖 Using as an AI Agent Skill

This repository includes a `SKILL.md` file. You can import this entire folder into your AI Agent's workspace or skill directory.

The `SKILL.md` file contains precise instructions for LLM agents to:
1. Identify when a user wants to extract YouTube subtitles.
2. Automatically run the Python script.
3. Handle long-running Whisper transcription tasks intelligently (e.g., dispatching to background tasks or subagents so the main chat is not blocked).

## 📄 License
MIT
