import os
import discord
from discord.ext import commands
from supabase import create_client

supabase = create_client(os.getenv("https://ytxydcxlsicanvwqxtah.supabase.co/rest/v1/"), os.getenv("sb_publishable_k90_Amof3K9_ddvst_LveQ_eeEIdIzp"))

bot = commands.Bot(command_prefix="/", intents=discord.Intents.default())

@bot.event
async def on_ready():
    await bot.tree.sync() # Enable / commands
    print(f"✅ {bot.user} online with slash commands")

# COMMAND /teams
@bot.tree.command(name="teams", description="Show all VANTA teams")
async def teams(interaction: discord.Interaction):
    res = supabase.table("teams").select("*").execute()
    if not res.data:
        await interaction.response.send_message("No teams yet.")
        return
    msg = "📋 **VANTA Teams:**\n"
    for t in res.data:
        msg += f"- {t['name']} ({t['budget']}€)\n"
    await interaction.response.send_message(msg)

# COMMAND /createteam
@bot.tree.command(name="createteam", description="Create a new team")
async def create_team(interaction: discord.Interaction, name: str):
    supabase.table("teams").insert({"name": name, "budget": 1000}).execute()
    await interaction.response.send_message(f"✅ Team **{name}** created!")

bot.run(os.getenv("BOT_TOKEN"))
