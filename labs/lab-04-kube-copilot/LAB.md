# Lab 04 — Kube-copilot: Auditoria e Boas Práticas com IA
### Curso 547 — IA no Universo Kubernetes

---

## Objetivo do Lab

Instalar e configurar o kube-copilot, realizar auditoria de segurança em pods e
deployments com IA, identificar vulnerabilidades em imagens de container e aprender
a gerar manifests seguros com auxílio de IA.

---

## O que é o Kube-copilot?

O kube-copilot é uma ferramenta open source que usa IA para auditar, diagnosticar
e analisar recursos Kubernetes. Diferente das ferramentas anteriores, ele tem
comandos específicos para cada tipo de análise:

| Comando | Para que serve |
|---|---|
| `audit` | Auditoria de segurança de um Pod (requer Trivy) |
| `diagnose` | Diagnóstico de problemas em um Pod |
| `analyze` | Análise de problemas em qualquer recurso |
| `generate` | Geração de manifests via linguagem natural |
| `execute` | Execução de operações via linguagem natural |

---

## Pré-Requisitos

- Cluster kind em execução
- kubectl instalado e configurado
- Go 1.21+ instalado (para instalação via `go install`)
- Trivy instalado (para o comando `audit`)
- OpenRouter API key ou OpenAI API key

---

## Parte 1 — Instalando o Kube-copilot

### 1.1 Instalação via Go

```bash
go install github.com/feiskyer/kube-copilot/cmd/kube-copilot@latest
```

Verifique se o binário está no PATH:
```bash
export PATH=$PATH:$(go env GOPATH)/bin
kube-copilot --help
```

### 1.2 Instalando o Trivy (necessário para auditoria)

```bash
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin
trivy --version
```

---

## Parte 2 — Configurando o Backend de IA

### 2.1 Configuração com OpenRouter (gratuito)

```bash
export OPENAI_API_KEY=$OPENROUTER_API_KEY
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
```

### 2.2 Configuração com OpenAI (pago)

```bash
export OPENAI_API_KEY="sua_chave_openai"
```

### 2.3 Testando a configuração

```bash
kube-copilot analyze pod pod-inseguro --namespace default --model nvidia/nemotron-3-super-120b-a12b:free
```

---

## Parte 3 — Subindo o Cluster com Recursos para Auditoria

### 3.1 Subindo o cluster (se necessário)

```bash
kind create cluster --config ../../ambiente/kind-cluster.yaml
```

### 3.2 Aplicando os manifests

```bash
kubectl apply -f manifests/auditoria.yaml
```

### 3.3 Verificando os recursos

```bash
kubectl get pods
```

> Os recursos são criados no namespace `default` — o kube-copilot funciona
> de forma mais confiável neste namespace.

**Recursos criados:**

| Recurso | Problema intencional |
|---|---|
| `pod-inseguro` | Root, privileged, sem resources, sem probes |
| `app-segura` | Referência com boas práticas aplicadas |
| `pod-imagem-antiga` | Imagem nginx:1.21 com CVEs conhecidos |
| `app-sem-seguranca` | Sem securityContext, resources ou probes |

---

## Parte 4 — Auditoria de Segurança

### 4.1 Auditoria completa de um Pod (com Trivy)

```bash
kube-copilot audit pod-inseguro default --model nvidia/nemotron-3-super-120b-a12b:free --verbose
```

> O comando `audit` combina análise estática do manifest com scan de vulnerabilidades
> da imagem via Trivy, entregando um relatório consolidado.

Para auditoria em português, use o `execute`:
```bash
kube-copilot execute \
  --instructions "Faça uma auditoria de segurança completa do pod pod-inseguro no namespace default e responda em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

### 4.2 Auditoria do pod com imagem antiga

```bash
kube-copilot execute \
  --instructions "Faça uma auditoria de segurança completa do pod pod-imagem-antiga no namespace default, incluindo scan de vulnerabilidades da imagem. Responda em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

### 4.3 Comparando pods seguros vs. inseguros

