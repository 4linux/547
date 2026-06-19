# Lab 01 — K8sGPT: Diagnóstico Inteligente de Clusters
### Curso 541 — IA no Universo Kubernetes

---

## Objetivo do Lab

Instalar e configurar o K8sGPT, criar um cluster Kubernetes com falhas propositais
e utilizar a ferramenta para diagnosticar e interpretar os problemas automaticamente
com auxílio de IA.

---

## Pré-requisitos

- kind instalado → https://kind.sigs.k8s.io/docs/user/quick-start/#installation
- kubectl instalado → https://kubernetes.io/docs/tasks/tools/
- Conta no OpenRouter com API key → https://openrouter.ai
- ~2GB de espaço em disco
- ~4GB de RAM disponíveis

---

## Parte 1 — Preparando o Ambiente

### 1.1 Subindo o cluster kind

```bash
kind create cluster --config ../../ambiente/kind-cluster.yaml
```

Verifique se o cluster está saudável:

```bash
kubectl get nodes
```

Saída esperada:
```
NAME                       STATUS   ROLES           AGE   VERSION
lab-k8sgpt-control-plane   Ready    control-plane   30s   v1.x.x
lab-k8sgpt-worker          Ready    <none>          15s   v1.x.x
lab-k8sgpt-worker2         Ready    <none>          15s   v1.x.x
```

---

### 1.2 Instalando o K8sGPT

**Linux / macOS (via brew):**
```bash
brew install k8sgpt
```

**Linux (via binário):**
```bash
curl -LO https://github.com/k8sgpt-ai/k8sgpt/releases/latest/download/k8sgpt_Linux_x86_64.tar.gz
tar -xzf k8sgpt_Linux_x86_64.tar.gz
sudo mv k8sgpt /usr/local/bin/
```

Verifique a instalação:
```bash
k8sgpt version
```

---

### 1.3 Configurando o Backend de IA (OpenRouter)

```bash
export OPENROUTER_API_KEY="sua_chave_aqui"
```

Configure o K8sGPT para usar o OpenRouter e defina como Default:

```bash
k8sgpt auth add \
  --backend openai \
  --model openrouter/auto \
  --baseurl https://openrouter.ai/api/v1 \
  --password $OPENROUTER_API_KEY

k8sgpt auth default --provider openai
```



Liste os backends configurados:
```bash
k8sgpt auth list
```

---

## Parte 2 — Criando as Falhas no Cluster

### 2.1 Aplicando os manifests com falhas

```bash
kubectl apply -f falhas.yaml
```

### 2.2 Aguardando os pods entrarem em estado de falha

```bash
watch kubectl get pods -n lab-falhas
```

Aguarde cerca de 1-2 minutos até ver os estados de falha:

```
NAME                              READY   STATUS             RESTARTS   AGE
app-imagem-invalida-xxx           0/1     ImagePullBackOff   0          90s
app-crash-xxx                     0/1     CrashLoopBackOff   3          90s
app-oom-xxx                       0/1     OOMKilled          2          90s
app-backend-xxx                   1/1     Running            0          90s
app-com-pvc-xxx                   0/1     Pending            0          90s
app-probe-errada-xxx              0/1     Running            0          90s
```

> **Dica:** Antes de rodar o K8sGPT, tente identificar manualmente os problemas
> usando `kubectl describe pod <nome> -n lab-falhas`. Isso ajuda a comparar
> o diagnóstico manual com o diagnóstico assistido por IA.

---

## Parte 3 — Diagnóstico com K8sGPT

### 3.1 Análise básica do cluster

```bash
k8sgpt analyze
```

### 3.2 Análise focada no namespace de falhas

```bash
k8sgpt analyze --namespace lab-falhas
```

### 3.3 Análise com explicação detalhada da IA

```bash
k8sgpt analyze --namespace lab-falhas --explain --backend openai --language portuguese
```

> O flag `--explain` é o que aciona a IA. Sem ele, o K8sGPT apenas lista
> os problemas. Com ele, a IA explica o que está errado e sugere correções.

### 3.4 Filtrando por tipo de recurso

Analisar apenas Pods:
```bash
k8sgpt analyze --namespace lab-falhas --explain --filter Pod -backend openai --language portuguese
```

Analisar apenas Services:
```bash
k8sgpt analyze --namespace lab-falhas --explain --filter Service --backend openai --language portuguese
```

Analisar apenas PVCs:
```bash
k8sgpt analyze --namespace lab-falhas --explain --filter PersistentVolumeClaim --backend openai --language portuguese
```

