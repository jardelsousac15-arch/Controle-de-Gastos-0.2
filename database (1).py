"""
Camada de banco de dados - conexões seguras com context manager
"""
import os
import sqlite3
import hashlib
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    FUSO_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    FUSO_BR = timezone(timedelta(hours=-3))

DB_PATH = os.environ.get("DB_PATH", "gastos_usuarios.db")


def agora() -> datetime:
    return datetime.now(FUSO_BR)


def agora_str() -> str:
    return agora().strftime("%Y-%m-%d %H:%M:%S")


def hoje_str() -> str:
    return agora().date().isoformat()


@contextmanager
def get_db():
    """Context manager para conexão com SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    senha_hash    TEXT NOT NULL,
    nome          TEXT,
    trial_expires TIMESTAMP,
    criado_em     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gastos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL CHECK(valor > 0),
    categoria       TEXT DEFAULT 'Outros',
    forma_pagamento TEXT DEFAULT 'Não Informado',
    tipo            TEXT DEFAULT 'saida' CHECK(tipo IN ('saida','entrada')),
    data            DATE NOT NULL,
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS configuracoes (
    usuario_id   INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
    renda_mensal REAL DEFAULT 0,
    cor_destaque TEXT DEFAULT '#22c55e'
);

CREATE TABLE IF NOT EXISTS gastos_fixos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    descricao       TEXT NOT NULL,
    valor           REAL NOT NULL CHECK(valor > 0),
    tipo            TEXT DEFAULT 'saida' CHECK(tipo IN ('saida','entrada')),
    dia_vencimento  INTEGER DEFAULT 1 CHECK(dia_vencimento BETWEEN 1 AND 31),
    ativo           INTEGER DEFAULT 1,
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS convites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    token      TEXT UNIQUE NOT NULL,
    dias_trial INTEGER DEFAULT 30,
    max_usos   INTEGER DEFAULT 1,
    usos       INTEGER DEFAULT 0,
    criado_por INTEGER REFERENCES usuarios(id),
    expira_em  TIMESTAMP,
    ativo      INTEGER DEFAULT 1,
    criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gastos_usuario_data ON gastos(usuario_id, data);
CREATE INDEX IF NOT EXISTS idx_gastos_tipo ON gastos(tipo);
"""


