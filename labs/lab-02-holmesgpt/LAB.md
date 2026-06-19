# Lab 02 — HolmesGPT: Root Cause Analysis com IA
### Curso 541 — IA no Universo Kubernetes

---

## Objetivo do Lab

Instalar e configurar o HolmesGPT, simular incidentes reais em um cluster Kubernetes
e utilizar a ferramenta para investigar root causes em linguagem natural, correlacionando
logs, eventos e estado dos recursos automaticamente.

---

## Diferença entre K8sGPT e HolmesGPT

| | K8sGPT | HolmesGPT |
|---|---|---|
| **Abordagem** | Scan proativo do cluster | Investigação orientada a perguntas |
| **Uso** | "O que está errado no cluster?" | "Por que esse pod está falhando?" |
| **Atuação** | Analisa todos os recursos | Investiga um problema específico |
| **Melhor para** | Health check contínuo | Root cause analysis de incidentes |

> Use os dois em conjunto: K8sGPT para detectar, HolmesGPT para investigar.

---

## Pré-requisitos

- Cluster kind em execução (do Lab 01 ou crie um novo)
- Python **3.10+** instalado (obrigatório para o HolmesGPT)
- Conta na OpenAI com **mínimo $5 de crédito** → https://platform.openai.com
- ~4GB de RAM disponíveis

> **Por que modelo pago?**
> O HolmesGPT usa um loop agêntico que faz múltiplas chamadas encadeadas de tool calling
> para correlacionar logs, eventos e recursos. Modelos gratuitos (OpenRouter, Gemini free,
> DeepSeek free) não suportam esse protocolo de forma confiável. O `gpt-4o-mini` custa
> ~$0.01 por investigação — $5 de crédito é suficiente para o lab inteiro.

Verifique a versão do Python:
```bash
python3 --version
```

---

## Parte 1 — Instalando o HolmesGPT

### 1.1 Instalação via pip

```bash
pipx install holmesgpt
```

Verifique a instalação:
```bash
holmes --version
```

### 1.2 Instalação via brew (macOS / Linux)

```bash
brew tap robusta-dev/homebrew-holmesgpt
brew install holmesgpt
```

---

## Parte 2 — Configurando o Backend de IA

### 2.1 Configuração recomendada para o lab (gpt-4o-mini)

```bash
export OPENAI_API_KEY="sua_chave_openai"
```

Crie o arquivo de configuração:

```bash
cat > ~/.holmes/config.yaml << EOF
model: openai/gpt-4o-mini
api_key: ${OPENROUTER_API_KEY}
api_base: https://openrouter.ai/api/v1
EOF
```

> **Dica:** Adicione o export no seu `~/.bashrc` ou `~/.zshrc`
> para não precisar repetir a cada sessão.

### 2.2 Alternativas de modelo

| Modelo | Provedor | Custo aproximado | Observação |
|---|---|---|---|
| `gpt-4o-mini` | OpenAI | ~$0.01/investigação | **Recomendado para o lab** |
| `claude-haiku-3` | Anthropic | ~$0.01/investigação | Boa alternativa |
| `gpt-4o` | OpenAI | ~$0.10/investigação | Para investigações complexas |

### 2.3 Testando a configuração

```bash
holmes ask "o que é Kubernetes?"
```

Se responder normalmente, a configuração está correta.

---

## Parte 3 — Criando os Incidentes no Cluster

### 3.1 Subindo o cluster (se necessário)

```bash
kind create cluster --config ../../ambiente/kind-cluster.yaml
```

### 3.2 Aplicando os manifests com incidentes

```bash
kubectl apply -f manifests/incidente.yaml
```

### 3.3 Observando os estados

```bash
watch kubectl get all -n lab-holmes
```

Aguarde 1-2 minutos. Você verá:

```
NAME                              READY   STATUS             RESTARTS   AGE
pod/app-web-xxx                   0/1     CrashLoopBackOff   3          90s
pod/app-gulosa-xxx                0/1     Pending            0          90s
pod/job-listagem-pods-xxx         0/1     Error              0          60s
pod/db-postgres-xxx               1/1     Running            0          90s
```

**Incidentes simulados:**

| Recurso | Problema |
|---|---|
| `app-web` | CrashLoopBackOff — tenta conectar no banco pelo hostname errado |
| `app-gulosa` | Pending — solicita 999Gi de memória, impossível de alocar |
| `job-listagem-pods` | Error — ServiceAccount sem permissão RBAC para listar pods |
| `db-postgres` | Running — banco está ok, mas inacessível pelo nome errado |

---

## Parte 4 — Investigando com HolmesGPT

> **Nota:** O HolmesGPT pode levar 1-2 minutos por investigação — ele faz dezenas
> de queries no cluster antes de entregar a resposta. Isso é normal e esperado.

### 4.1 Pergunta ampla sobre o namespace

```bash
holmes ask "quais problemas existem no namespace lab-holmes e quais são suas causas?"
```

