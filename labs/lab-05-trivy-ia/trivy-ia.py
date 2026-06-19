#!/usr/bin/env python3
"""
trivy-ia.py — Integração Trivy + IA
Escaneia imagens e manifests Kubernetes com Trivy e envia os resultados
para análise e sugestões de correção via OpenRouter.
"""

import json
import subprocess
import urllib.request
import urllib.error
import sys
import os
import argparse

# ─── Configurações ────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL   = os.getenv("TRIVY_IA_MODEL", "openrouter/free")
# ──────────────────────────────────────────────────────────────────────────────


def rodar_trivy_imagem(imagem: str) -> dict:
    """Executa trivy image e retorna o resultado em JSON."""
    print(f"\n[Trivy] Escaneando imagem: {imagem}")
    try:
        resultado = subprocess.run(
            ["trivy", "image", "--format", "json", "--quiet", imagem],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120
        )
        stdout = resultado.stdout.decode("utf-8") if isinstance(resultado.stdout, bytes) else resultado.stdout
        stderr = resultado.stderr.decode("utf-8") if isinstance(resultado.stderr, bytes) else resultado.stderr
        if resultado.returncode != 0 and not stdout:
            print(f"[ERRO] Trivy falhou: {stderr}")
            sys.exit(1)
        return json.loads(stdout)
    except subprocess.TimeoutExpired:
        print("[ERRO] Trivy excedeu o tempo limite de 120s")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERRO] Trivy não encontrado. Instale em: https://aquasecurity.github.io/trivy")
        sys.exit(1)


def rodar_trivy_manifest(arquivo: str) -> dict:
    """Executa trivy config em um manifest Kubernetes."""
    print(f"\n[Trivy] Escaneando manifest: {arquivo}")
    try:
        resultado = subprocess.run(
            ["trivy", "config", "--format", "json", "--quiet", arquivo],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60
        )
        stdout = resultado.stdout.decode("utf-8") if isinstance(resultado.stdout, bytes) else resultado.stdout
        return json.loads(stdout) if stdout else {}
    except FileNotFoundError:
        print("[ERRO] Trivy não encontrado.")
        sys.exit(1)


def resumir_vulnerabilidades(dados: dict) -> str:
    """Extrai e formata as vulnerabilidades mais relevantes do JSON do Trivy."""
    linhas = []
    resultados = dados.get("Results", [])

    for resultado in resultados:
        target = resultado.get("Target", "")
        vulns = resultado.get("Vulnerabilities", []) or []
        misconfigs = resultado.get("Misconfigurations", []) or []

        if vulns:
            # Agrupa por severidade
            criticas  = [v for v in vulns if v.get("Severity") == "CRITICAL"]
            altas     = [v for v in vulns if v.get("Severity") == "HIGH"]
            medias    = [v for v in vulns if v.get("Severity") == "MEDIUM"]

            linhas.append(f"\n### Target: {target}")
            linhas.append(f"Total: {len(vulns)} vulnerabilidades "
                         f"({len(criticas)} CRITICAL, {len(altas)} HIGH, {len(medias)} MEDIUM)\n")

            # Lista as 10 mais graves
            for v in (criticas + altas)[:10]:
                linhas.append(
                    f"- [{v.get('Severity')}] {v.get('VulnerabilityID')} — "
                    f"{v.get('PkgName')} {v.get('InstalledVersion')} "
                    f"(fix: {v.get('FixedVersion', 'sem fix disponível')})\n"
                    f"  {v.get('Title', '')}"
                )

        if misconfigs:
            linhas.append(f"\n### Misconfigurations: {target}")
            for m in misconfigs[:10]:
                linhas.append(
                    f"- [{m.get('Severity')}] {m.get('ID')} — {m.get('Title')}\n"
                    f"  {m.get('Description', '')}"
                )

    return "\n".join(linhas) if linhas else "Nenhuma vulnerabilidade encontrada."


def analisar_com_ia(resumo: str, contexto: str) -> str:
    """Envia o resumo do Trivy para análise via OpenRouter."""
    if not OPENROUTER_API_KEY:
        print("[ERRO] OPENROUTER_API_KEY não configurada.")
        print("       Execute: export OPENROUTER_API_KEY='sua_chave_aqui'")
        sys.exit(1)

    prompt = f"""Você é um especialista em segurança de containers e Kubernetes.
O Trivy escaneou {contexto} e encontrou os seguintes resultados:

{resumo}

## Sua tarefa:
1. Explique as vulnerabilidades mais críticas de forma clara e objetiva
2. Indique o impacto real de cada uma no ambiente Kubernetes
3. Forneça as correções recomendadas com exemplos práticos
4. Sugira boas práticas para evitar esses problemas no futuro
5. Ao final, dê uma nota de segurança geral (0-10) com justificativa

Responda em português brasileiro de forma direta e prática.
"""

    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": 0.2
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://lab-trivy-ia",
            "X-Title": "Lab Trivy IA K8s"
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            dados = json.loads(resp.read().decode())
            return dados["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        print(f"[ERRO] HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERRO] Falha ao chamar OpenRouter: {e}")
        sys.exit(1)


def salvar_relatorio(contexto: str, resumo_trivy: str, analise_ia: str):
    """Salva o relatório completo em Markdown."""
    nome = contexto.replace("/", "_").replace(":", "_").replace(" ", "_")
    caminho = f"relatorio_{nome}.md"

    conteudo = f"""# Relatório de Segurança — Trivy + IA
## {contexto}

---

## Resultados do Trivy

{resumo_trivy}

---

## Análise e Recomendações (IA)

{analise_ia}
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"\n[OK] Relatório salvo em: {caminho}")


def main():
    parser = argparse.ArgumentParser(
        description="Trivy + IA — Scan de segurança com análise inteligente"
    )
    subparsers = parser.add_subparsers(dest="comando")

    # Subcomando: imagem
    p_img = subparsers.add_parser("imagem", help="Escanear uma imagem de container")
    p_img.add_argument("imagem", help="Ex: nginx:latest, python:3.9")

    # Subcomando: manifest
    p_man = subparsers.add_parser("manifest", help="Escanear um manifest Kubernetes")
    p_man.add_argument("arquivo", help="Ex: deployment.yaml")

    args = parser.parse_args()

    if not args.comando:
        parser.print_help()
        sys.exit(1)

    print("=" * 60)
    print("  Trivy + IA — Análise de Segurança K8s")
    print("=" * 60)

    if args.comando == "imagem":
        dados = rodar_trivy_imagem(args.imagem)
        contexto = f"imagem {args.imagem}"
    else:
        dados = rodar_trivy_manifest(args.arquivo)
        contexto = f"manifest {args.arquivo}"

    print("\n[1/3] Resumindo resultados do Trivy...")
    resumo = resumir_vulnerabilidades(dados)
    print(resumo)

    print("\n[2/3] Enviando para análise da IA...")
    analise = analisar_com_ia(resumo, contexto)
    print("\n--- Análise da IA ---")
    print(analise)

    print("\n[3/3] Salvando relatório...")
    salvar_relatorio(contexto, resumo, analise)

    print("\n[CONCLUÍDO]")


if __name__ == "__main__":
    main()