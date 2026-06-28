import argparse
import os
import re
import tempfile
import sys
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
import opencc

# Fix Windows console output encoding
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Initialize OpenCC for Simplified to Traditional conversion
cc = opencc.OpenCC('s2t')

def get_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def get_video_info(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get('id'), info.get('title', 'video')
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return None, "video"

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)

def fetch_and_format_transcript(transcript_obj):
    try:
        data = transcript_obj.fetch()
        formatter = SRTFormatter()
        srt_formatted = formatter.format_transcript(data)
        return srt_formatted
    except Exception as e:
        print(f"Error formatting transcript: {e}")
        return None

def download_audio_and_transcribe(url):
    print("No usable subtitles found. Downloading audio for Whisper transcription...")
    
    # yt-dlp options to download audio
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.m4a")
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': audio_path,
            'quiet': False
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        print("Audio downloaded. Starting Whisper transcription (this may take a while depending on hardware)...")
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("Error: faster_whisper is not installed.")
            return None
            
        # Using 'small' model since user is running on CPU. It provides a good balance of speed and accuracy.
        # compute_type "int8" is good for CPU.
        try:
            model = WhisperModel("small", device="cpu", compute_type="int8")
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            return None
        
        segments, info = model.transcribe(
            audio_path,
            language="zh",
            initial_prompt="以下是一段繁體中文的影片逐字稿。"
        )
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        srt_content = []
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            # Ensure text is converted to Traditional Chinese
            text = cc.convert(segment.text.strip())
            srt_content.append(f"{i}\n{start} --> {end}\n{text}\n")
            # print progress
            print(f"[{start} -> {end}] {text}")
            
        return "\n".join(srt_content)

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def process_video(url, output_dir="."):
    video_id, title = get_video_info(url)
    if not video_id:
        video_id = get_video_id(url)
        if not video_id:
            print("Could not extract video ID from URL.")
            return
            
    print(f"Processing video: {title} ({video_id})")
    
    srt_content = None
    
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        # Priority mapping
        # 1. Manual Traditional Chinese
        # 2. Manual Simplified Chinese (converted)
        # 3. Generated Traditional Chinese
        # 4. Generated Simplified Chinese (converted)
        # 5. Manual English (translated)
        # 6. Generated English (translated)
        
        target_transcript = None
        translation_needed = False
        convert_to_tw = False
        
        # Let's inspect available transcripts
        manual_langs = list(transcript_list._manually_created_transcripts.keys())
        generated_langs = list(transcript_list._generated_transcripts.keys())
        
        print(f"Available manual transcripts: {manual_langs}")
        print(f"Available generated transcripts: {generated_langs}")
        
        if 'zh-TW' in manual_langs:
            target_transcript = transcript_list.find_manually_created_transcript(['zh-TW'])
        elif 'zh-Hant' in manual_langs:
            target_transcript = transcript_list.find_manually_created_transcript(['zh-Hant'])
        elif 'zh-CN' in manual_langs or 'zh-Hans' in manual_langs or 'zh' in manual_langs:
            langs = [l for l in ['zh-CN', 'zh-Hans', 'zh'] if l in manual_langs]
            target_transcript = transcript_list.find_manually_created_transcript(langs)
            convert_to_tw = True
        elif 'zh-TW' in generated_langs:
            target_transcript = transcript_list.find_generated_transcript(['zh-TW'])
        elif 'zh-Hant' in generated_langs:
            target_transcript = transcript_list.find_generated_transcript(['zh-Hant'])
        elif 'zh-CN' in generated_langs or 'zh-Hans' in generated_langs or 'zh' in generated_langs:
            langs = [l for l in ['zh-CN', 'zh-Hans', 'zh'] if l in generated_langs]
            target_transcript = transcript_list.find_generated_transcript(langs)
            convert_to_tw = True
        elif manual_langs:
            target_transcript = transcript_list.find_manually_created_transcript(manual_langs)
            translation_needed = True
        elif generated_langs:
            target_transcript = transcript_list.find_generated_transcript(generated_langs)
            translation_needed = True
            
        if target_transcript:
            print(f"Using transcript: {target_transcript.language} (Generated: {target_transcript.is_generated})")
            
            if translation_needed and target_transcript.is_translatable:
                print("Translating transcript to zh-TW...")
                target_transcript = target_transcript.translate('zh-TW')
            elif translation_needed and not target_transcript.is_translatable:
                print("Translation not supported for this transcript. Using OpenCC fallback...")
                convert_to_tw = True
                
            srt_content = fetch_and_format_transcript(target_transcript)
            
            if srt_content and convert_to_tw:
                print("Converting text to Traditional Chinese via OpenCC...")
                srt_content = cc.convert(srt_content)
                
    except Exception as e:
        print(f"YouTube Transcript API could not find subtitles: {e}")
        
    if not srt_content:
        srt_content = download_audio_and_transcribe(url)
        
    if srt_content:
        filename = sanitize_filename(f"{title}.srt")
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        print(f"Successfully saved subtitles to: {output_path}")
    else:
        print("Failed to extract or generate subtitles.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and convert YouTube subtitles to Traditional Chinese")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    args = parser.parse_args()
    
    process_video(args.url, args.output)
