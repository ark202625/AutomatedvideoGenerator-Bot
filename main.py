import os
import json
import requests
import discord
from discord.ext import commands
import google.generativeai as genai
import threading
from flask import Flask

# --- 1. KEEP-ALIVE WEB SERVER FOR RENDER / UPTIMEROBOT ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# --- 2. CONFIGURATION & CREDENTIALS ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GDRIVE_CLIENT_ID = os.getenv("GDRIVE_CLIENT_ID")
GDRIVE_CLIENT_SECRET = os.getenv("GDRIVE_CLIENT_SECRET")
GDRIVE_REFRESH_TOKEN = os.getenv("GDRIVE_REFRESH_TOKEN")
# Initialize Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot initialized and online as {bot.user}")

@bot.command(name="generate")
async def generate_video(ctx, *, user_prompt: str):
    await ctx.send(f"🎬 **Idea received:** *'{user_prompt}'*\nGenerating video script & scene prompts...")

    system_instruction = (
        f"You are an expert AI video director. Based on this topic/idea: '{user_prompt}', "
        f"generate exactly 5 highly detailed, cinematic image-to-video text prompts. "
        f"Output strictly ONLY the 5 prompts, one per line, with no extra text or numbers."
    )

    try:
        response = llm_model.generate_content(system_instruction)
        scene_prompts = [line.strip() for line in response.text.strip().split("\n") if line.strip()][:5]

        script_saved = save_script_to_gdrive(scene_prompts)

        if script_saved:
            formatted_prompts = "\n".join([f"{i+1}. {p}" for i, p in enumerate(scene_prompts)])
            await ctx.send(
                f"📝 **Script generated and saved to Google Drive:**\n```\n{formatted_prompts}\n```\n"
                f"⚙️ **Next Step:** Run your Kaggle notebook to render the video!"
            )
        else:
            await ctx.send("❌ Script was generated, but failed to save to Google Drive.")

    except Exception as e:
        await ctx.send(f"❌ Error generating script: `{str(e)}`")

def get_gdrive_access_token():
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': GDRIVE_CLIENT_ID,
        'client_secret': GDRIVE_CLIENT_SECRET,
        'refresh_token': GDRIVE_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    res = requests.post(token_url, data=token_data).json()
    return res.get('access_token')

def save_script_to_gdrive(scene_prompts, drive_filename="active_script.json"):
    access_token = get_gdrive_access_token()
    if not access_token:
        return False

    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    payload = json.dumps({"prompts": scene_prompts})

    search_url = f"https://www.googleapis.com/drive/v3/files?q=name='{drive_filename}' and trashed=false"
    search_res = requests.get(search_url, headers=headers).json()
    files = search_res.get('files', [])

    if files:
        file_id = files[0]['id']
        upload_url = f"https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=media"
        upload_resp = requests.patch(upload_url, headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, data=payload)
        return upload_resp.status_code in [200, 201]
    else:
        upload_req = requests.post(
            'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
            headers=headers,
            json={'name': drive_filename, 'mimeType': 'application/json'}
        )
        upload_url = upload_req.headers.get('Location')
        upload_resp = requests.put(upload_url, headers={'Content-Length': str(len(payload))}, data=payload)
        return upload_resp.status_code in [200, 201]

# --- 3. START BOT & KEEP ALIVE (MUST BE AT THE VERY BOTTOM) ---
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
