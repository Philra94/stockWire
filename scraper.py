import os
import datetime
import subprocess
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import openai
# Load environment variables from .env file
load_dotenv()

# Set the OpenAI API key from environment variables

# Configuration
OUTPUT_DIR = "output"
CHANNELS_FILE = "channels.txt"
MODEL = "medium"  # Whisper model name: tiny, base, small, medium, large
NUM_VIDEOS = 3  # Number of recent videos to process per channel (adjust as needed)


def get_channels():
    """Read channels from channels.txt (ignoring lines that start with #)."""
    channels = []
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            channels.append(line)
    return channels


def download_audio(url, output_path):
    """
    Download the audio for a given YouTube URL using yt_dlp.
    Saves the audio track to `output_path`.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'output/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def transcribe_audio(audio_path):
    """
    Transcribe the audio file using OpenAI's Whisper API.
    """
    with open(audio_path, "rb") as audio_file:
        transcription = openai.Audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"  # Change to 'verbose_json' for more detailed output
        )
    return transcription["text"]


# OPTIONAL: Summarize using OpenAI GPT
# def summarize_text(text):
#     prompt = (f"Please summarize the following transcript focusing on market and "
#               f"stock news. Return a concise summary with key takeaways.\n\n{text}")
#     response = openai.Completion.create(
#         engine="text-davinci-003",
#         prompt=prompt,
#         max_tokens=200,
#         temperature=0.7
#     )
#     return response["choices"][0]["text"].strip()

def simple_keyword_summarizer(text, keywords=None):
    """
    A simple approach to 'summarize' by returning lines containing certain keywords.
    You can expand this logic or replace with your own summarization approach.
    """
    if keywords is None:
        keywords = ["market", "stock", "trading", "finance", "earnings", "economy"]
    summarized_lines = []
    for line in text.split("\n"):
        for kw in keywords:
            if kw.lower() in line.lower():
                summarized_lines.append(line)
                break
    summary = "\n".join(summarized_lines)
    return summary


def save_markdown(filename, content):
    """
    Save the given content to a Markdown file in OUTPUT_DIR.
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    date_str = datetime.date.today().isoformat()
    daily_summary_md = f"{date_str}_summary.md"
    daily_summary_lines = []

    channels = get_channels()

    for channel in channels:
        print(f"Processing channel: {channel}")

        # 1. Retrieve the most recent video URLs
        #    We can do this by using yt_dlp in 'dump-json' mode with a --playlist-end parameter
        #    or we can rely on a search approach. Here's a simpler method:

        fetch_cmd = [
            "yt-dlp",
            "--get-id",
            "--dateafter", "now-4day",  # fetch videos from the last day, for example
            "--playlist-end", str(NUM_VIDEOS),
            channel
        ]
        try:
            output = subprocess.check_output(fetch_cmd).decode().split()
            video_ids = [vid_id.strip() for vid_id in output if vid_id.strip()]
        except subprocess.CalledProcessError:
            print(f"Error fetching videos for channel: {channel}")
            continue

        # 2. For each video, download audio, transcribe, and summarize
        for video_id in video_ids:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"  -> Processing video: {video_url}")

            # Construct a safe filename for the audio track
            audio_filename = f"{video_id}.mp3"
            audio_path = os.path.join(OUTPUT_DIR, audio_filename)

            # Download audio
            download_audio(video_url, audio_path)

            # Transcribe audio
            transcript_text = transcribe_audio(audio_path)

            # Summarize text (using either GPT or a local keyword-based approach)
            # summary_text = summarize_text(transcript_text)  # GPT approach
            summary_text = simple_keyword_summarizer(transcript_text)

            # Build MD content for transcript
            transcript_md_content = (
                f"# Transcript: {video_url}\n\n"
                f"**Date:** {date_str}\n\n"
                "## Full Transcript\n"
                f"{transcript_text}\n"
            )

            # Build MD content for summary
            summary_md_content = (
                f"# Summary: {video_url}\n\n"
                f"**Date:** {date_str}\n\n"
                "## Key Statements on Market/Stock:\n\n"
                f"{summary_text}\n"
            )

            # Save transcript & summary as separate files or combine them.
            transcript_md_filename = f"{date_str}_transcript_{video_id}.md"
            summary_md_filename = f"{date_str}_summary_{video_id}.md"

            save_markdown(transcript_md_filename, transcript_md_content)
            save_markdown(summary_md_filename, summary_md_content)

            # Add short summary to daily summary
            daily_summary_lines.append(f"## {video_url}\n\n{summary_text}\n")

    # Finally, save a daily summary file that references all videos processed
    daily_summary_content = (
            f"# Daily Summary for {date_str}\n\n" +
            "\n---\n".join(daily_summary_lines)
    )
    save_markdown(daily_summary_md, daily_summary_content)


if __name__ == "__main__":
    main()