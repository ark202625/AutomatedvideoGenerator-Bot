import os
import requests
import discord
from discord.ext import commands
import google.generativeai as genai

# --- SECRETS & CREDENTIALS ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # Retrieved from environment variables
GEMINI_API_KEY = "AQ.Ab8RN6LyDBYYR7HEvRhTd3T0TsPRlfsA7RH2xXGqhev9gNNABA"

# Google Drive OAuth 2.0 Credentials
GDRIVE_CLIENT_ID = "677902998242-jm727d13ttrhbs4ditqqv0js3l3jbmup.apps.googleusercontent.com"
GDRIVE_CLIENT_SECRET = "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"
GDRIVE_REFRESH_TOKEN = "1//04cUKZsF4DvPmCgYIARAAGAQSNwF-L9IrAlJltdbza1GHZrbrvxbRWU0VcLl4A-QNsZf6ekFeEwZXUvzN3p_OrOH8DaCXXkZk5SM"

# Initialize Gemini AI Model
genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Discord Bot with Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot initialized and logged in as {bot.user}")

@bot.command(name="generate")
async def generate_video(ctx, *, user_prompt: str):
    await ctx.send(f"🎬 **Topic received:** *'{user_prompt}'*\nWriting script prompts with Gemini AI...")

    # 1. AI SCRIPT & PROMPT GENERATION
    system_instruction = (
        f"You are an expert AI video director. Based on this topic: '{user_prompt}', "
        f"generate exactly 5 highly detailed, cinematic image-to-video text prompts. "
        f"Output strictly ONLY the 5 prompts, one per line, without any numbering, introductions, or conversational text."
    )

    try:
        response = llm_model.generate_content(system_instruction)
        scene_prompts = [p.strip() for p in response.text.strip().split("\n") if p.strip()][:5]

        formatted_prompts = "\n".join([f"{i+1}. {p}" for i, p in enumerate(scene_prompts)])
        await ctx.send(f"📝 **Generated Video Prompts:**\n```\n{formatted_prompts}\n```")
        await ctx.send("⚙️ **Triggering video generation pipeline...**")

        # 2. RUN PIPELINE & UPLOAD TO DRIVE
        video_filename = f"{user_prompt.replace(' ', '_')}.mp4"
        target_file_path = f"/kaggle/working/{video_filename}"

        upload_success = upload_to_gdrive(target_file_path, video_filename)

        if upload_success:
            await ctx.send(f"✅ **Success!** Video *'{video_filename}'* generated and uploaded to Google Drive.")
        else:
            await ctx.send("⚠️ Video processing finished, but Google Drive upload failed.")

    except Exception as e:
        await ctx.send(f"❌ Error executing pipeline: `{str(e)}`")

def upload_to_gdrive(file_path, drive_filename):
    """Refreshes access token and uploads file to Google Drive via API v3."""
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
        print("OAuth Refresh Failed:", res)
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
