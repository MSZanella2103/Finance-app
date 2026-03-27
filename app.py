from flask import Flask, render_template, request, redirect
from flask import session
import sqlite3
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


if not os.path.exists("database.db"):
    import init_db

def get_user_id():
    return session.get("user_id", 1)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

# =========================
# CONEXÃO
# =========================
def get_db():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dict(rows):
    return [dict(row) for row in rows]

# =========================
# HELPERS
# =========================
def get_mes_ano():
    hoje = datetime.today()
    return hoje.month, hoje.year

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return redirect("/dashboard")

@app.route("/trocar-usuario/<int:user_id>")
def trocar_usuario(user_id):
    session["user_id"] = user_id
    return redirect(request.referrer or "/dashboard")

@app.context_processor
def inject_usuarios():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome FROM usuarios")
    usuarios = rows_to_dict(cursor.fetchall())

    conn.close()

    return dict(usuarios_global=usuarios)

@app.context_processor
def inject_user():
    return dict(user_id_logado=get_user_id())


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    conn = get_db()
    cursor = conn.cursor()

    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)
    anual = request.args.get("anual")

    mes_atual, ano_atual = get_mes_ano()

    # padrão: mês atual
    if not mes:
        mes = mes_atual

    if not ano:
        ano = ano_atual

    modo_anual = True if anual == "1" else False


    # =========================
    # GASTOS
    # =========================
    
    
    user_id = get_user_id()

    if modo_anual:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(valor_previsto), 0),
                COALESCE(SUM(valor_pago), 0)
            FROM gastos
            WHERE usuario_id = ?
            AND strftime('%Y', data) = ?
        """, (user_id, str(ano)))
    else:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(valor_previsto), 0),
                COALESCE(SUM(valor_pago), 0)
            FROM gastos
            WHERE usuario_id = ?
            AND strftime('%m', data) = ? 
            AND strftime('%Y', data) = ?
        """, (user_id, f"{mes:02d}", str(ano)))

    total_previsto, total_pago = cursor.fetchone()

    total_pendente = total_previsto - total_pago

    if modo_anual:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(valor_previsto), 0),
                COALESCE(SUM(valor_pago), 0)
            FROM gastos
            WHERE usuario_id = ?
            AND strftime('%Y', data) = ?
        """, (user_id, str(ano)))
    else:
        cursor.execute("""
        SELECT 
            COALESCE(SUM(valor_previsto), 0),
            COALESCE(SUM(valor_pago), 0)
        FROM gastos
        WHERE usuario_id = ?
        AND strftime('%m', data) = ? 
        AND strftime('%Y', data) = ?
        """, (user_id, f"{mes:02d}", str(ano)))

    # =========================
    # GANHOS
    # =========================

    if modo_anual:
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM ganhos
            WHERE usuario_id = ?
            AND strftime('%Y', data) = ?
        """, (user_id, str(ano)))
    else:
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM ganhos
            WHERE usuario_id = ?
            AND strftime('%m', data) = ? 
            AND strftime('%Y', data) = ?
        """, (user_id, f"{mes:02d}", str(ano)))

    total_ganhos = cursor.fetchone()[0]

    # =========================
    # SALDO
    # =========================
    saldo = total_ganhos - total_previsto

    # =========================
    # POR CATEGORIA
    # =========================
    cursor.execute("""
    SELECT 
        COALESCE(c.nome, 'Sem categoria') as nome, 
        SUM(g.valor_previsto) as total
    FROM gastos g
    LEFT JOIN categorias c ON g.categoria_id = c.id
    WHERE g.usuario_id = ?
    AND strftime('%m', g.data) = ? 
    AND strftime('%Y', g.data) = ?
    GROUP BY c.nome
    """, (user_id, f"{mes:02d}", str(ano)))

    categorias = rows_to_dict(cursor.fetchall())

    # =========================
    # EVOLUÇÃO MENSAL
    # =========================
    cursor.execute("""
    SELECT 
        strftime('%m', data) as mes, 
        SUM(valor_previsto) as total
    FROM gastos
    WHERE usuario_id = ?
    AND strftime('%Y', data) = ?
    GROUP BY strftime('%m', data)
    ORDER BY strftime('%m', data)
    """, (user_id, str(ano)))

    dados_mensais = rows_to_dict(cursor.fetchall())

    # =========================
    # MÊS ANTERIOR
    # =========================
    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1

    cursor.execute("""
    SELECT COALESCE(SUM(valor_previsto), 0)
    FROM gastos
    WHERE usuario_id = ?
    AND strftime('%m', data) = ? 
    AND strftime('%Y', data) = ?
    """, (user_id, f"{mes_anterior:02d}", str(ano_anterior)))

    total_anterior = cursor.fetchone()[0]

    # =========================
    # CARTÃO
    # =========================
    cursor.execute("""
    SELECT 
        c.id,
        c.nome,
        c.limite,
        COALESCE(SUM(g.valor_previsto - g.valor_pago), 0) as gasto
    FROM cartoes c
    LEFT JOIN gastos g 
        ON g.cartao_id = c.id
        AND g.usuario_id = ?
    WHERE c.usuario_id = ?
    GROUP BY c.id
    """, (user_id, user_id))

    cartoes_dashboard = rows_to_dict(cursor.fetchall())

    # calcular percentual
    for c in cartoes_dashboard:
        if c["limite"] > 0:
            c["percentual"] = (c["gasto"] / c["limite"]) * 100
        else:
            c["percentual"] = 0

    # FORA do loop
    cursor.execute("""
    SELECT COALESCE(SUM(valor_previsto - valor_pago), 0)
    FROM gastos
    WHERE usuario_id = ?
    AND cartao_id IS NOT NULL
    """, (user_id,))

    total_cartao = cursor.fetchone()[0]

    # soma dos limites
    limite_total = sum([
        c["limite"] if c["limite"] else 0
        for c in cartoes_dashboard
    ])

    # evita divisão por zero
    uso_percentual = (total_cartao / limite_total) * 100 if limite_total > 0 else 0

    # Ganhos por categoria
    cursor.execute("""
    SELECT 
        COALESCE(tipo, 'Sem categoria') as nome,
        SUM(valor) as total
    FROM ganhos
    WHERE usuario_id = ?
    AND strftime('%m', data) = ?
    AND strftime('%Y', data) = ?
    GROUP BY tipo
    """, (user_id, f"{mes:02d}", str(ano)))
    ganhos_categoria = rows_to_dict(cursor.fetchall())

    conn.close()

    return render_template(
        "dashboard.html",
        total_previsto=total_previsto,
        total_pago=total_pago,
        total_pendente=total_pendente,
        total_ganhos=total_ganhos,
        saldo=saldo,
        categorias=categorias,
        ganhos_categoria=ganhos_categoria,
        dados_mensais=dados_mensais,
        total_anterior=total_anterior,
        mes=mes,
        ano=ano,
        #limite=limite,
        cartoes_dashboard=cartoes_dashboard,
        total_cartao=total_cartao,
        uso_percentual=uso_percentual,
    )

# =========================
# GASTOS
# =========================
@app.route("/gastos", methods=["GET", "POST"])
def gastos():
    conn = get_db()
    cursor = conn.cursor()

    user_id = get_user_id()
    mes = request.args.get("mes", type=int)
    ano = request.args.get("ano", type=int)

    if not mes or not ano:
        mes, ano = get_mes_ano()

    # =========================
    # POST (SALVAR GASTO)
    # =========================
    if request.method == "POST":
        descricao = request.form.get("descricao")
        valor = float(request.form.get("valor", 0))
        data = request.form.get("data")
        categoria_id = int(request.form.get("categoria_id", 0))
        parcelas = int(request.form.get("parcelas", 1))

        tipo = request.form.get("tipo", "variavel")
        pago = 1 if request.form.get("pago") else 0

        cartao_id = request.form.get("cartao_id")
        cartao_id = int(cartao_id) if cartao_id else None

        data_compra = datetime.strptime(data, "%Y-%m-%d")

        # =========================
        # CALCULAR DATA PRIMEIRA PARCELA
        # =========================
        if cartao_id:
            cursor.execute("""
                SELECT dia_vencimento, dia_fechamento 
                FROM cartoes 
                WHERE id = ? AND usuario_id = ?
            """, (cartao_id, user_id))
            
            cartao = cursor.fetchone()

            if cartao:
                dia_fechamento = cartao["dia_fechamento"]
                dia_vencimento = cartao["dia_vencimento"]

                if data_compra.day <= dia_fechamento:
                    meses_adicionar = 1
                else:
                    meses_adicionar = 2

                data_fatura = data_compra + relativedelta(months=meses_adicionar)

                ultimo_dia = (data_fatura + relativedelta(day=31)).day
                dia_final = min(dia_vencimento, ultimo_dia)

                data_primeira = data_fatura.replace(day=dia_final)
            else:
                data_primeira = data_compra
        else:
            data_primeira = data_compra

        # =========================
        # GERAR PARCELAS
        # =========================
        valor_parcela = round(valor / parcelas, 2)

        for i in range(parcelas):
            data_parcela = data_primeira + relativedelta(months=i)

            if cartao_id:
                cursor.execute("""
                INSERT OR IGNORE INTO faturas (usuario_id, cartao_id, mes, ano, pago)
                VALUES (?, ?, ?, ?, 0)
                """, (
                    user_id,
                    cartao_id,
                    data_parcela.month,
                    data_parcela.year
                ))

            valor_final = (
                round(valor - (valor_parcela * (parcelas - 1)), 2)
                if i == parcelas - 1 else valor_parcela
            )

            cursor.execute("""
            INSERT INTO gastos (
                descricao, valor_previsto, valor_pago,
                data, categoria_id, parcela_atual,
                parcelas_total, cartao_id, tipo, pago,
                usuario_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                descricao,
                valor_final,
                valor_final if pago else 0,
                data_parcela.strftime("%Y-%m-%d"),
                categoria_id,
                i + 1,
                parcelas,
                cartao_id,
                tipo,
                pago,
                user_id
            ))

        conn.commit()

        # AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": True}

        return redirect(f"/gastos?mes={mes}&ano={ano}")

    # =========================
    # GET (LISTAGEM)
    # =========================

    cursor.execute("""
    SELECT g.*, c.nome as categoria_nome
    FROM gastos g
    LEFT JOIN categorias c ON g.categoria_id = c.id
    WHERE g.usuario_id = ?
    AND strftime('%m', g.data) = ? 
    AND strftime('%Y', g.data) = ?
    ORDER BY g.data DESC
    """, (user_id, f"{mes:02d}", str(ano)))

    gastos = rows_to_dict(cursor.fetchall())

    cursor.execute("SELECT * FROM cartoes WHERE usuario_id = ?", (user_id,))
    cartoes = rows_to_dict(cursor.fetchall())

    cursor.execute("SELECT * FROM categorias")
    categorias = rows_to_dict(cursor.fetchall())

    cursor.execute("""
    SELECT 
        c.id,
        c.nome,
        COALESCE(SUM(g.valor_previsto), 0) as total
    FROM cartoes c
    LEFT JOIN gastos g 
        ON g.cartao_id = c.id
        AND g.usuario_id = ?
        AND strftime('%m', g.data) = ?
        AND strftime('%Y', g.data) = ?
    WHERE c.usuario_id = ?
    GROUP BY c.id
    """, (user_id, f"{mes:02d}", str(ano), user_id))

    totais_cartao = rows_to_dict(cursor.fetchall())

    cursor.execute("""
    SELECT cartao_id, pago
    FROM faturas
    WHERE usuario_id = ?
    AND mes = ? AND ano = ?
    """, (user_id, mes, ano))

    faturas_db = cursor.fetchall()
    status_faturas = {f["cartao_id"]: f["pago"] for f in faturas_db}

    for t in totais_cartao:
        if t["id"] not in status_faturas:
            status_faturas[t["id"]] = 0

    cursor.execute("""
    SELECT COALESCE(SUM(valor_previsto), 0)
    FROM gastos
    WHERE usuario_id = ?
    AND strftime('%m', data) = ? 
    AND strftime('%Y', data) = ?
    """, (user_id, f"{mes:02d}", str(ano)))

    total_mes = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "gastos.html",
        gastos=gastos,
        cartoes=cartoes,
        categorias=categorias,
        total_mes=total_mes,
        totais_cartao=totais_cartao,
        status_faturas=status_faturas,
        mes=mes,
        ano=ano,
        data_hoje=date.today().isoformat()
    )

