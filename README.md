# 547 — IA no Universo Kubernetes
## Ambiente de Lab com Vagrant

Este repositório contém o ambiente de laboratório do curso **547 — IA no Universo Kubernetes**.

A VM sobe com Ubuntu 22.04, Docker, kind e todas as ferramentas de IA já instaladas.

---

## Pré-Requisitos (máquina do aluno)

| Software | Versão mínima | Download |
|----------|:-------------:|----------|
| VirtualBox | 6.1+ | https://www.virtualbox.org/wiki/Downloads |
| Vagrant | 2.3+ | https://developer.hashicorp.com/vagrant/downloads |

**Recursos necessários na máquina host:**
- CPU: 4 vCPUs disponíveis para a VM
- RAM: 8 GB disponíveis para a VM (16 GB no host recomendado)
- Disco: ~15 GB livres
- Internet: necessária para baixar a box e as ferramentas

---

## Iniciando o Ambiente

```bash
# 1. Clonar ou baixar este repositório
git clone <url-do-repo>
cd 547

# 2. Subir a VM (primeira vez demora ~15-20 min)
vagrant up

# 3. Acessar a VM
vagrant ssh
```

> O provisionamento instala automaticamente: Docker, kubectl, kind, Helm, Trivy,
> K8sGPT, HolmesGPT, kubectl-ai, kube-copilot e cria o cluster Kubernetes.

---

## Configurando as Chaves de API

Dentro da VM, configure as chaves antes de começar os labs:

```bash
# Obrigatória — usada em 5 dos 7 labs (gratuita)
export OPENROUTER_API_KEY="sk-or-v1-sua-chave"

# Obrigatória para Lab 03 — kubectl-ai (gratuita)
export GEMINI_API_KEY="AIza-sua-chave"

# Obrigatória para Lab 02 — HolmesGPT (~US$ 5-10 de crédito)
export OPENAI_API_KEY="sk-sua-chave"
```

Para persistir entre sessões, adicione ao `~/.bashrc` dentro da VM:

```bash
echo 'export OPENROUTER_API_KEY="sk-or-v1-sua-chave"' >> ~/.bashrc
echo 'export GEMINI_API_KEY="AIza-sua-chave"'         >> ~/.bashrc
echo 'export OPENAI_API_KEY="sk-sua-chave"'           >> ~/.bashrc
source ~/.bashrc
```

> Onde obter as chaves:
> - OpenRouter: https://openrouter.ai (gratuito, sem cartão)
> - Google AI Studio: https://aistudio.google.com/apikey (gratuito)
> - OpenAI: https://platform.openai.com (requer crédito ~US$ 5–10)

---

## Verificando o Ambiente

```bash
bash /labs/verificar.sh
```

Saída esperada:

```
=== Ferramentas Base ===
Docker version 26.x.x
kubectl: v1.xx
kind v0.22.0
helm v3.x.x
trivy Version: x.x.x
Python 3.10.x

=== Ferramentas de IA ===
k8sgpt: vx.x.x
holmesgpt: x.x.x
kubectl-ai: ok
kube-copilot: ok

=== Chaves de API ===
OK  OPENROUTER_API_KEY
OK  GEMINI_API_KEY
OK  OPENAI_API_KEY

=== Cluster Kubernetes ===
NAME                        STATUS   ROLES
k8s-ai-labs-control-plane   Ready    control-plane
k8s-ai-labs-worker          Ready    <none>
k8s-ai-labs-worker2         Ready    <none>
```

---

## Estrutura dos Labs

```
labs/
├── lab-01-k8sgpt/              # Diagnóstico inteligente de clusters
│   ├── LAB.md                  ← instruções do lab
│   └── falhas.yaml             ← manifests com falhas para o lab
│
├── lab-02-holmesgpt/           # Root cause analysis com IA
│   ├── LAB.md
│   └── manifests/
│       └── incidente.yaml
│
├── lab-03-kubectl-ai/          # Kubernetes por linguagem natural
│   ├── LAB.md
│   └── manifests/
│       └── workloads.yaml
│
├── lab-04-kube-copilot/        # Auditoria de segurança com IA
│   ├── LAB.md
│   └── manifests/
│       └── auditoria.yaml
│
├── lab-05-trivy-ia/            # Scan de vulnerabilidades com IA
│   ├── LAB.md
│   ├── trivy-ia.py             ← script de análise com OpenRouter
│   ├── trivy-compare.py        ← script de comparação de imagens
│   └── manifests/
│       └── targets.yaml
│
├── lab-06-goldilocks/          # Otimização de resources com IA
│   ├── LAB.md
│   ├── goldilocks-ia.py        ← script de análise com OpenRouter
│   └── manifests/
│       └── workloads.yaml
│
└── lab-07-incidentes-simulados/ # Lab integrador — todas as ferramentas
    ├── LAB.md
    └── manifests/
        ├── cenario-01.yaml
        └── cenario-02.yaml
```

---

## Executando os Labs

```bash
# Acessar a VM
vagrant ssh

# Navegar até o lab desejado
cd /labs/lab-01-k8sgpt

# Ler as instruções
cat LAB.md

# Aplicar os manifests do lab
kubectl apply -f falhas.yaml
```

Cada `LAB.md` contém:
- Objetivo do lab
- Passo a passo comentado
- Comandos prontos para executar
- Pontos de atenção e boas práticas

---

## Comandos Úteis do Vagrant

```bash
vagrant up          # subir a VM
vagrant ssh         # acessar a VM
vagrant halt        # desligar a VM
vagrant destroy     # destruir a VM (apaga tudo)
vagrant reload      # reiniciar a VM
vagrant provision   # re-executar o provisionamento
```

---

## Limpeza entre Labs

Cada lab usa um namespace isolado. Para limpar após terminar um lab:

```bash
# Exemplo: limpar o namespace do lab 01
kubectl delete namespace lab-k8sgpt
```

O cluster kind persiste entre sessões — não precisa recriar a cada `vagrant ssh`.
Para recriar o cluster do zero:

```bash
kind delete cluster --name k8s-ai-labs
kind create cluster --config /ambiente/kind-cluster.yaml
```

---

> **Segurança:** nunca commite chaves de API. Adicione `.env` ao `.gitignore`.
