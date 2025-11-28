import os
import random
import requests
import json
from time import sleep

import asyncio
import edge_tts
import xml.etree.ElementTree as ET
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Libraries for Video Editing
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, 
    concatenate_videoclips, vfx
)

# --- CONFIGURATION ---
# IMPORTANT: Set your API Keys here or in environment variables
# Note: IMAGEMAGICK_BINARY configuration is handled differently in MoviePy 2.0+
# and is usually auto-detected or set via environment variables.
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not PEXELS_API_KEY or not GEMINI_API_KEY:
    raise ValueError("Missing API Keys in .env file")


class YouTubeShortsBot:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-flash-latest')

        self.assets_dir = "assets"
        self.output_dir = "output"
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Cleanup old assets
        self.cleanup_assets()

    def cleanup_assets(self):
        """Removes all files from the assets directory."""
        print("🧹 Cleaning up old assets...")
        for filename in os.listdir(self.assets_dir):
            file_path = os.path.join(self.assets_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

    def get_trending_topic(self, region='US'):
        """Fetches a trending topic from Google Trends RSS feed."""
        print("🔍 Searching for trends via RSS...")
        try:
            url = f"https://trends.google.com/trending/rss?geo={region}"
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"RSS Fetch failed: {response.status_code}")
            
            root = ET.fromstring(response.content)
            # Namespace for media/ht (not strictly needed if we just find 'title' in items)
            # Items are under channel/item
            items = root.findall('.//item')
            if not items:
                raise Exception("No items found in RSS")
            
            # Pick a random item
            item = random.choice(items[:10])
            topic = item.find('title').text
            print(f"📈 Trend Found (RSS): {topic}")
            return topic
        except Exception as e:
            print(f"⚠️ RSS trends failed: {e}. Using fallback.")
            return "Amazing Space Facts"

    def generate_script(self, topic):
        """Generates a structured JSON script with visual cues using Gemini."""
        print(f"📝 Writing script for: {topic}...")
        
        prompt = (
            f"Create a dynamic YouTube Shorts script about '{topic}'. "
            "Output strictly valid JSON. No markdown formatting. "
            "Structure: a list of objects, where each object represents a scene. "
            "Each object must have: "
            "'text' (the spoken narration, max 20 words per scene), "
            "'visual_query' (a specific, simple keyword for Pexels video search, e.g., 'space nebula', 'happy dog'). "
            "Total duration should be under 50 seconds (approx 130 words total). "
            "Ensure the visual queries match the text context perfectly. "
            "Example: [{'text': 'Did you know space is silent?', 'visual_query': 'space stars'}, ...]"
        )

        try:
            response = self.model.generate_content(prompt)
            raw_text = response.text.strip()
            # Clean up potential markdown code blocks
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            script_data = json.loads(raw_text.strip())
            print(f"DEBUG: script_data type: {type(script_data)}")
            print(f"DEBUG: script_data content: {script_data}")
            print("✅ Script generated (JSON).")
            return script_data
            print(f"DEBUG: script_data type: {type(script_data)}")
            print(f"DEBUG: script_data content: {script_data}")
            print("✅ Script generated (JSON).")
            return script_data
        except Exception as e:
            print(f"❌ AI Error: {e}")
            return None

    async def generate_audio_async(self, text, filename="voiceover.mp3"):
        """Converts script to Audio using edge-tts."""
        print("🎙️ Generating Voiceover with Edge TTS...")
        path = os.path.join(self.assets_dir, filename)
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+25%")
        await communicate.save(path)
        return path

    def generate_audio(self, text, filename="voiceover.mp3"):
        """Wrapper for async audio generation."""
        return asyncio.run(self.generate_audio_async(text, filename))

    def download_stock_assets(self, script_data):
        """Downloads stock footage for each scene in the script."""
        print(f"🎥 Downloading assets for {len(script_data)} scenes...")
        headers = {'Authorization': PEXELS_API_KEY}
        
        updated_script = []
        
        for i, scene in enumerate(script_data):
            query = scene['visual_query']
            print(f"  🎬 Scene {i+1}: Searching Pexels for '{query}'...")
            url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=3"
            
            try:
                r = requests.get(url, headers=headers)
                data = r.json()
                
                if not data['videos']:
                    print(f"  ⚠️ No videos found for '{query}'. Using fallback 'abstract background'.")
                    # Fallback search
                    fallback_url = "https://api.pexels.com/videos/search?query=abstract%20background&orientation=portrait&per_page=3"
                    r = requests.get(fallback_url, headers=headers)
                    data = r.json()
                
                if not data['videos']:
                     raise Exception("No videos found even after fallback.")

                # Pick a random video from top 3 to vary it up
                video_info = random.choice(data['videos'])
                video_files = video_info['video_files']
                
                # Sort by quality (width) to get decent quality but not massive 4k if possible, or just pick first
                # Pexels usually has 'hd' or 'sd'. Let's pick the one closest to 1080 width if possible
                # Simple logic: pick the first one that is at least 720p
                video_url = video_files[0]['link']
                for v in video_files:
                    if v['width'] >= 720 and v['width'] <= 1080:
                        video_url = v['link']
                        break
                
                print(f"  ⬇️ Downloading video for Scene {i+1}...")
                video_data = requests.get(video_url).content
                filename = f"scene_{i}_{random.randint(1000,9999)}.mp4"
                path = os.path.join(self.assets_dir, filename)
                
                with open(path, 'wb') as handler:
                    handler.write(video_data)
                
                scene['video_path'] = path
                updated_script.append(scene)
                
            except Exception as e:
                print(f"❌ Scene {i+1} Download Error: {e}")
                # If download fails, maybe skip scene or use a default placeholder?
                # For now, let's skip to avoid breaking everything
                continue
                
        return updated_script

    def create_video(self, script_data, output_filename="final_short.mp4"):
        """Edits the video: syncs audio, adds subtitles, stitches scenes."""
        print("🎬 Editing Video (Multi-Scene)...")
        
        final_clips = []
        
        try:
            for i, scene in enumerate(script_data):
                print(f"  ✂️ Processing Scene {i+1}...")
                
                # Add delay to avoid Edge TTS 429 Rate Limit
                if i > 0:
                    sleep(2)

                # 1. Generate Audio for this scene
                audio_path = self.generate_audio(scene['text'], filename=f"voice_{i}.mp3")
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                
                # 2. Load Video
                video_path = scene.get('video_path')
                if not video_path or not os.path.exists(video_path):
                    print(f"  ⚠️ Missing video for scene {i+1}, skipping.")
                    continue
                    
                video_clip = VideoFileClip(video_path)
                
                # Loop video if it's shorter than audio
                if video_clip.duration < duration:
                    video_clip = video_clip.with_effects([vfx.Loop(duration=duration)])
                
                # Cut video to exact audio length
                video_clip = video_clip.subclipped(0, duration)
                video_clip = video_clip.with_audio(audio_clip)

                # Resize to Vertical (1080x1920)
                # STRICT RESIZING: Ensure every clip is exactly 1080x1920
                w, h = video_clip.size
                target_ratio = 9/16
                current_ratio = w/h

                if current_ratio > target_ratio:
                    # Too wide, crop width
                    new_width = h * target_ratio
                    video_clip = video_clip.cropped(x1=w/2 - new_width/2, width=new_width, height=h)
                elif current_ratio < target_ratio:
                    # Too tall (unlikely for portrait, but possible), crop height
                    new_height = w / target_ratio
                    video_clip = video_clip.cropped(y1=h/2 - new_height/2, width=w, height=new_height)
                
                # Force resize to 1080x1920 to match standard
                video_clip = video_clip.resized(height=1920)
                if video_clip.w != 1080:
                     video_clip = video_clip.resized(width=1080)


                # 3. Generate Subtitles (Simple word overlay)
                words = scene['text'].split()
                # Chunk size can be smaller for better sync in short scenes
                chunk_size = 1 
                text_clips = []
                
                if words:
                    chunk_duration = duration / len(words)
                    
                    for j, word in enumerate(words):
                        start_time = j * chunk_duration
                        # Ensure we don't go past duration
                        if start_time >= duration: break
                        
                        txt_clip = TextClip(
                            text=word.upper(), 
                            font_size=90, 
                            color='white', 
                            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 
                            stroke_color='black', 
                            stroke_width=4,
                            size=(1080, None), # Use fixed width
                            method='caption'
                        )
                        txt_clip = txt_clip.with_position(('center', 'center')).with_duration(chunk_duration).with_start(start_time)
                        text_clips.append(txt_clip)

                # Compose scene with fixed size
                scene_clip = CompositeVideoClip([video_clip] + text_clips, size=(1080, 1920))
                
                # Add Transition (Fade In)
                # Apply fade in to all scenes for smooth entry
                scene_clip = scene_clip.with_effects([vfx.FadeIn(duration=0.2)])
                
                final_clips.append(scene_clip)

            if not final_clips:
                raise Exception("No clips were generated.")

            print("Creating Final Composite...")
            # Use compose method to fix glitches
            final_video = concatenate_videoclips(final_clips, method="compose")
            
            # Enforce 58s Max Duration (Shorts Limit)
            if final_video.duration > 58:
                print(f"⚠️ Video duration {final_video.duration}s exceeds 58s. Trimming.")
                final_video = final_video.subclipped(0, 58)

            output_path = os.path.join(self.output_dir, output_filename)
            final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24)
            print(f"✅ Video created: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Editing Error: {e}")
            import traceback
            traceback.print_exc()
            return None

# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    bot = YouTubeShortsBot()
    
    # 1. Find Trend
    trend = bot.get_trending_topic()
    
    # 2. Generate Script (JSON)
    if trend:
        script_data = bot.generate_script(trend)
    
    # 3. Get Assets (Multi-scene)
    if script_data:
        script_data = bot.download_stock_assets(script_data)
    
    # 4. Edit (Multi-scene)
    if script_data:
        final_video = bot.create_video(script_data)
