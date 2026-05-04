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

# ================== BOT ONLINE ==================
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    verificar_pagamentos.start()

# ================== BOTÕES ==================
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

# ================== COMANDO PARA ENVIAR PAINEL ==================
@bot.command()
async def painel(ctx):
    await ctx.send("💰 **Painel de Compras**", view=LojaView())

# ================== CRIAR PAGAMENTO ==================
async def criar_pagamento(interaction, plano):
    user_id = interaction.user.id
    preco = PLANOS[plano]["preco"]

    pagamento = {
        "transaction_amount": float(preco),
        "description": f"Plano {plano}",
        "payment_method_id": "pix",
        "payer": {
            "email": f"user{user_id}@gmail.com"
        }
    }

    response = sdk.payment().create(pagamento)
    data = response["response"]

    pagamentos[user_id] = {
        "id": data["id"],
        "plano": plano
    }

    pix = data["point_of_interaction"]["transaction_data"]

    await interaction.response.send_message(
        f"💰 **Pagamento criado!**\n\n"
        f"💸 Valor: R$ {preco}\n\n"
        f"📲 Copia e cola:\n```{pix['qr_code']}```\n\n"
        f"⏳ Aguardando pagamento...",
        ephemeral=True
    )

# ================== VERIFICAR PAGAMENTO ==================
@tasks.loop(seconds=10)
async def verificar_pagamentos():
    for user_id, info in list(pagamentos.items()):
        pagamento_id = info["id"]

        result = sdk.payment().get(pagamento_id)
        status = result["response"]["status"]

        if status == "approved":
            user = await bot.fetch_user(user_id)

            await user.send("✅ Pagamento aprovado!\nAgora envie seu UID:")

            aguardando_uid[user_id] = info["plano"]
            del pagamentos[user_id]

# ================== RECEBER UID ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id

    if user_id in aguardando_uid:
        plano = aguardando_uid[user_id]
        uid = message.content

        dias = PLANOS[plano]["dias"]

        try:
            response = requests.post(API_URL, json={
                "uid": uid,
                "dias": dias,
                "api_key": API_KEY
            })

            if response.status_code == 200:
                await message.reply("✅ Plano ativado com sucesso!")
            else:
                await message.reply("❌ Erro ao ativar plano.")

        except Exception as e:
            await message.reply("❌ Erro na API.")

        del aguardando_uid[user_id]

    await bot.process_commands(message)

# ================== START ==================
bot.run(TOKEN)