Esta é a pergunta mais poderosa — o HolmesGPT investiga todos os recursos
do namespace e entrega um relatório consolidado de root cause analysis.

### 4.2 Investigação específica — CrashLoopBackOff

```bash
holmes ask "por que o pod app-web está em CrashLoopBackOff no namespace lab-holmes?"
```

> O HolmesGPT vai buscar automaticamente: logs do pod, eventos do deployment,
> ConfigMap referenciado, Services do namespace — e correlacionar tudo.

### 4.3 Investigação do pod Pending

```bash
holmes ask "por que o pod app-gulosa está em Pending no namespace lab-holmes?"
```

### 4.4 Investigação do Job com erro

```bash
holmes ask "por que o job job-listagem-pods falhou no namespace lab-holmes?"
```

### 4.5 Modo interativo

O HolmesGPT suporta perguntas de acompanhamento no mesmo contexto:

```bash
holmes ask "por que o app-web está falhando no namespace lab-holmes?"
```

No modo interativo você pode continuar perguntando:
```
> como eu corrijo o problema de conexão?
> quais outros serviços podem ser afetados?
> mostre o ConfigMap que está causando o problema
```

---

## Parte 5 — Interpretando os Resultados

### O que o HolmesGPT faz por baixo dos panos

Diferente do K8sGPT que faz um scan estático, o HolmesGPT usa um **loop agêntico**:

```
Pergunta → Monta plano de investigação (Tasks)
       → Executa dezenas de queries no cluster (Tools)
       → Coleta logs, eventos, ConfigMaps, Services
       → Correlaciona todos os dados
       → Entrega Root Cause Analysis + Próximos Passos
```

### Comparando os diagnósticos

Para o `app-web`, compare o diagnóstico manual com o HolmesGPT:

**Diagnóstico manual (4 comandos):**
```bash
kubectl logs -l app=web -n lab-holmes
kubectl describe deployment app-web -n lab-holmes
kubectl get configmap app-config -n lab-holmes -o yaml
kubectl get svc -n lab-holmes
```

**Diagnóstico com HolmesGPT (1 pergunta):**
```bash
holmes ask "por que o app-web falha no namespace lab-holmes?"
```

> **Reflexão:** O HolmesGPT não apenas lista o erro — ele explica o *porquê*,
> aponta a causa raiz e sugere os próximos passos. Para um SRE, isso reduz
> drasticamente o tempo de investigação em incidentes fora do horário comercial.

---

## Parte 6 — Corrigindo os Incidentes

### Correção 1: Hostname errado no ConfigMap

```bash
kubectl patch configmap app-config -n lab-holmes \
  --patch '{"data": {"DATABASE_HOST": "db-service"}}'

kubectl rollout restart deployment/app-web -n lab-holmes
```

### Correção 2: Recursos excessivos

```bash
kubectl patch deployment app-gulosa -n lab-holmes --patch '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "resources": {
            "requests": {"memory": "64Mi", "cpu": "100m"},
            "limits": {"memory": "128Mi", "cpu": "200m"}
          }
        }]
      }
    }
  }
}'
```

### Correção 3: Permissão RBAC para o Job

```bash
kubectl create role pod-reader \
  --verb=get,list \
  --resource=pods \
  -n lab-holmes

kubectl create rolebinding job-pod-reader \
  --role=pod-reader \
  --serviceaccount=lab-holmes:job-sem-permissao \
  -n lab-holmes

kubectl delete job job-listagem-pods -n lab-holmes
kubectl apply -f manifests/incidente.yaml
```

### Verificando as correções

```bash
watch kubectl get all -n lab-holmes
```

### Confirmando com HolmesGPT

```bash
holmes ask "ainda existem problemas no namespace lab-holmes?"
```

---

## Parte 7 — Limpeza do Ambiente

```bash
kubectl delete namespace lab-holmes
kind delete cluster --name k8s-ai-labs
```

---

## Resumo do Lab

| Etapa | O que foi feito |
|---|---|
| Ambiente | Cluster kind com incidentes simulados |
| Incidentes criados | CrashLoopBackOff (hostname errado), Pending (recursos excessivos), Job com erro RBAC |
| Investigação | HolmesGPT identificou root cause de cada incidente via linguagem natural |
| Correções | ConfigMap corrigido, recursos ajustados, RBAC criado |
| Resultado | Cluster saudável — HolmesGPT confirma ausência de problemas |

---

## Pontos de Atenção

- O HolmesGPT tem **acesso somente leitura** — ele nunca modifica o cluster
- Cada investigação leva 1-2 minutos e consome ~$0.01 de crédito
- Em clusters grandes, seja específico na pergunta para reduzir consumo de tokens
- Em ambientes corporativos, avalie o que o HolmesGPT envia para a API (logs, eventos, specs)
- Modelos gratuitos não funcionam com o HolmesGPT — o loop agêntico exige tool calling robusto