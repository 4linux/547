# 547 — IA no Universo Kubernetes
## Repositório de Laboratórios

Este repositório contém o ambiente completo de laboratórios do curso
**547 — IA no Universo Kubernetes** da 4Linux.

Você vai aprender a usar **6 ferramentas open source de IA** para diagnosticar
incidentes, auditar segurança, operar clusters via linguagem natural e otimizar
resources — tudo em Kubernetes real.

---

## O que você vai praticar

| Lab | Ferramenta | O que você faz |
|-----|-----------|---------------|
| Lab 01 | **K8sGPT** | Cria falhas propositais num cluster e deixa a IA diagnosticar tudo |
| Lab 02 | **HolmesGPT** | Simula 3 incidentes reais (ConfigMap errado, RBAC faltando, memória insuficiente) e usa IA para encontrar a causa raiz |
| Lab 03 | **kubectl-ai** | Opera o cluster inteiro via linguagem natural — sem decorar flags |
| Lab 04 | **Kube-copilot** | Audita pods com problemas de segurança e aprende o que corrigi-los |
| Lab 05 | **Trivy + IA** | Escaneia imagens de container e recebe análise inteligente dos CVEs |
| Lab 06 | **Goldilocks + IA** | Descobre que seus pods estão com resources mal dimensionados e corrige |
| Lab 07 | **Lab Integrador** | Dois cenários de incidente real — você usa todas as ferramentas sem passo a passo |

---

## Pré-Requisitos (máquina do aluno)

### Para usar a VM automática (recomendado):

| Software | Versão mínima | Download |
|----------|:-------------:|----------|
| VirtualBox | 6.1+ | https://www.virtualbox.org/wiki/Downloads |
| Vagrant | 2.3+ | https://developer.hashicorp.com/vagrant/downloads |

**Recursos mínimos do host:**
- 4 vCPUs disponíveis para a VM
- 8 GB RAM disponíveis (16 GB no host recomendado)
- 15 GB de disco livre
- Internet para baixar a box e ferramentas

### Para instalar manualmente (sem VM):
Docker, kubectl, kind, Helm, Trivy, Python 3.10+, Go 1.21+.
Siga o Capítulo 03 da apostila para o passo a passo completo.

---

## Contas de IA necessárias

Antes de começar, crie as contas abaixo. São necessárias para os labs — sem elas as ferramentas de IA não funcionam.

| Conta | Custo | Para que serve | Onde criar |
|-------|-------|---------------|-----------|
| **OpenRouter** | Gratuito | K8sGPT, Kube-copilot, Trivy + IA, Goldilocks + IA | https://openrouter.ai |
| **Google AI Studio** | Gratuito | kubectl-ai (Gemini 2.5 Flash) | https://aistudio.google.com/apikey |
| **OpenAI** | ~US$ 5–10 de crédito | HolmesGPT (obrigatório modelo pago) | https://platform.openai.com |

> O HolmesGPT é a única ferramenta paga — seu loop agêntico exige tool calling
> robusto que modelos gratuitos não suportam. US$ 5 é suficiente para o lab inteiro.

---

## Iniciando o Ambiente (opção automática)

```bash
# 1. Clonar este repositório
git clone https://github.com/4linux/547.git
cd 547

# 2. Subir a VM — primeira vez demora ~15-20 min para baixar e provisionar
vagrant up

# 3. Acessar a VM
vagrant ssh
```

Dentro da VM, **tudo já está instalado**: Docker, kubectl, kind (com cluster criado),
Helm, Trivy, K8sGPT, HolmesGPT, kubectl-ai e kube-copilot.

Você só precisa configurar as chaves de API:

```bash
# Dentro da VM
export OPENROUTER_API_KEY="sk-or-v1-sua-chave"   # gratuito, sem cartão
export GEMINI_API_KEY="AIza-sua-chave"            # gratuito, conta Google
export OPENAI_API_KEY="sk-sua-chave"              # requer crédito ~US$ 5

# Persistir entre sessões
echo 'export OPENROUTER_API_KEY="sk-or-v1-sua-chave"' >> ~/.bashrc
echo 'export GEMINI_API_KEY="AIza-sua-chave"'         >> ~/.bashrc
echo 'export OPENAI_API_KEY="sk-sua-chave"'           >> ~/.bashrc
source ~/.bashrc
```

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

Se alguma chave aparecer como `FALTA`, configure a variável correspondente
conforme a seção "Contas de IA" acima.

---

## Executando os Labs

Os labs estão em `/labs/` dentro da VM (pasta `labs/` no repositório).

```bash
# Acessar o diretório do lab desejado
cd /labs/lab-01-k8sgpt

# Ler as instruções completas
cat LAB.md

# Aplicar os recursos do lab
kubectl apply -f falhas.yaml
```

Cada `LAB.md` é autocontido e inclui:
- **Objetivo** — o que você vai aprender
- **Pré-requisitos** — o que precisa estar funcionando
- **Passo a passo** — comandos numerados e comentados
- **O que esperar** — exemplos de saída esperada
- **Pontos de atenção** — erros comuns e como evitá-los
- **Limpeza** — como resetar o namespace ao terminar

