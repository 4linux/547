#!/usr/bin/env python3
"""
goldilocks-ia.py — Integração Goldilocks + IA
Coleta recomendações do VPA via Goldilocks e envia para análise
e sugestões de otimização via OpenRouter.
"""

import json
import subprocess
import urllib.request
import urllib.error
import sys
import os

# ─── Configurações ────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL   = os.getenv("GOLDILOCKS_IA_MODEL", "openrouter/auto")
NAMESPACE          = os.getenv("GOLDILOCKS_NAMESPACE", "lab-goldilocks")
# ──────────────────────────────────────────────────────────────────────────────


def rodar_kubectl(args):
    """Executa um comando kubectl e retorna o output."""
    resultado = subprocess.run(
        ["kubectl"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout = resultado.stdout.decode("utf-8") if isinstance(resultado.stdout, bytes) else resultado.stdout
    stderr = resultado.stderr.decode("utf-8") if isinstance(resultado.stderr, bytes) else resultado.stderr
    return stdout, stderr, resultado.returncode


def coletar_vpas(namespace):
    """Coleta os objetos VPA criados pelo Goldilocks."""
    print(f"\n[Goldilocks] Coletando VPAs do namespace: {namespace}")
    stdout, stderr, rc = rodar_kubectl([
        "get", "vpa", "-n", namespace, "-o", "json"
    ])
    if rc != 0:
        print(f"[ERRO] Falha ao coletar VPAs: {stderr}")
        print("       Verifique se o Goldilocks está instalado e o namespace habilitado.")
        sys.exit(1)
    return json.loads(stdout) if stdout else {"items": []}


def coletar_deployments(namespace):
    """Coleta os deployments do namespace com seus resources atuais."""
    stdout, stderr, rc = rodar_kubectl([
        "get", "deployments", "-n", namespace, "-o", "json"
    ])
    if rc != 0:
        return {"items": []}
    return json.loads(stdout) if stdout else {"items": []}


def formatar_recomendacoes(vpas, deployments):
    """Formata as recomendações do VPA para o prompt."""
    linhas = []

    # Mapa de resources atuais por deployment
    resources_atuais = {}
    for dep in deployments.get("items", []):
        nome = dep["metadata"]["name"]
        containers = dep["spec"]["template"]["spec"].get("containers", [])
        for c in containers:
            resources_atuais[nome] = c.get("resources", {})

    for vpa in vpas.get("items", []):
        nome = vpa["metadata"]["name"]
        recomendacao = vpa.get("status", {}).get("recommendation", {})
        containers_rec = recomendacao.get("containerRecommendations", [])

        if not containers_rec:
            linhas.append(f"\n### {nome}")
            linhas.append("  Aguardando dados suficientes para recomendação...")
            continue

        linhas.append(f"\n### Deployment: {nome}")

        # Resources atuais
        atual = resources_atuais.get(nome, {})
        if atual:
            req = atual.get("requests", {})
            lim = atual.get("limits", {})
            linhas.append(f"  Atual — requests: cpu={req.get('cpu','N/A')} memory={req.get('memory','N/A')}")
            linhas.append(f"  Atual — limits:   cpu={lim.get('cpu','N/A')} memory={lim.get('memory','N/A')}")

        for container in containers_rec:
            c_nome = container.get("containerName", "")
            target  = container.get("target", {})
            lower   = container.get("lowerBound", {})
            upper   = container.get("upperBound", {})

            linhas.append(f"\n  Container: {c_nome}")
            linhas.append(f"  Recomendado (target):  cpu={target.get('cpu','N/A')} memory={target.get('memory','N/A')}")
            linhas.append(f"  Mínimo (lowerBound):   cpu={lower.get('cpu','N/A')} memory={lower.get('memory','N/A')}")
            linhas.append(f"  Máximo (upperBound):   cpu={upper.get('cpu','N/A')} memory={upper.get('memory','N/A')}")

    return "\n".join(linhas) if linhas else "Nenhuma recomendação disponível ainda."


def analisar_com_ia(recomendacoes):
    """Envia as recomendações para análise via OpenRouter."""
    if not OPENROUTER_API_KEY:
        print("[ERRO] OPENROUTER_API_KEY não configurada.")
        sys.exit(1)

    prompt = f"""Você é um especialista em otimização de recursos Kubernetes e FinOps.
O Goldilocks (via VPA) analisou os workloads e gerou as seguintes recomendações:

{recomendacoes}

## Sua tarefa:
1. Para cada deployment, explique se está superprovisionado, subprovisionado ou bem dimensionado
2. Calcule a diferença percentual entre o atual e o recomendado (quando disponível)
3. Indique o impacto financeiro de cada ajuste (economia ou risco de instabilidade)
4. Forneça o YAML de resources corrigido para cada deployment
5. Priorize os ajustes por impacto (qual corrigir primeiro)
6. Dê boas práticas gerais de dimensionamento de resources no Kubernetes

Responda em português brasileiro de forma prática e direta.
"""

    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8000,
        "temperature": 0.2
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://lab-goldilocks-ia",
            "X-Title": "Lab Goldilocks IA K8s"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            dados = json.loads(resp.read().decode())
            mensagem = dados.get("choices", [{}])[0].get("message", {})
            conteudo = mensagem.get("content")
            # Modelos de raciocínio colocam a resposta em "reasoning" quando content é null
            if not conteudo:
                conteudo = mensagem.get("reasoning", "")
                if conteudo:
                    print("[INFO] Usando campo 'reasoning' como resposta (modelo de raciocínio)")
            if not conteudo:
                print(f"[AVISO] Resposta vazia. finish_reason: {dados.get('choices',[{}])[0].get('finish_reason')}")
            return conteudo
    except urllib.error.HTTPError as e:
        corpo = e.read().decode()
        print(f"[ERRO] HTTP {e.code}: {corpo}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERRO] Falha ao chamar OpenRouter: {e}")
        sys.exit(1)


def salvar_relatorio(recomendacoes, analise_ia, namespace):
    """Salva o relatório completo em Markdown."""
    caminho = f"relatorio_goldilocks_{namespace}.md"
    conteudo = f"""# Relatório de Otimização de Resources — Goldilocks + IA
## Namespace: {namespace}

---

## Recomendações do Goldilocks (VPA)

{recomendacoes}

---

## Análise e Recomendações da IA

{analise_ia}
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"\n[OK] Relatório salvo em: {caminho}")


def main():
    print("=" * 60)
    print("  Goldilocks + IA — Otimização de Resources K8s")
    print("=" * 60)

    namespace = NAMESPACE

    print(f"\n[1/4] Coletando VPAs do namespace '{namespace}'...")
    vpas = coletar_vpas(namespace)
    print(f"      {len(vpas.get('items', []))} VPA(s) encontrado(s).")

    print("\n[2/4] Coletando deployments...")
    deployments = coletar_deployments(namespace)

    print("\n[3/4] Formatando recomendações...")
    recomendacoes = formatar_recomendacoes(vpas, deployments)
    print(recomendacoes)

    print("\n[4/4] Enviando para análise da IA...")
    analise = analisar_com_ia(recomendacoes)
    print("\n--- Análise da IA ---")
    print(analise)

    salvar_relatorio(recomendacoes, analise, namespace)
    print("\n[CONCLUÍDO]")


if __name__ == "__main__":
    main()