@app.route("/toggle_fatura/<int:cartao_id>/<int:mes>/<int:ano>")
def toggle_fatura(cartao_id, mes, ano):
    conn = get_db()
    cursor = conn.cursor()

    user_id = get_user_id()

    cursor.execute("""
    SELECT id, pago FROM faturas
    WHERE usuario_id = ?
    AND cartao_id = ? AND mes = ? AND ano = ?
    """, (user_id, cartao_id, mes, ano))

    fatura = cursor.fetchone()

    if fatura:
        novo_status = 0 if fatura["pago"] else 1

        # atualiza fatura
        cursor.execute("""
        UPDATE faturas SET pago = ?
        WHERE id = ?
        """, (novo_status, fatura["id"]))

        # 🔥 AQUI ESTÁ O SEGREDO
        if novo_status == 1:
            # marcar como pago
            cursor.execute("""
            UPDATE gastos
            SET valor_pago = valor_previsto, pago = 1
            WHERE usuario_id = ?
            AND cartao_id = ?
            AND strftime('%m', data) = ?
            AND strftime('%Y', data) = ?
            """, (user_id, cartao_id, f"{mes:02d}", str(ano)))
        else:
            # desmarcar pagamento
            cursor.execute("""
            UPDATE gastos
            SET valor_pago = 0, pago = 0
            WHERE usuario_id = ?
            AND cartao_id = ?
            AND strftime('%m', data) = ?
            AND strftime('%Y', data) = ?
            """, (user_id, cartao_id, f"{mes:02d}", str(ano)))

    else:
        # cria fatura já paga
        user_id = get_user_id()

        cursor.execute("""
        INSERT INTO faturas (usuario_id, cartao_id, mes, ano, pago)
        VALUES (?, ?, ?, ?, 1)
        """, (user_id, cartao_id, mes, ano))

        # 🔥 garantir que gastos também sejam pagos
        cursor.execute("""
        UPDATE gastos
        SET valor_pago = valor_previsto, pago = 1
        WHERE usuario_id = ?
        AND cartao_id = ?
        AND strftime('%m', data) = ?
        AND strftime('%Y', data) = ?
        """, (user_id, cartao_id, f"{mes:02d}", str(ano)))

    conn.commit()
    conn.close()

    return redirect(f"/gastos?mes={mes}&ano={ano}")

