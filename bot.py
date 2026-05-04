import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import mercadopago
import requests
import os

TOKEN = os.getenv("TOKEN")
MP_TOKEN = os.getenv("MP_TOKEN")
API_KEY = os.getenv("API_KEY")

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
async def painel(ctx):
    embed = discord.Embed(
        title="🛒 Loja",
        description="Escolha um plano:",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=LojaView())

async def criar_pagamento(interaction, plano):
    preco = PLANOS[plano]["preco"]

    pagamento = {
        "transaction_amount": preco,
        "description": f"Plano {plano}",
        "payment_method_id": "pix",
        "payer": {"email": "cliente@email.com"}
    }

    response = sdk.payment().create(pagamento)
    data = response["response"]

    pagamentos[data["id"]] = {
        "user": interaction.user.id,
        "plano": plano,
        "status": "pending"
    }

    qr = data["point_of_interaction"]["transaction_data"]["qr_code"]
    copia_cola = data["point_of_interaction"]["transaction_data"]["qr_code_base64"]

    embed = discord.Embed(
        title="💰 Pagamento PIX",
        description=f"Plano: {plano}\nValor: R${preco}",
        color=discord.Color.yellow()
    )

    embed.add_field(name="PIX copia e cola", value=f"```{qr}```", inline=False)

    await interaction.response.send_message(embed=embed)

@tasks.loop(seconds=20)
async def verificar_pagamentos():
    for payment_id, info in pagamentos.items():
        response = sdk.payment().get(payment_id)
        status = response["response"]["status"]

        if status == "approved" and info["status"] == "pending":
            info["status"] = "approved"

            user = await bot.fetch_user(info["user"])
            await user.send(f"✅ Pagamento aprovado! Plano: {info['plano']}")

bot.run(TOKEN)
