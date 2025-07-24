import aiosqlite

DB_NAME = "fichas.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS fichas (
            id_usuario TEXT PRIMARY KEY,
            nome TEXT,
            conceito TEXT,
            tipo TEXT,
            contrato TEXT,
            atributos TEXT,
            habilidades TEXT,
            estados TEXT,
            poderes TEXT,
            ancoras TEXT
        );
        """)
        await db.commit()

# Salva ou atualiza uma ficha completa
async def create_character(
    id_usuario,
    nome,
    conceito,
    tipo,
    contrato,
    atributos,
    habilidades,
    estados,
    poderes,
    ancoras
):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR REPLACE INTO fichas (
            id_usuario, nome, conceito, tipo, contrato,
            atributos, habilidades, estados, poderes, ancoras
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            id_usuario,
            nome,
            conceito,
            tipo,
            contrato,
            atributos,
            habilidades,
            estados,
            poderes,
            ancoras
        ))
        await db.commit()

# Busca uma ficha pelo ID do usuário
async def get_character(id_usuario):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM fichas WHERE id_usuario = ?;", (id_usuario,))
        result = await cursor.fetchone()
        await cursor.close()
        return result

# Atualiza apenas um campo da ficha
async def update_character_field(id_usuario, campo, valor):
    async with aiosqlite.connect(DB_NAME) as db:
        query = f"UPDATE fichas SET {campo} = ? WHERE id_usuario = ?;"
        await db.execute(query, (valor, id_usuario))
        await db.commit()