# =========================
# GANHOS
# =========================
@app.route("/ganhos", methods=["GET", "POST"])
def ganhos():
    conn = get_db()
    cursor = conn.cursor()

    user_id = get_user_id()
    
    if request.method == "POST":
        cursor.execute("""
        INSERT INTO ganhos (descricao, valor, data, tipo, usuario_id)
        VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["descricao"],
            float(request.form["valor"]),
            request.form["data"],
            request.form["tipo"],
            user_id
        ))

        conn.commit()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": True}

        return redirect("/ganhos")

    mes, ano = get_mes_ano()

    cursor.execute("""
    SELECT * FROM ganhos
    WHERE usuario_id = ?
    AND strftime('%m', data) = ?
    AND strftime('%Y', data) = ?
    ORDER BY data DESC
    """, (user_id, f"{mes:02d}", str(ano)))

    ganhos = rows_to_dict(cursor.fetchall())

    cursor.execute("""
    SELECT tipo, SUM(valor) as total
    FROM ganhos
    WHERE usuario_id = ?
    AND strftime('%m', data) = ?
    AND strftime('%Y', data) = ?
    GROUP BY tipo
    """, (user_id, f"{mes:02d}", str(ano)))

    ganhos_categoria = rows_to_dict(cursor.fetchall())

    total_mes = sum([g['total'] for g in ganhos_categoria])


    conn.close()

    return render_template(
        "ganhos.html",
        ganhos=ganhos,
        ganhos_categoria=ganhos_categoria,
        total_mes=total_mes,   # ← ESSENCIAL
        mes=mes,
        ano=ano,
        data_hoje=date.today().isoformat()
    )


# =========================
# CARTÕES
# =========================
@app.route("/cartoes", methods=["GET", "POST"])
def cartoes():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        vencimento = int(request.form["vencimento"])
        fechamento = int(request.form["fechamento"])
        limite = float(request.form["limite"])

        cursor.execute("""
        INSERT INTO cartoes (nome, dia_vencimento, dia_fechamento, limite, usuario_id)
        VALUES (?, ?, ?, ?, ?)
        """, (nome, vencimento, fechamento, limite, get_user_id()))

        conn.commit()
        return redirect("/cartoes")

    # GET
    user_id = get_user_id()

    cursor.execute("""
        SELECT id, COALESCE(nome, 'Sem nome') as nome, dia_vencimento, dia_fechamento
        FROM cartoes WHERE usuario_id = ?
    """, (user_id,))

    # Buscar cartões
    user_id = get_user_id()
    cursor.execute("SELECT * FROM cartoes WHERE usuario_id = ?", (user_id,))
    cartoes = rows_to_dict(cursor.fetchall())

    # 🔥 BUSCA CATEGORIAS ANTES DE FECHAR
    cursor.execute("SELECT * FROM categorias")
    categorias = rows_to_dict(cursor.fetchall())

    conn.close()

    return render_template(
        "cartoes.html",
        cartoes=cartoes,
        categorias=categorias,
        data_hoje=date.today().isoformat()
    )

@app.route("/cartoes/deletar/<int:id>", methods=["GET", "DELETE"])
def deletar_cartao(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
    "DELETE FROM cartoes WHERE id = ? AND usuario_id = ?",
    (id, get_user_id())
    )
    conn.commit()
    conn.close()
    # Se for GET, redireciona de volta
    if request.method == "GET":
        return redirect("/cartoes")
    return {"success": True}


# =========================
# INVESTIMENTOS
# =========================
@app.route("/investimentos", methods=["GET", "POST"])
def investimentos():
    conn = get_db()
    cursor = conn.cursor()

    user_id = get_user_id()

    if request.method == "POST":
        cursor.execute("""
        INSERT INTO investimentos (nome, tipo, instituicao, valor, valor_atual, data, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["nome"],
            request.form["tipo"],
            request.form["instituicao"],
            float(request.form["valor"]),
            float(request.form["valor_atual"]),
            request.form["data"],
            user_id
        ))

        conn.commit()
        return redirect("/investimentos")

    # BUSCAR DADOS
    cursor.execute("SELECT * FROM investimentos WHERE usuario_id = ? ORDER BY data ASC", (user_id,))
    investimentos = rows_to_dict(cursor.fetchall())

    # TOTAL INVESTIDO
    total_investido = sum([i["valor"] for i in investimentos])

    # TOTAL ATUAL
    total_atual = sum([i["valor_atual"] for i in investimentos])

    rendimento_total = total_atual - total_investido

    conn.close()

    return render_template(
        "investimentos.html",
        investimentos=investimentos,
        total_investido=total_investido,
        total_atual=total_atual,
        rendimento_total=rendimento_total,
        data_hoje=date.today().isoformat()
    )