---

## Estrutura dos Labs

```
labs/
├── lab-01-k8sgpt/                  # K8sGPT — diagnóstico inteligente
│   ├── LAB.md                      ← leia primeiro
│   └── falhas.yaml                 ← manifests com 6 tipos de falha
│
├── lab-02-holmesgpt/               # HolmesGPT — root cause analysis
│   ├── LAB.md
│   └── manifests/
│       └── incidente.yaml          ← 3 incidentes simultâneos
│
├── lab-03-kubectl-ai/              # kubectl-ai — linguagem natural
│   ├── LAB.md
│   └── manifests/
│       └── workloads.yaml          ← recursos para operar
│
├── lab-04-kube-copilot/            # Kube-copilot — auditoria de segurança
│   ├── LAB.md
│   └── manifests/
│       └── auditoria.yaml          ← pods com diferentes níveis de segurança
│
├── lab-05-trivy-ia/                # Trivy + IA — scan de vulnerabilidades
│   ├── LAB.md
│   ├── trivy-ia.py                 ← script: escaneia imagem e analisa com IA
│   ├── trivy-compare.py            ← script: compara duas imagens lado a lado
│   └── manifests/
│       └── targets.yaml
│
├── lab-06-goldilocks/              # Goldilocks + IA — otimização de resources
│   ├── LAB.md
│   ├── goldilocks-ia.py            ← script: coleta VPAs e analisa com IA
│   └── manifests/
│       └── workloads.yaml          ← 4 cenários de dimensionamento
│
└── lab-07-incidentes-simulados/    # Lab integrador — sem passo a passo
    ├── LAB.md
    └── manifests/
        ├── cenario-01.yaml         ← "a app subiu mas não responde"
        └── cenario-02.yaml         ← "o deploy foi feito mas nada funciona"
```

---

## Sequência Recomendada

Os labs foram desenhados para serem feitos em ordem — cada um usa ferramentas
ensinadas no anterior:

```
Lab 01 (K8sGPT)
  → Lab 02 (HolmesGPT)
    → Lab 03 (kubectl-ai)
      → Lab 04 (Kube-copilot)
        → Lab 05 (Trivy + IA)
          → Lab 06 (Goldilocks + IA)
            → Lab 07 (Integrador — usa tudo)
```

O **Lab 07** é o desafio final: dois cenários de incidente reais sem passo a passo.
Você decide quais ferramentas usar e em que ordem.

---

## Limpeza entre Labs

Cada lab usa um namespace isolado. Ao terminar um lab, limpe o namespace:

```bash
kubectl delete namespace lab-falhas          # Lab 01
kubectl delete namespace lab-holmes          # Lab 02
kubectl delete namespace lab-kubectl-ai      # Lab 03
kubectl delete namespace lab-kube-copilot    # Lab 04
kubectl delete namespace lab-trivy           # Lab 05
kubectl delete namespace lab-goldilocks      # Lab 06
kubectl delete namespace incidente-1 incidente-2  # Lab 07
```

O cluster kind **persiste entre sessões** — não precisa recriar a cada `vagrant ssh`.

Para recriar o cluster do zero:
```bash
kind delete cluster --name k8s-ai-labs
kind create cluster --config /ambiente/kind-cluster.yaml
```

---

## Comandos Úteis do Vagrant

```bash
vagrant up          # subir a VM
vagrant ssh         # acessar a VM
vagrant halt        # desligar a VM (preserva o estado)
vagrant destroy     # destruir a VM (apaga tudo)
vagrant reload      # reiniciar a VM
vagrant provision   # re-executar o provisionamento
```

---

## Dúvidas Frequentes

**O cluster some depois de `vagrant halt`?**
Não — o kind persiste dentro da VM. Ao fazer `vagrant up` novamente, o cluster
ainda está lá. Se por algum motivo o cluster sumiu:
```bash
kind create cluster --config /ambiente/kind-cluster.yaml
```

**Erro 429 no Gemini (kubectl-ai)?**
O Gemini Free tem limite de 250 req/dia. Se estourar, use o OpenRouter como fallback:
```bash
export OPENAI_API_KEY=$OPENROUTER_API_KEY
export OPENAI_ENDPOINT="https://openrouter.ai/api/v1"
kubectl-ai --llm-provider=openai --model "openai/gpt-oss-20b:free" "sua pergunta"
```

**HolmesGPT trava ou não responde?**
É normal demorar 1-2 minutos — ele faz dezenas de queries no cluster antes de
responder. Se passar de 5 minutos, verifique se `OPENAI_API_KEY` está configurada
e se há crédito na conta OpenAI.

**Como verificar se as ferramentas de IA estão configuradas?**
```bash
bash /labs/verificar.sh
```

---

> **Segurança:** nunca commite chaves de API. Adicione `.env` ao `.gitignore`.
> As variáveis de ambiente dentro da VM não são commitadas.