Tipos disponíveis:
```bash
k8sgpt filters list
```

### 3.5 Exportando o relatório

Em JSON (útil para automações):
```bash
k8sgpt analyze --namespace lab-falhas --explain --output json > relatorio.json
```

---

## Parte 4 — Interpretando os Resultados

### O que esperar do diagnóstico

Para cada falha criada, o K8sGPT deve identificar e explicar:

| Falha | O que o K8sGPT deve reportar |
|---|---|
| `app-imagem-invalida` | Imagem não encontrada no registry, verificar nome e tag |
| `app-crash` | Container terminando com exit code 1, verificar logs |
| `app-oom` | Container excedendo limite de memória, aumentar memory limit |
| `svc-backend` | Service sem endpoints, selector não bate com labels dos pods |
| `pvc-sem-storage` | PVC em Pending, StorageClass não encontrada no cluster |
| `app-probe-errada` | Liveness probe falhando, endpoint /healthz não existe |

### Comparando diagnóstico manual vs. IA

Execute o comando abaixo para cada pod com falha e compare com o que o K8sGPT reportou:

```bash
kubectl describe pod -l falha=imagepullbackoff -n lab-falhas
kubectl describe pod -l falha=crashloopbackoff -n lab-falhas
kubectl describe pod -l falha=oomkilled -n lab-falhas
kubectl describe pod -l falha=liveness-probe -n lab-falhas
```

> **Reflexão:** O K8sGPT não apenas lista o erro — ele explica o *porquê*
> e sugere como corrigir. Para um SRE, isso reduz drasticamente o tempo
> de investigação, especialmente em incidentes fora do horário comercial.

---

## Parte 5 — Corrigindo as Falhas

Após o diagnóstico, corrija cada problema e observe o K8sGPT deixar de reportá-los.

### Falha 1: ImagePullBackOff
```bash
kubectl set image deployment/app-imagem-invalida \
  app=nginx:alpine -n lab-falhas
```

### Falha 2: CrashLoopBackOff
```bash
kubectl set image deployment/app-crash \
  app=nginx:alpine -n lab-falhas
```

### Falha 3: OOMKilled
```bash
kubectl patch deployment app-oom -n lab-falhas --patch '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "image": "nginx:alpine",
          "resources": {
            "limits": {"memory": "128Mi"},
            "requests": {"memory": "64Mi"}
          }
        }]
      }
    }
  }
}'
```

### Falha 4: Service selector errado
```bash
kubectl patch service svc-backend -n lab-falhas \
  --patch '{"spec": {"selector": {"app": "backend"}}}'
```

### Falha 5: PVC sem StorageClass
```bash
kubectl patch pvc pvc-sem-storage -n lab-falhas \
  --patch '{"spec": {"storageClassName": "standard"}}'
```

### Falha 6: Liveness probe errada
```bash
kubectl patch deployment app-probe-errada -n lab-falhas --patch '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "app",
          "livenessProbe": {
            "httpGet": {
              "path": "/",
              "port": 80
            }
          }
        }]
      }
    }
  }
}'
```

### Verificando que as correções funcionaram

```bash
watch kubectl get pods -n lab-falhas
```

Todos os pods devem estar `Running` e `Ready`.

### Rodando o K8sGPT novamente

```bash
k8sgpt analyze --namespace lab-falhas --explain
```

Saída esperada:
```
No problems detected
```

---

## Parte 6 — Limpeza do Ambiente

```bash
kubectl delete namespace lab-falhas
kind delete cluster --name lab-k8sgpt
```

---

## Resumo do Lab

| Etapa | O que foi feito |
|---|---|
| Ambiente | Cluster kind com 1 control-plane e 2 workers |
| Falhas criadas | ImagePullBackOff, CrashLoopBackOff, OOMKilled, Service sem endpoints, PVC Pending, Liveness probe errada |
| Diagnóstico | K8sGPT com backend OpenRouter identificou e explicou todas as falhas |
| Correções | Todas as falhas corrigidas e validadas |
| Resultado | Cluster saudável — K8sGPT confirma "No problems detected" |

---

## Pontos de Atenção

- O K8sGPT **não corrige** — ele diagnostica e sugere. A ação é sempre do engenheiro.
- A qualidade da explicação depende do modelo de IA escolhido no backend.
- Em ambientes corporativos, avalie se os dados do cluster podem ser enviados para APIs externas.
- O flag `--explain` consome tokens da API — em clusters grandes, filtre por namespace ou tipo de recurso.