def init_db():
    """Cria tabelas e aplica migrations."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)


def _migrate(conn: sqlite3.Connection):
    """Migrations seguras (idempotentes)."""
    migrations = [
        # gastos.tipo
        "ALTER TABLE gastos ADD COLUMN tipo TEXT DEFAULT 'saida'",
        # configuracoes.cor_destaque
        "ALTER TABLE configuracoes ADD COLUMN cor_destaque TEXT DEFAULT '#22c55e'",
        # usuarios.trial_expires
        "ALTER TABLE usuarios ADD COLUMN trial_expires TIMESTAMP",
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError:
            pass  # coluna já existe


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------

def criar_usuario(username: str, email: str, senha: str, nome: str = "", dias_trial: int = 7) -> dict:
    trial_expires = (agora() + timedelta(days=dias_trial)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO usuarios (username,email,senha_hash,nome,trial_expires) VALUES (?,?,?,?,?)",
                (username, email, hash_senha(senha), nome or username, trial_expires),
            )
            return {"ok": True, "user_id": cur.lastrowid}
    except sqlite3.IntegrityError as e:
        campo = "username" if "username" in str(e) else "email"
        return {"ok": False, "erro": f"{'Usuário' if campo == 'username' else 'E-mail'} já cadastrado"}


def verificar_login(username: str, senha: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id,username,nome FROM usuarios WHERE username=? AND senha_hash=?",
            (username, hash_senha(senha)),
        ).fetchone()
    if row:
        return {"ok": True, "user_id": row["id"], "username": row["username"], "nome": row["nome"]}
    return {"ok": False, "erro": "Usuário ou senha incorretos"}


def trial_expirado(usuario_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT trial_expires FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
    if not row or not row["trial_expires"]:
        return False
    exp = datetime.strptime(row["trial_expires"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=FUSO_BR)
    return agora() > exp


def dias_trial_restantes(usuario_id: int) -> int:
    with get_db() as conn:
        row = conn.execute("SELECT trial_expires FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
    if not row or not row["trial_expires"]:
        return 999
    exp = datetime.strptime(row["trial_expires"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=FUSO_BR)
    return max(0, (exp - agora()).days)


def atualizar_trial(usuario_id: int, dias: int) -> dict:
    expires = (agora() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("UPDATE usuarios SET trial_expires=? WHERE id=?", (expires, usuario_id))
    return {"ok": True, "trial_expires": expires}


def get_usuario(usuario_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id,username,email,nome FROM usuarios WHERE id=?", (usuario_id,)
        ).fetchone()
    return dict(row) if row else None


def atualizar_perfil(usuario_id: int, username: str, nome: str, email: str) -> dict:
    with get_db() as conn:
        dup = conn.execute(
            "SELECT id FROM usuarios WHERE username=? AND id!=?", (username, usuario_id)
        ).fetchone()
        if dup:
            return {"ok": False, "erro": "Nome de usuário já em uso"}
        conn.execute(
            "UPDATE usuarios SET username=?,nome=?,email=? WHERE id=?",
            (username, nome or username, email, usuario_id),
        )
    return {"ok": True}


# ---------------------------------------------------------------------------
# Gastos
# ---------------------------------------------------------------------------

def adicionar_gasto(usuario_id: int, descricao: str, valor: float,
                    categoria: str, forma_pagamento: str,
                    tipo: str = "saida", data: str | None = None) -> int:
    data = data or hoje_str()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO gastos (usuario_id,descricao,valor,categoria,forma_pagamento,tipo,data,criado_em)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (usuario_id, descricao, valor, categoria, forma_pagamento, tipo, data, agora_str()),
        )
        return cur.lastrowid


def listar_gastos(usuario_id: int, *, limite: int | None = None,
                  data_inicio: str | None = None, data_fim: str | None = None,
                  tipo: str | None = None) -> list[dict]:
    sql = "SELECT * FROM gastos WHERE usuario_id=?"
    params: list = [usuario_id]
    if data_inicio:
        sql += " AND data>=?"; params.append(data_inicio)
    if data_fim:
        sql += " AND data<=?"; params.append(data_fim)
    if tipo:
        sql += " AND tipo=?"; params.append(tipo)
    sql += " ORDER BY data DESC, criado_em DESC"
    if limite:
        sql += " LIMIT ?"; params.append(limite)
    with get_db() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def gastos_hoje(usuario_id: int) -> list[dict]:
    h = hoje_str()
    return listar_gastos(usuario_id, data_inicio=h, data_fim=h)


def deletar_gasto(gasto_id: int, usuario_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM gastos WHERE id=? AND usuario_id=?", (gasto_id, usuario_id)
        )
        return cur.rowcount > 0


def deletar_gastos_hoje(usuario_id: int) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM gastos WHERE usuario_id=? AND data=?", (usuario_id, hoje_str())
        )
        return cur.rowcount


def editar_gasto(gasto_id: int, usuario_id: int, **campos) -> bool:
    with get_db() as conn:
        ok = conn.execute(
            "SELECT id FROM gastos WHERE id=? AND usuario_id=?", (gasto_id, usuario_id)
        ).fetchone()
        if not ok:
            return False
        conn.execute(
            "UPDATE gastos SET descricao=?,valor=?,categoria=?,forma_pagamento=?,tipo=?,data=? WHERE id=?",
            (campos["descricao"], campos["valor"], campos["categoria"],
             campos["forma_pagamento"], campos["tipo"], campos["data"], gasto_id),
        )
        return True


def resumo(usuario_id: int, periodo: str = "mes") -> dict:
    hoje = agora().date()
    if periodo == "mes":
        inicio = f"{hoje.year}-{hoje.month:02d}-01"
        dias = hoje.day
    elif periodo == "ano":
        inicio = f"{hoje.year}-01-01"
        dias = hoje.timetuple().tm_yday
    else:
        inicio = hoje.isoformat()
        dias = 1

    with get_db() as conn:
        saidas = conn.execute(
            "SELECT COALESCE(SUM(valor),0) t, COUNT(*) q FROM gastos"
            " WHERE usuario_id=? AND data>=? AND tipo='saida'",
            (usuario_id, inicio),
        ).fetchone()
        entradas = conn.execute(
            "SELECT COALESCE(SUM(valor),0) t FROM gastos"
            " WHERE usuario_id=? AND data>=? AND tipo='entrada'",
            (usuario_id, inicio),
        ).fetchone()
        maior = conn.execute(
            "SELECT COALESCE(MAX(valor),0) m FROM gastos"
            " WHERE usuario_id=? AND data>=? AND tipo='saida'",
            (usuario_id, inicio),
        ).fetchone()
        cats = conn.execute(
            "SELECT categoria, SUM(valor) total FROM gastos"
            " WHERE usuario_id=? AND data>=? AND tipo='saida'"
            " GROUP BY categoria ORDER BY total DESC",
            (usuario_id, inicio),
        ).fetchall()

    ts, te = saidas["t"], entradas["t"]
    return {
        "total_saidas": ts,
        "total_entradas": te,
        "quantidade": saidas["q"],
        "maior_gasto": maior["m"],
        "media_diaria": ts / dias if dias else 0,
        "categorias": [{"nome": r["categoria"], "total": r["total"]} for r in cats],
        "periodo": periodo,
    }


# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------

CORES = {
    "verde":    ("#22c55e", "34, 197, 94"),
    "azul":     ("#3b82f6", "59, 130, 246"),
    "roxo":     ("#8b5cf6", "139, 92, 246"),
    "rosa":     ("#ec4899", "236, 72, 153"),
    "amarelo":  ("#f59e0b", "245, 158, 11"),
    "vermelho": ("#ef4444", "239, 68, 68"),
    "cyan":     ("#06b6d4", "6, 182, 212"),
    "laranja":  ("#f97316", "249, 115, 22"),
}


def _upsert_config(usuario_id: int, campo: str, valor):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO configuracoes (usuario_id) VALUES (?) ON CONFLICT(usuario_id) DO NOTHING",
            (usuario_id,),
        )
        conn.execute(
            f"UPDATE configuracoes SET {campo}=? WHERE usuario_id=?", (valor, usuario_id)
        )


def get_config(usuario_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT renda_mensal, cor_destaque FROM configuracoes WHERE usuario_id=?",
            (usuario_id,),
        ).fetchone()
    if row:
        hex_cor = row["cor_destaque"] or "#22c55e"
        nome_cor = next((k for k, v in CORES.items() if v[0] == hex_cor), "verde")
        return {"renda_mensal": row["renda_mensal"] or 0, "cor_hex": hex_cor,
                "cor_nome": nome_cor, "cor_rgb": CORES.get(nome_cor, CORES["verde"])[1]}
    return {"renda_mensal": 0, "cor_hex": "#22c55e", "cor_nome": "verde", "cor_rgb": "34, 197, 94"}


def salvar_renda(usuario_id: int, renda: float):
    _upsert_config(usuario_id, "renda_mensal", renda)


def salvar_cor(usuario_id: int, cor_nome: str) -> dict:
    hex_cor, rgb = CORES.get(cor_nome, CORES["verde"])
    _upsert_config(usuario_id, "cor_destaque", hex_cor)
    return {"ok": True, "cor": hex_cor, "nome": cor_nome, "rgb": rgb}


# ---------------------------------------------------------------------------
# Gastos fixos
# ---------------------------------------------------------------------------

def adicionar_fixo(usuario_id: int, descricao: str, valor: float,
                   tipo: str = "saida", dia: int = 1) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO gastos_fixos (usuario_id,descricao,valor,tipo,dia_vencimento) VALUES (?,?,?,?,?)",
            (usuario_id, descricao, valor, tipo, dia),
        )
        return cur.lastrowid


def listar_fixos(usuario_id: int) -> list[dict]:
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM gastos_fixos WHERE usuario_id=? AND ativo=1 ORDER BY dia_vencimento",
            (usuario_id,),
        ).fetchall()]


def deletar_fixo(fixo_id: int, usuario_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE gastos_fixos SET ativo=0 WHERE id=? AND usuario_id=?", (fixo_id, usuario_id)
        )
        return cur.rowcount > 0


def editar_fixo(fixo_id: int, usuario_id: int, **campos) -> bool:
    with get_db() as conn:
        ok = conn.execute(
            "SELECT id FROM gastos_fixos WHERE id=? AND usuario_id=?", (fixo_id, usuario_id)
        ).fetchone()
        if not ok:
            return False
        conn.execute(
            "UPDATE gastos_fixos SET descricao=?,valor=?,tipo=?,dia_vencimento=? WHERE id=?",
            (campos["descricao"], campos["valor"], campos["tipo"], campos["dia_vencimento"], fixo_id),
        )
        return True


# ---------------------------------------------------------------------------
# Convites
# ---------------------------------------------------------------------------

def gerar_convite(dias_trial: int = 30, max_usos: int = 1,
                  expira_dias: int | None = None, criado_por: int | None = None) -> dict:
    token = secrets.token_urlsafe(16)
    expira = None
    if expira_dias:
        expira = (agora() + timedelta(days=expira_dias)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO convites (token,dias_trial,max_usos,expira_em,criado_por) VALUES (?,?,?,?,?)",
            (token, dias_trial, max_usos, expira, criado_por),
        )
        return {"ok": True, "id": cur.lastrowid, "token": token}


def validar_convite(token: str) -> dict:
    if not token:
        return {"valido": False, "erro": "Token não fornecido"}
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM convites WHERE token=? AND ativo=1", (token,)
        ).fetchone()
    if not row:
        return {"valido": False, "erro": "Token inválido"}
    if row["expira_em"] and row["expira_em"] < agora_str():
        return {"valido": False, "erro": "Token expirado"}
    if row["usos"] >= row["max_usos"]:
        return {"valido": False, "erro": "Token já utilizado"}
    return {"valido": True, "dias_trial": row["dias_trial"], "id": row["id"]}


def usar_convite(token: str):
    with get_db() as conn:
        conn.execute("UPDATE convites SET usos=usos+1 WHERE token=?", (token,))


def listar_convites() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.*, u.username AS criado_por_username
            FROM convites c LEFT JOIN usuarios u ON c.criado_por=u.id
            ORDER BY c.criado_em DESC
        """).fetchall()
    return [dict(r) for r in rows]


