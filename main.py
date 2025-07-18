import os
import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive
import random
import asyncio

token = os.environ['TOKEN_BOT_DISCORD']

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

duels = {}
EMOJIS = {"rouge": "🔴", "noir": "⚫", "pair": "🔵", "impair": "🟣"}


# --- Check personnalisé pour rôle sleeping ---
def is_sleeping():

    async def predicate(interaction: discord.Interaction) -> bool:
        role = discord.utils.get(interaction.guild.roles, name="sleeping")
        return role in interaction.user.roles

    return app_commands.check(predicate)


# Gestion des erreurs globales des commandes
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ Tu n'as pas la permission d'utiliser cette commande.",
            ephemeral=True)


class RejoindreView(discord.ui.View):
    def __init__(self, message_id, joueur1, type_pari, valeur_choisie, montant):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.joueur1 = joueur1
        self.type_pari = type_pari
        self.valeur_choisie = valeur_choisie
        self.montant = montant

    @discord.ui.button(label="🎯 Rejoindre le duel", style=discord.ButtonStyle.green)
    async def rejoindre(self, interaction: discord.Interaction, button: discord.ui.Button):
        joueur2 = interaction.user

        if joueur2.id == self.joueur1.id:
            await interaction.response.send_message("❌ Tu ne peux pas rejoindre ton propre duel.", ephemeral=True)
            return

        duel_data = duels.get(self.message_id)
        if duel_data is None:
            await interaction.response.send_message("❌ Ce duel n'existe plus ou a déjà été joué.", ephemeral=True)
            return

        for data in duels.values():
            if data["joueur1"].id == joueur2.id or ("joueur2" in data and data["joueur2"] and data["joueur2"].id == joueur2.id):
                await interaction.response.send_message(
                    "❌ Tu participes déjà à un autre duel. Termine-le avant d’en rejoindre un autre.",
                    ephemeral=True)
                return

        duel_data["joueur2"] = joueur2
        self.rejoindre.disabled = True
        await interaction.response.defer()
        original_message = await interaction.channel.fetch_message(self.message_id)

        # 💬 Affichage duel prêt avec joueurs
        valeur_joueur2 = {
            "rouge": "noir",
            "noir": "rouge",
            "pair": "impair",
            "impair": "pair"
        }[self.valeur_choisie]

        duel_embed = discord.Embed(
            title="🎰 Duel Prêt !",
            description="La roulette va bientôt tourner... Préparez-vous !",
            color=discord.Color.blue()
        )
        duel_embed.add_field(
            name="👤 Joueur 1",
            value=f"{self.joueur1.mention}\nChoix : {EMOJIS[self.valeur_choisie]} `{self.valeur_choisie.upper()}`",
            inline=True)
        duel_embed.add_field(
            name="👤 Joueur 2",
            value=f"{joueur2.mention}\nChoix : {EMOJIS[valeur_joueur2]} `{valeur_joueur2.upper()}`",
            inline=True)
        duel_embed.set_footer(text="🎲 Début du tirage dans 5 secondes...")

        await original_message.edit(embed=duel_embed, view=None)
        await asyncio.sleep(5)

        # 🎰 Animation roulette
        suspense_embed = discord.Embed(
            title="🎰 La roulette tourne...",
            description="On croise les doigts 🤞🏻 !",
            color=discord.Color.greyple())
        suspense_embed.set_image(url="https://i.makeagif.com/media/11-22-2017/gXYMAo.gif")
        await original_message.edit(embed=suspense_embed)

        for i in range(10, 0, -1):
            suspense_embed.title = f"🎰 Tirage en cours ...!"
            await original_message.edit(embed=suspense_embed)
            await asyncio.sleep(1)

        numero = random.randint(0, 36)
        ROUGES = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        NOIRS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

        couleur = "vert" if numero == 0 else "rouge" if numero in ROUGES else "noir"
        parite = "aucune" if numero == 0 else "pair" if numero % 2 == 0 else "impair"

        condition_gagnante = (couleur == self.valeur_choisie) if self.type_pari == "couleur" else (parite == self.valeur_choisie)
        gagnant = self.joueur1 if condition_gagnante else joueur2

        result_embed = discord.Embed(
            title="🎲 Résultat du Duel Roulette",
            description=(
                f"🎯 **Numéro tiré** : `{numero}`\n"
                f"{'🔴 Rouge' if couleur == 'rouge' else '⚫ Noir' if couleur == 'noir' else '🟩 Vert'} — "
                f"{'🔵 Pair' if parite == 'pair' else '🟣 Impair' if parite == 'impair' else '❔ Aucune'}"
            ),
            color=discord.Color.green() if gagnant == joueur2 else discord.Color.red())

        result_embed.add_field(
            name="👤 Joueur 1",
            value=f"{self.joueur1.mention}\nChoix : {EMOJIS[self.valeur_choisie]} `{self.valeur_choisie.upper()}`",
            inline=True)
        result_embed.add_field(
            name="👤 Joueur 2",
            value=f"{joueur2.mention}\nChoix : {EMOJIS[valeur_joueur2]} `{valeur_joueur2.upper()}`",
            inline=False)
        result_embed.add_field(name=" ", value="─" * 20, inline=False)
         result_embed.add_field(name="💰 Montant misé", value=f"**{self.montant:,} kamas** par joueur ",
            inline=False)
        result_embed.add_field(
            name="🏆 Gagnant",
            value=f"**{gagnant.mention}** remporte **{2 * self.montant:,} kamas** 💰",
            inline=False)
        result_embed.set_footer(text="🎰 Duel terminé • Bonne chance pour le prochain !")

        await original_message.edit(embed=result_embed, view=None)
        duels.pop(self.message_id, None)


