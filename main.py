import os
import requests
import discord
from discord.ext import commands
from google import genai
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GDRIVE_CLIENT_ID = os.getenv("GDRIVE_CLIENT_ID")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET")
GDRIVE_REFRESH_TOKEN = os.getenv("GDRIVE_REFRESH_TOKEN")

# Initialize modern Gemini client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot successfully online and logged in as {bot.user}")

@bot.command(name="generate")
async def generate_video(ctx, *, user_prompt: str):
    await ctx.send(f"🎬 **Received topic:** *'{user_prompt}'*\nGenerating script prompts using Gemini AI...")

    system_instruction = (
        f"You are an expert AI video director. Based on this topic: '{user_prompt}', "
        f"generate exactly 5 cinematic, detailed text prompts for video generation. "
        f"Output ONLY the 5 prompts, one per line, with no extra text or numbering."
    )

    try:
        # Call Gemini model using modern client syntax
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_instruction
        )
        scene_prompts = [line.strip() for line in response.text.strip().split("\n") if line.strip()][:5]

        formatted_prompts = "\n".join([f"{i+1}. {p}" for i, p in enumerate(scene_prompts)])
        await ctx.send(f"📝 **Generated Script Prompts:**\n```\n{formatted_prompts}\n```")
        await ctx.send("⚙️ **Triggering video generation pipeline...**")

        video_filename = f"{user_prompt.replace(' ', '_')}.mp4"
        target_file_path = f"/kaggle/working/{video_filename}"

        upload_success = upload_to_gdrive(target_file_path, video_filename)

        if upload_success:
            await ctx.send(f"✅ **Success!** Video *'{video_filename}'* uploaded to Google Drive.")
        else:
            await ctx.send("⚠️ Video finished processing, but Google Drive upload failed.")

    except Exception as e:
        await ctx.send(f"❌ Pipeline execution error: `{str(e)}`")

def upload_to_gdrive(file_path, drive_filename):
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': GDRIVE_CLIENT_ID,
        'client_secret': GDRIVE_CLIENT_SECRET,
        'refresh_token': GDRIVE_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }

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
        return False

    with open(file_path, 'rb') as f:
        upload_resp = requests.put(
            upload_url,
            headers={'Content-Length': str(os.path.getsize(file_path))},
            data=f
        )

    return upload_resp.status_code in [200, 201]

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
    system_instruction = (
        f"You are an expert AI video director. Based on this topic: '{user_prompt}', "
        f"generate exactly 5 cinematic, detailed text prompts for video generation. "
        f"Output ONLY the 5 prompts, one per line, with no extra text or numbering."
    )

    try:
        response = llm_model.generate_content(system_instruction)
        scene_prompts = [line.strip() for line in response.text.strip().split("\n") if line.strip()][:5]

        formatted_prompts = "\n".join([f"{i+1}. {p}" for i, p in enumerate(scene_prompts)])
        await ctx.send(f"📝 **Generated Script Prompts:**\n```\n{formatted_prompts}\n```")
        await ctx.send("⚙️ **Triggering video generation pipeline...**")

        # 2. RUN PIPELINE & UPLOAD TO DRIVE
        video_filename = f"{user_prompt.replace(' ', '_')}.mp4"
        target_file_path = f"/kaggle/working/{video_filename}"

        upload_success = upload_to_gdrive(target_file_path, video_filename)

        if upload_success:
            await ctx.send(f"✅ **Success!** Video *'{video_filename}'* uploaded to Google Drive.")
        else:
            await ctx.send("⚠️ Video finished processing, but Google Drive upload failed.")

    except Exception as e:
        await ctx.send(f"❌ Pipeline execution error: `{str(e)}`")

def upload_to_gdrive(file_path, drive_filename):
    """Exchanges refresh token for access token and uploads file to Google Drive."""
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': GDRIVE_CLIENT_ID,
        'client_secret': GDRIVE_CLIENT_SECRET,
        'refresh_token': GDRIVE_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }

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
        return False

    with open(file_path, 'rb') as f:
        upload_resp = requests.put(
            upload_url,
            headers={'Content-Length': str(os.path.getsize(file_path))},
            data=f
        )

    return upload_resp.status_code in [200, 201]

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