def desativar_convite(convite_id: int):
    with get_db() as conn:
        conn.execute("UPDATE convites SET ativo=0 WHERE id=?", (convite_id,))


# ---------------------------------------------------------------------------
# Stats (admin)
# ---------------------------------------------------------------------------

def stats_app() -> dict:
    agora_s = agora_str()
    hoje = agora().date().isoformat()
    with get_db() as conn:
        total_u = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        hoje_u  = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE DATE(criado_em)=?", (hoje,)
        ).fetchone()[0]
        trial_a = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE trial_expires>?", (agora_s,)
        ).fetchone()[0]
        trial_e = conn.execute(
            "SELECT COUNT(*) FROM usuarios WHERE trial_expires<=?", (agora_s,)
        ).fetchone()[0]
        total_g = conn.execute("SELECT COUNT(*) FROM gastos").fetchone()[0]
        usuarios = conn.execute("""
            SELECT u.id, u.username, u.nome, u.email, u.criado_em, u.trial_expires,
                   COALESCE((SELECT SUM(valor) FROM gastos WHERE usuario_id=u.id AND tipo='saida'),0) total_gasto,
                   COALESCE((SELECT COUNT(*) FROM gastos WHERE usuario_id=u.id),0) qtd_gastos
            FROM usuarios u ORDER BY u.criado_em DESC
        """).fetchall()
    return {
        "total_usuarios": total_u,
        "usuarios_hoje": hoje_u,
        "trial_ativo": trial_a,
        "trial_expirado": trial_e,
        "total_gastos": total_g,
        "agora": agora_s,
        "usuarios": [dict(u) for u in usuarios],
    }


