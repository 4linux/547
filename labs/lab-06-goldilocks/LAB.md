# Lab 06 — Goldilocks + IA: Otimização de Resources Kubernetes
### Curso 541 — IA no Universo Kubernetes

---

## Objetivo do Lab

Instalar o Goldilocks com VPA para coletar recomendações de resources, integrar
com IA para análise inteligente e aprender a dimensionar corretamente CPU e memória
dos workloads Kubernetes.

---

## O problema que o Goldilocks resolve

Definir `requests` e `limits` corretos é um dos maiores desafios práticos no
Kubernetes. Times geralmente erram para um dos dois lados:

| Problema | Consequência |
|---|---|
| **Superprovisionado** | Nós com capacidade desperdiçada, custos altos |
| **Subprovisionado** | OOMKilled, throttling de CPU, instabilidade |
| **Sem resources** | Pod pode consumir todo o nó, afetando outros workloads |

O Goldilocks usa o **VPA Recommender** para observar o uso real dos pods e
gerar recomendações baseadas em dados — não em chutes.

---

## Pré-Requisitos

- Cluster kind em execução
- Helm instalado
- kubectl instalado
- OPENROUTER_API_KEY configurada
- Python 3.6+

---

## Parte 1 — Instalando o Metrics Server

O VPA precisa de métricas de uso para gerar recomendações.
No kind, o Metrics Server precisa de um patch especial:

```bash
# Instalar o Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch necessário para kind (TLS inseguro em ambiente local)
kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

# Verificar
kubectl get pods -n kube-system | grep metrics-server
```

---

## Parte 2 — Instalando o VPA (apenas o Recommender)

> Instalamos **apenas o Recommender** — sem o Updater nem o Admission Webhook,
> para evitar que o VPA altere os pods automaticamente.

```bash
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler
./hack/vpa-up.sh
cd ../..

# Verificar
kubectl get pods -n kube-system | grep vpa
```

---

## Parte 3 — Instalando o Goldilocks

```bash
helm repo add fairwinds-stable https://charts.fairwinds.com/stable
helm repo update

helm install goldilocks fairwinds-stable/goldilocks \
  --namespace goldilocks \
  --create-namespace

# Verificar
kubectl get pods -n goldilocks
```

---

## Parte 4 — Subindo os Workloads

> O cluster já deve estar em execução desde o início do lab.
> Se ainda não subiu, execute: `kind create cluster --config ../../ambiente/kind-cluster.yaml`

```bash
kubectl apply -f manifests/workloads.yaml
kubectl get pods -n lab-goldilocks
```

**Workloads criados:**

| Deployment | Cenário |
|---|---|
| `app-superprovisionada` | requests muito acima do necessário (512Mi / 500m) |
| `app-subprovisionada` | requests muito abaixo (1Mi / 1m) — risco de OOMKilled |
| `app-sem-resources` | sem resources definidos — pior prática |
| `app-bem-dimensionada` | referência com boas práticas (32Mi / 50m) |

> O namespace `lab-goldilocks` já vem com a label
> `goldilocks.fairwinds.com/enabled: "true"` — o Goldilocks começa a criar
> VPAs automaticamente assim que os pods sobem.

---

## Parte 5 — Aguardando as Recomendações

O VPA precisa observar o uso dos pods por alguns minutos antes de gerar
recomendações. Acompanhe a criação dos VPAs:

```bash
# Verificar se os VPAs foram criados
kubectl get vpa -n lab-goldilocks

# Ver detalhes de um VPA específico
kubectl describe vpa goldilocks-app-superprovisionada -n lab-goldilocks
```

> Aguarde **5-10 minutos** para o VPA coletar métricas suficientes.
> Em produção, recomenda-se aguardar 24-48h para recomendações mais precisas.

---

## Parte 6 — Dashboard do Goldilocks

O Goldilocks tem um dashboard visual para ver todas as recomendações:

```bash
kubectl -n goldilocks port-forward svc/goldilocks-dashboard 8080:80
```

Acesse: http://localhost:8080

O dashboard mostra para cada deployment:
- Resources atuais vs. recomendados
- Classes QoS (Guaranteed vs. Burstable)
- YAML pronto para copiar e aplicar

---

## Parte 7 — Goldilocks + IA

Enquanto espera as recomendações ou após tê-las, use o script para análise
com IA:

```bash
export OPENROUTER_API_KEY="sua_chave_aqui"
python3 goldilocks-ia.py
```

Para analisar um namespace diferente:
```bash
export GOLDILOCKS_NAMESPACE="outro-namespace"
python3 goldilocks-ia.py
```

### O que a IA entrega

Para cada deployment, o relatório contém:

1. **Classificação** — superprovisionado, subprovisionado ou adequado
2. **Diferença percentual** — quanto está acima ou abaixo do recomendado
3. **Impacto financeiro** — economia potencial ou risco de instabilidade
4. **YAML corrigido** — pronto para aplicar
5. **Priorização** — qual ajustar primeiro

---

## Parte 8 — Aplicando as Recomendações

Após entender as recomendações, aplique as correções:

```bash
# Exemplo: corrigindo a app superprovisionada
kubectl patch deployment app-superprovisionada -n lab-goldilocks --patch '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "resources": {
            "requests": {"memory": "32Mi", "cpu": "50m"},
            "limits":   {"memory": "64Mi", "cpu": "100m"}
          }
        }]
      }
    }
  }
}'
```

Depois rode o script novamente para ver as recomendações atualizadas.

---

## Parte 9 — Limpeza do Ambiente

```bash
kubectl delete namespace lab-goldilocks
helm uninstall goldilocks -n goldilocks
kubectl delete namespace goldilocks
kind delete cluster --name k8s-ai-labs
```

---

## Resumo do Lab

| Etapa | O que foi feito |
|---|---|
| Instalação | Metrics Server + VPA Recommender + Goldilocks |
| Workloads | 4 cenários: superprovisionado, subprovisionado, sem resources, adequado |
| Dashboard | Visualização das recomendações no browser |
| Goldilocks + IA | Análise inteligente com impacto financeiro e YAML corrigido |
| Correção | Resources ajustados com base nas recomendações |

---

## Pontos de Atenção

- O VPA Recommender precisa de tempo para coletar dados — mínimo 5-10 minutos em lab, 24-48h em produção
- **Nunca instale o VPA Updater + Admission Webhook junto com HPA** — eles conflitam
- O Goldilocks é somente leitura — não altera recursos automaticamente
- Recomendações baseadas em pouco tempo de uso podem ser imprecisas
- Em produção, aplique as mudanças gradualmente e monitore o comportamento