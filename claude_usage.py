#!/usr/bin/env python3
"""
Claude Usage Widget — zero external dependencies, Python 3.8+
Run: python3 claude_usage.py
"""
import http.server
import json
import os
import threading
import urllib.error
import urllib.request
import webbrowser
from urllib.parse import parse_qs, urlparse

PORT = 7432

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

  .model-select { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: 1rem; }
  .model-btn {
    background: #0f0f18; border: 1px solid var(--border); border-radius: 6px;
    color: var(--muted); padding: .35rem .85rem; font-size: .8rem; cursor: pointer;
    transition: all .15s;
  }
  .model-btn.active { border-color: var(--accent2); color: var(--text); background: #1e1e2e; }

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
  .tier-api { background: #1e3a2a; color: #5ad49f; }

  .reset-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.25rem; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem; }
  .reset-icon { font-size: 1.4rem; }
  .reset-label { font-size: .8rem; color: var(--muted); }
  .reset-value { font-size: 1rem; font-weight: 600; }

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
<p class="subtitle">Monitore limites e gastos da sua subscription em tempo real</p>

<div class="card">
  <label>Anthropic API Key</label>
  <div class="row">
    <input type="password" id="apiKey" placeholder="sk-ant-api03-..." autocomplete="off">
    <button id="checkBtn" onclick="checkUsage()">Verificar</button>
  </div>
  <div class="model-select" id="modelSelect">
    <span style="font-size:.8rem;color:var(--muted);line-height:2">Modelo:</span>
    <button class="model-btn active" data-model="claude-sonnet-4-5">Sonnet 4.5</button>
    <button class="model-btn" data-model="claude-opus-4-5">Opus 4.5</button>
    <button class="model-btn" data-model="claude-haiku-4-5-20251001">Haiku 4.5</button>
  </div>
</div>

<div id="results"></div>

<p class="footnote">Dados obtidos via headers de rate-limit da Anthropic API · Nenhuma chave é salva no servidor</p>

<script>
let savedKey = localStorage.getItem('claude_api_key') || '';
let selectedModel = 'claude-sonnet-4-5';
if (savedKey) document.getElementById('apiKey').value = savedKey;

document.querySelectorAll('.model-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedModel = btn.dataset.model;
  });
});

function fmt(n) {
  if (!n && n !== 0) return '—';
  if (n >= 1_000_000) return (n/1_000_000).toFixed(1)+'M';
  if (n >= 1_000) return (n/1_000).toFixed(0)+'K';
  return n.toString();
}

function pct(remaining, limit) {
  if (!limit) return 0;
  return Math.round(((limit - remaining) / limit) * 100);
}

function colorClass(used) {
  if (used < 60) return ['color-green', 'bar-green'];
  if (used < 85) return ['color-yellow', 'bar-yellow'];
  return ['color-red', 'bar-red'];
}

function detectTier(limits) {
  // Heuristic from public Anthropic rate-limit docs
  const rpm = limits.requestsPerMinute;
  const tpm = limits.tokensPerMinute;
  if (!rpm && !tpm) return {label:'Desconhecido', cls:'tier-free'};
  if (tpm >= 200_000) return {label:'Max 20', cls:'tier-max20'};
  if (tpm >= 40_000) return {label:'Max 5', cls:'tier-max5'};
  if (tpm >= 20_000) return {label:'Pro', cls:'tier-pro'};
  if (tpm >= 8_000) return {label:'Free', cls:'tier-free'};
  return {label:'API', cls:'tier-api'};
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
    return d.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'});
  } catch { return iso; }
}

