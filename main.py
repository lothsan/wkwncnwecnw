# main.py
import os
import discord
from discord.ext import commands
from discord import app_commands
from db import init_db, create_character, get_character, update_character_field
import random
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

init_db()

# Sessões de criação de personagem por usuário
sessions = {}

class CharacterCreation:
    def __init__(self):
        self.step = 0
        self.data = {}

    def next_step(self):
        self.step += 1

@tree.command(name="criar_personagem", description="Crie sua ficha de personagem para Contrato de Sangue.")
async def criar_personagem(interaction: discord.Interaction):
    await interaction.response.send_message("Detectando nova anomalia... Iniciando criação da ficha.", ephemeral=True)
    sessions[interaction.user.id] = CharacterCreation()
    await ask_name(interaction)

async def ask_name(interaction):
    await interaction.followup.send("Passo 1: Qual o nome do personagem? (Responda aqui nesta conversa)", ephemeral=True)

def check_author(author):
    def inner_check(message):
        return message.author.id == author.id
    return inner_check

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    if user_id not in sessions:
        return

    session = sessions[user_id]

    if session.step == 0:
        session.data['nome'] = message.content
        session.next_step()
        await message.channel.send("Qual o conceito do personagem?")
    elif session.step == 1:
        session.data['conceito'] = message.content
        session.next_step()
        await message.channel.send("Agora, vamos distribuir os atributos. Primeiro, os **Mentais**: Você tem 7 pontos para distribuir entre Inteligência, Raciocínio e Determinação. Ex: 3 2 2")
    elif session.step == 2:
        pontos = list(map(int, message.content.split()))
        if len(pontos) != 3 or sum(pontos) != 7:
            await message.channel.send("Distribuição inválida. Use 7 pontos no formato: 3 2 2")
            return
        session.data['mentais'] = pontos
        session.next_step()
        await message.channel.send("Agora os **Físicos** (5 pontos): Força, Destreza, Vigor")
    elif session.step == 3:
        pontos = list(map(int, message.content.split()))
        if len(pontos) != 3 or sum(pontos) != 5:
            await message.channel.send("Distribuição inválida. Use 5 pontos no formato: 2 2 1")
            return
        session.data['fisicos'] = pontos
        session.next_step()
        await message.channel.send("Agora os **Sociais** (3 pontos): Carisma, Manipulação, Autocontrole")
    elif session.step == 4:
        pontos = list(map(int, message.content.split()))
        if len(pontos) != 3 or sum(pontos) != 3:
            await message.channel.send("Distribuição inválida. Use 3 pontos no formato: 1 1 1")
            return
        session.data['sociais'] = pontos
        session.next_step()
        await message.channel.send("Agora, liste 13 pontos em Habilidades. Ex: Investigação 3, Furtividade 2, Ocultismo 2...")
    elif session.step == 5:
        habilidades = message.content.split(",")
        total = 0
        parsed = {}
        try:
            for h in habilidades:
                nome, valor = h.strip().rsplit(" ", 1)
                parsed[nome] = int(valor)
                total += int(valor)
        except:
            await message.channel.send("Formato inválido. Ex: Investigação 3, Furtividade 2")
            return
        if total != 13:
            await message.channel.send("Você deve usar exatamente 13 pontos.")
            return
        session.data['habilidades'] = parsed
        session.next_step()
        await message.channel.send("Você é um Upiór ou um Wilkołaki?")
    elif session.step == 6:
        tipo = message.content.lower()
        if tipo not in ["upiór", "wilkołaki"]:
            await message.channel.send("Digite apenas 'Upiór' ou 'Wilkołaki'.")
            return
        session.data['tipo'] = tipo.capitalize()
        if tipo == "upiór":
            session.data['humanidade'] = 7
            session.data['sangue'] = 5
            session.next_step()
            await message.channel.send("Liste de 1 a 3 Pedras de Toque (uma por linha).")
        else:
            session.data['sabedoria'] = 6
            session.data['furia'] = 2
            session.next_step()
            await message.channel.send("Descreva seu Erro do Passado:")
    elif session.step == 7:
        tipo = session.data['tipo']
        if tipo == "Upiór":
            session.data['pedras_toque'] = message.content.split("\n")
        else:
            session.data['erro_passado'] = message.content
        session.next_step()
        await message.channel.send("Escolha 3 Disciplinas (ou Dons), cada uma com 1 ponto. Ex: Ofuscação, Auspícios, Potência")
    elif session.step == 8:
        poderes = [p.strip() for p in message.content.split(",")]
        if len(poderes) != 3:
            await message.channel.send("Você precisa indicar exatamente 3 nomes.")
            return
        session.data['poderes'] = poderes
        session.next_step()
        await message.channel.send("Por fim, descreva seu Contrato de Sangue:")
    elif session.step == 9:
        session.data['contrato'] = message.content
        data = session.data
        create_character(
            user_id=message.author.id,
            nome=data['nome'],
            conceito=data['conceito'],
            tipo=data['tipo'],
            contrato=data['contrato'],
            atributos={
                "mentais": data['mentais'],
                "fisicos": data['fisicos'],
                "sociais": data['sociais']
            },
            habilidades=data['habilidades'],
            poderes=data['poderes'],
            pedras_erro=data.get('pedras_toque') or data.get('erro_passado'),
            humanidade=data.get('humanidade'),
            sangue=data.get('sangue'),
            sabedoria=data.get('sabedoria'),
            furia=data.get('furia')
        )
        del sessions[user_id]
        await message.channel.send("🩸 Ficha concluída e registrada pelo Cronista do Pacto.")

