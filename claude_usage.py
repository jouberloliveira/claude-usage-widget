#!/usr/bin/env python3
"""
Claude Usage Widget — zero external dependencies, Python 3.8+
Run: python3 claude_usage.py

Auth: uses the `sessionKey` cookie from a browser logged into claude.ai
to call the internal subscription endpoints. No Anthropic API key required.
"""
import errno
import http.server
import json
import sys
import threading
import urllib.error
import urllib.request
import webbrowser

PORT = 7432
CLAUDE_BASE = "https://claude.ai"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Claude Usage Widget</title>
<style>
  :root {
    --bg: #0f0f13;
    --card: #1a1a24;
    --border: #2a2a3a;
    --accent: #cc785c;
    --accent2: #7c6fcd;
    --text: #e8e8f0;
    --muted: #888;
    --green: #4caf7d;
    --yellow: #e0a84b;
    --red: #e05555;
    --radius: 12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; padding: 2rem 1rem; }
  h1 { text-align: center; font-size: 1.6rem; font-weight: 700; margin-bottom: .25rem; }
  h1 span { color: var(--accent); }
  .subtitle { text-align: center; color: var(--muted); font-size: .9rem; margin-bottom: 2rem; }

  .card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; max-width: 560px; margin: 0 auto 1.5rem; }
  label { display: block; font-size: .85rem; color: var(--muted); margin-bottom: .5rem; }
  .row { display: flex; gap: .75rem; }
  input[type=text], input[type=password] {
    flex: 1; background: #0f0f18; border: 1px solid var(--border); border-radius: 8px;
    color: var(--text); padding: .65rem 1rem; font-size: .95rem; outline: none;
    transition: border-color .2s;
  }
  input:focus { border-color: var(--accent2); }
  button {
    background: var(--accent); color: #fff; border: none; border-radius: 8px;
    padding: .65rem 1.4rem; font-size: .95rem; font-weight: 600; cursor: pointer;
    transition: opacity .2s;
  }
  button:hover { opacity: .85; }
  button:disabled { opacity: .4; cursor: not-allowed; }

  .help { font-size: .78rem; color: var(--muted); margin-top: .75rem; line-height: 1.5; }
  .help code { background: #0f0f18; padding: .1rem .35rem; border-radius: 4px; color: #c8c8d8; }
  .help ol { padding-left: 1.2rem; margin-top: .35rem; }

  #results { max-width: 560px; margin: 0 auto; }
  .section-title { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: .75rem; }

  .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; margin-bottom: 1.5rem; }
  .metric {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 1.1rem; position: relative; overflow: hidden;
  }
  .metric .label { font-size: .78rem; color: var(--muted); margin-bottom: .3rem; }
  .metric .value { font-size: 1.5rem; font-weight: 700; }
  .metric .sub { font-size: .78rem; color: var(--muted); margin-top: .2rem; }
  .metric .bar-wrap { height: 4px; background: var(--border); border-radius: 2px; margin-top: .75rem; }
  .metric .bar { height: 4px; border-radius: 2px; transition: width .6s ease; }

  .tier-badge {
    display: inline-block; padding: .2rem .7rem; border-radius: 20px; font-size: .75rem;
    font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
  }
  .tier-free { background: #2a2a2a; color: #999; }
  .tier-pro { background: #1e2a3a; color: #5a9fd4; }
  .tier-max5 { background: #2a1e3a; color: #a07cd4; }
  .tier-max20 { background: #3a1e2a; color: #d47ca0; }

  .info-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.25rem; margin-bottom: 1.5rem; }
  .info-row { display: flex; justify-content: space-between; align-items: center; padding: .45rem 0; border-bottom: 1px solid var(--border); font-size: .9rem; }
  .info-row:last-child { border-bottom: none; }
  .info-key { color: var(--muted); }
  .info-val { font-weight: 600; font-family: monospace; }

  .error { background: #2a1515; border: 1px solid #5a2020; border-radius: var(--radius); padding: 1rem 1.25rem; color: #e08080; font-size: .9rem; max-width: 560px; margin: 0 auto 1rem; }
  .spinner { text-align: center; padding: 2rem; color: var(--muted); font-size: .95rem; }

  .color-green { color: var(--green); }
  .color-yellow { color: var(--yellow); }
  .color-red { color: var(--red); }
  .bar-green { background: var(--green); }
  .bar-yellow { background: var(--yellow); }
  .bar-red { background: var(--red); }

  .refresh-btn { display: block; margin: 0 auto 2rem; background: transparent; border: 1px solid var(--border); color: var(--muted); font-size: .85rem; padding: .45rem 1.2rem; }
  .refresh-btn:hover { border-color: var(--accent2); color: var(--text); }

  .footnote { text-align: center; color: var(--muted); font-size: .78rem; margin-top: 2rem; }
</style>
</head>
<body>

<h1>Claude <span>Usage</span> Widget</h1>
<p class="subtitle">Monitore limites e gastos da sua subscription Pro/Max</p>

<div class="card">
  <label>Session Key (cookie <code>sessionKey</code> do claude.ai)</label>
  <div class="row">
    <input type="password" id="sessionKey" placeholder="sk-ant-sid01-..." autocomplete="off">
    <button id="checkBtn" onclick="checkUsage()">Verificar</button>
  </div>
  <div class="help">
    Como obter:
    <ol>
      <li>Faça login em <code>https://claude.ai</code></li>
      <li>Abra DevTools (F12) → <b>Application</b> → <b>Cookies</b> → <code>https://claude.ai</code></li>
      <li>Copie o valor do cookie <code>sessionKey</code> (começa com <code>sk-ant-sid01-</code>)</li>
    </ol>
    A chave fica apenas no <code>localStorage</code> do browser. Nada é enviado fora da sua máquina exceto para o próprio <code>claude.ai</code>.
  </div>
</div>

<div id="results"></div>

<p class="footnote">Dados obtidos via APIs internas de claude.ai · Auth por cookie de sessão</p>

<script>
let savedKey = localStorage.getItem('claude_session_key') || '';
if (savedKey) document.getElementById('sessionKey').value = savedKey;

function fmt(n) {
  if (n === null || n === undefined) return '—';
  if (n >= 1_000_000) return (n/1_000_000).toFixed(1)+'M';
  if (n >= 1_000) return (n/1_000).toFixed(0)+'K';
  return n.toString();
}

function pct(used, limit) {
  if (!limit) return 0;
  return Math.max(0, Math.min(100, Math.round((used / limit) * 100)));
}

function colorClass(p) {
  if (p < 60) return ['color-green', 'bar-green'];
  if (p < 85) return ['color-yellow', 'bar-yellow'];
  return ['color-red', 'bar-red'];
}

function fmtReset(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = Math.round((d - now) / 1000);
    if (diff <= 0) return 'agora';
    if (diff < 60) return diff+'s';
    if (diff < 3600) return Math.ceil(diff/60)+'min';
    if (diff < 86400) return Math.ceil(diff/3600)+'h';
    return d.toLocaleString('pt-BR', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
  } catch { return iso; }
}

function tierBadge(t) {
  if (!t) return '<span class="tier-badge tier-free">—</span>';
  const k = String(t).toLowerCase();
  if (k.includes('max') && k.includes('20')) return '<span class="tier-badge tier-max20">Max 20</span>';
  if (k.includes('max')) return '<span class="tier-badge tier-max5">Max 5</span>';
  if (k.includes('pro')) return '<span class="tier-badge tier-pro">Pro</span>';
  return '<span class="tier-badge tier-free">'+t+'</span>';
}

async function checkUsage() {
  const key = document.getElementById('sessionKey').value.trim();
  if (!key) { showError('Informe o sessionKey'); return; }
  localStorage.setItem('claude_session_key', key);

  const btn = document.getElementById('checkBtn');
  btn.disabled = true; btn.textContent = '...';
  document.getElementById('results').innerHTML = '<div class="spinner">Consultando claude.ai...</div>';

  try {
    const resp = await fetch('/api/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({sessionKey: key})
    });
    const data = await resp.json();
    if (data.error) { showError(data.error); return; }
    renderResults(data);
  } catch(e) {
    showError('Erro de conexão: ' + e.message);
  } finally {
    btn.disabled = false; btn.textContent = 'Verificar';
  }
}

function showError(msg) {
  document.getElementById('results').innerHTML = '<div class="error">⚠ ' + msg + '</div>';
}

function renderResults(d) {
  const org = d.organization || {};
  const buckets = d.usage_buckets || [];

  let html = `
  <div class="section-title">Organização</div>
  <div class="info-card">
    <div class="info-row"><span class="info-key">Nome</span><span class="info-val">${org.name || '—'}</span></div>
    <div class="info-row"><span class="info-key">Plano</span><span class="info-val">${tierBadge(org.tier)}</span></div>
    <div class="info-row"><span class="info-key">Org ID</span><span class="info-val">${(org.uuid || '').slice(0,8) || '—'}</span></div>
    <div class="info-row"><span class="info-key">Atualizado em</span><span class="info-val">${new Date().toLocaleTimeString('pt-BR')}</span></div>
  </div>`;

  if (buckets.length) {
    html += '<div class="section-title">Uso e Limites</div><div class="metric-grid">';
    for (const b of buckets) {
      const used = b.used ?? 0;
      const limit = b.limit ?? 0;
      const hasPct = typeof b.utilization === 'number';
      const p = hasPct ? Math.round(b.utilization) : pct(used, limit);
      const [cc, bc] = colorClass(p);
      const reset = fmtReset(b.resets_at);
      const valueDisplay = hasPct && !limit ? `${p}%` : fmt(used);
      const subDisplay = hasPct && !limit
        ? `${p}% utilizado`
        : `de ${fmt(limit)} ${b.unit || ''} · ${p}% usado`;
      html += `
      <div class="metric">
        <div class="label">${b.label}</div>
        <div class="value ${cc}">${valueDisplay}</div>
        <div class="sub">${subDisplay}</div>
        <div class="bar-wrap"><div class="bar ${bc}" style="width:${p}%"></div></div>
        <div class="sub" style="margin-top:.6rem">Reset em: ${reset}</div>
      </div>`;
    }
    html += '</div>';
  } else {
    const keys = (d.raw_keys && d.raw_keys.length) ? d.raw_keys.join(', ') : '(nenhuma)';
    html += `<div class="error">⚠ Sem dados de uso reconhecidos. Chaves retornadas pela API: <code style="background:#0f0f18;padding:.1rem .35rem;border-radius:4px">${keys}</code><br><br>Endpoint consultado: <code style="background:#0f0f18;padding:.1rem .35rem;border-radius:4px">${d.usage_path || '—'}</code>${d.warning ? '<br><br>'+d.warning : ''}</div>`;
  }

  if (d.raw_keys && d.raw_keys.length && buckets.length) {
    html += `<div class="section-title">Campos brutos detectados</div><div class="info-card">`;
    html += `<div class="info-row"><span class="info-key">keys</span><span class="info-val">${d.raw_keys.join(', ')}</span></div>`;
    html += '</div>';
  }

  html += `<button class="refresh-btn" onclick="checkUsage()">↻ Atualizar</button>`;
  document.getElementById('results').innerHTML = html;
}

if (savedKey) checkUsage();
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if self.path != "/api/check":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            body = {}
        session_key = (body.get("sessionKey") or "").strip()

        result = fetch_subscription_usage(session_key)
        payload = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _claude_request(path: str, session_key: str) -> dict:
    url = f"{CLAUDE_BASE}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Cookie": f"sessionKey={session_key}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Referer": f"{CLAUDE_BASE}/",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


_WINDOW_LABELS = {
    "five_hour": "Janela 5h",
    "seven_day": "Janela 7 dias",
    "seven_day_opus": "Opus · 7 dias",
    "seven_day_sonnet": "Sonnet · 7 dias",
    "seven_day_oauth_apps": "OAuth Apps · 7 dias",
    "seven_day_cowork": "Co-work · 7 dias",
    "seven_day_omelette": "Omelette · 7 dias",
    "tangelo": "Tangelo",
    "iguana_necktie": "Iguana Necktie",
    "omelette_promotional": "Omelette Promo",
    "extra_usage": "Uso Extra",
    "weekly": "Semanal",
    "daily": "Diário",
    "monthly": "Mensal",
    "hourly": "Hora",
}


def _label_for(name: str) -> str:
    base = name.replace("_limit_window", "").replace("_window", "")
    return _WINDOW_LABELS.get(base, base.replace("_", " ").title())


def _normalize_buckets(raw) -> list:
    """Map heterogeneous usage_limit shapes into a flat list of buckets.

    Supports:
      - list-shaped: usage_limits / limits / buckets / rate_limits
      - dict-shaped: same keys mapping name -> {used, limit, ...}
      - flat prefix pairs: {five_hour_used, five_hour_limit, ...}
      - claude.ai subscription shape: {five_hour_limit_window: {utilization, resets_at}, ...}
    """
    buckets = []
    if not isinstance(raw, dict):
        return buckets

    candidates = []
    for key in ("usage_limits", "limits", "buckets", "rate_limits"):
        v = raw.get(key)
        if isinstance(v, list):
            candidates.extend(v)
        elif isinstance(v, dict):
            for name, item in v.items():
                if isinstance(item, dict):
                    candidates.append({**item, "_name": name})

    for prefix in ("five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet",
                   "weekly", "daily", "monthly", "hourly"):
        used = raw.get(f"{prefix}_used") or raw.get(f"{prefix}_usage")
        limit = raw.get(f"{prefix}_limit")
        reset = raw.get(f"{prefix}_resets_at") or raw.get(f"{prefix}_reset_at")
        if used is not None or limit is not None:
            buckets.append({
                "label": _WINDOW_LABELS.get(prefix, prefix.title()),
                "used": used,
                "limit": limit,
                "resets_at": reset,
                "unit": "msgs",
            })

    # claude.ai subscription shape: *_limit_window: {utilization, resets_at}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        if not (k.endswith("_limit_window") or k.endswith("_window")):
            continue
        if "utilization" not in v and "resets_at" not in v and "used" not in v:
            continue
        utilization = v.get("utilization")
        used = v.get("used", v.get("usage"))
        limit = v.get("limit", v.get("max"))
        reset = v.get("resets_at") or v.get("reset_at")
        if utilization is not None and isinstance(utilization, (int, float)) and utilization <= 1:
            utilization = utilization * 100
        buckets.append({
            "label": _label_for(k),
            "used": used,
            "limit": limit,
            "utilization": utilization,
            "resets_at": reset,
            "unit": "msgs",
        })

    # claude.ai /usage shape: bare keys {utilization, resets_at}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        if k.endswith(("_limit_window", "_window")):
            continue
        if "utilization" not in v and "resets_at" not in v and "used" not in v:
            continue
        label = _label_for(k)
        if any(b["label"] == label for b in buckets):
            continue
        utilization = v.get("utilization")
        if utilization is not None and isinstance(utilization, (int, float)) and utilization <= 1:
            utilization = utilization * 100
        buckets.append({
            "label": label,
            "used": v.get("used", v.get("usage")),
            "limit": v.get("limit", v.get("max")),
            "utilization": utilization,
            "resets_at": v.get("resets_at") or v.get("reset_at"),
            "unit": "msgs",
        })

    for item in candidates:
        if not isinstance(item, dict):
            continue
        label = (
            item.get("label")
            or item.get("display_name")
            or item.get("name")
            or item.get("_name")
            or item.get("window")
            or "Limite"
        )
        used = item.get("used", item.get("usage", item.get("current")))
        limit = item.get("limit", item.get("max", item.get("cap")))
        reset = item.get("resets_at") or item.get("reset_at") or item.get("resets")
        utilization = item.get("utilization")
        if utilization is not None and isinstance(utilization, (int, float)) and utilization <= 1:
            utilization = utilization * 100
        unit = item.get("unit") or "msgs"
        buckets.append({
            "label": str(label).replace("_", " ").title(),
            "used": used,
            "limit": limit,
            "utilization": utilization,
            "resets_at": reset,
            "unit": unit,
        })

    return buckets


def fetch_subscription_usage(session_key: str) -> dict:
    if not session_key:
        return {"error": "sessionKey vazio."}
    if not session_key.startswith("sk-ant-sid"):
        return {"error": "sessionKey inválido. Deve começar com 'sk-ant-sid'."}

    try:
        orgs = _claude_request("/api/organizations", session_key)
    except urllib.error.HTTPError as e:
        return _http_error(e, "/api/organizations")
    except Exception as e:
        return {"error": f"Falha ao chamar /api/organizations: {e}"}

    if not isinstance(orgs, list) or not orgs:
        return {"error": "Nenhuma organização encontrada para esta sessão."}

    org = _pick_primary_org(orgs)
    org_id = org.get("uuid") or org.get("id")
    if not org_id:
        return {"error": "Resposta de /api/organizations sem uuid."}

    tier = (
        org.get("settings", {}).get("rate_limit_tier")
        if isinstance(org.get("settings"), dict) else None
    ) or org.get("rate_limit_tier") or org.get("subscription_tier") or org.get("tier")

    usage_paths = [
        f"/api/organizations/{org_id}/usage_limit",
        f"/api/organizations/{org_id}/usage",
        f"/api/organizations/{org_id}/rate_limits",
        f"/api/bootstrap/{org_id}/statsig",
        f"/api/account",
    ]
    usage_raw = None
    used_path = None
    last_err = None
    for p in usage_paths:
        try:
            usage_raw = _claude_request(p, session_key)
            used_path = p
            break
        except urllib.error.HTTPError as e:
            last_err = (p, e.code)
            continue
        except Exception as e:
            last_err = (p, str(e))
            continue

    buckets = _normalize_buckets(usage_raw) if usage_raw else []
    raw_keys = list(usage_raw.keys()) if isinstance(usage_raw, dict) else []

    return {
        "organization": {
            "uuid": org_id,
            "name": org.get("name"),
            "tier": tier,
        },
        "usage_buckets": buckets,
        "usage_path": used_path,
        "raw_keys": raw_keys,
        "warning": (
            f"Endpoint de uso indisponível (último erro: {last_err})."
            if not usage_raw else None
        ),
    }


def _pick_primary_org(orgs: list) -> dict:
    for o in orgs:
        caps = o.get("capabilities") or []
        if any("claude_pro" in c or "claude_max" in c or "chat" in c for c in caps):
            return o
    return orgs[0]


def _http_error(e: urllib.error.HTTPError, path: str) -> dict:
    body = ""
    try:
        body = e.read().decode(errors="replace")[:200]
    except Exception:
        pass
    if e.code in (401, 403):
        return {"error": f"sessionKey rejeitado por claude.ai ({e.code}). Refaça login e copie o cookie novamente."}
    return {"error": f"HTTP {e.code} em {path}: {body}"}


class ReusableHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True


def _bind_server(start_port: int, attempts: int = 11):
    for offset in range(attempts):
        port = start_port + offset
        try:
            server = ReusableHTTPServer(("127.0.0.1", port), Handler)
        except OSError as exc:
            if exc.errno in (errno.EADDRINUSE, errno.EACCES):
                continue
            raise
        if port != start_port:
            print(f"  ⚠ Porta {start_port} ocupada, usando {port}")
        return server, port
    return None, None


def main():
    server, port = _bind_server(PORT)
    if server is None:
        print(
            f"\n  ✗ Erro: nenhuma porta livre no intervalo {PORT}-{PORT + 10}.\n"
            f"  Encerre o processo que está usando a porta {PORT} e tente novamente.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    url = f"http://127.0.0.1:{port}"
    print(f"\n  Claude Usage Widget")
    print(f"  -------------------")
    print(f"  Abrindo {url}")
    print(f"  Ctrl+C para parar\n")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.")


if __name__ == "__main__":
    main()
