# LinkedIn Prospector

Busca perfis de CEOs, Founders e outros cargos no LinkedIn e gera mensagens personalizadas automaticamente.

## Funcionalidades

- 🔗 Login na conta LinkedIn (salva sessão local)
- 🔍 Busca por cargo e formação acadêmica (MBA, PhD, etc.)
- ✉️ Geração automática de mensagens de conexão e follow-up
- 📋 Gestão de prospects com status (novo, contatado, respondeu, reunião)

## Instalação

**Pré-requisitos:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```bash
git clone https://github.com/seu-usuario/linkedin-prospector
cd linkedin-prospector

# Criar ambiente virtual com Python 3.11
uv python install 3.11
uv venv --python 3.11
uv pip install -r requirements.txt

# Instalar o browser
.venv/bin/playwright install chromium
```

## Como usar

```bash
./run.sh
```

Acesse `http://localhost:8501` no browser.

1. **Conectar LinkedIn** — faça login uma vez, a sessão fica salva localmente
2. **Prospectar** — escolha cargos e formação, clique em Buscar
3. **Mensagens** — edite e regenere as mensagens antes de enviar

## Estrutura

```
├── app.py                    # Página inicial
├── pages/
│   ├── 1_Conectar_LinkedIn.py  # Autenticação
│   ├── 2_Prospectar.py         # Busca e mensagens
│   └── 3_Debug.py              # Debug de seletores
├── scraper.py                # Automação do LinkedIn
├── generator.py              # Geração de mensagens por templates
├── database.py               # SQLite para prospects
└── run.sh                    # Script de execução
```

## Aviso

Este projeto usa automação de browser para acessar o LinkedIn.
Use com moderação para não violar os termos de uso da plataforma.