# =========================
# DESAFIOS
# =========================
@app.route("/desafios", methods=["GET", "POST"])
def desafios():
    user_id = get_user_id()
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
        INSERT INTO desafios (
            titulo, descricao, valor_meta, valor_atual,
            data_limite, link, usuario_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["titulo"],
            request.form["descricao"],
            float(request.form.get("valor_meta") or 0),
            float(request.form.get("valor_atual", 0)),
            request.form["data_limite"],
            request.form.get("link"),
            user_id
        ))

        conn.commit()
        return redirect("/desafios")

    cursor.execute(
    "SELECT * FROM desafios WHERE usuario_id = ? ORDER BY data_limite ASC",
    (user_id,)
    )
    desafios = rows_to_dict(cursor.fetchall())

    # CALCULAR PROGRESSO
    for d in desafios:
        meta = d["valor_meta"] or 0
        atual = d["valor_atual"] or 0

        if meta > 0:
            d["percentual"] = min((atual / meta) * 100, 100)
        else:
            d["percentual"] = 0    

    conn.close()

    return render_template("desafios.html", desafios=desafios)

@app.route("/desafios/toggle/<int:id>")
def toggle_desafio(id):
    conn = get_db()
    cursor = conn.cursor()

    user_id = get_user_id()
    cursor.execute("SELECT concluido FROM desafios WHERE usuario_id = ? AND id = ?", (user_id, id))
    status = cursor.fetchone()["concluido"]

    cursor.execute("""
    UPDATE desafios
    SET concluido = ?
    WHERE id = ? AND usuario_id = ?
    """, (0 if status else 1, id))

    conn.commit()
    conn.close()

    return redirect("/desafios")


# =========================
# PROTEÇÃO SISTEMA
# =========================

@app.before_request
def proteger():
    if request.path.startswith("/static"):
        return

    token = request.args.get("token")

    # se enviou token válido → salva sessão
    if token == "21033007":
        session["auth"] = True

    # se não estiver autenticado → bloqueia
    if not session.get("auth"):
        return "Acesso negado"

# =========================
# START
# =========================
if __name__ == "__main__":
    app.run()