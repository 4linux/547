# Relatório de Otimização de Resources — Goldilocks + IA
## Namespace: lab-goldilocks

---

## Recomendações do Goldilocks (VPA)


### Deployment: goldilocks-app-bem-dimensionada

  Container: app
  Recomendado (target):  cpu=25m memory=250Mi
  Mínimo (lowerBound):   cpu=25m memory=250Mi
  Máximo (upperBound):   cpu=895m memory=1920111149

### Deployment: goldilocks-app-sem-resources

  Container: app
  Recomendado (target):  cpu=25m memory=250Mi
  Mínimo (lowerBound):   cpu=25m memory=250Mi
  Máximo (upperBound):   cpu=890m memory=2933870609

### Deployment: goldilocks-app-subprovisionada

  Container: app
  Recomendado (target):  cpu=25m memory=250Mi
  Mínimo (lowerBound):   cpu=25m memory=250Mi
  Máximo (upperBound):   cpu=25m memory=250Mi

### Deployment: goldilocks-app-superprovisionada

  Container: app
  Recomendado (target):  cpu=25m memory=250Mi
  Mínimo (lowerBound):   cpu=25m memory=250Mi
  Máximo (upperBound):   cpu=875m memory=1876968835

---

## Análise e Recomendações da IA

A leitura prática é esta: **todos os workloads convergiram para request recomendado de `cpu=25m` e `memory=250Mi`**.  
O que muda é o **estado atual** de cada deployment e o **risco/custo** do ajuste.

> **Observação importante:** o output do Goldilocks mostra o recomendado, mas **não mostra os resources atuais** de cada deployment.  
> Então o **% exato** só é calculável quando o valor atual é conhecido. Onde não dá para fechar a conta, eu marco **N/D**.

---

## 1) Diagnóstico por deployment

### Resumo executivo

| Deployment | Diagnóstico | Diferença vs recomendado | Impacto financeiro / operacional | Ação |
|---|---|---:|---|---|
| `goldilocks-app-bem-dimensionada` | **Bem dimensionado** | **CPU: 0% / Mem: 0%** *(assumindo que já está em 25m/250Mi)* | Impacto financeiro praticamente nulo | Manter e monitorar |
| `goldilocks-app-sem-resources` | **Sem dimensionamento** *(não está bem dimensionado)* | **N/D** | Pode aumentar custo “visível” ao declarar requests, mas reduz risco de contenção, noisy neighbor e scheduling ruim | Corrigir logo |
| `goldilocks-app-subprovisionada` | **Subprovisionado** | **N/D** *(mas será aumento)* | Pequeno aumento de custo reservado, com grande redução de risco de instabilidade | **Prioridade alta** |
| `goldilocks-app-superprovisionada` | **Superprovisionado** | **N/D** *(mas será redução)* | **Economia direta** por melhorar densidade no cluster e reduzir desperdício | **Prioridade alta em FinOps** |

---

### Deployment: `goldilocks-app-bem-dimensionada`

- **Classificação:** bem dimensionado
- **Recomendado:** `25m / 250Mi`
- **Leitura prática:** se ele já está nesses valores
