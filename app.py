"""
Money X — Controle Financeiro Multi-Usuário
Arquivo único. Dependência: Flask.

Instalar:  pip install flask
Rodar:     python app.py
           python app.py 8080
"""
import os
import sys
import io
import sqlite3
import hashlib
import secrets
import calendar
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import (Flask, jsonify, redirect, render_template_string,
                   request, session, url_for, make_response)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    try:
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    except ImportError:
        TA_CENTER, TA_RIGHT, TA_LEFT = 1, 2, 0
    REPORTLAB_OK = True
except Exception as _rl_err:
    print(f"[AVISO] reportlab não carregou: {_rl_err}")
    REPORTLAB_OK = False

try:
    from zoneinfo import ZoneInfo
    FUSO_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    FUSO_BR = timezone(timedelta(hours=-3))

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ==============================================================
# BANCO DE DADOS
# ==============================================================

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


# ==============================================================
# HTML TEMPLATES
# ==============================================================

# ──────────────────────────────────────────────────────────────────────────────
# CSS compartilhado — variáveis e base
# ──────────────────────────────────────────────────────────────────────────────
_BASE_CSS = """
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--c:#22c55e;--c-rgb:34,197,94;--c-a:rgba(34,197,94,.15)}
body{font-family:'Sora',sans-serif;background:#000;color:#fff;min-height:100vh}
.card{background:#111;border-radius:12px;padding:20px;border:1px solid #1a1a1a;transition:border-color .2s}
.card:hover{border-color:#333}
.btn{padding:12px 24px;border:none;border-radius:14px;font:600 .95rem 'Sora',sans-serif;cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:8px}
.btn-primary{background:#fff;color:#000}.btn-primary:hover{background:#e5e5e5}
.btn-secondary{background:#1a1a1a;color:#888;border:1px solid #222}.btn-secondary:hover{background:#222;color:#fff}
.btn-danger{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:#ef4444}
input,select{width:100%;padding:14px 16px;border:1px solid #222;border-radius:12px;background:#111;color:#fff;font:inherit;transition:border-color .2s}
input:focus,select:focus{outline:none;border-color:var(--c)}
input::placeholder{color:#333}
select option{background:#111}
label{display:block;color:#666;margin-bottom:8px;font:.75rem 'Sora',sans-serif;font-weight:600;text-transform:uppercase;letter-spacing:1px}
.erro{background:rgba(255,59,48,.08);border:1px solid rgba(255,59,48,.2);color:#ff3b30;padding:12px 16px;border-radius:10px;margin-bottom:20px;text-align:center;font-size:.85rem}
.toast{position:fixed;bottom:30px;right:30px;padding:14px 24px;border-radius:12px;font-weight:500;font-size:.9rem;z-index:9999;animation:slideIn .3s ease}
.toast.sucesso{background:var(--c);color:#000}
.toast.erro{background:#ef4444;color:#fff}
@keyframes slideIn{from{transform:translateX(100%);opacity:0}to{transform:translateX(0);opacity:1}}
.badge-saida{display:inline-block;padding:3px 10px;border-radius:100px;font-size:.7rem;font-weight:600;background:rgba(239,68,68,.1);color:#ef4444}
.badge-entrada{display:inline-block;padding:3px 10px;border-radius:100px;font-size:.7rem;font-weight:600;background:rgba(34,197,94,.1);color:var(--c)}
.valor-saida{color:#ef4444;font-weight:600}
.valor-entrada{color:var(--c);font-weight:600}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(8px);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:#0a0a0a;border-radius:20px;padding:32px;width:90%;max-width:450px;max-height:90vh;overflow-y:auto;border:1px solid #1a1a1a;animation:mFade .3s ease}
@keyframes mFade{from{opacity:0;transform:scale(.92) translateY(20px)}to{opacity:1;transform:scale(1) translateY(0)}}
.modal h2{margin-bottom:24px;font-size:1.3rem;font-weight:600;display:flex;align-items:center;gap:8px}
.form-group{margin-bottom:18px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.modal-buttons{display:flex;gap:12px;margin-top:24px}
.modal-buttons .btn{flex:1;justify-content:center}
.modal-close-btn{background:rgba(239,68,68,.1);border:none;color:#ef4444;width:36px;height:36px;border-radius:50%;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s;margin-left:auto}
.modal-close-btn:hover{background:rgba(239,68,68,.2)}
</style>
"""

_TOGGLE_PASS_JS = """
<script>
function toggleSenha(id){
  const i=document.getElementById(id),b=i.parentElement.querySelector('.eye-btn');
  i.type=i.type==='password'?'text':'password';
  b.innerHTML=i.type==='password'?'&#128065;':'&#128583;';
}
</script>"""

_PASS_INPUT = lambda fid: f"""
<div style="position:relative;display:flex;align-items:center">
  <input type="password" name="{fid}" id="{fid}" placeholder="Mínimo 4 caracteres" required style="padding-right:44px">
  <button type="button" class="eye-btn" onclick="toggleSenha('{fid}')"
    style="position:absolute;right:12px;background:none;border:none;color:#333;cursor:pointer;font-size:1rem">&#128065;</button>
</div>"""

# ──────────────────────────────────────────────────────────────────────────────
# LOGIN
# ──────────────────────────────────────────────────────────────────────────────

LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
  <title>Login — Money X</title>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  {_BASE_CSS}
  <style>
    body{{display:flex;align-items:center;justify-content:center;padding:20px}}
    .box{{background:#0a0a0a;border-radius:20px;padding:48px 36px;width:100%;max-width:400px;border:1px solid #1a1a1a}}
    .logo{{text-align:center;margin-bottom:36px}}
    .logo-m{{font-size:2rem;font-weight:400}}
    .logo-x{{font-size:2.4rem;font-weight:800;color:var(--c)}}
    h1{{color:#fff;text-align:center;font-size:1.4rem;font-weight:600;margin-bottom:6px}}
    .sub{{color:#555;text-align:center;font-size:.85rem;margin-bottom:32px}}
    .link{{text-align:center;margin-top:24px;color:#444;font-size:.85rem}}
    .link a{{color:#fff;text-decoration:none;font-weight:500}}
    .link a:hover{{color:#ccc}}
    input{{padding:14px 16px}}
  </style>
</head>
<body>
<div class="box">
  <div class="logo">
    <span class="logo-m">Money </span><span class="logo-x">X</span>
  </div>
  <h1>Bem-vindo de volta</h1>
  <p class="sub">Entre na sua conta para continuar</p>
  {{% if erro %}}<div class="erro">{{{{ erro }}}}</div>{{% endif %}}
  <form method="POST">
    <div class="form-group"><label>Usuário</label><input type="text" name="username" placeholder="Seu usuário" required autofocus></div>
    <div class="form-group"><label>Senha</label>{_PASS_INPUT('senha')}</div>
    <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">Entrar</button>
  </form>
  <div class="link">Não tem conta? <a href="/registro">Criar conta</a></div>
</div>
{_TOGGLE_PASS_JS}
</body>
</html>"""

# ──────────────────────────────────────────────────────────────────────────────
# REGISTRO
# ──────────────────────────────────────────────────────────────────────────────

REGISTRO_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
  <title>Registro — Money X</title>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  {_BASE_CSS}
  <style>
    body{{display:flex;align-items:center;justify-content:center;padding:20px}}
    .box{{background:#0a0a0a;border-radius:20px;padding:44px 36px;width:100%;max-width:400px;border:1px solid #1a1a1a}}
    h1{{color:#fff;text-align:center;font-size:1.4rem;font-weight:600;margin-bottom:6px}}
    .sub{{color:#555;text-align:center;font-size:.85rem;margin-bottom:8px}}
    .trial-badge{{display:block;margin:0 auto 28px;width:fit-content;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.15);color:var(--c);padding:6px 14px;border-radius:100px;font:.75rem 'Sora',sans-serif;font-weight:600}}
    .link{{text-align:center;margin-top:24px;color:#444;font-size:.85rem}}
    .link a{{color:#fff;text-decoration:none;font-weight:500}}
    .link a:hover{{color:#ccc}}
  </style>
</head>
<body>
<div class="box">
  <h1>Criar sua conta</h1>
  <p class="sub">Comece a controlar seus gastos</p>
  <span class="trial-badge">{{{{ dias_trial }}}} dias grátis</span>
  {{% if erro %}}<div class="erro">{{{{ erro }}}}</div>{{% endif %}}
  <form method="POST">
    <input type="hidden" name="token" value="{{{{ token }}}}">
    <div class="form-group"><label>Nome</label><input type="text" name="nome" placeholder="Seu nome"></div>
    <div class="form-group"><label>Usuário</label><input type="text" name="username" placeholder="Nome de usuário" required></div>
    <div class="form-group"><label>Email</label><input type="email" name="email" placeholder="Seu email" required></div>
    <div class="form-group"><label>Senha</label>{_PASS_INPUT('senha')}</div>
    <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center">Criar Conta</button>
  </form>
  <div class="link">Já tem conta? <a href="/login">Fazer login</a></div>
</div>
{_TOGGLE_PASS_JS}
</body>
</html>"""

# ──────────────────────────────────────────────────────────────────────────────
# REGISTRO ERRO (token inválido)
# ──────────────────────────────────────────────────────────────────────────────

REGISTRO_ERRO_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Convite Inválido — Money X</title>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
  {_BASE_CSS}
  <style>
    body{{display:flex;align-items:center;justify-content:center;padding:20px}}
    .box{{background:#0a0a0a;border-radius:20px;padding:44px 36px;width:100%;max-width:400px;border:1px solid #1a1a1a;text-align:center}}
    .icon{{font-size:3rem;margin-bottom:20px}}
    h1{{margin-bottom:16px;font-size:1.4rem}}
    .info{{color:#555;font-size:.85rem;line-height:1.7;margin-bottom:24px}}
    a.btn{{text-decoration:none;background:#0f0f0f;border:1px solid #1e1e1e;color:#fff}}
    a.btn:hover{{background:#1a1a1a}}
  </style>
</head>
<body>
<div class="box">
  <div class="icon">&#128274;</div>
  <h1>Convite Inválido</h1>
  <div class="erro">{{{{ erro }}}}</div>
  <p class="info">Este link não é válido ou já foi utilizado.<br>Solicite um novo convite ao administrador.</p>
  <a href="/login" class="btn" style="padding:12px 28px">Ir para Login</a>
</div>
</body>
</html>"""

# ──────────────────────────────────────────────────────────────────────────────
# TRIAL EXPIRADO
# ──────────────────────────────────────────────────────────────────────────────

TRIAL_EXPIRADO_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Trial Expirado — Money X</title>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
  {_BASE_CSS}
  <style>
    body{{display:flex;align-items:center;justify-content:center;padding:20px}}
    .box{{background:#0a0a0a;border-radius:24px;padding:48px 40px;width:100%;max-width:420px;border:1px solid #1a1a1a;text-align:center}}
    .icon-wrap{{width:72px;height:72px;background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);border-radius:20px;display:inline-flex;align-items:center;justify-content:center;font-size:2rem;margin-bottom:24px}}
    h1{{font-size:1.5rem;font-weight:600;margin-bottom:12px}}
    p{{color:#666;margin-bottom:32px;line-height:1.7;font-size:.95rem}}
    .hl{{color:var(--c);font-weight:600}}
    a.btn{{text-decoration:none;background:#fff;color:#000;padding:16px 40px;border-radius:14px}}
    a.btn:hover{{background:#e5e5e5}}
  </style>
</head>
<body>
<div class="box">
  <div class="icon-wrap">&#9200;</div>
  <h1>Período gratuito expirou</h1>
  <p>Os <span class="hl">dias de teste</span> chegaram ao fim.<br>Entre em contato para liberar o acesso.</p>
  <a href="/logout" class="btn">Sair</a>
</div>
</body>
</html>"""

# ──────────────────────────────────────────────────────────────────────────────
# STATS (Admin)
# ──────────────────────────────────────────────────────────────────────────────

STATS_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Stats — Money X</title>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  {_BASE_CSS}
  <style>
    body{{padding:24px}}
    .container{{max-width:960px;margin:0 auto}}
    .back{{display:inline-block;margin-bottom:24px;color:var(--c);text-decoration:none;font-size:.85rem;font-weight:500}}
    .back:hover{{opacity:.8}}
    h1{{text-align:center;font-size:1.8rem;font-weight:600;margin-bottom:8px}}
    .page-sub{{text-align:center;color:#555;font-size:.9rem;margin-bottom:36px}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:32px}}
    .stat-card{{background:#0a0a0a;border-radius:16px;padding:20px;text-align:center;border:1px solid #1a1a1a}}
    .stat-num{{font-size:2rem;font-weight:700}}
    .stat-lbl{{font-size:.75rem;color:#666;margin-top:6px;text-transform:uppercase;letter-spacing:.5px}}
    .section{{background:#0a0a0a;border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #1a1a1a;overflow-x:auto}}
    .section-title{{font-size:1.1rem;font-weight:600;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center}}
    table{{width:100%;border-collapse:collapse}}
    th{{text-align:left;padding:12px 10px;border-bottom:1px solid #1a1a1a;color:#555;font-size:.75rem;text-transform:uppercase;letter-spacing:.5px;font-weight:500}}
    td{{padding:12px 10px;border-bottom:1px solid #111;font-size:.85rem;color:#ccc}}
    tr:hover td{{background:rgba(255,255,255,.02)}}
    .tag-ativo{{color:var(--c);font-weight:600}}
    .tag-exp{{color:#ef4444;font-weight:600}}
    .tag-gen-btn{{background:var(--c);color:#000;border:none;padding:8px 16px;border-radius:8px;font:.8rem 'Sora',sans-serif;font-weight:600;cursor:pointer}}
    .tag-dis-btn{{background:none;border:1px solid #ef4444;color:#ef4444;padding:4px 10px;border-radius:6px;font:.7rem 'Sora',sans-serif;cursor:pointer}}
    .copy-btn{{background:none;border:none;color:var(--c);cursor:pointer;font-size:.7rem;margin-left:6px}}
  </style>
</head>
<body>
<div class="container">
  <a href="/" class="back">← Voltar</a>
  <h1>Painel de Estatísticas</h1>
  <p class="page-sub">Visão geral do aplicativo</p>

  <div class="cards">
    <div class="stat-card"><div class="stat-num" style="color:var(--c)">{{{{ total_usuarios }}}}</div><div class="stat-lbl">Usuários</div></div>
    <div class="stat-card"><div class="stat-num" style="color:var(--c)">{{{{ trial_ativo }}}}</div><div class="stat-lbl">Trial Ativo</div></div>
    <div class="stat-card"><div class="stat-num" style="color:#ef4444">{{{{ trial_expirado }}}}</div><div class="stat-lbl">Trial Expirado</div></div>
    <div class="stat-card"><div class="stat-num" style="color:#f59e0b">{{{{ usuarios_hoje }}}}</div><div class="stat-lbl">Cadastros Hoje</div></div>
    <div class="stat-card"><div class="stat-num" style="color:#4ade80">{{{{ total_gastos }}}}</div><div class="stat-lbl">Total Gastos</div></div>
  </div>

  <div class="section">
    <div class="section-title">Lista de Usuários</div>
    <table>
      <thead><tr><th>#</th><th>Usuário</th><th>Nome</th><th>Cadastro</th><th>Status</th><th>Gastos</th><th>Total</th><th>Ação</th></tr></thead>
      <tbody>
        {{% for u in usuarios %}}
        <tr>
          <td>{{{{ u.id }}}}</td>
          <td>{{{{ u.username }}}}</td>
          <td>{{{{ u.nome }}}}</td>
          <td>{{{{ u.criado_em[:10] if u.criado_em else '-' }}}}</td>
          <td>
            {{% if u.trial_expires and u.trial_expires > agora %}}<span class="tag-ativo">Ativo</span>
            {{% elif u.trial_expires %}}<span class="tag-exp">Expirado</span>
            {{% else %}}<span style="color:#555">—</span>{{% endif %}}
          </td>
          <td>{{{{ u.qtd_gastos }}}}</td>
          <td>R$ {{{{ "%.2f"|format(u.total_gasto) }}}}</td>
          <td><button onclick="renovarTrial({{{{ u.id }}}})" style="background:none;border:1px solid #333;color:#888;padding:4px 10px;border-radius:6px;font:.7rem 'Sora',sans-serif;cursor:pointer">Renovar Trial</button></td>
        </tr>
        {{% endfor %}}
      </tbody>
    </table>
  </div>

  <div class="section">
    <div class="section-title">
      <span>Convites</span>
      <button class="tag-gen-btn" onclick="gerarConvite()">+ Gerar Convite</button>
    </div>
    <table>
      <thead><tr><th>Token</th><th>Dias</th><th>Usos</th><th>Status</th><th>Criado</th><th>Ação</th></tr></thead>
      <tbody>
        {{% for c in convites %}}
        <tr>
          <td style="font-family:monospace;font-size:.75rem">
            {{{{ c.token[:12] }}}}...
            <button class="copy-btn" onclick="copiarToken('{{{{ c.token }}}}')">Copiar link</button>
          </td>
          <td>{{{{ c.dias_trial }}}}d</td>
          <td>{{{{ c.usos }}}}/{{{{ c.max_usos }}}}</td>
          <td>
            {{% if c.ativo and (not c.expira_em or c.expira_em > agora) and c.usos < c.max_usos %}}<span class="tag-ativo">Ativo</span>
            {{% elif not c.ativo %}}<span style="color:#555">Desativado</span>
            {{% elif c.usos >= c.max_usos %}}<span class="tag-exp">Usado</span>
            {{% else %}}<span class="tag-exp">Expirado</span>{{% endif %}}
          </td>
          <td>{{{{ c.criado_em[:10] if c.criado_em else '-' }}}}</td>
          <td>
            {{% if c.ativo %}}<button class="tag-dis-btn" onclick="desativar({{{{ c.id }}}})">Desativar</button>{{% endif %}}
          </td>
        </tr>
        {{% endfor %}}
      </tbody>
    </table>
  </div>
</div>
<script>
function gerarConvite(){{
  const dias=prompt('Dias de trial?','30');
  const usos=prompt('Usos máximos?','1');
  if(!dias||!usos)return;
  fetch('/api/convites/gerar',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{dias_trial:+dias,max_usos:+usos}})}})
    .then(r=>r.json()).then(d=>{{if(d.ok||d.token)location.reload();}});
}}
function copiarToken(token){{
  const link=location.origin+'/registro/'+token;
  navigator.clipboard.writeText(link).then(()=>alert('Link copiado:\\n'+link));
}}
function desativar(id){{
  if(!confirm('Desativar este convite?'))return;
  fetch('/api/convites/desativar/'+id,{{method:'POST'}}).then(()=>location.reload());
}}
function renovarTrial(id){{
  const dias=prompt('Quantos dias de trial?','30');
  if(!dias)return;
  fetch('/api/usuarios/'+id+'/trial',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{dias:+dias}})}})
    .then(r=>r.json()).then(d=>{{if(d.ok)alert('Trial renovado!');else alert('Erro');}});
}}
</script>
</body>
</html>"""

# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────

DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Money X — Controle Financeiro</title>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  {_BASE_CSS}
  <style>
    /* Layout */
    body{{overflow:hidden}}
    .app{{display:flex;height:100vh}}
    .sidebar{{width:210px;flex-shrink:0;background:#000;display:flex;flex-direction:column;border-right:1px solid #1a1a1a}}
    .sidebar-hd{{padding:20px;border-bottom:1px solid #1a1a1a}}
    .logo-m{{font-size:1.15rem;font-weight:400}}
    .logo-x{{font-size:1.4rem;font-weight:800;color:var(--c)}}
    .sidebar-nav{{padding:16px 12px;flex:1}}
    .s-section{{margin-bottom:24px}}
    .s-label{{font-size:10px;text-transform:uppercase;letter-spacing:2px;color:#444;padding:0 8px;margin-bottom:8px}}
    .s-item{{width:100%;display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;border:none;background:transparent;color:#888;cursor:pointer;font:400 13px 'Sora',sans-serif;text-align:left;transition:all .15s}}
    .s-item svg{{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.6;flex-shrink:0}}
    .s-item:hover{{background:#111;color:#ccc}}
    .s-item.active{{background:var(--c-a);color:var(--c);font-weight:600}}
    .s-item.active svg{{stroke:var(--c)}}
    .sidebar-ft{{padding:16px;border-top:1px solid #1a1a1a}}
    .s-user{{display:flex;align-items:center;gap:12px}}
    .s-avatar{{width:30px;height:30px;border-radius:50%;background:var(--c-a);border:1px solid var(--c);display:flex;align-items:center;justify-content:center;color:var(--c);font:700 11px 'Sora',sans-serif;flex-shrink:0}}
    .s-name{{font:600 13px 'Sora',sans-serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
    .s-sub{{font-size:11px;color:var(--c)}}
    .s-logout{{color:#444;cursor:pointer;padding:4px;background:none;border:none;display:flex}}
    .s-logout:hover{{color:#888}}
    .s-logout svg{{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.6}}
    .main{{flex:1;overflow-y:auto;padding:24px}}
    .container{{max-width:1100px;margin:0 auto}}
    /* Tabs (mobile) */
    .tabs{{display:none;gap:4px;margin-bottom:20px;border-bottom:1px solid #1a1a1a}}
    .tab-btn{{padding:12px 18px;background:transparent;border:none;color:#555;font:600 .9rem 'Sora',sans-serif;cursor:pointer;border-bottom:2px solid transparent;transition:all .2s}}
    .tab-btn.active{{color:#fff;border-bottom-color:var(--c)}}
    .tab-btn:hover:not(.active){{color:#888}}
    .tab-content{{display:none;opacity:0;transform:translateX(20px);transition:opacity .3s,transform .3s}}
    .tab-content.active{{display:block;opacity:1;transform:translateX(0)}}
    /* Header */
    header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px;flex-wrap:wrap;gap:12px}}
    .greet{{color:#aaa;font-size:.95rem}}
    .greet strong{{color:var(--c);font-size:1.15rem;font-weight:700}}
    .btn-add-main{{padding:10px 20px;background:var(--c);color:#000;border:none;border-radius:20px;font:600 .9rem 'Sora',sans-serif;cursor:pointer;display:flex;align-items:center;gap:6px;transition:transform .2s}}
    .btn-add-main:hover{{transform:scale(1.05)}}
    /* Trial banner */
    .trial-banner{{margin-top:10px;padding:10px 16px;background:var(--c-a);border:1px solid var(--c);border-radius:10px;font-size:.9rem;width:100%}}
    /* Cards */
    .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:24px}}
    .card{{animation:cFade .4s ease backwards}}
    @keyframes cFade{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
    .card:nth-child(1){{animation-delay:.05s}}.card:nth-child(2){{animation-delay:.1s}}
    .card:nth-child(3){{animation-delay:.15s}}.card:nth-child(4){{animation-delay:.2s}}
    .card.clickable{{cursor:pointer}}
    .card.clickable:hover{{border-color:var(--c);transform:translateY(-2px);box-shadow:0 4px 20px var(--c-a)}}
    .card.clickable:active{{transform:scale(.97)}}
    .card-hd{{display:flex;align-items:center;gap:14px;margin-bottom:4px}}
    .card-icon{{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;background:var(--c-a)}}
    .card-title{{font-size:.75rem;color:var(--c);text-transform:uppercase;letter-spacing:.5px;font-weight:500}}
    .card-val{{font-size:1.8rem;font-weight:700}}
    .card-sub{{font-size:.8rem;color:#444;margin-top:4px}}
    /* Section */
    .section{{background:#0a0a0a;border-radius:16px;padding:24px;margin-bottom:16px;border:1px solid #1a1a1a;overflow-x:auto}}
    .section-hd{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:10px}}
    .section-title{{font-size:1rem;font-weight:600;color:var(--c);display:flex;align-items:center;gap:8px}}
    table{{width:100%;border-collapse:collapse}}
    th{{text-align:left;padding:12px 10px;border-bottom:1px solid #1a1a1a;color:#555;font-size:.75rem;text-transform:uppercase;letter-spacing:.5px;font-weight:500}}
    td{{padding:12px 10px;border-bottom:1px solid #111;font-size:.85rem;color:#ccc}}
    tr:hover td{{background:rgba(255,255,255,.02)}}
    .cat-tag{{display:inline-block;padding:4px 10px;border-radius:100px;font-size:.75rem;background:var(--c-a);color:var(--c)}}
    .pay-tag{{display:inline-block;padding:4px 10px;border-radius:100px;font-size:.7rem;font-weight:600;text-transform:uppercase;background:#1a1a1a;color:#888}}
    .pay-pix{{background:rgba(34,197,94,.1);color:var(--c)}}
    .pay-à-vista{{background:rgba(74,222,128,.1);color:#4ade80}}
    .pay-cartão-parcelado{{background:rgba(245,158,11,.1);color:#f59e0b}}
    .pay-cartão-débito{{background:rgba(34,197,94,.1);color:var(--c)}}
    .pay-boleto{{background:rgba(107,114,128,.1);color:#6b7280}}
    .btn-del{{background:rgba(239,68,68,.1);border:none;color:#ef4444;padding:6px 10px;border-radius:8px;cursor:pointer;transition:background .2s}}
    .btn-del:hover{{background:rgba(239,68,68,.2)}}
    .btn-edt{{background:rgba(59,130,246,.1);border:none;color:#3b82f6;padding:6px 10px;border-radius:8px;cursor:pointer;transition:background .2s}}
    .btn-edt:hover{{background:rgba(59,130,246,.2)}}
    .btn-cl{{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:#ef4444;padding:8px 16px;border-radius:10px;cursor:pointer;font:.8rem 'Sora',sans-serif;font-weight:500}}
    .btn-cl:hover{{background:rgba(239,68,68,.2)}}
    .sem-dados{{text-align:center;padding:40px;color:#333}}
    /* Gráfico */
    .grafico-section{{background:#0a0a0a;border-radius:16px;padding:24px;margin-bottom:16px;border:1px solid #1a1a1a}}
    .grafico-hd{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:10px}}
    .grafico-title{{font-size:1rem;font-weight:600;color:var(--c)}}
    .filtro{{display:flex;gap:8px}}
    .filtro-btn{{padding:8px 16px;border:1px solid #222;background:transparent;color:#888;border-radius:100px;cursor:pointer;font:.8rem 'Sora',sans-serif;font-weight:500;transition:all .2s}}
    .filtro-btn.active{{background:#fff;color:#000;border-color:#fff}}
    .filtro-btn:hover:not(.active){{border-color:#444;color:#fff}}
    .grafico-container{{display:flex;gap:30px;align-items:center;flex-wrap:wrap}}
    .chart-wrap{{width:260px;height:260px;position:relative;flex-shrink:0}}
    .legend-item{{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #111}}
    .legend-lbl{{display:flex;align-items:center;gap:10px}}
    .legend-dot{{width:10px;height:10px;border-radius:3px}}
    .legend-val{{font-weight:600;color:var(--c)}}
    .legend-pct{{color:#555;font-size:.8rem;margin-left:8px}}
    /* Renda */
    .renda-box{{background:#0a0a0a;border-radius:16px;padding:24px;margin-bottom:16px;border:1px solid #1a1a1a}}
    .renda-topo{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px;flex-wrap:wrap;gap:8px}}
    .renda-lbl{{font-size:.75rem;color:var(--c);text-transform:uppercase;letter-spacing:.5px}}
    .renda-val{{font-size:1.8rem;font-weight:700;line-height:1}}
    .renda-bar{{width:100%;height:24px;background:#1a1a1a;border-radius:12px;overflow:hidden;position:relative;margin:10px 0}}
    .renda-fill{{height:100%;border-radius:12px;transition:width .6s ease;position:relative;min-width:4px}}
    .renda-pct{{position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.75rem;font-weight:700;color:#fff}}
    .renda-lbs{{display:flex;justify-content:space-between;font-size:.75rem;color:#444;margin-top:6px}}
    .renda-det{{display:flex;gap:24px;margin-top:14px;flex-wrap:wrap}}
    .renda-det-item{{display:flex;flex-direction:column;gap:2px}}
    .renda-det-lbl{{font-size:.7rem;color:#555;text-transform:uppercase}}
    .renda-det-val{{font-size:1rem;font-weight:700}}
    /* Gastos Fixos */
    .fixo-item{{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid #111}}
    .fixo-info{{display:flex;flex-direction:column;gap:4px}}
    .fixo-desc{{font-weight:600;color:#ccc}}
    .fixo-dia{{font-size:.8rem;color:#555}}
    .fixo-val{{font-weight:700;font-size:1rem}}
    /* Cores */
    .cores-grid{{display:flex;flex-wrap:wrap;gap:12px;padding:15px 0}}
    .cor-op{{display:flex;flex-direction:column;align-items:center;gap:6px;cursor:pointer;padding:10px;border-radius:12px;border:2px solid transparent;transition:all .2s}}
    .cor-op:hover{{background:rgba(255,255,255,.04)}}
    .cor-op.ativa{{border-color:var(--c);background:rgba(255,255,255,.04)}}
    .cor-bola{{width:36px;height:36px;border-radius:50%;border:2px solid rgba(255,255,255,.1);transition:transform .2s}}
    .cor-op:hover .cor-bola{{transform:scale(1.1)}}
    .cor-op.ativa .cor-bola{{border-color:#fff;box-shadow:0 0 10px var(--c)}}
    .cor-op span{{font-size:.7rem;color:#666}}
    .cor-op.ativa span{{color:var(--c);font-weight:600}}
    /* Modal List */
    .lista-modal .modal{{max-width:700px;width:95%;max-height:90vh;display:flex;flex-direction:column}}
    .lista-modal .modal h2{{justify-content:space-between}}
    .lista-body{{overflow-y:auto;max-height:55vh}}
    .lista-resumo{{display:flex;gap:20px;padding:14px 0;border-bottom:1px solid #1a1a1a;flex-wrap:wrap;margin-bottom:10px}}
    .lista-r-item{{display:flex;flex-direction:column;gap:4px}}
    .lista-r-lbl{{font-size:.75rem;color:#555;text-transform:uppercase}}
    .lista-r-val{{font-size:1.2rem;font-weight:700}}
    /* Modal Confirm */
    .modal-confirm .modal{{max-width:360px;text-align:center;padding:36px 30px}}
    .modal-confirm .modal h2{{font-size:1.2rem;margin-bottom:10px;justify-content:center}}
    .modal-confirm .modal p{{color:#666;font-size:.9rem;margin-bottom:0}}
    /* Calendar */
    .cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}}
    .cal-day-hd{{text-align:center;font-size:.7rem;color:#555;font-weight:600;text-transform:uppercase;padding:6px 0}}
    .cal-day{{background:#111;border-radius:10px;padding:8px 4px;text-align:center;border:1px solid #1a1a1a;min-height:68px;display:flex;flex-direction:column;justify-content:center;gap:3px}}
    .cal-day.hoje{{border-color:var(--c)}}
    .cal-day-num{{font-size:.85rem;font-weight:600}}
    .cal-saida{{font-size:.65rem;color:#ef4444;font-weight:600}}
    .cal-entrada{{font-size:.65rem;color:var(--c);font-weight:600}}
    /* Responsive */
    @media(max-width:768px){{
      .sidebar{{display:none}}.app{{display:block}}.main{{overflow-y:auto;height:100vh;padding:16px}}
      .tabs{{display:flex}}.tab-btn{{display:block}}
      .cards{{grid-template-columns:repeat(2,1fr);gap:8px}}
      .card-val{{font-size:1.2rem}}.form-row{{grid-template-columns:1fr}}
      .modal{{padding:20px;width:95%;max-height:85vh}}
      .modal-overlay{{align-items:flex-start;padding-top:20px}}
      .grafico-container{{flex-direction:column}}.chart-wrap{{width:100%;max-width:220px;height:220px;margin:0 auto}}
    }}
  </style>
</head>
<body>
<div class="app">
  <!-- Sidebar -->
  <div class="sidebar">
    <div class="sidebar-hd">
      <span class="logo-m">Money </span><span class="logo-x">X</span>
    </div>
    <nav class="sidebar-nav">
      <div class="s-section">
        <div class="s-label">Principal</div>
        <button class="s-item active" onclick="switchTab('dashboard')">
          <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          <span>Dashboard</span>
        </button>
        <button class="s-item" onclick="switchTab('financeiro')">
          <svg viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>
          <span>Financeiro</span>
        </button>
      </div>
      <div class="s-section">
        <div class="s-label">Conta</div>
        <button class="s-item" onclick="switchTab('pessoal')">
          <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>Perfil</span>
        </button>
      </div>
    </nav>
    <div class="sidebar-ft">
      <div class="s-user">
        <div class="s-avatar">{{{{ session.username[:2].upper() }}}}</div>
        <div style="flex:1;min-width:0">
          <div class="s-name">{{{{ session.username }}}}</div>
          <div class="s-sub">Conta pessoal</div>
        </div>
        <a href="/logout" class="s-logout">
          <svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>
        </a>
      </div>
    </div>
  </div>

  <!-- Main -->
  <div class="main">
    <div class="container">
      <header>
        <p class="greet">Olá, <strong>{{{{ nome }}}}</strong></p>
        <button class="btn-add-main" onclick="abrirModal()">+ Adicionar</button>
        {{% if dias_restantes_trial <= 7 %}}
        <div class="trial-banner">
          ⏰ <strong style="color:var(--c)">Trial:</strong>
          {{% if dias_restantes_trial == 0 %}}<span style="color:var(--c)">Expira hoje!</span>
          {{% elif dias_restantes_trial == 1 %}}<span>Falta <strong style="color:var(--c)">1 dia</strong></span>
          {{% else %}}<span>Faltam <strong style="color:var(--c)">{{{{ dias_restantes_trial }}}} dias</strong></span>{{% endif %}}
        </div>
        {{% endif %}}
      </header>

      <!-- Mobile tabs -->
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('dashboard')">Dashboard</button>
        <button class="tab-btn" onclick="switchTab('financeiro')">Financeiro</button>
        <button class="tab-btn" onclick="switchTab('pessoal')">Perfil</button>
      </div>

      <!-- ===== ABA DASHBOARD ===== -->
      <div class="tab-content active" id="tab-dashboard">
        <div class="cards">
          <div class="card clickable" onclick="abrirLista('dia')">
            <div class="card-hd">
              <div class="card-icon">◎</div>
              <div><div class="card-title">Hoje</div><div class="card-val" id="total-dia">{{{{ "%.2f"|format(total_dia) }}}}</div></div>
            </div>
            <div class="card-sub">Dia {{{{ dia_hoje }}}}</div>
          </div>
          <div class="card clickable" onclick="abrirCalMes()">
            <div class="card-hd">
              <div class="card-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--c)" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="3"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/></svg></div>
              <div><div class="card-title">Este Mês</div><div class="card-val" id="total-mes">{{{{ "%.2f"|format(resumo_mensal.total_saidas) }}}}</div></div>
            </div>
            <div class="card-sub">{{{{ mes_nome }}}}</div>
          </div>
          <div class="card clickable" onclick="abrirCalAno()">
            <div class="card-hd">
              <div class="card-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--c)" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="3"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="7" y1="14" x2="17" y2="14"/><line x1="7" y1="18" x2="17" y2="18"/></svg></div>
              <div><div class="card-title">Este Ano</div><div class="card-val" id="total-ano">{{{{ "%.2f"|format(resumo_anual.total_saidas) }}}}</div></div>
            </div>
            <div class="card-sub">{{{{ ano_atual }}}}</div>
          </div>
          <div class="card">
            <div class="card-hd">
              <div class="card-icon">▲</div>
              <div><div class="card-title">Maior Gasto</div><div class="card-val" id="maior-gasto">{{{{ "%.2f"|format(resumo_mensal.maior_gasto) }}}}</div></div>
            </div>
            <div class="card-sub">Este mês</div>
          </div>
        </div>

        <!-- Gráfico -->
        <div class="grafico-section">
          <div class="grafico-hd">
            <div class="grafico-title">Gastos por Categoria</div>
            <div class="filtro">
              <button class="filtro-btn active" onclick="filtrarGrafico('mes',event)">Este Mês</button>
              <button class="filtro-btn" onclick="filtrarGrafico('ano',event)">Este Ano</button>
            </div>
          </div>
          <div class="grafico-container">
            <div class="chart-wrap"><canvas id="graficoPizza"></canvas></div>
            <div id="graficoLegend" style="flex:1;min-width:180px"></div>
          </div>
        </div>

        <!-- Gastos do dia -->
        <div class="section">
          <div class="section-hd">
            <div class="section-title">Gastos de Hoje</div>
            {{% if gastos_dia %}}<button class="btn-cl" onclick="deletarHoje()">Limpar Hoje</button>{{% endif %}}
          </div>
          {{% if gastos_dia %}}
          <table>
            <thead><tr><th>Data</th><th>Tipo</th><th>Descrição</th><th>Categoria</th><th>Pagamento</th><th>Valor</th><th></th></tr></thead>
            <tbody id="tabela-dia">
              {{% for g in gastos_dia %}}
              <tr>
                <td>{{{{ g.data }}}}</td>
                <td><span class="badge-{{{{ g.tipo or 'saida' }}}}">{{{{ 'Entrada' if g.tipo=='entrada' else 'Saída' }}}}</span></td>
                <td>{{{{ g.descricao }}}}</td>
                <td><span class="cat-tag">{{{{ g.categoria }}}}</span></td>
                <td><span class="pay-tag pay-{{{{ (g.forma_pagamento or '')|lower|replace(' ','-') }}}}">{{{{ g.forma_pagamento }}}}</span></td>
                <td class="valor-{{{{ g.tipo or 'saida' }}}}">R$ {{{{ "%.2f"|format(g.valor) }}}}</td>
                <td style="display:flex;gap:4px">
                  <button class="btn-edt" onclick="editarGasto({{{{ g.id }}}},'{{{{ g.descricao }}}}',{{{{ g.valor }}}},'{{{{ g.categoria }}}}','{{{{ g.forma_pagamento }}}}','{{{{ g.tipo or 'saida' }}}}','{{{{ g.data }}}}')">✏️</button>
                  <button class="btn-del" onclick="deletarGasto({{{{ g.id }}}})">🗑</button>
                </td>
              </tr>
              {{% endfor %}}
            </tbody>
          </table>
          {{% else %}}<div class="sem-dados">😴 Nenhum gasto hoje</div>{{% endif %}}
        </div>
      </div><!-- /tab-dashboard -->

      <!-- ===== ABA FINANCEIRO ===== -->
      <div class="tab-content" id="tab-financeiro">
        {{% if renda_maxima > 0 %}}
        {{% set gasto_liq = resumo_mensal.total_saidas - resumo_mensal.total_entradas %}}
        {{% set restante = renda_maxima - gasto_liq %}}
        {{% set pct = (gasto_liq / renda_maxima * 100) if renda_maxima > 0 else 0 %}}
        <div class="renda-box">
          <div class="renda-topo">
            <div><div class="renda-lbl">Renda Mensal</div><div class="renda-val">R$ {{{{ "%.2f"|format(renda_maxima) }}}}</div></div>
            <div style="text-align:right">
              <div class="renda-lbl">Restante</div>
              <div class="renda-val" id="renda-restante" style="color:{{% if restante < 0 %}}#ef4444{{% elif restante < renda_maxima * 0.2 %}}#f59e0b{{% else %}}var(--c){{% endif %}}">R$ {{{{ "%.2f"|format(restante) }}}}</div>
            </div>
          </div>
          <div class="renda-bar">
            <div class="renda-fill" id="renda-fill"
              style="width:{{{{ (pct if pct > 0 else 0) if pct < 100 else 100 }}}}%;background:{{% if pct > 80 or pct > 100 %}}#ef4444{{% elif pct > 50 %}}#f59e0b{{% else %}}var(--c){{% endif %}}">
              <span class="renda-pct">{{{{ "%.0f"|format(pct) }}}}%</span>
            </div>
          </div>
          <div class="renda-lbs"><span>R$ 0</span>{{% if pct > 100 %}}<span style="color:#ef4444">⚠️ Ultrapassou R$ {{{{ "%.2f"|format(-restante) }}}}</span>{{% endif %}}<span>R$ {{{{ "%.2f"|format(renda_maxima) }}}}</span></div>
          <div class="renda-det">
            <div class="renda-det-item"><span class="renda-det-lbl">Saídas</span><span class="renda-det-val valor-saida" id="renda-saidas">R$ {{{{ "%.2f"|format(resumo_mensal.total_saidas) }}}}</span></div>
            <div class="renda-det-item"><span class="renda-det-lbl">Entradas</span><span class="renda-det-val valor-entrada" id="renda-entradas">R$ {{{{ "%.2f"|format(resumo_mensal.total_entradas) }}}}</span></div>
            <div class="renda-det-item"><span class="renda-det-lbl">% Usado</span><span class="renda-det-val" id="renda-pct" style="color:{{% if pct > 80 %}}#ef4444{{% elif pct > 50 %}}#f59e0b{{% else %}}#00d4ff{{% endif %}}">{{{{ "%.1f"|format(pct) }}}}%</span></div>
          </div>
        </div>
        {{% else %}}
        <div class="section" style="text-align:center;padding:32px">
          <p style="color:var(--c);margin-bottom:16px">⚠️ Defina sua renda mensal para monitorar seus gastos</p>
          <button class="btn btn-primary" onclick="editarRenda()">Definir Renda</button>
        </div>
        {{% endif %}}
      </div><!-- /tab-financeiro -->

      <!-- ===== ABA PESSOAL ===== -->
      <div class="tab-content" id="tab-pessoal">
        <div class="section">
          <div class="section-hd">
            <div class="section-title">Gastos Fixos</div>
            <button class="btn btn-primary" style="padding:8px 16px;font-size:.85rem" onclick="abrirModalFixo()">+ Adicionar</button>
          </div>
          {{% if renda_maxima > 0 %}}
          <div style="margin-bottom:15px;padding:12px;background:rgba(0,212,255,.08);border-radius:10px;display:flex;justify-content:space-between;align-items:center">
            <span style="color:#aaa">Renda: <strong style="color:var(--c)">R$ {{{{ "%.2f"|format(renda_maxima) }}}}</strong></span>
            <button onclick="editarRenda()" style="background:none;border:1px solid rgba(255,255,255,.2);color:#aaa;padding:4px 12px;border-radius:6px;cursor:pointer;font:.8rem 'Sora',sans-serif">Editar</button>
          </div>
          {{% else %}}
          <div style="padding:12px;background:rgba(34,197,94,.08);border-radius:10px;text-align:center;margin-bottom:15px">
            <span style="color:var(--c)">⚠️ Defina sua renda mensal</span><br>
            <button onclick="editarRenda()" style="margin-top:8px;background:var(--c);border:none;color:#000;padding:10px 20px;border-radius:8px;cursor:pointer;font:700 .9rem 'Sora',sans-serif">Definir Renda</button>
          </div>
          {{% endif %}}

          {{% if gastos_fixos %}}
            {{% set ts = namespace(v=0) %}}{{% set te = namespace(v=0) %}}
            {{% for f in gastos_fixos %}}
              {{% if f.tipo == 'saida' %}}{{% set ts.v = ts.v + f.valor %}}{{% else %}}{{% set te.v = te.v + f.valor %}}{{% endif %}}
            <div class="fixo-item">
              <div class="fixo-info">
                <div class="fixo-desc"><span class="badge-{{{{ f.tipo or 'saida' }}}}">{{{{ 'Entrada' if f.tipo=='entrada' else 'Saída' }}}}</span> {{{{ f.descricao }}}}</div>
                <div class="fixo-dia">📅 Vence dia {{{{ f.dia_vencimento }}}}</div>
              </div>
              <div style="display:flex;align-items:center;gap:10px">
                <span class="fixo-val valor-{{{{ f.tipo or 'saida' }}}}">R$ {{{{ "%.2f"|format(f.valor) }}}}</span>
                <button class="btn-edt" onclick="editarFixo({{{{ f.id }}}},'{{{{ f.descricao }}}}',{{{{ f.valor }}}},'{{{{ f.tipo or 'saida' }}}}',{{{{ f.dia_vencimento }}}})">✏️</button>
                <button class="btn-del" onclick="deletarFixo({{{{ f.id }}}})">🗑</button>
              </div>
            </div>
            {{% endfor %}}
            <div style="margin-top:14px;padding-top:14px;border-top:2px solid rgba(255,255,255,.08);display:flex;justify-content:space-between">
              <span style="color:#aaa">Total Saídas Fixas</span>
              <strong class="valor-saida">R$ {{{{ "%.2f"|format(ts.v) }}}}</strong>
            </div>
            {{% if te.v > 0 %}}
            <div style="margin-top:8px;display:flex;justify-content:space-between">
              <span style="color:#aaa">Total Entradas Fixas</span>
              <strong class="valor-entrada">R$ {{{{ "%.2f"|format(te.v) }}}}</strong>
            </div>
            {{% endif %}}
          {{% else %}}<div class="sem-dados">📝 Nenhum gasto fixo</div>{{% endif %}}
        </div>

        <div class="section">
          <div class="section-hd"><div class="section-title">Configurações</div></div>
          <div class="fixo-item">
            <div class="fixo-info"><div class="fixo-desc">👤 Usuário</div><div class="fixo-dia" id="disp-username">{{{{ session.username }}}}</div></div>
            <button class="btn btn-primary" style="padding:8px 16px;font-size:.85rem" onclick="abrirPerfil()">Editar</button>
          </div>
          <div class="fixo-item">
            <div class="fixo-info"><div class="fixo-desc">📛 Nome</div><div class="fixo-dia" id="disp-nome">{{{{ nome }}}}</div></div>
          </div>
          <div class="fixo-item">
            <div class="fixo-info"><div class="fixo-desc">🎨 Cor de Destaque</div><div class="fixo-dia">Personalize a cor principal</div></div>
          </div>
          <div class="cores-grid">
            {{% for cor_item in [
              ['verde','#22c55e'],['azul','#3b82f6'],['roxo','#8b5cf6'],['rosa','#ec4899'],
              ['amarelo','#f59e0b'],['vermelho','#ef4444'],['cyan','#06b6d4'],['laranja','#f97316']
            ] %}}
            <div class="cor-op" data-cor="{{{{ cor_item[0] }}}}" onclick="mudarCor('{{{{ cor_item[0] }}}}')">
              <div class="cor-bola" style="background:{{{{ cor_item[1] }}}}"></div>
              <span>{{{{ cor_item[0]|capitalize }}}}</span>
            </div>
            {{% endfor %}}
          </div>
        </div>
      </div><!-- /tab-pessoal -->
    </div><!-- /container -->
  </div><!-- /main -->
</div><!-- /app -->

<!-- ===== MODAIS ===== -->
<!-- Adicionar -->
<div class="modal-overlay" id="mAdicionar">
  <div class="modal">
    <h2>Nova Movimentação</h2>
    <form id="fGasto">
      <div class="form-group"><label>Tipo</label><select id="g_tipo"><option value="saida">Saída (Gasto)</option><option value="entrada">Entrada (Receita)</option></select></div>
      <div class="form-group"><label>Descrição</label><input type="text" id="g_desc" placeholder="Ex: Almoço, Salário..." required></div>
      <div class="form-group"><label>Valor (R$)</label><input type="number" id="g_val" placeholder="0.00" step="0.01" min="0.01" required></div>
      <div class="form-group"><label>Data</label><input type="date" id="g_data"></div>
      <div class="form-row">
        <div class="form-group"><label>Categoria</label><select id="g_cat"><option>Alimentação</option><option>Transporte</option><option>Moradia</option><option>Saúde</option><option>Lazer</option><option>Educação</option><option>Vestuário</option><option>Tecnologia</option><option>Salário</option><option>Freelance</option><option>Investimento</option><option selected>Outros</option></select></div>
        <div class="form-group"><label>Pagamento</label><select id="g_pag"><option value="PIX">PIX</option><option value="À Vista">À Vista</option><option value="Cartão Parcelado">Parcelado</option><option value="Cartão Débito">Débito</option><option value="Boleto">Boleto</option></select></div>
      </div>
      <div class="modal-buttons">
        <button type="button" class="btn btn-secondary" onclick="closeModal('mAdicionar')">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</div>

<!-- Editar Gasto -->
<div class="modal-overlay" id="mEditar">
  <div class="modal">
    <h2>Editar Gasto</h2>
    <form id="fEditar">
      <input type="hidden" id="e_id">
      <div class="form-group"><label>Tipo</label><select id="e_tipo"><option value="saida">Saída</option><option value="entrada">Entrada</option></select></div>
      <div class="form-group"><label>Descrição</label><input type="text" id="e_desc" required></div>
      <div class="form-group"><label>Valor (R$)</label><input type="number" id="e_val" step="0.01" min="0.01" required></div>
      <div class="form-group"><label>Data</label><input type="date" id="e_data"></div>
      <div class="form-row">
        <div class="form-group"><label>Categoria</label><select id="e_cat"><option>Alimentação</option><option>Transporte</option><option>Moradia</option><option>Saúde</option><option>Lazer</option><option>Educação</option><option>Vestuário</option><option>Tecnologia</option><option>Salário</option><option>Freelance</option><option>Investimento</option><option>Outros</option></select></div>
        <div class="form-group"><label>Pagamento</label><select id="e_pag"><option value="PIX">PIX</option><option value="À Vista">À Vista</option><option value="Cartão Parcelado">Parcelado</option><option value="Cartão Débito">Débito</option><option value="Boleto">Boleto</option></select></div>
      </div>
      <div class="modal-buttons">
        <button type="button" class="btn btn-secondary" onclick="closeModal('mEditar')">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</div>

<!-- Gasto Fixo -->
<div class="modal-overlay" id="mFixo">
  <div class="modal">
    <h2>Novo Gasto Fixo</h2>
    <form id="fFixo">
      <div class="form-group"><label>Tipo</label><select id="f_tipo"><option value="saida">Saída</option><option value="entrada">Entrada</option></select></div>
      <div class="form-group"><label>Descrição</label><input type="text" id="f_desc" placeholder="Ex: Aluguel, Salário..." required></div>
      <div class="form-row">
        <div class="form-group"><label>Valor (R$)</label><input type="number" id="f_val" step="0.01" min="0.01" required></div>
        <div class="form-group"><label>Dia Vencimento</label><input type="number" id="f_dia" min="1" max="31" value="1"></div>
      </div>
      <div class="modal-buttons">
        <button type="button" class="btn btn-secondary" onclick="closeModal('mFixo')">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</div>

<!-- Editar Fixo -->
<div class="modal-overlay" id="mEditarFixo">
  <div class="modal">
    <h2>Editar Gasto Fixo</h2>
    <form id="fEditarFixo">
      <input type="hidden" id="ef_id">
      <div class="form-group"><label>Tipo</label><select id="ef_tipo"><option value="saida">Saída</option><option value="entrada">Entrada</option></select></div>
      <div class="form-group"><label>Descrição</label><input type="text" id="ef_desc" required></div>
      <div class="form-row">
        <div class="form-group"><label>Valor (R$)</label><input type="number" id="ef_val" step="0.01" min="0.01" required></div>
        <div class="form-group"><label>Dia Vencimento</label><input type="number" id="ef_dia" min="1" max="31" required></div>
      </div>
      <div class="modal-buttons">
        <button type="button" class="btn btn-secondary" onclick="closeModal('mEditarFixo')">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</div>

<!-- Renda -->
<div class="modal-overlay" id="mRenda">
  <div class="modal" style="max-width:400px">
    <h2>Renda Mensal</h2>
    <form id="fRenda">
      <div class="form-group"><label>Sua renda mensal (R$)</label><input type="number" id="r_val" placeholder="0.00" step="0.01" min="0" required></div>
      <div class="modal-buttons">
        <button type="button" class="btn btn-secondary" onclick="closeModal('mRenda')">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</div>

<!-- Perfil -->
<div class="modal-overlay" id="mPerfil">
  <div class="modal" style="max-width:420px">
    <h2>Editar Perfil</h2>
    <form id="fPerfil">
      <div class="form-group"><label>Usuário</label><input type="text" id="p_user" required></div>
      <div class="form-group"><label>Nome</label><input type="text" id="p_nome"></div>
      <div class="form-group"><label>Email</label><input type="email" id="p_email"></div>
      <div class="modal-buttons">
        <button type="button" class="btn btn-secondary" onclick="closeModal('mPerfil')">Cancelar</button>
        <button type="submit" class="btn btn-primary">Salvar</button>
      </div>
    </form>
  </div>
</div>

<!-- Lista Período -->
<div class="modal-overlay lista-modal" id="mLista">
  <div class="modal">
    <h2><span id="lista-titulo">Gastos</span><button class="modal-close-btn" onclick="closeModal('mLista')">✕</button></h2>
    <div class="lista-resumo">
      <div class="lista-r-item"><span class="lista-r-lbl">Saídas</span><span class="lista-r-val valor-saida" id="l-saidas">R$ 0,00</span></div>
      <div class="lista-r-item"><span class="lista-r-lbl">Entradas</span><span class="lista-r-val valor-entrada" id="l-entradas">R$ 0,00</span></div>
      <div class="lista-r-item"><span class="lista-r-lbl">Registros</span><span class="lista-r-val" id="l-qtd">0</span></div>
    </div>
    <div class="lista-body"><table><thead><tr><th>Data</th><th>Tipo</th><th>Descrição</th><th>Categoria</th><th>Valor</th><th></th></tr></thead><tbody id="l-tbody"></tbody></table></div>
  </div>
</div>

<!-- Calendário Mês -->
<div class="modal-overlay lista-modal" id="mCalMes">
  <div class="modal" style="max-width:800px">
    <h2>
      <span id="calmes-titulo">📅 Calendário</span>
      <div style="display:flex;gap:8px;align-items:center">
        <button onclick="baixarPDF('mes')" id="btn-pdf-mes"
          style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:var(--c);color:#000;border:none;border-radius:8px;font:.8rem 'Sora',sans-serif;font-weight:700;cursor:pointer;transition:all .2s">
          ⬇ PDF Mês
        </button>
        <button class="modal-close-btn" onclick="closeModal('mCalMes')">✕</button>
      </div>
    </h2>
    <div id="calmes-grid" class="cal-grid"></div>
  </div>
</div>

<!-- Calendário Ano -->
<div class="modal-overlay lista-modal" id="mCalAno">
  <div class="modal" style="max-width:900px">
    <h2>
      <span id="calano-titulo">📊 Ano</span>
      <div style="display:flex;gap:8px;align-items:center">
        <button onclick="baixarPDF('ano')" id="btn-pdf-ano"
          style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:var(--c);color:#000;border:none;border-radius:8px;font:.8rem 'Sora',sans-serif;font-weight:700;cursor:pointer;transition:all .2s">
          ⬇ PDF Ano
        </button>
        <button class="modal-close-btn" onclick="closeModal('mCalAno')">✕</button>
      </div>
    </h2>
    <div style="width:100%;height:260px;margin-bottom:20px"><canvas id="graficoAno"></canvas></div>
    <div id="calano-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px"></div>
  </div>
</div>

<!-- Confirmar Ação -->
<div class="modal-overlay modal-confirm" id="mConfirm">
  <div class="modal">
    <h2 style="justify-content:center">Confirmar</h2>
    <p id="confirm-msg" style="color:#666;font-size:.9rem;margin-bottom:0"></p>
    <div class="modal-buttons">
      <button class="btn btn-secondary" onclick="closeModal('mConfirm')">Cancelar</button>
      <button class="btn btn-danger" id="confirm-btn">Confirmar</button>
    </div>
  </div>
</div>

<script>
// ── Utilidades ──────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const fmt = v => 'R$ ' + v.toFixed(2).replace('.',',');

function toast(msg, tipo='sucesso') {{
  const t = document.createElement('div');
  t.className = 'toast ' + tipo;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}}

async function api(url, method='GET', body=null) {{
  const opts = {{ method, headers: body ? {{'Content-Type':'application/json'}} : {{}} }};
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  return r.json();
}}

function openModal(id) {{ $(id).classList.add('active'); }}
function closeModal(id) {{ $(id).classList.remove('active'); }}

// Fecha modal clicando fora
document.querySelectorAll('.modal-overlay').forEach(o =>
  o.addEventListener('click', e => {{ if(e.target===o) o.classList.remove('active'); }})
);
document.addEventListener('keydown', e => {{
  if(e.key==='Escape') document.querySelectorAll('.modal-overlay.active').forEach(o=>o.classList.remove('active'));
}});

// ── Tabs ────────────────────────────────────────────────────────────────────
const TAB_ORDER = ['dashboard','financeiro','pessoal'];
let currentTab = 'dashboard';

function switchTab(tab) {{
  if(tab===currentTab) return;
  const old = $('tab-'+currentTab);
  const nw  = $('tab-'+tab);
  old.classList.remove('active');
  setTimeout(() => {{ nw.classList.add('active'); }}, 50);
  currentTab = tab;
  document.querySelectorAll('.tab-btn,.s-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => {{
    if(b.textContent.toLowerCase().includes(tab==='dashboard'?'dash':tab==='financeiro'?'financ':'perfil'))
      b.classList.add('active');
  }});
  document.querySelectorAll('.s-item').forEach(b => {{
    const t = b.textContent.trim().toLowerCase();
    if((tab==='dashboard'&&t==='dashboard')||(tab==='financeiro'&&t==='financeiro')||(tab==='pessoal'&&t==='perfil'))
      b.classList.add('active');
  }});
}}

// ── Animação de valores ──────────────────────────────────────────────────────
function animVal(id, end, dur=700) {{
  const el = $(id); if(!el) return;
  const start = parseFloat(el.textContent.replace(',','.')) || 0;
  const t0 = performance.now();
  function up(t) {{
    const p = Math.min((t-t0)/dur,1);
    const v = start + (end-start)*(1-Math.pow(1-p,3));
    el.textContent = v.toFixed(2).replace('.',',');
    if(p<1) requestAnimationFrame(up);
  }}
  requestAnimationFrame(up);
}}
// Animação inicial
window.addEventListener('load',() => {{
  ['total-dia','total-mes','total-ano','maior-gasto'].forEach(id => {{
    const el = $(id); if(!el) return;
    const end = parseFloat(el.textContent.replace(',','.')) || 0;
    el.textContent = '0,00';
    animVal(id, end);
  }});
}});

// ── Adicionar Gasto ─────────────────────────────────────────────────────────
function abrirModal() {{
  $('g_data').value = new Date().toISOString().split('T')[0];
  openModal('mAdicionar');
  setTimeout(()=>$('g_desc').focus(),100);
}}

$('fGasto').addEventListener('submit', async e => {{
  e.preventDefault();
  const d = await api('/api/adicionar','POST',{{
    descricao: $('g_desc').value, valor: +$('g_val').value,
    categoria: $('g_cat').value, forma_pagamento: $('g_pag').value,
    tipo: $('g_tipo').value, data: $('g_data').value || null
  }});
  if(d.sucesso) {{ toast(d.mensagem); closeModal('mAdicionar'); $('fGasto').reset(); location.reload(); }}
  else toast(d.erro,'erro');
}});

// ── Deletar ─────────────────────────────────────────────────────────────────
function confirmar(msg, cb) {{
  $('confirm-msg').textContent = msg;
  $('confirm-btn').onclick = () => {{ closeModal('mConfirm'); cb(); }};
  openModal('mConfirm');
}}

async function deletarGasto(id) {{
  confirmar('Deletar este gasto?', async () => {{
    const d = await api('/api/deletar/'+id,'DELETE');
    if(d.sucesso) {{ toast(d.mensagem); location.reload(); }}
    else toast(d.erro,'erro');
  }});
}}

async function deletarHoje() {{
  confirmar('Deletar TODOS os gastos de hoje?', async () => {{
    const d = await api('/api/deletar_hoje','DELETE');
    if(d.sucesso) {{ toast(d.mensagem); location.reload(); }}
  }});
}}

// ── Editar Gasto ────────────────────────────────────────────────────────────
function editarGasto(id,desc,val,cat,pag,tipo,data) {{
  $('e_id').value=id; $('e_tipo').value=tipo; $('e_desc').value=desc;
  $('e_val').value=val; $('e_data').value=data;
  $('e_cat').value=cat||'Outros'; $('e_pag').value=pag||'PIX';
  openModal('mEditar');
}}

$('fEditar').addEventListener('submit', async e => {{
  e.preventDefault();
  const id = $('e_id').value;
  const d = await api('/api/editar/'+id,'PUT',{{
    descricao:$('e_desc').value, valor:+$('e_val').value,
    categoria:$('e_cat').value, forma_pagamento:$('e_pag').value,
    tipo:$('e_tipo').value, data:$('e_data').value||null
  }});
  if(d.sucesso) {{ toast('Gasto atualizado!'); closeModal('mEditar'); location.reload(); }}
  else toast(d.erro,'erro');
}});

// ── Gastos Fixos ────────────────────────────────────────────────────────────
function abrirModalFixo() {{ openModal('mFixo'); setTimeout(()=>$('f_desc').focus(),100); }}

$('fFixo').addEventListener('submit', async e => {{
  e.preventDefault();
  const d = await api('/api/gastos_fixos','POST',{{
    descricao:$('f_desc').value, valor:+$('f_val').value,
    tipo:$('f_tipo').value, dia_vencimento:+$('f_dia').value||1
  }});
  if(d.sucesso) {{ toast('Fixo adicionado!'); closeModal('mFixo'); $('fFixo').reset(); location.reload(); }}
  else toast(d.erro,'erro');
}});

function editarFixo(id,desc,val,tipo,dia) {{
  $('ef_id').value=id; $('ef_tipo').value=tipo; $('ef_desc').value=desc;
  $('ef_val').value=val; $('ef_dia').value=dia;
  openModal('mEditarFixo');
}}

$('fEditarFixo').addEventListener('submit', async e => {{
  e.preventDefault();
  const id = $('ef_id').value;
  const d = await api('/api/editar_fixo/'+id,'PUT',{{
    descricao:$('ef_desc').value, valor:+$('ef_val').value,
    tipo:$('ef_tipo').value, dia_vencimento:+$('ef_dia').value
  }});
  if(d.sucesso) {{ toast('Fixo atualizado!'); closeModal('mEditarFixo'); location.reload(); }}
  else toast(d.erro,'erro');
}});

async function deletarFixo(id) {{
  confirmar('Remover gasto fixo?', async () => {{
    const d = await api('/api/gastos_fixos','DELETE',{{id}});
    if(d.sucesso) {{ toast('Removido!'); location.reload(); }}
    else toast(d.erro,'erro');
  }});
}}

// ── Renda ────────────────────────────────────────────────────────────────────
function editarRenda() {{ openModal('mRenda'); setTimeout(()=>$('r_val').focus(),100); }}
$('fRenda').addEventListener('submit', async e => {{
  e.preventDefault();
  const d = await api('/api/renda_maxima','POST',{{renda_maxima:+$('r_val').value}});
  if(d.sucesso) {{ toast('Renda atualizada!'); closeModal('mRenda'); location.reload(); }}
  else toast(d.erro,'erro');
}});

// ── Perfil ───────────────────────────────────────────────────────────────────
async function abrirPerfil() {{
  const u = await api('/api/perfil');
  $('p_user').value=u.username||''; $('p_nome').value=u.nome||''; $('p_email').value=u.email||'';
  openModal('mPerfil'); setTimeout(()=>$('p_user').focus(),100);
}}
$('fPerfil').addEventListener('submit', async e => {{
  e.preventDefault();
  const d = await api('/api/perfil','POST',{{
    username:$('p_user').value.trim(), nome:$('p_nome').value.trim(), email:$('p_email').value.trim()
  }});
  if(d.ok||d.sucesso) {{ toast('Perfil atualizado!'); closeModal('mPerfil'); location.reload(); }}
  else toast(d.erro,'erro');
}});

// ── Gráfico Pizza ────────────────────────────────────────────────────────────
let pizzaChart = null;
const CORES_CAT = {{
  'Alimentação':'#ef4444','Transporte':'#4ade80','Moradia':'#22c55e',
  'Saúde':'#06b6d4','Lazer':'#f59e0b','Educação':'#3b82f6',
  'Vestuário':'#ec4899','Tecnologia':'#8b5cf6','Outros':'#9ca3af'
}};

async function carregarGrafico(periodo) {{
  const dados = await api('/api/grafico/'+periodo);
  if(dados.erro||!dados.categorias?.length) {{ $('graficoLegend').innerHTML='<p style="color:#333;text-align:center;padding:20px">Sem dados</p>'; return; }}
  const ctx = $('graficoPizza').getContext('2d');
  if(pizzaChart) pizzaChart.destroy();
  pizzaChart = new Chart(ctx,{{
    type:'doughnut',
    data:{{
      labels:dados.categorias.map(c=>c.nome),
      datasets:[{{
        data:dados.categorias.map(c=>c.valor),
        backgroundColor:dados.categorias.map(c=>CORES_CAT[c.nome]||'#9ca3af'),
        borderWidth:0,hoverOffset:8
      }}]
    }},
    options:{{
      responsive:true,maintainAspectRatio:true,cutout:'60%',
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'#0a0a0a',titleColor:'#fff',bodyColor:'#fff',padding:12,cornerRadius:8,
          callbacks:{{label:c=>`R$ ${{c.raw.toFixed(2).replace('.',',')}} (${{((c.raw/dados.total)*100).toFixed(1)}}%)`}}
        }}
      }}
    }}
  }});
  $('graficoLegend').innerHTML = dados.categorias.map(c => {{
    const pct=((c.valor/dados.total)*100).toFixed(1);
    return `<div class="legend-item">
      <div class="legend-lbl"><div class="legend-dot" style="background:${{CORES_CAT[c.nome]||'#9ca3af'}}"></div><span>${{c.nome}}</span></div>
      <div><span class="legend-val">${{fmt(c.valor)}}</span><span class="legend-pct">(${{pct}}%)</span></div>
    </div>`;
  }}).join('');
}}

function filtrarGrafico(periodo, ev) {{
  document.querySelectorAll('.filtro-btn').forEach(b=>b.classList.remove('active'));
  ev.target.classList.add('active');
  carregarGrafico(periodo);
}}
carregarGrafico('mes');

// ── Lista Período ────────────────────────────────────────────────────────────
const TITULOS = {{dia:'Gastos de Hoje',mes:'Gastos do Mês',ano:'Gastos do Ano'}};
async function abrirLista(periodo) {{
  $('lista-titulo').textContent = TITULOS[periodo] || 'Gastos';
  $('l-saidas').textContent = '...'; $('l-entradas').textContent = '...'; $('l-qtd').textContent = '...';
  $('l-tbody').innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:#444">Carregando...</td></tr>';
  openModal('mLista');
  const d = await api('/api/gastos_periodo/'+periodo);
  if(d.erro) {{ toast(d.erro,'erro'); return; }}
  $('l-saidas').textContent = fmt(d.total_saidas);
  $('l-entradas').textContent = fmt(d.total_entradas);
  $('l-qtd').textContent = d.gastos.length;
  $('l-tbody').innerHTML = d.gastos.length
    ? d.gastos.map(g => {{
        const t=g.tipo||'saida';
        return `<tr>
          <td>${{g.data}}</td>
          <td><span class="badge-${{t}}">${{t==='entrada'?'Entrada':'Saída'}}</span></td>
          <td>${{g.descricao}}</td>
          <td><span class="cat-tag">${{g.categoria||''}}</span></td>
          <td class="valor-${{t}}">${{fmt(g.valor)}}</td>
          <td style="display:flex;gap:4px">
            <button class="btn-edt" onclick="editarGasto(${{g.id}},'${{g.descricao}}',${{g.valor}},'${{g.categoria||''}}','${{g.forma_pagamento||''}}','${{t}}','${{g.data}}')">✏️</button>
            <button class="btn-del" onclick="deletarGastoLista(${{g.id}},'${{periodo}}')">🗑</button>
          </td>
        </tr>`;
      }}).join('')
    : '<tr><td colspan="6" style="text-align:center;padding:20px;color:#555">Nenhum registro</td></tr>';
}}

async function deletarGastoLista(id, periodo) {{
  confirmar('Deletar este registro?', async () => {{
    const d = await api('/api/deletar/'+id,'DELETE');
    if(d.sucesso) {{ toast(d.mensagem); abrirLista(periodo); }}
    else toast(d.erro,'erro');
  }});
}}

// ── Calendário Mês ───────────────────────────────────────────────────────────
async function abrirCalMes() {{
  const hoje = new Date();
  const meses = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
  $('calmes-titulo').textContent = '📅 ' + meses[hoje.getMonth()] + ' ' + hoje.getFullYear();
  $('calmes-grid').innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:#444">Carregando...</div>';
  openModal('mCalMes');
  const d = await api('/api/calendario_mes');
  if(d.erro) {{ toast(d.erro,'erro'); return; }}
  const dias = ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
  const primeiro = new Date(d.ano, d.mes-1, 1).getDay();
  let html = dias.map(ds=>`<div class="cal-day-hd">${{ds}}</div>`).join('');
  for(let i=0;i<primeiro;i++) html += '<div></div>';
  d.dias.forEach(dia => {{
    const isHoje = dia.dia===hoje.getDate();
    html += `<div class="cal-day${{isHoje?' hoje':''}}">
      <div class="cal-day-num">${{dia.dia}}</div>
      ${{dia.saidas>0?`<div class="cal-saida">-${{dia.saidas.toFixed(0)}}</div>`:''}}
      ${{dia.entradas>0?`<div class="cal-entrada">+${{dia.entradas.toFixed(0)}}</div>`:''}}
    </div>`;
  }});
  $('calmes-grid').innerHTML = html;
}}

// ── Calendário Ano ───────────────────────────────────────────────────────────
let anoChart = null;
async function abrirCalAno() {{
  const hoje = new Date();
  $('calano-titulo').textContent = '📊 Resumo de ' + hoje.getFullYear();
  $('calano-grid').innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:#444">Carregando...</div>';
  openModal('mCalAno');
  const d = await api('/api/calendario_ano');
  if(d.erro) {{ toast(d.erro,'erro'); return; }}
  $('calano-grid').innerHTML = d.meses.map(m => {{
    const saldo = m.entradas-m.saidas;
    return `<div style="background:#111;border-radius:12px;padding:14px;border:1px solid #1a1a1a">
      <div style="font-weight:600;margin-bottom:8px">${{m.mes_nome}}</div>
      <div style="display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:4px"><span style="color:#666">Saídas</span><span style="color:#ef4444">R$ ${{m.saidas.toFixed(2).replace('.',',')}}</span></div>
      <div style="display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:8px"><span style="color:#666">Entradas</span><span style="color:var(--c)">R$ ${{m.entradas.toFixed(2).replace('.',',')}}</span></div>
      <div style="font-weight:700;font-size:.85rem;padding-top:6px;border-top:1px solid #222;color:${{saldo>=0?'var(--c)':'#ef4444'}}">Saldo: R$ ${{saldo.toFixed(2).replace('.',',')}}</div>
    </div>`;
  }}).join('');
  const ctx = $('graficoAno').getContext('2d');
  if(anoChart) anoChart.destroy();
  anoChart = new Chart(ctx, {{
    type:'bar',
    data:{{
      labels:d.meses.map(m=>m.mes_nome.slice(0,3)),
      datasets:[
        {{label:'Saídas',data:d.meses.map(m=>m.saidas),backgroundColor:'rgba(239,68,68,.7)',borderRadius:4}},
        {{label:'Entradas',data:d.meses.map(m=>m.entradas),backgroundColor:'rgba(34,197,94,.7)',borderRadius:4}}
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{labels:{{color:'#888',font:{{family:'Sora',size:11}}}}}},
        tooltip:{{backgroundColor:'#0a0a0a',titleColor:'#fff',bodyColor:'#fff',
          callbacks:{{label:c=>`${{c.dataset.label}}: R$ ${{c.raw.toFixed(2).replace('.',',')}}`}}
        }}
      }},
      scales:{{
        x:{{ticks:{{color:'#555',font:{{family:'Sora',size:10}}}},grid:{{color:'rgba(255,255,255,.03)'}}}},
        y:{{ticks:{{color:'#555',font:{{family:'Sora',size:10}},callback:v=>'R$ '+v}},grid:{{color:'rgba(255,255,255,.05)'}}}}
      }}
    }}
  }});
}}

// ── Cores ────────────────────────────────────────────────────────────────────
async function mudarCor(nome) {{
  const d = await api('/api/cor_destaque','POST',{{cor:nome}});
  if(d.sucesso||d.ok) {{
    document.documentElement.style.setProperty('--c', d.cor);
    document.documentElement.style.setProperty('--c-rgb', d.rgb);
    document.documentElement.style.setProperty('--c-a', `rgba(${{d.rgb}},.15)`);
    document.querySelectorAll('.cor-op').forEach(el=>el.classList.remove('ativa'));
    document.querySelector(`[data-cor="${{nome}}"]`)?.classList.add('ativa');
    toast('Cor atualizada!');
  }}
}}

async function carregarCor() {{
  const d = await api('/api/cor_destaque');
  if(d.cor_hex) {{
    document.documentElement.style.setProperty('--c', d.cor_hex);
    document.documentElement.style.setProperty('--c-rgb', d.cor_rgb);
    document.documentElement.style.setProperty('--c-a', `rgba(${{d.cor_rgb}},.15)`);
    document.querySelectorAll('.cor-op').forEach(el=>el.classList.remove('ativa'));
    document.querySelector(`[data-cor="${{d.cor_nome}}"]`)?.classList.add('ativa');
  }}
}}
carregarCor();

// ── Auto-update ──────────────────────────────────────────────────────────────
async function autoUpdate() {{
  try {{
    const d = await api('/api/dados');
    if(d.erro) return;
    $('total-dia').textContent = d.total_dia.toFixed(2).replace('.',',');
    $('total-mes').textContent = d.resumo_mensal.total_saidas.toFixed(2).replace('.',',');
    $('total-ano').textContent = d.resumo_anual.total_saidas.toFixed(2).replace('.',',');
    $('maior-gasto').textContent = d.resumo_mensal.maior_gasto.toFixed(2).replace('.',',');
  }} catch(e) {{ console.error(e); }}
}}
setInterval(autoUpdate, 15000);

// ── Download PDF ─────────────────────────────────────────────────
async function baixarPDF(periodo) {{
  const btnId = periodo === 'mes' ? 'btn-pdf-mes' : 'btn-pdf-ano';
  const btn   = $(btnId);
  const orig  = btn.innerHTML;
  btn.innerHTML = '⏳ Gerando...';
  btn.disabled  = true;

  try {{
    const resp = await fetch('/api/pdf/' + periodo);
    if (!resp.ok) {{
      const err = await resp.json();
      toast(err.erro || 'Erro ao gerar PDF', 'erro');
      return;
    }}
    // trigger download
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    const cd   = resp.headers.get('Content-Disposition') || '';
    const match = cd.match(/filename="(.+)"/);
    a.download = match ? match[1] : `extrato_${{periodo}}.pdf`;
    a.href = url;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast('PDF gerado com sucesso!', 'sucesso');
  }} catch (e) {{
    toast('Erro: ' + e.message, 'erro');
  }} finally {{
    btn.innerHTML = orig;
    btn.disabled  = false;
  }}
}}

</script>
</body>
</html>"""



# ==============================================================
# GERADOR DE PDF
# ==============================================================

def _cor_hex_to_reportlab(hex_cor: str):
    """Converte cor hex para objeto Color do ReportLab."""
    hex_cor = hex_cor.lstrip('#')
    r, g, b = int(hex_cor[0:2],16)/255, int(hex_cor[2:4],16)/255, int(hex_cor[4:6],16)/255
    return colors.Color(r, g, b)


def gerar_pdf_periodo(usuario_id: int, periodo: str, renda_mensal: float, cor_hex: str) -> bytes:
    """Gera PDF de extrato do período (mes ou ano). Retorna bytes."""
    buf = io.BytesIO()

    hoje = agora().date()
    meses_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

    if periodo == "mes":
        titulo_periodo = f"{meses_pt[hoje.month-1]} {hoje.year}"
        di = f"{hoje.year}-{hoje.month:02d}-01"
        df = None
    else:
        titulo_periodo = str(hoje.year)
        di = f"{hoje.year}-01-01"
        df = None

    gastos = listar_gastos(usuario_id, data_inicio=di, data_fim=df)
    res    = resumo(usuario_id, periodo)
    cfg    = get_config(usuario_id)
    cor_rl = _cor_hex_to_reportlab(cfg["cor_hex"])

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title=f"Extrato {titulo_periodo}"
    )

    styles = getSampleStyleSheet()
    cor_branca  = colors.white
    cor_cinza   = colors.Color(0.12, 0.12, 0.12)
    cor_fundo   = colors.Color(0.06, 0.06, 0.06)
    cor_borda   = colors.Color(0.15, 0.15, 0.15)
    cor_vermelho = colors.Color(0.94, 0.27, 0.27)
    cor_verde    = colors.Color(0.13, 0.77, 0.37)

    # (estilos de cabeçalho definidos abaixo junto ao bloco de header)
    s_label  = ParagraphStyle("label", fontSize=7, textColor=colors.Color(0.4,0.4,0.4),
                               fontName="Helvetica", spaceBefore=0, spaceAfter=1,
                               alignment=TA_LEFT)
    s_valor  = ParagraphStyle("valor", fontSize=13, textColor=cor_branca,
                               fontName="Helvetica-Bold", alignment=TA_LEFT)
    s_secao  = ParagraphStyle("secao", fontSize=9, textColor=cor_rl,
                               fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
                               alignment=TA_LEFT)
    s_cell   = ParagraphStyle("cell", fontSize=8, textColor=colors.Color(0.8,0.8,0.8),
                               fontName="Helvetica", leading=10)
    s_cell_r = ParagraphStyle("cell_r", fontSize=8, textColor=colors.Color(0.8,0.8,0.8),
                               fontName="Helvetica", leading=10, alignment=TA_RIGHT)

    story = []

    # ── Cabeçalho ─────────────────────────────────────────────────
    from reportlab.platypus import KeepTogether

    s_logo_nome = ParagraphStyle("logo_nome", fontSize=24, textColor=cor_rl,
                                  fontName="Helvetica-Bold", leading=28, alignment=TA_LEFT,
                                  spaceAfter=2)
    s_logo_tag  = ParagraphStyle("logo_tag", fontSize=8, textColor=colors.Color(0.4,0.4,0.4),
                                  fontName="Helvetica", leading=12, alignment=TA_LEFT,
                                  spaceAfter=0)
    s_extrato_t = ParagraphStyle("extrato_t", fontSize=9, textColor=colors.Color(0.45,0.45,0.45),
                                  fontName="Helvetica", leading=12, alignment=TA_RIGHT,
                                  spaceAfter=2)
    s_periodo_t = ParagraphStyle("periodo_t", fontSize=17, textColor=cor_branca,
                                  fontName="Helvetica-Bold", leading=20, alignment=TA_RIGHT,
                                  spaceAfter=0)

    # Largura útil da página
    page_w = A4[0] - 3*cm  # descontando margens

    # Cabeçalho: tabela simples com 1 linha, 2 células (sem listas aninhadas)
    hdr_data = [[
        Paragraph("Money X  <font size='8' color='#666666'>Controle Financeiro</font>", s_logo_nome),
        Paragraph(f"EXTRATO<br/><font size='17' color='#ffffff'><b>{titulo_periodo}</b></font>", s_extrato_t),
    ]]
    t_hdr = Table(hdr_data, colWidths=[page_w * 0.55, page_w * 0.45])
    t_hdr.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 0),
    ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=2, color=cor_rl, spaceAfter=14))

    # ── Cards de resumo ───────────────────────────────────────────
    saldo_liq = res["total_entradas"] - res["total_saidas"]

    def fmt_brl(v):
        return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

    cards_data = [
        [
            Paragraph("TOTAL SAÍDAS",   s_label),
            Paragraph("TOTAL ENTRADAS", s_label),
            Paragraph("SALDO LÍQUIDO",  s_label),
            Paragraph("MAIOR GASTO",    s_label),
        ],
        [
            Paragraph(fmt_brl(res["total_saidas"]),   ParagraphStyle("v_saida", parent=s_valor, textColor=cor_vermelho)),
            Paragraph(fmt_brl(res["total_entradas"]), ParagraphStyle("v_ent",   parent=s_valor, textColor=cor_verde)),
            Paragraph(fmt_brl(saldo_liq),             ParagraphStyle("v_saldo", parent=s_valor,
                                                        textColor=cor_verde if saldo_liq >= 0 else cor_vermelho)),
            Paragraph(fmt_brl(res["maior_gasto"]),    s_valor),
        ],
    ]
    t_cards = Table(cards_data, colWidths=["25%","25%","25%","25%"])
    t_cards.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,-1), cor_cinza),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[cor_cinza]),
        ("BOX",         (0,0),(-1,-1), 0.5, cor_borda),
        ("INNERGRID",   (0,0),(-1,-1), 0.5, cor_borda),
        ("TOPPADDING",  (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING", (0,0),(-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("ROUNDEDCORNERS", (0,0),(-1,-1), 6),
    ]))
    story.append(t_cards)

    # ── Barra de renda (só se configurada) ───────────────────────
    if renda_mensal > 0 and periodo == "mes":
        story.append(Spacer(1, 10))
        pct = min((res["total_saidas"] / renda_mensal * 100), 100)
        cor_barra = cor_vermelho if pct > 80 else (colors.Color(0.96,0.62,0.04) if pct > 50 else cor_verde)

        renda_data = [[
            Paragraph("RENDA MENSAL", s_label),
            Paragraph("GASTO LÍQUIDO", s_label),
            Paragraph("RESTANTE", s_label),
            Paragraph(f"USO  {pct:.0f}%", s_label),
        ],[
            Paragraph(fmt_brl(renda_mensal), s_valor),
            Paragraph(fmt_brl(res["total_saidas"]-res["total_entradas"]),
                      ParagraphStyle("gl", parent=s_valor, textColor=cor_vermelho)),
            Paragraph(fmt_brl(renda_mensal - (res["total_saidas"]-res["total_entradas"])),
                      ParagraphStyle("rest", parent=s_valor,
                                     textColor=cor_verde if renda_mensal > res["total_saidas"] else cor_vermelho)),
            Paragraph(f"{'▓'*int(pct//5)}{'░'*int((100-pct)//5)}", 
                      ParagraphStyle("bar", fontSize=9, textColor=cor_barra,
                                     fontName="Helvetica", alignment=TA_LEFT)),
        ]]
        t_renda = Table(renda_data, colWidths=["25%","25%","25%","25%"])
        t_renda.setStyle(TableStyle([
            ("BACKGROUND",  (0,0),(-1,-1), cor_cinza),
            ("BOX",         (0,0),(-1,-1), 0.5, cor_borda),
            ("INNERGRID",   (0,0),(-1,-1), 0.5, cor_borda),
            ("TOPPADDING",  (0,0),(-1,-1), 8),
            ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("LEFTPADDING", (0,0),(-1,-1), 10),
            ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ]))
        story.append(t_renda)

    # ── Categorias ────────────────────────────────────────────────
    if res["categorias"]:
        story.append(Paragraph("GASTOS POR CATEGORIA", s_secao))
        cat_data = [[
            Paragraph("CATEGORIA", ParagraphStyle("th",parent=s_cell,textColor=colors.Color(0.4,0.4,0.4),fontName="Helvetica-Bold")),
            Paragraph("TOTAL",     ParagraphStyle("th",parent=s_cell_r,textColor=colors.Color(0.4,0.4,0.4),fontName="Helvetica-Bold")),
            Paragraph("%",         ParagraphStyle("th",parent=s_cell_r,textColor=colors.Color(0.4,0.4,0.4),fontName="Helvetica-Bold")),
        ]]
        total_saidas = res["total_saidas"] or 1
        for cat in res["categorias"]:
            pct_cat = cat["total"] / total_saidas * 100
            cat_data.append([
                Paragraph(cat["nome"], s_cell),
                Paragraph(fmt_brl(cat["total"]), ParagraphStyle("cr",parent=s_cell_r,textColor=cor_vermelho)),
                Paragraph(f"{pct_cat:.1f}%", s_cell_r),
            ])
        t_cat = Table(cat_data, colWidths=["60%","25%","15%"])
        t_cat.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  colors.Color(0.1,0.1,0.1)),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [cor_cinza, colors.Color(0.09,0.09,0.09)]),
            ("BOX",           (0,0),(-1,-1), 0.5, cor_borda),
            ("LINEBELOW",     (0,0),(-1,-2), 0.3, cor_borda),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ]))
        story.append(t_cat)

    # ── Lista de transações ───────────────────────────────────────
    story.append(Paragraph("TRANSAÇÕES", s_secao))

    th_style = ParagraphStyle("th2", parent=s_cell,
                               textColor=colors.Color(0.4,0.4,0.4), fontName="Helvetica-Bold")
    rows = [[
        Paragraph("DATA",       th_style),
        Paragraph("TIPO",       th_style),
        Paragraph("DESCRIÇÃO",  th_style),
        Paragraph("CATEGORIA",  th_style),
        Paragraph("PAGAMENTO",  th_style),
        Paragraph("VALOR",      ParagraphStyle("thr",parent=th_style,alignment=TA_RIGHT)),
    ]]

    for g in gastos:
        tipo   = g.get("tipo","saida")
        is_ent = tipo == "entrada"
        cor_v  = cor_verde if is_ent else cor_vermelho
        sinal  = "+" if is_ent else "-"
        rows.append([
            Paragraph(g["data"],                    s_cell),
            Paragraph("Entrada" if is_ent else "Saída",
                      ParagraphStyle("ct",parent=s_cell,textColor=cor_v)),
            Paragraph((g["descricao"] or "")[:40],  s_cell),
            Paragraph(g.get("categoria","") or "",  s_cell),
            Paragraph(g.get("forma_pagamento","") or "", s_cell),
            Paragraph(f"{sinal} {fmt_brl(g['valor'])}",
                      ParagraphStyle("vr",parent=s_cell_r,textColor=cor_v)),
        ])

    if len(rows) == 1:
        rows.append([Paragraph("Nenhuma transação no período", s_cell),"","","","",""])

    t_tx = Table(rows, colWidths=["13%","10%","27%","16%","16%","18%"])
    t_tx.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  colors.Color(0.1,0.1,0.1)),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [cor_cinza, colors.Color(0.09,0.09,0.09)]),
        ("BOX",           (0,0),(-1,-1), 0.5, cor_borda),
        ("LINEBELOW",     (0,0),(-1,-2), 0.3, cor_borda),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ]))
    story.append(t_tx)

    # ── Rodapé ────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=cor_borda))
    story.append(Paragraph(
        f"Gerado em {agora().strftime('%d/%m/%Y %H:%M')} · Money X",
        ParagraphStyle("footer", fontSize=7, textColor=colors.Color(0.3,0.3,0.3),
                       fontName="Helvetica", alignment=TA_RIGHT, spaceBefore=4)
    ))

    doc.build(story)
    return buf.getvalue()


# ==============================================================
# FLASK APP
# ==============================================================

# ============================================================
# App factory
# ============================================================

def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32))

    # ---------- Decorators ----------
    def login_required(f):
        @wraps(f)
        def deco(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if trial_expirado(session["user_id"]):
                return redirect(url_for("trial_page"))
            return f(*args, **kwargs)
        return deco

    def api_login_required(f):
        @wraps(f)
        def deco(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"erro": "Não autenticado"}), 401
            return f(*args, **kwargs)
        return deco

    uid = lambda: session["user_id"]

    # ============================================================
    # Auth
    # ============================================================

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        erro = None
        if request.method == "POST":
            res = verificar_login(
                request.form.get("username", "").strip(),
                request.form.get("senha", ""),
            )
            if res["ok"]:
                session.update(user_id=res["user_id"],
                               username=res["username"], nome=res["nome"])
                return redirect(url_for("dashboard"))
            erro = res["erro"]
        return render_template_string(LOGIN_HTML, erro=erro)

    @app.route("/registro", defaults={"token": None}, methods=["GET", "POST"])
    @app.route("/registro/<token>", methods=["GET", "POST"])
    def registro(token):
        token = token or request.args.get("token", "").strip()
        res_token = validar_convite(token)
        if not res_token["valido"]:
            return render_template_string(REGISTRO_ERRO_HTML, erro=res_token["erro"])
        dias = res_token["dias_trial"]
        erro = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email    = request.form.get("email", "").strip()
            senha    = request.form.get("senha", "")
            nome     = request.form.get("nome", "").strip()
            if not (username and email and senha):
                erro = "Todos os campos são obrigatórios"
            elif len(senha) < 4:
                erro = "Senha deve ter pelo menos 4 caracteres"
            else:
                res = criar_usuario(username, email, senha, nome, dias)
                if res["ok"]:
                    usar_convite(token)
                    session.update(user_id=res["user_id"],
                                   username=username, nome=nome or username)
                    return redirect(url_for("dashboard"))
                erro = res["erro"]
        return render_template_string(REGISTRO_HTML, erro=erro, dias_trial=dias, token=token)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/trial-expirado")
    def trial_page():
        return render_template_string(TRIAL_EXPIRADO_HTML)

    # ============================================================
    # Dashboard
    # ============================================================

    @app.route("/")
    @login_required
    def dashboard():
        u = uid()
        cfg      = get_config(u)
        res_mes  = resumo(u, "mes")
        res_ano  = resumo(u, "ano")
        hoje     = gastos_hoje(u)
        fixos    = listar_fixos(u)
        dias     = dias_trial_restantes(u)
        data_br  = agora()
        meses_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        total_dia    = sum(g["valor"] for g in hoje if g.get("tipo","saida") == "saida")
        total_dia_e  = sum(g["valor"] for g in hoje if g.get("tipo") == "entrada")
        return render_template_string(
            DASHBOARD_HTML,
            nome=session.get("nome", session.get("username")),
            gastos_dia=hoje,
            total_dia=total_dia,
            total_dia_entradas=total_dia_e,
            resumo_mensal=res_mes,
            resumo_anual=res_ano,
            renda_maxima=cfg["renda_mensal"],
            gastos_fixos=fixos,
            dias_restantes_trial=dias,
            dia_hoje=data_br.day,
            mes_nome=meses_pt[data_br.month - 1],
            ano_atual=data_br.year,
            atualizado_em=data_br.strftime("%d/%m/%Y %H:%M:%S"),
            cor_destaque=cfg["cor_hex"],
            session=session,
        )

    # ============================================================
    # APIs — Gastos
    # ============================================================

    @app.route("/api/dados")
    @api_login_required
    def api_dados():
        u = uid()
        cfg     = get_config(u)
        hoje    = gastos_hoje(u)
        rm      = resumo(u, "mes")
        ra      = resumo(u, "ano")
        return jsonify({
            "gastos_dia":    [{"indice": i, **g} for i, g in enumerate(hoje)],
            "total_dia":     sum(g["valor"] for g in hoje if g.get("tipo","saida") == "saida"),
            "total_dia_e":   sum(g["valor"] for g in hoje if g.get("tipo") == "entrada"),
            "resumo_mensal": rm,
            "resumo_anual":  ra,
            "ultimos_gastos": listar_gastos(u, limite=10),
            "renda_maxima":  cfg["renda_mensal"],
            "atualizado_em": agora().strftime("%d/%m/%Y %H:%M:%S"),
        })

    @app.route("/api/adicionar", methods=["POST"])
    @api_login_required
    def api_adicionar():
        d = request.json or {}
        descricao = d.get("descricao", "").strip()
        try:
            valor = float(d.get("valor", 0))
        except (ValueError, TypeError):
            return jsonify({"erro": "Valor inválido"}), 400
        if not descricao or valor <= 0:
            return jsonify({"erro": "Descrição e valor são obrigatórios"}), 400
        tipo = d.get("tipo", "saida")
        gid  = adicionar_gasto(uid(), descricao, valor,
                               d.get("categoria", "Outros"),
                               d.get("forma_pagamento", "Não Informado"),
                               tipo, d.get("data"))
        label = "Entrada" if tipo == "entrada" else "Saída"
        return jsonify({"sucesso": True,
                        "mensagem": f"{label} '{descricao}' (R$ {valor:.2f}) adicionado",
                        "gasto_id": gid})

    @app.route("/api/deletar/<int:gasto_id>", methods=["DELETE"])
    @api_login_required
    def api_deletar(gasto_id):
        if deletar_gasto(gasto_id, uid()):
            return jsonify({"sucesso": True, "mensagem": "Gasto removido"})
        return jsonify({"erro": "Gasto não encontrado"}), 404

    @app.route("/api/editar/<int:gasto_id>", methods=["PUT"])
    @api_login_required
    def api_editar(gasto_id):
        d = request.json or {}
        if editar_gasto(gasto_id, uid(), **d):
            return jsonify({"sucesso": True, "mensagem": "Gasto atualizado"})
        return jsonify({"erro": "Gasto não encontrado"}), 404

    @app.route("/api/deletar_hoje", methods=["DELETE"])
    @api_login_required
    def api_deletar_hoje():
        n = deletar_gastos_hoje(uid())
        return jsonify({"sucesso": True, "mensagem": f"{n} gastos removidos"})

    @app.route("/api/grafico/<periodo>")
    @api_login_required
    def api_grafico(periodo):
        r = resumo(uid(), periodo)
        return jsonify({"categorias": [{"nome": c["nome"], "valor": c["total"]}
                                       for c in r["categorias"]],
                        "total": r["total_saidas"], "periodo": periodo})

    @app.route("/api/gastos_periodo/<periodo>")
    @api_login_required
    def api_gastos_periodo(periodo):
        hoje = agora().date()
        if periodo == "dia":
            di, df = hoje.isoformat(), hoje.isoformat()
        elif periodo == "mes":
            di, df = f"{hoje.year}-{hoje.month:02d}-01", None
        elif periodo == "ano":
            di, df = f"{hoje.year}-01-01", None
        else:
            return jsonify({"erro": "Período inválido"}), 400
        gastos = listar_gastos(uid(), data_inicio=di, data_fim=df)
        saidas   = [g for g in gastos if g.get("tipo","saida") == "saida"]
        entradas = [g for g in gastos if g.get("tipo") == "entrada"]
        return jsonify({
            "gastos": gastos,
            "saidas": saidas, "entradas": entradas,
            "total_saidas":   sum(g["valor"] for g in saidas),
            "total_entradas": sum(g["valor"] for g in entradas),
            "periodo": periodo,
        })

    # ============================================================
    # APIs — Configurações
    # ============================================================

    @app.route("/api/renda_maxima", methods=["GET", "POST"])
    @api_login_required
    def api_renda():
        if request.method == "POST":
            try:
                renda = float((request.json or {}).get("renda_maxima", 0))
            except (ValueError, TypeError):
                return jsonify({"erro": "Valor inválido"}), 400
            if renda < 0:
                return jsonify({"erro": "Valor inválido"}), 400
            salvar_renda(uid(), renda)
            return jsonify({"sucesso": True, "renda_maxima": renda})
        return jsonify({"renda_maxima": get_config(uid())["renda_mensal"]})

    @app.route("/api/cor_destaque", methods=["GET", "POST"])
    @api_login_required
    def api_cor():
        if request.method == "POST":
            cor_nome = (request.json or {}).get("cor", "verde")
            return jsonify(salvar_cor(uid(), cor_nome))
        return jsonify(get_config(uid()) | {"sucesso": True})

    @app.route("/api/perfil", methods=["GET", "POST"])
    @api_login_required
    def api_perfil():
        if request.method == "GET":
            return jsonify(get_usuario(uid()))
        d = request.json or {}
        username = d.get("username", "").strip()
        if not username:
            return jsonify({"erro": "Nome de usuário é obrigatório"}), 400
        res = atualizar_perfil(uid(), username, d.get("nome","").strip(),
                               d.get("email","").strip())
        if res["ok"]:
            session["username"] = username
            session["nome"] = d.get("nome","").strip() or username
        return jsonify(res if res["ok"] else (res, 400))

    # ============================================================
    # APIs — Gastos Fixos
    # ============================================================

    @app.route("/api/gastos_fixos", methods=["GET", "POST", "DELETE"])
    @api_login_required
    def api_gastos_fixos():
        u = uid()
        if request.method == "GET":
            fixos = listar_fixos(u)
            return jsonify({
                "fixos": fixos,
                "total_saidas":   sum(f["valor"] for f in fixos if f.get("tipo","saida") == "saida"),
                "total_entradas": sum(f["valor"] for f in fixos if f.get("tipo") == "entrada"),
            })
        if request.method == "POST":
            d = request.json or {}
            descricao = d.get("descricao", "").strip()
            try:
                valor = float(d.get("valor", 0))
            except (ValueError, TypeError):
                return jsonify({"erro": "Valor inválido"}), 400
            if not descricao or valor <= 0:
                return jsonify({"erro": "Descrição e valor são obrigatórios"}), 400
            fid = adicionar_fixo(u, descricao, valor,
                                 d.get("tipo", "saida"), int(d.get("dia_vencimento", 1)))
            return jsonify({"sucesso": True, "fixo_id": fid})
        # DELETE
        fid = (request.json or {}).get("id")
        if deletar_fixo(fid, u):
            return jsonify({"sucesso": True})
        return jsonify({"erro": "Gasto fixo não encontrado"}), 404

    @app.route("/api/editar_fixo/<int:fixo_id>", methods=["PUT"])
    @api_login_required
    def api_editar_fixo(fixo_id):
        d = request.json or {}
        if editar_fixo(fixo_id, uid(), **d):
            return jsonify({"sucesso": True, "mensagem": "Atualizado"})
        return jsonify({"erro": "Gasto fixo não encontrado"}), 404

    # ============================================================
    # APIs — Calendário
    # ============================================================

    @app.route("/api/calendario_mes")
    @api_login_required
    def api_cal_mes():
        return jsonify(calendario_mes(uid()))

    @app.route("/api/calendario_ano")
    @api_login_required
    def api_cal_ano():
        return jsonify(calendario_ano(uid()))

    # ============================================================
    # Painel Admin / Stats
    # ============================================================

    @app.route("/stats")
    def stats():
        data = stats_app()
        return render_template_string(STATS_HTML,
                                      convites=listar_convites(),
                                      request=request, **data)

    @app.route("/api/convites/gerar", methods=["POST"])
    def api_gerar_convite():
        d = request.get_json() or {}
        return jsonify(gerar_convite(d.get("dias_trial", 30),
                                    d.get("max_usos", 1),
                                    d.get("expira_dias")))

    @app.route("/api/convites/desativar/<int:cid>", methods=["POST"])
    def api_desativar_convite(cid):
        desativar_convite(cid)
        return jsonify({"sucesso": True})

    @app.route("/api/usuarios/<int:usuario_id>/trial", methods=["POST"])
    def api_trial(usuario_id):
        dias = (request.get_json() or {}).get("dias", 30)
        return jsonify(atualizar_trial(usuario_id, dias))


    # ============================================================
    # PDF Export
    # ============================================================


    @app.route("/api/pdf/status")
    def api_pdf_status():
        """Diagnóstico do reportlab."""
        status = {"reportlab_ok": REPORTLAB_OK}
        try:
            import reportlab
            status["versao"] = reportlab.Version
        except Exception as e:
            status["erro_import"] = str(e)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            status["imports_ok"] = True
        except Exception as e:
            status["imports_ok"] = False
            status["erro_detalhe"] = str(e)
        return jsonify(status)

    @app.route("/api/pdf/<periodo>")
    @api_login_required
    def api_pdf(periodo):
        if periodo not in ("mes", "ano"):
            return jsonify({"erro": "Período inválido. Use 'mes' ou 'ano'"}), 400
        if not REPORTLAB_OK:
            return jsonify({"erro": "Biblioteca reportlab não instalada. Execute: pip install reportlab"}), 500
        try:
            u   = uid()
            cfg = get_config(u)
            pdf_bytes = gerar_pdf_periodo(u, periodo, cfg["renda_mensal"], cfg["cor_hex"])

            hoje = agora()
            meses_pt = ["jan","fev","mar","abr","mai","jun",
                        "jul","ago","set","out","nov","dez"]
            if periodo == "mes":
                nome_arquivo = f"extrato_{meses_pt[hoje.month-1]}_{hoje.year}.pdf"
            else:
                nome_arquivo = f"extrato_ano_{hoje.year}.pdf"

            resp = make_response(pdf_bytes)
            resp.headers["Content-Type"]        = "application/pdf"
            resp.headers["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
            return resp
        except Exception as e:
            return jsonify({"erro": f"Erro ao gerar PDF: {str(e)}"}), 500

    # ============================================================
    # Error handlers
    # ============================================================

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"erro": "Rota não encontrada"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"erro": str(e)}), 500

    return app


# ============================================================
# Entry point
# ============================================================

def main():
    porta = int(os.environ.get("PORT", 5000))
    if len(sys.argv) > 1:
        try:
            porta = int(sys.argv[1])
        except ValueError:
            pass

    init_db()
    print(f"""
╔══════════════════════════════════════════════╗
║   💸 Money X — Multi-usuário                ║
║   http://localhost:{porta:<26}║
╚══════════════════════════════════════════════╝
    """)
    app = create_app()
    app.run(host="0.0.0.0", port=porta, debug=False)


if __name__ == "__main__":
    main()
