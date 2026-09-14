import os
import asyncio
import requests
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Secrets
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GDRIVE_CLIENT_ID = os.getenv("GDRIVE_CLIENT_ID")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET")
GDRIVE_REFRESH_TOKEN = os.getenv("GDRIVE_REFRESH_TOKEN")

# Initialize Gemini Client
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def upload_to_gdrive(file_path, drive_filename):
    """Exchanges refresh token for access token and uploads file to Google Drive."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return False

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': GDRIVE_CLIENT_ID,
        'client_secret': GDRIVE_CLIENT_SECRET,
        'refresh_token': GDRIVE_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }

    try:
        res = requests.post(token_url, data=token_data).json()
        access_token = res.get('access_token')

        if not access_token:
            print("OAuth Refresh Error:", res)
            return False

        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        upload_req = requests.post(
            'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
            headers=headers,
            json={'name': drive_filename}
        )
        upload_url = upload_req.headers.get('Location')

        if not upload_url:
            print("Error: Could not get upload URL from Google Drive API")
            return False

        with open(file_path, 'rb') as f:
            upload_resp = requests.put(
                upload_url,
                headers={'Content-Length': str(os.path.getsize(file_path))},
                data=f
            )

        return upload_resp.status_code in [200, 201]
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return False


def generate_video_mock(prompts, output_path):
    """Mock video generation function. Replace with actual video generation API."""
    # TODO: Implement actual video generation using your preferred API
    # (Runway ML, Synthesia, Hugging Face, etc.)
    # For now, create a placeholder file for testing
    with open(output_path, 'wb') as f:
        f.write(b'Mock video file for testing')
    return True


@bot.event
async def on_ready():
    print(f"✅ Bot successfully online and logged in as {bot.user}")


@bot.command(name="generate")
async def generate_video(ctx, *, user_prompt: str):
    """Generate video prompts using Gemini and upload to Google Drive."""
    await ctx.send(f"🎬 **Received topic:** *'{user_prompt}'*\nGenerating script prompts using Gemini AI...")

    system_instruction = (
        f"You are an expert AI video director. Based on this topic: '{user_prompt}', "
        f"generate exactly 5 cinematic, detailed text prompts for video generation. "
        f"Output ONLY the 5 prompts, one per line, with no extra text or numbering."
    )

    try:
        # Call Gemini model
        response = gemini_model.generate_content(system_instruction)
        scene_prompts = [line.strip() for line in response.text.strip().split("\n") if line.strip()][:5]
        
        if not scene_prompts:
            await ctx.send("❌ Failed to generate prompts. Please try again.")
            return
        
        formatted_prompts = "\n".join([f"{i+1}. {p}" for i, p in enumerate(scene_prompts)])
        
        # Send formatted prompts to Discord channel
        await ctx.send(f"📝 **Generated Script Prompts:**\n```\n{formatted_prompts}\n```")
        await ctx.send("🎥 **Generating video from prompts...**")

        # Generate video filename
        video_filename = f"{user_prompt.replace(' ', '_').replace('/', '_')}.mp4"
        target_file_path = f"/tmp/{video_filename}"

        # Generate video (blocking operation in separate thread)
        video_generated = await asyncio.to_thread(generate_video_mock, scene_prompts, target_file_path)
        
        if not video_generated:
            await ctx.send("⚠️ Video generation failed.")
            return

        await ctx.send("⚙️ **Uploading to Google Drive...**")

        # Upload to Google Drive (blocking operation in separate thread)
        upload_success = await asyncio.to_thread(upload_to_gdrive, target_file_path, video_filename)

        if upload_success:
            await ctx.send(f"✅ **Success!** Video *'{video_filename}'* uploaded to Google Drive.")
            # Clean up local file after successful upload
            try:
                os.remove(target_file_path)
            except Exception as e:
                print(f"Warning: Could not delete local file: {str(e)}")
        else:
            await ctx.send("⚠️ Video generated, but Google Drive upload failed.")

    except Exception as e:
        await ctx.send(f"❌ Pipeline execution error: `{str(e)}`")
        print(f"Error details: {str(e)}")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
