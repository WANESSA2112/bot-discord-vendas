import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import mercadopago
import requests
import os

TOKEN = os.getenv("TOKEN")
MP_TOKEN = os.getenv("MP_TOKEN")
API_KEY = os.getenv("API_KEY")

API_URL = "http://painel.reflexo-games.com/api/add_uid"

sdk = mercadopago.SDK(APP_USR-815231345790722-011418-bf44cf706f205f8e248a5fd078701741-3134496921)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

PLANOS = {
    "1d": {"dias": 1, "preco": 10},
    "7d": {"dias": 7, "preco": 40},
    "30d": {"dias": 30, "preco": 80}
}

pagamentos = {}
aguardando_uid = {}

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    verificar_pagamentos.start()

class LojaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="1 DIA", style=discord.ButtonStyle.green)
    async def um_dia(self, interaction: discord.Interaction, button: Button):
        await criar_pagamento(interaction, "1d")

    @discord.ui.button(label="7 DIAS", style=discord.ButtonStyle.blurple)
    async def sete_dias(self, interaction: discord.Interaction, button: Button):
        await criar_pagamento(interaction, "7d")

    @discord.ui.button(label="30 DIAS", style=discord.ButtonStyle.red)
    async def trinta_dias(self, interaction: discord.Interaction, button: Button):
        await criar_pagamento(interaction, "30d")