class PariView(discord.ui.View):

    def __init__(self, interaction, montant):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.montant = montant

    async def lock_in_choice(self, interaction, type_pari, valeur):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message(
                "❌ Seul le joueur qui a lancé le duel peut choisir le pari.",
                ephemeral=True)
            return

        joueur1 = self.interaction.user
        opposés = {
            "rouge": "noir",
            "noir": "rouge",
            "pair": "impair",
            "impair": "pair"
        }
        choix_restant = opposés[valeur]

        embed = discord.Embed(
            title="🎰 Duel Roulette",
            description=
            f"{joueur1.mention} a choisi : {EMOJIS[valeur]} **{valeur.upper()}** ({type_pari})\nMontant : **{self.montant:,} kamas** 💰",
            color=discord.Color.orange())
        embed.add_field(name="👤 Joueur 1",
                        value=f"{joueur1.mention} - {EMOJIS[valeur]} {valeur}",
                        inline=True)
        embed.add_field(name="👤 Joueur 2",
                        value="🕓 En attente...",
                        inline=True)
        embed.set_footer(
            text=
            f"📋 Pari pris : {joueur1.display_name} - {EMOJIS[valeur]} {valeur.upper()} | Choix restant : {EMOJIS[choix_restant]} {choix_restant.upper()}"
        )

        await interaction.response.edit_message(embed=embed, view=None)

        rejoindre_view = RejoindreView(message_id=None,
                                       joueur1=joueur1,
                                       type_pari=type_pari,
                                       valeur_choisie=valeur,
                                       montant=self.montant)
        message = await interaction.channel.send(embed=embed,
                                                 view=rejoindre_view)
        rejoindre_view.message_id = message.id

        duels[message.id] = {
            "joueur1": joueur1,
            "montant": self.montant,
            "type": type_pari,
            "valeur": valeur
        }

    @discord.ui.button(label="🔴 Rouge", style=discord.ButtonStyle.danger)
    async def rouge(self, interaction: discord.Interaction,
                    button: discord.ui.Button):
        await self.lock_in_choice(interaction, "couleur", "rouge")

    @discord.ui.button(label="⚫ Noir", style=discord.ButtonStyle.secondary)
    async def noir(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        await self.lock_in_choice(interaction, "couleur", "noir")

    @discord.ui.button(label="🔵 Pair", style=discord.ButtonStyle.primary)
    async def pair(self, interaction: discord.Interaction,
                   button: discord.ui.Button):
        await self.lock_in_choice(interaction, "pair", "pair")

    @discord.ui.button(label="🟣 Impair", style=discord.ButtonStyle.blurple)
    async def impair(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        await self.lock_in_choice(interaction, "pair", "impair")


# Commande /sleeping accessible uniquement aux membres avec rôle 'sleeping'
@bot.tree.command(name="sleeping", description="Lancer un duel roulette avec un montant.")
@is_sleeping()
@app_commands.describe(montant="Montant misé en kamas")
async def sleeping(interaction: discord.Interaction, montant: int):
    if interaction.channel.name != "roulettesleeping":
        await interaction.response.send_message(
            "❌ Tu dois utiliser cette commande dans le salon `#roulettesleeping`.", ephemeral=True)
        return

    if montant <= 0:
        await interaction.response.send_message("❌ Le montant doit être supérieur à 0.", ephemeral=True)
        return

    for duel_data in duels.values():
        if duel_data["joueur1"].id == interaction.user.id or (
            "joueur2" in duel_data and duel_data["joueur2"] and duel_data["joueur2"].id == interaction.user.id):
            await interaction.response.send_message(
                "❌ Tu participes déjà à un autre duel. Termine-le ou utilise `/quit` pour l'annuler.",
                ephemeral=True)
            return

    embed = discord.Embed(
        title="🎰 Nouveau Duel Roulette",
        description=f"{interaction.user.mention} veut lancer un duel pour **{montant:,} kamas** 💰",
        color=discord.Color.gold())
    embed.add_field(
        name="Choix du pari",
        value="Clique sur un bouton ci-dessous : 🔴 Rouge / ⚫ Noir / 🔵 Pair / 🟣 Impair",
        inline=False)

    view = PariView(interaction, montant)

    # 💬 Mention du rôle sleeping
    sleeping_role = discord.utils.get(interaction.guild.roles, name="sleeping")
    content = f"{sleeping_role.mention} — 🎯 Un nouveau duel est prêt !"

    await interaction.response.send_message(
        content=content,
        embed=embed,
        view=view,
        allowed_mentions=discord.AllowedMentions(roles=True)
    )


# Commande /quit accessible uniquement aux membres avec rôle 'sleeping'
@bot.tree.command(name="quit",
                  description="Annule le duel en cours que tu as lancé.")
@is_sleeping()
async def quit_duel(interaction: discord.Interaction):
    if interaction.channel.name != "roulettesleeping":
        await interaction.response.send_message(
            "❌ Tu dois utiliser cette commande dans le salon `#roulettesleeping`.",
            ephemeral=True)
        return

    duel_a_annuler = None
    for message_id, duel_data in duels.items():
        if duel_data["joueur1"].id == interaction.user.id:
            duel_a_annuler = message_id
            break

    if duel_a_annuler is None:
        await interaction.response.send_message(
            "❌ Tu n'as aucun duel en attente à annuler.", ephemeral=True)
        return

    duels.pop(duel_a_annuler)

    try:
        channel = interaction.channel
        message = await channel.fetch_message(duel_a_annuler)
        embed = message.embeds[0]
        embed.color = discord.Color.red()
        embed.title += " (Annulé)"
        embed.description = "⚠️ Ce duel a été annulé par son créateur."
        await message.edit(embed=embed, view=None)
    except Exception:
        pass

    await interaction.response.send_message("✅ Ton duel a bien été annulé.",
                                            ephemeral=True)


@bot.event
async def on_ready():
    print(f"{bot.user} est prêt !")
    try:
        await bot.tree.sync()
        print("✅ Commandes synchronisées.")
    except Exception as e:
        print(f"Erreur : {e}")


keep_alive()
bot.run(token)
