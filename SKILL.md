# YouTube Subtitle Extractor Skill

This skill extracts subtitles from YouTube videos. It prioritizes Traditional Chinese subtitles. If none exist, it will use `yt-dlp` to download the audio and `faster-whisper` (running locally on CPU/GPU) to generate a high-quality Traditional Chinese transcript.

## Environment & Dependencies Installation

Before running the extractor script for the first time on a new system, you **MUST** ensure the required dependencies are installed. 

1. **System Requirement**: Ensure `ffmpeg` is installed and available in the system's PATH.
2. **Python Dependencies**: Run the following command to install required packages:
   ```bash
   pip install -r C:\Users\biop1\.opencode\skill\youtube-subtitles\requirements.txt
   ```
   *(If you are running on a different system, adjust the path to the `requirements.txt` accordingly).*

## Usage

When the user asks you to extract subtitles for a YouTube URL, use your terminal/bash tool to run the provided Python script:

```bash
# Optional but recommended for Windows: Set encoding to avoid console errors
set PYTHONUTF8=1
python C:\Users\biop1\.opencode\skill\youtube-subtitles\yt_sub_extractor.py "<YOUTUBE_URL>" --output "<OUTPUT_DIR>"
```

### Script Arguments:
- `url`: The full YouTube URL.
- `--output` or `-o`: The directory where the `.srt` file will be saved. Defaults to the current working directory.

## Workflow & Background Execution
1. Run the script with the target URL.
2. Monitor the script output. 
   - If the script finds an existing transcript, it will download it instantly.
   - If the script outputs "No usable subtitles found. Downloading audio for Whisper transcription...", this means it is falling back to AI audio transcription.
3. **Handling Long Transcriptions**: Whisper transcription on CPU can take a very long time (e.g., hours for long videos).
   - **For Opencode Agents**: IMMEDIATELY cancel the current blocking execution and use the `Task` tool (`subagent_type: "general"`) to run the command in the background with a massive timeout (e.g., 10800000ms).
   - **For Other Agents**: If you do not have a dedicated Subagent/Task tool, execute the command as a background process (e.g., using `&`, `nohup`, or `Start-Process` depending on the OS) to avoid blocking the user's chat interface.
   - Inform the user that the task is running in the background and notify them once the `.srt` file is successfully created.
4. Provide the user with the path or content summary of the generated file.

## Developer Note
- The script automatically handles translations and conversions (Simplified to Traditional) via `opencc`.
- CPU inference uses the `small` Whisper model, optimized for average consumer hardware.