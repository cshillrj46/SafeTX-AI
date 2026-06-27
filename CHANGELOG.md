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

## 🔎 Motor de rastreamento on-chain — Fase 1 (BFS multi-hop)

Endpoints novos, protegidos por JWT como o resto da API:

- `POST /trace` — abre um caso de investigação (`address`, `chain`,
  `max_hops`, `case_reference`, `since` opcional). Roda em background
  (`BackgroundTasks`), retorna `202` imediatamente com `job_id`.
- `GET /trace/{job_id}` — status do job (`pending`/`running`/`completed`/
  `failed`) e o grafo resultante (`nodes`, `edges`).

**Como funciona**: a partir do endereço investigado, segue em BFS apenas as
transações de **saída** (para onde o dinheiro foi), ignorando transações
revertidas e valores abaixo de `TRACE_MIN_VALUE_ETH` (poeira). Profundidade
(`max_hops`) e volume são limitados por configuração
(`TRACE_MAX_NODES`, `TRACE_MAX_TXS_PER_ADDRESS`) para não deixar a
investigação rodar indefinidamente nem estourar o tier gratuito do
Etherscan.

**Fonte de dados**: Etherscan API v2 (`backend/etherscan_client.py`), com
rate limiting interno (tier free = 5 req/s) e retry com backoff em erro de
rede ou rate limit. Suporta hoje só Ethereum mainnet (`SUPPORTED_CHAINS` em
`backend/config.py` — extensível para outras chains EVM).

**Schema novo**: `trace_jobs`, `trace_nodes`, `trace_edges` em
`backend/database.py`. Os campos de enriquecimento em `TraceNode`
(`label`, `is_sanctioned`, `is_known_exchange`) já existem no schema mas
ficam vazios nesta fase — reservados para a próxima etapa (cruzamento com
sanctions list / exchanges conhecidas).

**Limitação conhecida**: erro de configuração (ex: `ETHERSCAN_API_KEY`
ausente) é capturado e grava `status: "failed"` com `error_message` claro
no job — não derruba a aplicação. Validado via smoke test manual.

**Testes**: `tests/test_tracing.py` (7 testes) — expansão multi-hop, filtro
de poeira/transação revertida/entrada, respeito ao `max_hops`, chain não
suportada, autenticação obrigatória nos endpoints.

## 💵 Stablecoins (USDT/USDC/DAI) — achado validado contra dado real

Conectei o MCP do Blockscout e testei o motor contra endereços reais
(`vitalik.eth` e a hot wallet 14 da Binance). Resultado: **9 de 10**
transações de saída da hot wallet da Binance eram transferências de
**USDT/token**, com `value` nativo igual a zero — o motor (só ETH nativo)
enxergaria apenas 10% do volume real. Como USDT é o canal mais comum em
golpe de investimento (corredor PIX→cripto), essa lacuna invalidaria o
caso de uso principal.

**Correção**: o motor agora também segue `action=tokentx` (Etherscan),
restrito a uma whitelist de contratos (`config.STABLECOIN_CONTRACTS`):
USDT, USDC, DAI — endereço, símbolo e decimais confirmados ao vivo contra
a rede antes de codar. BUSD foi deixada de fora (Paxos descontinuou a
emissão em 2024, volume residual irrelevante).

**Efeito colateral útil**: a mesma whitelist que adiciona stablecoins
também filtra **dusting/airdrop spam** — confirmado contra dado real
(endereço despejando token chamado literalmente "ETH" com saldo falso
gigante em `vitalik.eth`). Token fora da whitelist nunca entra no grafo.

**Schema**: `TraceEdge.amount_eth` renomeado para `amount` (agora cobre
ETH ou stablecoin) e ganhou `token_symbol` (`None` = ETH nativo).
⚠️ Se você já tinha rodado a versão anterior localmente, apague o arquivo
do banco (`safetx.db`) antes de subir esta versão — é uma mudança de
schema sem migração automática, e não há dado de produção em risco nessa
fase.

**Testes novos**: segue stablecoin corretamente, ignora token fora da
whitelist (dusting), combina aresta nativa + stablecoin no mesmo job.
