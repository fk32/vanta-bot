import discord
from discord import app_commands
import json
import os

CONFIG_FILE = "leagues.json"
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Vanta online as {bot.user} - Slash commands in English")

@tree.command(name="setup", description="Setup your league")
@app_commands.describe(
    league_name="League name e.g: VFLG",
    coach_role="Role for coaches/managers",
    signs_channel="Channel for signs announcements",
    transfers_channel="Channel for transfers announcements",
    loans_channel="Channel for loans announcements"
)
async def setup(interaction: discord.Interaction, league_name: str, coach_role: discord.Role, signs_channel: discord.TextChannel, transfers_channel: discord.TextChannel, loans_channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Only admins can setup!", ephemeral=True)
        return
    config = load_config()
    config[str(interaction.guild.id)] = {
        "league_name": league_name,
        "coach_role_id": coach_role.id,
        "channels": {
            "signs": signs_channel.id,
            "transfers": transfers_channel.id,
            "loans": loans_channel.id
        },
        "team_role_ids": []
    }
    save_config(config)
    embed = discord.Embed(title=f"✅ {league_name} configured!", color=0xD4AF37)
    embed.add_field(name="Coach Role", value=coach_role.mention, inline=False)
    embed.add_field(name="Channels", value=f"Signs: {signs_channel.mention}\nTransfers: {transfers_channel.mention}\nLoans: {loans_channel.mention}", inline=False)
    embed.set_footer(text="Now use /set-teams to add your teams")
    await interaction.response.send_message(embed=embed)

@tree.command(name="set-teams", description="Set team roles after setup")
async def set_teams(interaction: discord.Interaction):
    config = load_config()
    gid = str(interaction.guild.id)
    if gid not in config:
        await interaction.response.send_message("❌ Do /setup first", ephemeral=True)
        return
    view = discord.ui.View()
    select = discord.ui.RoleSelect(placeholder="Select all team roles", min_values=1, max_values=25)
    async def callback(inter: discord.Interaction):
        config[gid]["team_role_ids"] = [r.id for r in select.values]
        save_config(config)
        await inter.response.send_message(f"✅ Saved {len(select.values)} teams!", ephemeral=True)
    select.callback = callback
    view.add_item(select)
    await interaction.response.send_message("Select team roles:", view=view, ephemeral=True)

def get_player_team(member: discord.Member, team_ids):
    for role in member.roles:
        if role.id in team_ids:
            return role
    return None

@tree.command(name="sign", description="Sign a free agent")
@app_commands.describe(player="Player to sign", team="Team signing the player")
async def sign(interaction: discord.Interaction, player: discord.Member, team: discord.Role):
    config = load_config().get(str(interaction.guild.id))
    if not config: return await interaction.response.send_message("❌ Do /setup first", ephemeral=True)
    if config["coach_role_id"] not in [r.id for r in interaction.user.roles] and not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Only coaches can use this", ephemeral=True)
    if team.id not in config["team_role_ids"]:
        return await interaction.response.send_message("❌ Invalid team role", ephemeral=True)
    if get_player_team(player, config["team_role_ids"]):
        return await interaction.response.send_message(f"❌ {player.mention} already has a contract! Use /transfer or /loan", ephemeral=True)
    await player.add_roles(team)
    channel = interaction.guild.get_channel(config["channels"]["signs"])
    embed = discord.Embed(title="📝 SIGN", description=f"{player.mention} signed for {team.mention}", color=0x00FF00)
    embed.add_field(name="Signed by", value=interaction.user.mention)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ {player.mention} signed for {team.mention}!", ephemeral=True)

@tree.command(name="transfer", description="Buy a player from another team")
@app_commands.describe(player="Player to transfer", new_team="New team")
async def transfer(interaction: discord.Interaction, player: discord.Member, new_team: discord.Role):
    config = load_config().get(str(interaction.guild.id))
    if not config: return await interaction.response.send_message("❌ Do /setup first", ephemeral=True)
    old_team = get_player_team(player, config["team_role_ids"])
    if not old_team:
        return await interaction.response.send_message(f"❌ {player.mention} is a free agent! Use /sign", ephemeral=True)
    await player.remove_roles(old_team)
    await player.add_roles(new_team)
    channel = interaction.guild.get_channel(config["channels"]["transfers"])
    embed = discord.Embed(title="🔄 TRANSFER", description=f"{player.mention} from {old_team.mention} to {new_team.mention}", color=0xFFFF00)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Transfer completed!", ephemeral=True)

@tree.command(name="loan", description="Loan a player")
@app_commands.describe(player="Player to loan", new_team="Team receiving on loan")
async def loan(interaction: discord.Interaction, player: discord.Member, new_team: discord.Role):
    config = load_config().get(str(interaction.guild.id))
    if not config: return await interaction.response.send_message("❌ Do /setup first", ephemeral=True)
    old_team = get_player_team(player, config["team_role_ids"])
    if not old_team:
        return await interaction.response.send_message(f"❌ {player.mention} is a free agent! Use /sign", ephemeral=True)
    await player.add_roles(new_team)
    channel = interaction.guild.get_channel(config["channels"]["loans"])
    embed = discord.Embed(title="🤝 LOAN", description=f"{player.mention} on loan from {old_team.mention} to {new_team.mention}", color=0x0099FF)
    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Loan completed!", ephemeral=True)

bot.run(os.environ.get("TOKEN"))