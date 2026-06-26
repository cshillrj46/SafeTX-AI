# Changelog — Auditoria e correções de segurança/qualidade

Este documento resume as correções aplicadas a partir de uma auditoria de
segurança e qualidade de código do projeto.

## 🚨 Crítico

- **Credencial exposta removida**: `backend/email_service.py` continha um
  e-mail e uma senha de app do Gmail em texto puro, commitados em um
  repositório público. As credenciais agora vêm de variáveis de ambiente
  (`GMAIL_USER` / `GMAIL_APP_PASSWORD` em `.env`, nunca commitado).
  **Ação manual necessária**: revogue a senha de app antiga na sua conta
  Google e gere uma nova antes de configurar o `.env`.

## 🔐 Segurança

- **Autenticação JWT implementada** (`backend/auth.py`): endpoints
  `POST /register` e `POST /token`. Todas as rotas de negócio (`/analyze`,
  `/history`, `/reclassify/{id}`, `/reclassifications`) agora exigem um
  Bearer token válido. Antes, o `README` anunciava "JWT Auth", mas nenhuma
  rota era protegida.
- **`reclassified_by` deixou de ser um campo livre enviado pelo cliente** —
  agora é derivado do usuário autenticado no token, evitando que qualquer
  pessoa assine reclassificações em nome de outra.
- **Sessões de banco de dados agora são sempre fechadas** via dependency
  `get_db()` do FastAPI (`backend/database.py`), eliminando o vazamento de
  conexões que existia (sessões abertas com `SessionLocal()` e nunca
  fechadas em nenhum endpoint).
- **`drop_transactions.py`** agora exige a flag `--confirm` e uma confirmação
  interativa antes de apagar a tabela `transactions`. Antes, rodava
  destrutivamente sem nenhum aviso.
- **CORS, URL do webhook e e-mail de destino** agora vêm de variáveis de
  ambiente (`backend/config.py`) em vez de hardcoded.
- **Bytecode (`.pyc`) commitado por engano** em `backend/__pycache__` e
  `alembic/__pycache__` foi removido do controle de versão (o `.gitignore`
  já excluía `__pycache__/`, mas esses arquivos tinham sido adicionados
  antes da regra existir).

## 🐛 Bugs corrigidos

- **Paginação real em `/history`**: antes, o backend ignorava os parâmetros
  `page`/`limit` enviados pelo frontend e retornava todos os registros
  sempre. Agora retorna `{items, page, limit, total, total_pages}`.
- **Frontend não lia o resultado de `/analyze` corretamente**: o backend
  retorna o nível de risco como string simples (`"high-risk"`), mas o
  componente lia `result.risk` (sempre `undefined`). Corrigido em
  `TransactionAnalyzer.tsx`.
- **`except:` genérico em `ai_model.py`** mascarava silenciosamente
  sender/recipient desconhecidos pelo encoder. Agora captura `ValueError`
  especificamente e registra um aviso via `logging`.
- **`README.md` desatualizado**: instruções apontavam para uma pasta
  `frontend/` com `npm start` (Create React App), mas o projeto real é
  `safetx-dashboard/` (Vite) com `npm run dev`. `requirements.txt` era
  referenciado mas não existia.

## 🧹 Qualidade / arquitetura

- Adicionado `requirements.txt` (não existia).
- Adicionado `.env.example` (backend e frontend) e `.gitignore` atualizado
  para nunca commitar `.env`.
- `print()` de debug substituído por `logging` configurado em `main.py`.
- Adicionada suíte de testes automatizados com `pytest` em `tests/`
  (autenticação, autorização, análise de transação, paginação e
  reclassificação) — 8 testes, todos passando.
- Frontend: cliente de API centralizado (`src/api.ts`) com tratamento de
  erros e injeção automática do token JWT; tela de login/registro
  (`src/Login.tsx`).

## ✅ Validação

- Suíte `pytest` (8 testes) passando.
- Build de produção do frontend (`npm run build`) sem erros de TypeScript.
- Teste de fumaça ponta-a-ponta com o servidor real: registro → login →
  bloqueio sem token (401) → análise → histórico paginado → reclassificação
  vinculada ao usuário autenticado — todos os passos validados manualmente.
