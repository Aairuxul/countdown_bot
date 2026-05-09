import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone
import asyncio
from dotenv import load_dotenv
import os

from keep_alive import keep_alive

# ──────────────────────────────────────────────
#  CONFIG — keep_alive
# ──────────────────────────────────────────────
keep_alive()
# ──────────────────────────────────────────────
#  CONFIG — token
# ──────────────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ──────────────────────────────────────────────
#  Stockage des comptes à rebours actifs
#  { message_id: { "target": datetime, "channel_id": int, "title": str } }
# ──────────────────────────────────────────────
countdowns: dict[int, dict] = {}

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────
def format_delta(delta_seconds: float) -> str:
    """Formate un nombre de secondes en jj h mm ss."""
    if delta_seconds <= 0:
        return "**C'est l'heure !**"

    total = int(delta_seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    parts = []
    if days:
        parts.append(f"**{days}** jour{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"**{hours}** h")
    if minutes:
        parts.append(f"**{minutes}** min")
    parts.append(f"**{seconds}** s")

    return "  ".join(parts)


def build_embed(title: str, target: datetime, now: datetime) -> discord.Embed:
    delta = (target - now).total_seconds()

    if delta > 0:
        color = discord.Color.blurple()
        description = f"⏳  {format_delta(delta)}"
        footer = f"Échéance : {target.strftime('%d/%m/%Y à %H:%M:%S')} UTC"
    else:
        color = discord.Color.green()
        description = "🎉 Le compte à rebours est **terminé** !"
        footer = f"Arrivée à échéance le {target.strftime('%d/%m/%Y à %H:%M:%S')} UTC"

    embed = discord.Embed(title=f"⏱️  {title}", description=description, color=color)
    embed.set_footer(text=footer)
    embed.timestamp = now
    return embed


# ──────────────────────────────────────────────
#  Background task : update every seconds
# ──────────────────────────────────────────────
@tasks.loop(seconds=1)
async def update_countdowns():
    now = datetime.now(timezone.utc)
    to_remove = []

    for msg_id, data in list(countdowns.items()):
        channel = bot.get_channel(data["channel_id"])
        if channel is None:
            continue
        try:
            message = await channel.fetch_message(msg_id)
        except discord.NotFound:
            to_remove.append(msg_id)
            continue

        embed = build_embed(data["title"], data["target"], now)
        await message.edit(embed=embed)

        # stop update when finished
        if (data["target"] - now).total_seconds() <= 0:
            to_remove.append(msg_id)

    for msg_id in to_remove:
        countdowns.pop(msg_id, None)


@update_countdowns.before_loop
async def before_update():
    await bot.wait_until_ready()


# ──────────────────────────────────────────────
#  Commande slash  /countdown
# ──────────────────────────────────────────────
@bot.tree.command(
    name="countdown",
    description="Lance un compte à rebours en direct vers une date cible."
)
@app_commands.describe(
    titre="Titre du compte à rebours (ex: Sortie de GTA VI)",
    date="Date cible au format JJ-MM-AAAA (ex: 09-05-2026)",
    heure="Heure cible au format HH:MM:SS en UTC (ex: 23:59:00, défaut 00:00:00)",
)
async def countdown_cmd(
    interaction: discord.Interaction,
    titre: str,
    date: str,
    heure: str = "00:00:00",
):
    # Parse de la date/heure
    try:
        target = datetime.strptime(f"{date} {heure}", "%d-%m-%Y %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        await interaction.response.send_message(
            "❌ Format invalide. Utilise `JJ-MM-AAAA` pour la date et `HH:MM:SS` pour l'heure.",
            ephemeral=True,
        )
        return

    now = datetime.now(timezone.utc)
    if target <= now:
        await interaction.response.send_message(
            "❌ La date cible est déjà passée !", ephemeral=True
        )
        return

    # Envoi du message initial
    embed = build_embed(titre, target, now)
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()

    # Enregistrement pour la mise à jour automatique
    countdowns[message.id] = {
        "channel_id": interaction.channel_id,
        "target": target,
        "title": titre,
    }


# ──────────────────────────────────────────────
#  Commande slash  /stop_countdown
# ──────────────────────────────────────────────
@bot.tree.command(
    name="stop_countdown",
    description="Arrête le compte à rebours du message spécifié."
)
@app_commands.describe(message_id="L'ID du message contenant le compte à rebours")
async def stop_countdown_cmd(interaction: discord.Interaction, message_id: str):
    try:
        mid = int(message_id)
    except ValueError:
        await interaction.response.send_message("❌ ID de message invalide.", ephemeral=True)
        return

    if mid in countdowns:
        countdowns.pop(mid)
        await interaction.response.send_message("✅ Compte à rebours arrêté.", ephemeral=True)
    else:
        await interaction.response.send_message(
            "❌ Aucun compte à rebours actif avec cet ID.", ephemeral=True
        )


# ──────────────────────────────────────────────
#  Événements du bot
# ──────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"   {len(synced)} commande(s) slash synchronisée(s).")
    except Exception as e:
        print(f"   Erreur lors de la synchronisation des commandes : {e}")
    update_countdowns.start()


# ──────────────────────────────────────────────
#  Lancement
# ──────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
