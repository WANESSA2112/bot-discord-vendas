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

sdk = mercadopago.SDK(MP_TOKEN)

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

@bot.command()
async def loja(ctx):
    embed = discord.Embed(
        title="🔥 LOJA OFICIAL",
        description="Escolha seu plano:",
        color=discord.Color.green()
    )
    embed.add_field(name="1 DIA", value="R$10", inline=False)
    embed.add_field(name="7 DIAS", value="R$40", inline=False)
    embed.add_field(name="30 DIAS", value="R$80", inline=False)

    await ctx.send(embed=embed, view=LojaView())

async def criar_pagamento(interaction, plano):
    preco = PLANOS[plano]["preco"]

    payment = sdk.payment().create({
        "transaction_amount": preco,
        "description": f"Plano {plano}",
        "payment_method_id": "pix",
        "payer": {"email": f"user{interaction.user.id}@gmail.com"}
    })

    data = payment["response"]
    payment_id = data["id"]

    pagamentos[payment_id] = {
        "user_id": interaction.user.id,
        "plano": plano
    }

    qr = data["point_of_interaction"]["transaction_data"]["qr_code"]

    await interaction.response.send_message(
        f"💰 PIX:\n{qr}\n\nAguardando pagamento...",
        ephemeral=True
    )

@tasks.loop(seconds=10)
async def verificar_pagamentos():
    for payment_id in list(pagamentos.keys()):
        payment = sdk.payment().get(payment_id)
        if payment["response"]["status"] == "approved":
            info = pagamentos[payment_id]
            user = await bot.fetch_user(info["user_id"])

            aguardando_uid[user.id] = info["plano"]

            await user.send("✅ Pagamento aprovado! Envie seu UID.")
            del pagamentos[payment_id]

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if isinstance(message.channel, discord.DMChannel):
        if message.author.id not in aguardando_uid:
            return

        plano = aguardando_uid[message.author.id]
        dias = PLANOS[plano]["dias"]

        r = requests.post(API_URL, json={
            "account_id": message.content,
            "for_days": dias
        }, headers={
            "X-API-KEY": API_KEY,
            "Content-Type": "application/json"
        })

        if r.json().get("success"):
            await message.channel.send("🔥 ATIVADO!")
        else:
            await message.channel.send("❌ ERRO")

        del aguardando_uid[message.author.id]

bot.run(TOKEN)
