"""
Templates HTML do Money X
"""

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
    <h2><span id="calmes-titulo">📅 Calendário</span><button class="modal-close-btn" onclick="closeModal('mCalMes')">✕</button></h2>
    <div id="calmes-grid" class="cal-grid"></div>
  </div>
</div>

<!-- Calendário Ano -->
<div class="modal-overlay lista-modal" id="mCalAno">
  <div class="modal" style="max-width:900px">
    <h2><span id="calano-titulo">📊 Ano</span><button class="modal-close-btn" onclick="closeModal('mCalAno')">✕</button></h2>
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
</script>
</body>
</html>"""