async function checkUsage() {
  const key = document.getElementById('apiKey').value.trim();
  if (!key) { showError('Informe a API Key'); return; }
  localStorage.setItem('claude_api_key', key);

  const btn = document.getElementById('checkBtn');
  btn.disabled = true; btn.textContent = '...';
  document.getElementById('results').innerHTML = '<div class="spinner">Consultando API...</div>';

  try {
    const resp = await fetch('/api/check', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({key, model: selectedModel})
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
  const tier = detectTier(d.limits || {});
  const lim = d.limits || {};
  const rem = d.remaining || {};
  const resets = d.resets || {};

  function metric(label, used, remaining, limit, unit='tokens') {
    const p = pct(remaining, limit);
    const [cc, bc] = colorClass(p);
    return `
    <div class="metric">
      <div class="label">${label}</div>
      <div class="value ${cc}">${fmt(remaining)}</div>
      <div class="sub">de ${fmt(limit)} ${unit} · ${p}% usado</div>
      <div class="bar-wrap"><div class="bar ${bc}" style="width:${p}%"></div></div>
    </div>`;
  }

  let html = `
  <div class="section-title">Perfil da chave</div>
  <div class="info-card">
    <div class="info-row"><span class="info-key">Tier detectado</span><span class="info-val"><span class="tier-badge ${tier.cls}">${tier.label}</span></span></div>
    <div class="info-row"><span class="info-key">Modelo testado</span><span class="info-val">${d.model || selectedModel}</span></div>
    <div class="info-row"><span class="info-key">Input tokens usados</span><span class="info-val">${fmt(d.usage?.input_tokens)}</span></div>
    <div class="info-row"><span class="info-key">Output tokens usados</span><span class="info-val">${fmt(d.usage?.output_tokens)}</span></div>
    <div class="info-row"><span class="info-key">Atualizado em</span><span class="info-val">${new Date().toLocaleTimeString('pt-BR')}</span></div>
  </div>`;

  if (lim.tokensPerMinute || lim.requestsPerMinute) {
    html += '<div class="section-title">Limites por Minuto</div><div class="metric-grid">';
    if (lim.tokensPerMinute) html += metric('Tokens / min (restante)', pct(rem.tokensPerMinute, lim.tokensPerMinute), rem.tokensPerMinute, lim.tokensPerMinute);
    if (lim.requestsPerMinute) html += metric('Requests / min (restante)', pct(rem.requestsPerMinute, lim.requestsPerMinute), rem.requestsPerMinute, lim.requestsPerMinute, 'reqs');
    html += '</div>';
  }

  if (lim.tokensPerDay || lim.requestsPerDay) {
    html += '<div class="section-title">Limites Diários</div><div class="metric-grid">';
    if (lim.tokensPerDay) html += metric('Tokens / dia (restante)', pct(rem.tokensPerDay, lim.tokensPerDay), rem.tokensPerDay, lim.tokensPerDay);
    if (lim.requestsPerDay) html += metric('Requests / dia (restante)', pct(rem.requestsPerDay, lim.requestsPerDay), rem.requestsPerDay, lim.requestsPerDay, 'reqs');
    html += '</div>';
  }

  // resets
  const resetEntries = Object.entries(resets).filter(([,v])=>v);
  if (resetEntries.length) {
    html += `<div class="section-title">Próximos Resets</div><div class="info-card">`;
    for (const [k, v] of resetEntries) {
      const label = k.replace(/([A-Z])/g,' $1').toLowerCase();
      html += `<div class="info-row"><span class="info-key">${label}</span><span class="info-val">${fmtReset(v)}</span></div>`;
    }
    html += '</div>';
  }

  html += `<button class="refresh-btn" onclick="checkUsage()">↻ Atualizar</button>`;
  document.getElementById('results').innerHTML = html;
}

// auto-check if key saved
if (savedKey) checkUsage();
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # silence default logs

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
        body = json.loads(self.rfile.read(length))
        api_key = body.get("key", "")
        model = body.get("model", "claude-sonnet-4-5")

        result = call_anthropic(api_key, model)
        payload = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def call_anthropic(api_key: str, model: str) -> dict:
    """Make a minimal API call and extract rate-limit headers + usage."""
    req_body = json.dumps({
        "model": model,
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "hi"}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=req_body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )

    def parse_headers(resp_headers) -> dict:
        h = {}
        # rate limit headers
        mapping = {
            "anthropic-ratelimit-tokens-limit":         ("limits",    "tokensPerMinute"),
            "anthropic-ratelimit-tokens-remaining":     ("remaining", "tokensPerMinute"),
            "anthropic-ratelimit-tokens-reset":         ("resets",    "tokensPerMinute"),
            "anthropic-ratelimit-requests-limit":       ("limits",    "requestsPerMinute"),
            "anthropic-ratelimit-requests-remaining":   ("remaining", "requestsPerMinute"),
            "anthropic-ratelimit-requests-reset":       ("resets",    "requestsPerMinute"),
            "anthropic-ratelimit-input-tokens-limit":   ("limits",    "inputTokensPerMinute"),
            "anthropic-ratelimit-input-tokens-remaining":("remaining","inputTokensPerMinute"),
            "anthropic-ratelimit-input-tokens-reset":   ("resets",    "inputTokensPerMinute"),
            "anthropic-ratelimit-output-tokens-limit":  ("limits",    "outputTokensPerMinute"),
            "anthropic-ratelimit-output-tokens-remaining":("remaining","outputTokensPerMinute"),
            "anthropic-ratelimit-output-tokens-reset":  ("resets",    "outputTokensPerMinute"),
        }
        limits, remaining, resets = {}, {}, {}
        for header_name, (bucket, key) in mapping.items():
            val = resp_headers.get(header_name)
            if val is None: continue
            target = {"limits": limits, "remaining": remaining, "resets": resets}[bucket]
            try:
                target[key] = int(val)
            except ValueError:
                target[key] = val  # ISO string for reset times
        return {"limits": limits, "remaining": remaining, "resets": resets}

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = json.loads(resp.read())
            rl = parse_headers(resp.headers)
            return {
                "model": model,
                "usage": resp_body.get("usage", {}),
                **rl,
            }
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode(errors="replace")
        try:
            err = json.loads(body_txt)
            msg = err.get("error", {}).get("message", body_txt)
        except Exception:
            msg = body_txt
        # still extract rate-limit headers if present (e.g. 429)
        rl = parse_headers(e.headers) if e.headers else {}
        return {"error": f"HTTP {e.code}: {msg}", **rl}
    except Exception as e:
        return {"error": str(e)}


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
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
