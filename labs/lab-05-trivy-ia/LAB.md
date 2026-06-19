# Lab 05 — Trivy + IA: Segurança de Containers com Análise Inteligente
### Curso 541 — IA no Universo Kubernetes

---

## Objetivo do Lab

Utilizar o Trivy para escanear imagens de container e manifests Kubernetes,
e integrar os resultados com IA via OpenRouter para análise inteligente,
priorização de vulnerabilidades e sugestões de correção em português.

---

## Por que Trivy + IA?

O Trivy é a ferramenta de scan de segurança mais usada no ecossistema Kubernetes —
presente em pipelines CI/CD de empresas reais. Combinado com IA, ele passa de uma
lista crua de CVEs para um relatório com contexto, impacto e correções práticas.

| Trivy sozinho | Trivy + IA |
|---|---|
| Lista CVEs com severidade | Explica o impacto real de cada CVE |
| Aponta misconfigurations | Sugere correções com exemplos práticos |
| Output em inglês técnico | Relatório em português com nota de segurança |
| Exige conhecimento para interpretar | Acessível para times com menos experiência em segurança |

---

## Pré-Requisitos

- Trivy instalado → https://aquasecurity.github.io/trivy/latest/getting-started/installation/
- Python 3.8+
- OPENROUTER_API_KEY configurada
- Cluster kind em execução (para scan de manifests)

Verifique o Trivy:
```bash
trivy --version
```

---

## Parte 1 — Instalando o Trivy

```bash
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
  | sudo sh -s -- -b /usr/local/bin
```

---

## Parte 2 — Trivy sem IA (baseline)

Antes de usar a IA, rode o Trivy puro para entender o output bruto:

### 2.1 Scan de imagem

```bash
# Imagem antiga — muitos CVEs esperados
trivy image nginx:1.21

# Imagem recente — menos CVEs
trivy image nginx:alpine
```

### 2.2 Scan de manifest Kubernetes

```bash
trivy config manifests/targets.yaml
```

### 2.3 Output em JSON (necessário para integração com IA)

```bash
trivy image nginx:1.21 --format json --output resultado.json
cat resultado.json | python3 -m json.tool | head -100
```

> **Reflexão:** O JSON do Trivy é rico mas difícil de interpretar manualmente.
> É exatamente aqui que a IA agrega valor.

---

## Parte 3 — Trivy + IA (trivy-ia.py)

### 3.1 Configurando o ambiente

```bash
export OPENROUTER_API_KEY="sua_chave_aqui"
```

### 3.2 Scan de imagem com análise de IA

```bash
# Imagem antiga — muitas vulnerabilidades
python3 trivy-ia.py imagem nginx:1.21

# Imagem Alpine — poucas vulnerabilidades
python3 trivy-ia.py imagem nginx:alpine

# Python antigo
python3 trivy-ia.py imagem python:3.9
```

### 3.3 Scan de manifest com análise de IA

```bash
python3 trivy-ia.py manifest manifests/targets.yaml
```

### 3.4 Comparando imagens

```bash
# Rode os dois e compare os relatórios gerados
python3 trivy-ia.py imagem nginx:1.21
python3 trivy-ia.py imagem nginx:1.27-alpine

# Os relatórios são salvos automaticamente como:
# relatorio_imagem_nginx_1.21.md
# relatorio_imagem_nginx_1.27-alpine.md
```

---

## Parte 4 — Interpretando os Relatórios

### O que a IA entrega

Para cada scan, o relatório contém:

1. **Resumo das vulnerabilidades** — agrupadas por severidade (CRITICAL, HIGH, MEDIUM)
2. **Explicação do impacto** — o que cada CVE significa na prática
3. **Correções recomendadas** — com exemplos de comandos e configurações
4. **Boas práticas** — como evitar os problemas no futuro
5. **Nota de segurança (0-10)** — avaliação geral da imagem

### Comparando imagens

| Imagem | CVEs esperados | Nota esperada |
|---|---|---|
| `nginx:1.21` | Muitos (CRITICAL/HIGH) | Baixa (0-4) |
| `nginx:alpine` | Poucos | Alta (7-9) |
| `python:3.9` | Moderados | Média (4-7) |

---

## Parte 5 — Usando Trivy no Cluster

### 5.1 Subindo o cluster

```bash
kind create cluster --config ../../ambiente/kind-cluster.yaml
kubectl apply -f manifests/targets.yaml
kubectl get pods -n lab-trivy
```

### 5.2 Escaneando imagens dos pods em execução

```bash
# Liste as imagens em uso no cluster
kubectl get pods -n lab-trivy -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}'

# Escaneie cada imagem com IA
python3 trivy-ia.py imagem nginx:1.21
python3 trivy-ia.py imagem nginxinc/nginx-unprivileged:alpine
python3 trivy-ia.py imagem python:3.9
```

### 5.3 Escaneando todos os manifests do cluster

```bash
python3 trivy-ia.py manifest manifests/targets.yaml
```

---

## Parte 6 — Usando Modelo Diferente

O script usa `openrouter/auto` por padrão. Para usar um modelo específico:

```bash
# DeepSeek (gratuito via OpenRouter)
export TRIVY_IA_MODEL="deepseek/deepseek-chat-v3-0324:free"
python3 trivy-ia.py imagem nginx:1.21

# gpt-4o-mini (pago, mais preciso)
export OPENAI_API_KEY="sua_chave_openai"
export TRIVY_IA_MODEL="gpt-4o-mini"
python3 trivy-ia.py imagem nginx:1.21
```

---

## Parte 7 — Limpeza do Ambiente

```bash
kubectl delete namespace lab-trivy
kind delete cluster --name k8s-ai-labs
```

---

## Resumo do Lab

| Etapa | O que foi feito |
|---|---|
| Trivy baseline | Scan de imagens e manifests sem IA |
| Trivy + IA | Análise inteligente com explicações em português |
| Comparação | nginx:1.21 vs nginx:alpine — diferença de segurança clara |
| Manifests | Scan de configurações Kubernetes com recomendações |
| Cluster | Imagens dos pods em produção escaneadas |

---

## Pontos de Atenção

- Trivy baixa o banco de CVEs na primeira execução — pode demorar alguns minutos
- Imagens grandes (python, java) geram muitos CVEs — filtre por CRITICAL e HIGH
- O script limita a análise às 10 vulnerabilidades mais graves para economizar tokens
- Em pipelines CI/CD, o Trivy com `--exit-code 1` quebra o build se encontrar CVEs críticos
- Sempre avalie o contexto: um CVE em biblioteca não usada tem impacto menor