# Lab 03 — kubectl-ai: Kubernetes por Linguagem Natural
### Curso 547 — IA no Universo Kubernetes

---

## Objetivo do Lab

Instalar e configurar o kubectl-ai, aprender a operar um cluster Kubernetes
usando linguagem natural e entender os limites e cuidados no uso dessa ferramenta
no dia a dia do DevOps/SRE.

---

## O que é o kubectl-ai?

O kubectl-ai é uma ferramenta open source do Google Cloud Platform que traduz
linguagem natural em comandos kubectl. Diferente do HolmesGPT (que investiga
incidentes) e do K8sGPT (que faz scan do cluster), o kubectl-ai é um **assistente
de produtividade** — ele ajuda o engenheiro a executar operações sem precisar
memorizar flags e sintaxe complexa.

| Ferramenta | Para que serve |
|---|---|
| K8sGPT | Detectar problemas no cluster |
| HolmesGPT | Investigar root cause de incidentes |
| **kubectl-ai** | **Operar o cluster via linguagem natural** |

---

## Pré-Requisitos

- Cluster kind em execução
- kubectl instalado e configurado
- Conta no Google AI Studio (gratuita, sem cartão) → https://aistudio.google.com/apikey
- ~2GB de RAM disponíveis

> **Boas notícias:** o kubectl-ai funciona com modelos gratuitos!
> O Gemini via Google AI Studio tem tier gratuito suficiente para o lab inteiro.

---

## Parte 1 — Instalando o kubectl-ai

### 1.1 Instalação via script (Linux / macOS)

```bash
curl -sSL https://raw.githubusercontent.com/GoogleCloudPlatform/kubectl-ai/main/install.sh | bash
```

### 1.2 Instalação via binário (Linux x86_64)

```bash
curl -LO https://github.com/GoogleCloudPlatform/kubectl-ai/releases/latest/download/kubectl-ai_linux_amd64.tar.gz
tar -xzf kubectl-ai_linux_amd64.tar.gz
chmod +x kubectl-ai
sudo mv kubectl-ai /usr/local/bin/
```

### 1.3 Instalação via brew (macOS / Linux)

```bash
brew install kubectl-ai
```

Verifique a instalação:
```bash
kubectl-ai --version
```

---

## Parte 2 — Configurando o Backend de IA

### 2.1 Configuração recomendada — Gemini (gratuito)

Obtenha sua chave em: https://aistudio.google.com/apikey

```bash
export GEMINI_API_KEY="sua_chave_gemini"
export KUBECTL_AI_MODEL="gemini-2.5-flash"
```

### 2.2 Alternativas

**OpenRouter (modelos variados):**
```bash
export OPENAI_API_KEY="sua_chave_openrouter"
export OPENAI_ENDPOINT="https://openrouter.ai/api/v1"
```

**OpenAI (pago, maior qualidade):**
```bash
export OPENAI_API_KEY="sua_chave_openai"
```

### 2.3 Testando a configuração

```bash
kubectl-ai --model gemini-2.5-flash "quantos nodes existem no cluster?"
```

Se responder com o número correto de nodes, está funcionando.

---

## Parte 3 — Subindo o Cluster

```bash
kind create cluster --config ../../ambiente/kind-cluster.yaml
```

Aplique alguns recursos para ter o que explorar:

```bash
kubectl apply -f manifests/workloads.yaml
```

Verifique:
```bash
kubectl get all -n lab-kubectl-ai
```

---

## Parte 4 — Operando o Cluster com Linguagem Natural

### 4.1 Modo interativo

```bash
kubectl-ai
```

No modo interativo você digita perguntas e comandos em sequência:

```
>>> liste todos os pods do namespace lab-kubectl-ai
>>> quais pods estão em estado de falha?
>>> mostre os logs do pod nginx-deployment
>>> quantos replicas tem o deployment nginx?
```

Saia com `exit` ou `Ctrl+C`.

### 4.2 Modo não-interativo (um comando por vez)

```bash
kubectl-ai --model gemini-2.5-flash "liste todos os pods do namespace lab-kubectl-ai"
kubectl-ai "mostre o status de todos os nodes"
kubectl-ai "quais deployments existem no namespace lab-kubectl-ai?"
kubectl-ai "mostre os eventos recentes do cluster"
```

### 4.3 Gerando manifests com linguagem natural

