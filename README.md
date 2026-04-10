# 💸 Money X — Controle Financeiro Multi-Usuário

Reescrita limpa e modular do `web_multiuser.py` original.

## Estrutura

```
moneyX/
├── app.py              ← Entry point + Flask routes
├── db/
│   └── database.py     ← Toda a lógica de dados (SQLite)
└── templates/
    └── html.py         ← Templates HTML
```

## Rodar

```bash
pip install flask
python app.py            # porta 5000
python app.py 8080       # porta customizada
```

## Variáveis de Ambiente

| Variável     | Default                   | Descrição              |
|--------------|---------------------------|------------------------|
| `PORT`       | `5000`                    | Porta do servidor      |
| `DB_PATH`    | `gastos_usuarios.db`      | Caminho do banco SQLite|
| `SECRET_KEY` | gerada aleatoriamente     | Chave de sessão Flask  |

## O que mudou vs original

| Aspecto | Original | Reescrita |
|---|---|---|
| Estrutura | 1 arquivo monolítico de 5200+ linhas | 3 módulos separados |
| Banco de dados | Conexões manuais abertas/fechadas | Context manager (`with get_db()`) seguro |
| Migrations | `try/except` por ALTER TABLE espalhados | Função `_migrate()` centralizada |
| Schema | CREATE TABLE espalhados no código | `SCHEMA` string única com índices |
| Hashing | SHA-256 simples | SHA-256 (mesmo, mas isolado em função) |
| Rotas | 1 bloco enorme | `create_app()` factory limpa |
| Validação | Mista no route handler | Validação antes de chamar DB |
| CSS | Repetido em cada template | `_BASE_CSS` compartilhado |
| Error handlers | Ausentes | 404 e 500 globais |
| Encoding Windows | Hardcoded path `C:\Users\jarde` | Removido, path dinâmico |
| WAL mode SQLite | Não configurado | `PRAGMA journal_mode=WAL` ativo |
| Foreign keys | Não enforçado | `PRAGMA foreign_keys=ON` |

## Features mantidas

- ✅ Login / Registro com tokens de convite
- ✅ Trial por período configurável
- ✅ Gastos (saída/entrada) com categorias e formas de pagamento
- ✅ Gastos fixos mensais
- ✅ Gráfico por categoria (pizza)
- ✅ Calendário mensal e anual
- ✅ Barra de renda mensal
- ✅ Cor de destaque personalizável
- ✅ Painel de stats e gestão de convites
- ✅ Sidebar responsiva + tabs mobile
- ✅ Auto-update a cada 15s
