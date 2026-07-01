# Lab 07 — Incidentes Simulados: Lab Integrador
### Curso 547 — IA no Universo Kubernetes

---

## Objetivo do Lab

Usar todas as ferramentas aprendidas no curso para diagnosticar e resolver
incidentes reais simulados em um cluster Kubernetes. Este é o lab integrador —
não há passo a passo detalhado. O aluno recebe um cluster com problemas e
precisa resolver usando as ferramentas certas.

---

## Regras do Lab

1. **Não há respostas prontas** — use as ferramentas para descobrir os problemas
2. **Use a ferramenta certa para cada situação** — parte do aprendizado é escolher
3. **Documente o root cause de cada problema encontrado**
4. **Corrija e valide** — o cluster deve terminar com todos os pods Running

---

## Ferramentas Disponíveis

| Ferramenta | Quando usar |
|---|---|
| **K8sGPT** | Primeiro scan — visão geral do que está errado |
| **HolmesGPT** | Investigação profunda de um problema específico |
| **kubectl-ai** | Operações e consultas via linguagem natural |
| **Trivy + IA** | Se suspeitar de problema com imagens |
| **Goldilocks** | Se suspeitar de resources mal dimensionados |

---

## Cenário 1 — "A aplicação subiu mas não responde"

### Situação

O time de desenvolvimento fez o deploy de uma aplicação com 4 componentes:
`postgres`, `api`, `frontend` e `worker`. O deploy foi concluído mas a aplicação
não está funcionando. Você foi acionado para investigar.

### Subindo o cenário

```bash
kubectl apply -f manifests/cenario-01.yaml
kubectl get pods -n incidente-1
```

### Sua missão

1. Identifique todos os problemas usando as ferramentas do curso
2. Documente o root cause de cada problema
3. Corrija todos os problemas
4. Valide que todos os pods estão Running

### Dica de abordagem

```bash
# 1. Comece com uma visão geral
k8sgpt analyze --namespace incidente-1 --explain --backend openai --language portuguese

# 2. Para cada problema encontrado, investigue com HolmesGPT
holmes ask "por que o pod api está falhando no namespace incidente-1?"

# 3. Use kubectl-ai para operações
kubectl-ai --model gemini-2.5-flash "liste todos os pods com problema no namespace incidente-1"
```

### Problemas presentes

<details>
<summary>🔍 Ver gabarito (tente resolver antes de abrir!)</summary>

| Componente | Problema | Correção |
|---|---|---|
| `api` | CrashLoopBackOff — `DB_HOST` aponta para `postgres-svc-errado` | Corrigir para `postgres` |
| `frontend` | ImagePullBackOff — imagem `minha-empresa/frontend:v2.1.0` não existe | Trocar por `nginx:alpine` |
| `worker` | OOMKilled — limite de 15Mi insuficiente para o processo Python | Aumentar para 256Mi |
| `postgres` | Running — está ok, mas a API não consegue conectar por hostname errado | Corrigido ao corrigir a API |

**Correções:**

```bash
# Corrigir DB_HOST da API
kubectl set env deployment/api DB_HOST=postgres -n incidente-1

# Corrigir imagem do frontend
kubectl set image deployment/frontend frontend=nginx:alpine -n incidente-1

# Corrigir memória do worker
kubectl patch deployment worker -n incidente-1 --patch '
{
  "spec": {"template": {"spec": {"containers": [{
    "name": "worker",
    "image": "nginx:alpine",
    "resources": {"requests": {"memory": "32Mi"}, "limits": {"memory": "64Mi"}}
  }]}}}
}'
```

</details>

---

## Cenário 2 — "O deploy foi feito mas nada funciona"

### Situação

Um novo ambiente foi provisionado e o time de infra aplicou os manifests.
Três componentes têm problemas distintos. Você precisa identificar e corrigir todos.

### Subindo o cenário

```bash
kubectl apply -f manifests/cenario-02.yaml
kubectl get all -n incidente-2
```

### Sua missão

1. Identifique os 3 problemas usando as ferramentas do curso
2. Documente o root cause de cada um
3. Corrija todos os problemas
4. Valide que o cluster está saudável

### Dica de abordagem

```bash
# Scan geral
k8sgpt analyze --namespace incidente-2 --explain --backend openai --language portuguese

# Investigação profunda
holmes ask "quais problemas existem no namespace incidente-2 e quais são suas causas?"

# Operações via linguagem natural
kubectl-ai --model gemini-2.5-flash "liste todos os recursos com problema no namespace incidente-2"
```

### Problemas presentes

<details>
<summary>🔍 Ver gabarito (tente resolver antes de abrir!)</summary>

| Componente | Problema | Correção |
|---|---|---|
| `job-configuracao` | Error — ServiceAccount sem permissão RBAC para listar ConfigMaps | Criar Role + RoleBinding |
| `app-com-dados` | Pending — PVC `dados-app` usa StorageClass `premium-ssd` inexistente | Corrigir para `standard` |
| `app-probe-errada` | CrashLoopBackOff — Liveness probe aponta para `/healthz` que não existe no nginx | Corrigir para `/` |

**Correções:**

```bash
# Corrigir RBAC
kubectl create role configmap-reader \
  --verb=get,list \
  --resource=configmaps \
  -n incidente-2

kubectl create rolebinding job-configmap-reader \
  --role=configmap-reader \
  --serviceaccount=incidente-2:app-service-account \
  -n incidente-2

# Corrigir StorageClass do PVC (PVC é imutável — delete e recrie)
kubectl delete pvc dados-app -n incidente-2
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dados-app
  namespace: incidente-2
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
EOF

# Corrigir Liveness probe
kubectl patch deployment app-probe-errada -n incidente-2 --patch '
{
  "spec": {"template": {"spec": {"containers": [{
    "name": "app",
    "livenessProbe": {"httpGet": {"path": "/", "port": 80}}
  }]}}}
}'
```

</details>

---

## Validação Final

Após corrigir todos os problemas, valide com as ferramentas:

```bash
# K8sGPT — confirma que não há mais problemas
k8sgpt analyze --namespace incidente-1 --explain --backend openai --language portuguese
k8sgpt analyze --namespace incidente-2 --explain --backend openai --language portuguese

# HolmesGPT — confirmação final
holmes ask "ainda existem problemas nos namespaces incidente-1 e incidente-2?"

# kubectl-ai — verificação geral
kubectl-ai --model gemini-2.5-flash "liste todos os pods de incidente-1 e incidente-2 e seus status"
```

**Resultado esperado:** todos os pods Running e K8sGPT reportando "No problems detected".

---

## Limpeza do Ambiente

```bash
kubectl delete namespace incidente-1 incidente-2
kind delete cluster --name k8s-ai-labs
```

---

## Resumo do Lab

| Cenário | Problemas | Ferramentas usadas |
|---|---|---|
| Cenário 1 | CrashLoopBackOff, ImagePullBackOff, OOMKilled | K8sGPT, HolmesGPT, kubectl-ai |
| Cenário 2 | RBAC, PVC Pending, Liveness probe errada | K8sGPT, HolmesGPT, kubectl-ai |

---

## Pontos de Atenção

- Este lab não tem passo a passo — a investigação é parte do aprendizado
- Use o gabarito apenas depois de tentar resolver sozinho
- O tempo de investigação com IA deve ser significativamente menor que sem ela
- Documente quanto tempo levou com IA vs. quanto levaria manualmente