```bash
kubectl-ai "crie um deployment chamado app-teste com a imagem nginx:alpine e 2 replicas no namespace lab-kubectl-ai"
```

> O kubectl-ai vai gerar o manifest YAML e perguntar se deseja aplicar.
> **Sempre revise o manifest antes de confirmar!**

```bash
kubectl-ai "crie um service do tipo ClusterIP para o deployment app-teste na porta 80"
kubectl-ai "aumente o número de replicas do deployment app-teste para 3"
```

### 4.4 Troubleshooting com linguagem natural

```bash
kubectl-ai "por que o pod app-falha está com problema no namespace lab-kubectl-ai?"
kubectl-ai "mostre os logs do pod app-falha no namespace lab-kubectl-ai"
kubectl-ai "descreva o pod app-falha no namespace lab-kubectl-ai"
```

### 4.5 Operações de manutenção

```bash
kubectl-ai "quais nodes estão disponíveis para scheduling?"
kubectl-ai "mostre o uso de recursos de todos os pods no namespace lab-kubectl-ai"
kubectl-ai "liste todos os services e suas portas no namespace lab-kubectl-ai"
kubectl-ai "mostre os configmaps do namespace lab-kubectl-ai"
```

### 4.6 Usando com modelo específico (Gemini Flash — mais rápido)

```bash
kubectl-ai --model gemini-2.5-flash "liste os pods do namespace lab-kubectl-ai"
```

---

## Parte 5 — Desafios Práticos

> Tente resolver cada desafio usando **apenas linguagem natural** com o kubectl-ai.
> Depois compare com o comando kubectl equivalente.

**Desafio 1:** Liste todos os pods que não estão em estado Running

**Desafio 2:** Mostre quantos pods existem em cada namespace

**Desafio 3:** Crie um ConfigMap chamado `app-config` com as chaves `ENV=production` e `LOG_LEVEL=info` no namespace `lab-kubectl-ai`

**Desafio 4:** Faça o rollout restart do deployment `nginx-deployment` no namespace `lab-kubectl-ai`

**Desafio 5:** Delete todos os pods com status `Error` no namespace `lab-kubectl-ai`

---

## Parte 6 — Limites e Cuidados

### O que o kubectl-ai faz bem
- Gerar comandos de leitura (`get`, `describe`, `logs`)
- Criar manifests simples via linguagem natural
- Explicar o que um comando faz
- Ajudar quem está aprendendo kubectl

### O que NÃO delegar ao kubectl-ai sem revisão
- Operações destrutivas (`delete`, `drain`, `cordon`)
- Modificações em produção
- Operações com RBAC e permissões
- Qualquer comando que altere o estado do cluster

> **Regra de ouro:** o kubectl-ai mostra o comando antes de executar.
> **Sempre leia o comando gerado antes de confirmar.**

### Comparando eficiência

| Tarefa | kubectl manual | kubectl-ai |
|---|---|---|
| Listar pods por status | `kubectl get pods --field-selector=status.phase=Running` | `"liste apenas os pods em Running"` |
| Ver logs das últimas 100 linhas | `kubectl logs <pod> --tail=100` | `"mostre as últimas 100 linhas de log do pod X"` |
| Criar deployment | Escrever YAML completo | `"crie um deployment nginx com 3 replicas"` |

---

## Parte 7 — Limpeza do Ambiente

```bash
kubectl delete namespace lab-kubectl-ai
kind delete cluster --name k8s-ai-labs
```

---

## Resumo do Lab

| Etapa | O que foi feito |
|---|---|
| Instalação | kubectl-ai com Gemini (gratuito) |
| Operações | Cluster operado inteiramente via linguagem natural |
| Geração de manifests | Deployments, Services e ConfigMaps criados via linguagem natural |
| Troubleshooting | Pods investigados via perguntas em português |
| Limites | Revisão humana obrigatória antes de aplicar qualquer operação |

---

## Pontos de Atenção

- O kubectl-ai é uma ferramenta de **produtividade**, não de diagnóstico
- Sempre revise o comando gerado antes de confirmar — especialmente em produção
- O Gemini gratuito tem rate limits — se travar, aguarde alguns segundos e tente novamente
- Operações destrutivas exigem atenção redobrada independente da ferramenta usada
- Em ambientes corporativos, avalie se os dados do cluster podem ser enviados para APIs externas