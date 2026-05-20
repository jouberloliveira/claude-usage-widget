# Claude Usage Widget

Widget web local para monitorar limites e uso da sua **subscription** Claude (Pro/Max). Sem API key — usa o cookie de sessão do `claude.ai`.

## Como usar

```bash
bash run.sh
```

Ou diretamente:

```bash
python3 claude_usage.py
```

Abre automaticamente em `http://localhost:7432`. Cole seu `sessionKey` e clique em **Verificar**.

## Como obter o `sessionKey`

1. Faça login em [claude.ai](https://claude.ai) no seu browser.
2. Abra DevTools (F12 ou `Cmd+Option+I`).
3. Vá em **Application** (Chrome/Edge) ou **Storage** (Firefox) → **Cookies** → `https://claude.ai`.
4. Copie o valor do cookie `sessionKey` (começa com `sk-ant-sid01-`).
5. Cole no campo do widget. Ele fica salvo apenas no `localStorage` do seu browser local.

> O widget só conversa com `claude.ai` usando seu cookie. Nenhum dado é enviado para terceiros.

## O que mostra

- Plano detectado (Pro / Max 5 / Max 20)
- Buckets de uso da subscription: mensagens usadas / limite por janela (5h, semanal, etc.)
- Próximo horário de reset por bucket
- Nome e ID da organização

> Os endpoints internos de `claude.ai` (`/api/organizations`, `/api/organizations/{id}/usage_limit`) não são públicos e podem mudar. Se o widget parar de mostrar buckets, abra uma issue com os "campos brutos detectados" que aparecem no rodapé do resultado.

## Requisitos

- **Python 3.8+** — sem dependências externas. Só stdlib.
- Conta Claude Pro ou Max com sessão ativa no browser.

## Limitações

- Não funciona com contas Free sem subscription paga (não há buckets de uso para mostrar).
- O `sessionKey` expira; quando expirar, refaça login e copie de novo.
- Usuários que só têm API key (sem subscription) devem usar a versão anterior do widget (tag pré-cookie-auth) ou outro tooling baseado em `x-api-key`.