```bash
# Pegue o nome real do pod seguro
kubectl get pods  -l app=segura

# Audite o pod seguro e compare com o inseguro
kube-copilot execute \
  --instructions "Faça uma auditoria de segurança do pod <nome-do-pod-seguro> no namespace default e compare com as boas práticas de segurança. Responda em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

> **Reflexão:** Compare os relatórios do `pod-inseguro` com o pod da `app-segura`.
> O kube-copilot deve reportar muito mais problemas no primeiro.

---

## Parte 5 — Diagnóstico de Recursos

### 5.1 Diagnosticando um pod

```bash
kube-copilot diagnose pod-inseguro default --model nvidia/nemotron-3-super-120b-a12b:free --verbose
```

Para diagnóstico em português:
```bash
kube-copilot execute \
  --instructions "Diagnostique os problemas do pod pod-inseguro no namespace default e sugira correções. Responda em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

### 5.2 Analisando um deployment

```bash
kube-copilot execute \
  --instructions "Analise o deployment app-sem-seguranca no namespace default e liste os problemas encontrados em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

### 5.3 Analisando um namespace inteiro

```bash
kube-copilot execute \
  --instructions "Analise todos os pods do namespace default e liste os problemas de segurança encontrados. Responda em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

---

## Parte 6 — Gerando Manifests Seguros com IA

### 6.1 Gerando um deployment seguro

```bash
kube-copilot execute \
  --instructions "Gere um manifest de deployment chamado app-python com a imagem python:3.11-slim, 2 replicas, no namespace default, com boas práticas de segurança: runAsNonRoot, readOnlyRootFilesystem, sem privilege escalation, com resources e probes definidos. Responda em português brasileiro" \
  --model nvidia/nemotron-3-super-120b-a12b:free \
  --verbose
```

> O kube-copilot vai gerar o manifest e perguntar se deseja aplicar.
> **Revise antes de confirmar** e compare com o `app-segura` do manifests/auditoria.yaml.

### 6.2 Gerando um NetworkPolicy

```bash
kube-copilot generate \
  "crie uma NetworkPolicy que permita apenas tráfego interno entre pods com label app=segura no namespace default" \
  --model nvidia/nemotron-3-super-120b-a12b:free
```

---

## Parte 7 — Corrigindo os Problemas Encontrados

Com base nos relatórios de auditoria, corrija o `pod-inseguro` aplicando boas práticas.

### Boas práticas a aplicar

```yaml
# Checklist de segurança
securityContext:
  runAsNonRoot: true          # nunca rodar como root
  runAsUser: 1000             # usuário não-root específico
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL                   # remover todas as capabilities

resources:                    # sempre definir resources
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"

livenessProbe:                # sempre definir probes
  httpGet:
    path: /
    port: 80

readinessProbe:
  httpGet:
    path: /
    port: 80
```

---

## Parte 8 — Limpeza do Ambiente

```bash
kubectl delete pod pod-inseguro pod-imagem-antiga
kubectl delete deployment app-segura app-sem-seguranca
```

> Não derrube o cluster — ele será reutilizado nos próximos labs.

---

## Resumo do Lab

| Etapa | O que foi feito |
|---|---|
| Auditoria | kube-copilot auditou pods com problemas de segurança reais |
| Scan de imagem | Trivy identificou CVEs em imagens desatualizadas |
| Análise | Deployments analisados com recomendações de boas práticas |
| Geração | Manifests seguros gerados via linguagem natural |

---

## Pontos de Atenção

- O comando `audit` requer o Trivy instalado — sem ele só analisa o manifest
- O kube-copilot usa `gpt-4o` por padrão — sempre especifique `--model nvidia/nemotron-3-super-120b-a12b:free` para reduzir custo
- Revise sempre os manifests gerados antes de aplicar em produção
- Use `nvidia/nemotron-3-super-120b-a12b:free` via OpenRouter — gratuito e com bom suporte a tool calling
- Em ambientes corporativos, avalie o que é enviado para a API (specs, logs, configurações)s