@tree.command(name="ver_ficha", description="Veja sua ficha de personagem atual.")
async def ver_ficha(interaction: discord.Interaction):
    ficha = get_character(interaction.user.id)
    if ficha:
        await interaction.response.send_message(f"**FICHA DE PERSONAGEM: CONTRATO DE SANGUE**\n**NOME:** {ficha['nome']} | **TIPO:** {ficha['tipo']}\n**CONCEITO:** {ficha['conceito']}\n**CONTRATO DE SANGUE:** {ficha['contrato']}", ephemeral=True)
    else:
        await interaction.response.send_message("Você ainda não criou uma ficha. Use /criar_personagem.", ephemeral=True)

@tree.command(name="rolar", description="Role dados de 10 faces. Ex: /rolar 7d10")
@app_commands.describe(expressao="Ex: 7d10")
async def rolar(interaction: discord.Interaction, expressao: str):
    try:
        qtd, tipo = expressao.lower().split("d")
        qtd, tipo = int(qtd), int(tipo)
        if tipo != 10 or qtd <= 0:
            raise ValueError
        resultados = [random.randint(1, 10) for _ in range(qtd)]
        await interaction.response.send_message(f"🎲 Rolando {qtd}d10: {', '.join(map(str, resultados))}", ephemeral=True)
    except:
        await interaction.response.send_message("Expressão inválida. Use o formato correto: 7d10", ephemeral=True)

@tree.command(name="ajuda", description="Obtenha ajuda sobre os comandos do bot.")
async def ajuda(interaction: discord.Interaction):
    help_text = """
📜 **Ajuda do Cronista do Pacto**

- `/criar_personagem`: Inicia a criação de sua ficha.
- `/ver_ficha`: Exibe sua ficha atual.
- `/editar_ficha`: (em breve) Edite valores da sua ficha.
- `/rolar`: Role dados (ex: 7d10).
- `/ajuda`: Exibe este painel.
    """
    await interaction.response.send_message(help_text, ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot online como {bot.user}")

bot.run(TOKEN)

# db.py
import sqlite3
import json

DB_FILE = "fichas.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS fichas (
        user_id INTEGER PRIMARY KEY,
        nome TEXT,
        conceito TEXT,
        tipo TEXT,
        contrato TEXT,
        atributos TEXT,
        habilidades TEXT,
        poderes TEXT,
        pedras_erro TEXT,
        humanidade INTEGER,
        sangue INTEGER,
        sabedoria INTEGER,
        furia INTEGER
    )''')
    conn.commit()
    conn.close()

def create_character(user_id, nome, conceito, tipo, contrato, atributos, habilidades, poderes, pedras_erro, humanidade=None, sangue=None, sabedoria=None, furia=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO fichas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        user_id, nome, conceito, tipo, contrato,
        json.dumps(atributos), json.dumps(habilidades), json.dumps(poderes),
        json.dumps(pedras_erro), humanidade, sangue, sabedoria, furia
    ))
    conn.commit()
    conn.close()

def get_character(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM fichas WHERE user_id=?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'user_id': row[0],
            'nome': row[1],
            'conceito': row[2],
            'tipo': row[3],
            'contrato': row[4],
            'atributos': json.loads(row[5]),
            'habilidades': json.loads(row[6]),
            'poderes': json.loads(row[7]),
            'pedras_erro': json.loads(row[8]),
            'humanidade': row[9],
            'sangue': row[10],
            'sabedoria': row[11],
            'furia': row[12]
        }
    return None
