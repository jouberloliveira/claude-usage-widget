# Claude Usage Widget

Widget web local para monitorar limites e uso da sua subscription/API key do Claude.

## Como usar

```bash
bash run.sh
```

Ou diretamente:

```bash
python3 claude_usage.py
```

Abre automaticamente em `http://localhost:7432`. Cole sua Anthropic API Key e clique em **Verificar**.

## O que mostra

- Limites de tokens e requests por minuto e por dia
- Quanto resta antes do reset
- Tier detectado (Free / Pro / Max 5 / Max 20 / API)
- Tokens consumidos na verificação
- Próximos horários de reset

## Requisitos

- **Python 3.8+** — sem dependências externas. Só stdlib.
- Anthropic API Key (`sk-ant-api03-...`)

## Como obter a API Key

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Vá em **API Keys**
3. Crie ou copie uma chave existente

> A chave é salva apenas no `localStorage` do seu browser local. Nunca sai da sua máquina.