# ---------------------------------------------------------------------------
# Calendário
# ---------------------------------------------------------------------------

def calendario_mes(usuario_id: int) -> dict:
    import calendar
    hoje = agora().date()
    inicio = f"{hoje.year}-{hoje.month:02d}-01"
    with get_db() as conn:
        def _query(tipo):
            return {
                row["data"]: {"total": row["total"], "qtd": row["qtd"]}
                for row in conn.execute(
                    "SELECT data, SUM(valor) total, COUNT(*) qtd"
                    " FROM gastos WHERE usuario_id=? AND data>=? AND tipo=?"
                    " GROUP BY data ORDER BY data",
                    (usuario_id, inicio, tipo),
                ).fetchall()
            }
        saidas   = _query("saida")
        entradas = _query("entrada")
    _, dias_no_mes = calendar.monthrange(hoje.year, hoje.month)
    dias = []
    for dia in range(1, dias_no_mes + 1):
        ds = f"{hoje.year}-{hoje.month:02d}-{dia:02d}"
        s = saidas.get(ds,   {"total": 0, "qtd": 0})
        e = entradas.get(ds, {"total": 0, "qtd": 0})
        dias.append({"dia": dia, "data": ds,
                     "saidas": s["total"], "entradas": e["total"],
                     "qtd_saidas": s["qtd"], "qtd_entradas": e["qtd"],
                     "saldo": e["total"] - s["total"]})
    return {"ano": hoje.year, "mes": hoje.month, "dias": dias}


def calendario_ano(usuario_id: int) -> dict:
    hoje = agora().date()
    inicio = f"{hoje.year}-01-01"
    meses_nomes = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                   "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    with get_db() as conn:
        def _query(tipo):
            return {
                row["mes"]: {"total": row["total"], "qtd": row["qtd"]}
                for row in conn.execute(
                    "SELECT strftime('%m',data) mes, SUM(valor) total, COUNT(*) qtd"
                    " FROM gastos WHERE usuario_id=? AND data>=? AND tipo=?"
                    " GROUP BY strftime('%m',data)",
                    (usuario_id, inicio, tipo),
                ).fetchall()
            }
        saidas   = _query("saida")
        entradas = _query("entrada")
    meses = []
    for i in range(1, 13):
        ms = f"{i:02d}"
        s = saidas.get(ms,   {"total": 0, "qtd": 0})
        e = entradas.get(ms, {"total": 0, "qtd": 0})
        meses.append({"mes_num": i, "mes_nome": meses_nomes[i-1],
                      "saidas": s["total"], "entradas": e["total"],
                      "qtd_saidas": s["qtd"], "qtd_entradas": e["qtd"],
                      "saldo": e["total"] - s["total"]})
    return {"ano": hoje.year, "meses": meses}
