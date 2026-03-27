import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# =========================
# RESET
# =========================
cursor.execute("DROP TABLE IF EXISTS faturas")
cursor.execute("DROP TABLE IF EXISTS gastos")
cursor.execute("DROP TABLE IF EXISTS subcategorias")
cursor.execute("DROP TABLE IF EXISTS categorias")
cursor.execute("DROP TABLE IF EXISTS cartoes")
cursor.execute("DROP TABLE IF EXISTS ganhos")
cursor.execute("DROP TABLE IF EXISTS investimentos")
cursor.execute("DROP TABLE IF EXISTS desafios")

# =========================
# TABELAS
# =========================

# CATEGORIAS
cursor.execute("""
CREATE TABLE categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
)
""")

# SUBCATEGORIAS
cursor.execute("""
CREATE TABLE subcategorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria_id INTEGER,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
)
""")

# CARTÕES
cursor.execute("""
CREATE TABLE cartoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    dia_vencimento INTEGER NOT NULL,
    dia_fechamento INTEGER NOT NULL,
    limite REAL DEFAULT 0
)
""")

# GASTOS
cursor.execute("""
CREATE TABLE gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT,
    
    valor_previsto REAL DEFAULT 0,
    valor_pago REAL DEFAULT 0,

    data TEXT,

    categoria_id INTEGER,
    subcategoria_id INTEGER,

    parcela_atual INTEGER,
    parcelas_total INTEGER,

    cartao_id INTEGER,

    tipo TEXT DEFAULT 'variavel',
    pago INTEGER DEFAULT 0,
    forma_pagamento TEXT,

    recorrente INTEGER DEFAULT 0,

    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (subcategoria_id) REFERENCES subcategorias(id),
    FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
)
""")

# GANHOS
cursor.execute("""
CREATE TABLE ganhos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT,
    valor REAL DEFAULT 0,
    data TEXT,
    tipo TEXT
)
""")

# INVESTIMENTOS (🔥 COMPLETO)
cursor.execute("""
CREATE TABLE investimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    tipo TEXT,
    instituicao TEXT,

    valor REAL DEFAULT 0,          -- valor investido
    valor_atual REAL DEFAULT 0,    -- valor atual

    data TEXT
)
""")

# DESAFIOS (🔥 NOVO)
cursor.execute("""
CREATE TABLE desafios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT,

    valor_meta REAL,
    valor_atual REAL DEFAULT 0,

    data_limite TEXT,

    concluido INTEGER DEFAULT 0,

    link TEXT
)
""")

# FATURAS
cursor.execute("""
CREATE TABLE faturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cartao_id INTEGER,
    mes INTEGER,
    ano INTEGER,
    pago INTEGER DEFAULT 0,
    UNIQUE(cartao_id, mes, ano),
    FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
)
""")

# =========================
# ÍNDICES
# =========================
cursor.execute("CREATE INDEX idx_gastos_data ON gastos(data)")
cursor.execute("CREATE INDEX idx_gastos_cartao ON gastos(cartao_id)")
cursor.execute("CREATE INDEX idx_faturas_cartao ON faturas(cartao_id)")

# =========================
# DADOS INICIAIS
# =========================

cursor.executemany(
    "INSERT INTO categorias (nome) VALUES (?)",
    [
        ("Casa",),
        ("Alimentação",),
        ("Transporte",),
        ("Lazer",),
        ("Saúde",),
        ("Educação",),
        ("Assinaturas",),
        ("Investimentos",),
        ("Outros",)
    ]
)

cursor.executemany(
    "INSERT INTO subcategorias (nome, categoria_id) VALUES (?, ?)",
    [
        ("Aluguel", 1),
        ("Condomínio", 1),
        ("Energia", 1),
        ("Água", 1),
        ("Internet", 1),
        ("Supermercado", 2),
        ("Restaurante", 2),
        ("Delivery", 2),
        ("Combustível", 3),
        ("Uber", 3),
        ("Manutenção", 3),
        ("Viagem", 4),
        ("Cinema", 4),
        ("Passeios", 4),
        ("Farmácia", 5),
        ("Plano de saúde", 5),
        ("Academia", 5),
        ("Faculdade", 6),
        ("Cursos", 6),
        ("Netflix", 7),
        ("Spotify", 7),
        ("Outros apps", 7),
        ("Renda fixa", 8),
        ("Ações", 8),
        ("Cripto", 8),
        ("Diversos", 9)
    ]
)

cursor.executemany(
    "INSERT INTO cartoes (nome, dia_vencimento, dia_fechamento, limite) VALUES (?, ?, ?, ?)",
    [
        ("Bradesco", 3, 25, 3000),
        ("Nubank", 10, 1, 5000)
    ]
)

conn.commit()
conn.close()

print("Banco criado com INVESTIMENTOS + DESAFIOS 🚀")