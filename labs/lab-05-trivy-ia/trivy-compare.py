#!/usr/bin/env python3
"""
trivy-compare.py — Comparação de Segurança entre Imagens
Escaneia duas imagens com Trivy e usa IA para comparar os resultados,
mostrando o ganho de segurança ao migrar de uma versão para outra.

Uso:
  python3 trivy-compare.py nginx:1.21 nginx:alpine
  python3 trivy-compare.py python:3.9 python:3.11-slim
  python3 trivy-compare.py node:14 node:20-alpine
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
OPENROUTER_MODEL   = os.getenv("TRIVY_IA_MODEL", "openrouter/free")
# ──────────────────────────────────────────────────────────────────────────────


def rodar_trivy(imagem: str) -> dict:
    """Executa trivy image e retorna o resultado em JSON."""
    print(f"  → Escaneando {imagem}...")
    try:
        resultado = subprocess.run(
            ["trivy", "image", "--format", "json", "--quiet", imagem],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180
        )
        stdout = resultado.stdout.decode("utf-8") if isinstance(resultado.stdout, bytes) else resultado.stdout
        if not stdout:
            print(f"  [ERRO] Trivy não retornou dados para {imagem}")
            return {}
        return json.loads(stdout)
    except subprocess.TimeoutExpired:
        print(f"  [ERRO] Timeout ao escanear {imagem}")
        return {}
    except FileNotFoundError:
        print("[ERRO] Trivy não encontrado. Instale em: https://aquasecurity.github.io/trivy")
        sys.exit(1)


def extrair_stats(dados: dict) -> dict:
    """Extrai estatísticas resumidas do resultado do Trivy."""
    stats = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "total": 0,
        "top_criticos": [],
        "bibliotecas_afetadas": set()
    }

    for resultado in dados.get("Results", []):
        vulns = resultado.get("Vulnerabilities", []) or []
        for v in vulns:
            sev = v.get("Severity", "").upper()
            stats["total"] += 1
            if sev == "CRITICAL":
                stats["critical"] += 1
                if len(stats["top_criticos"]) < 5:
                    stats["top_criticos"].append({
                        "id": v.get("VulnerabilityID"),
                        "pkg": v.get("PkgName"),
                        "titulo": v.get("Title", "")
                    })
            elif sev == "HIGH":
                stats["high"] += 1
            elif sev == "MEDIUM":
                stats["medium"] += 1
            elif sev == "LOW":
                stats["low"] += 1
            stats["bibliotecas_afetadas"].add(v.get("PkgName", ""))

    stats["bibliotecas_afetadas"] = len(stats["bibliotecas_afetadas"])
    return stats


def formatar_comparacao(imagem_a: str, stats_a: dict,
                         imagem_b: str, stats_b: dict) -> str:
    """Formata a comparação lado a lado para exibição e para o prompt da IA."""

    def pct_reducao(antes, depois):
        if antes == 0:
            return "0%"
        reducao = ((antes - depois) / antes) * 100
        if reducao > 0:
            return f"-{reducao:.0f}%"
        elif reducao < 0:
            return f"+{abs(reducao):.0f}%"
        return "0%"

    linhas = []
    linhas.append(f"{'Métrica':<30} {'':>20} {'':>20}")
    linhas.append(f"{'':─<72}")
    linhas.append(f"{'Imagem':<30} {imagem_a:>20} {imagem_b:>20}")
    linhas.append(f"{'':─<72}")
    linhas.append(f"{'Total de CVEs':<30} {stats_a['total']:>20} {stats_b['total']:>20}  {pct_reducao(stats_a['total'], stats_b['total'])}")
    linhas.append(f"{'CRITICAL':<30} {stats_a['critical']:>20} {stats_b['critical']:>20}  {pct_reducao(stats_a['critical'], stats_b['critical'])}")
    linhas.append(f"{'HIGH':<30} {stats_a['high']:>20} {stats_b['high']:>20}  {pct_reducao(stats_a['high'], stats_b['high'])}")
    linhas.append(f"{'MEDIUM':<30} {stats_a['medium']:>20} {stats_b['medium']:>20}  {pct_reducao(stats_a['medium'], stats_b['medium'])}")
    linhas.append(f"{'LOW':<30} {stats_a['low']:>20} {stats_b['low']:>20}  {pct_reducao(stats_a['low'], stats_b['low'])}")
    linhas.append(f"{'Bibliotecas afetadas':<30} {stats_a['bibliotecas_afetadas']:>20} {stats_b['bibliotecas_afetadas']:>20}")
    linhas.append(f"{'':─<72}")

    if stats_a["top_criticos"]:
        linhas.append(f"\nTop CVEs CRITICAL em {imagem_a}:")
        for c in stats_a["top_criticos"]:
            linhas.append(f"  - {c['id']} ({c['pkg']}): {c['titulo'][:60]}")

    if stats_b["top_criticos"]:
        linhas.append(f"\nTop CVEs CRITICAL em {imagem_b}:")
        for c in stats_b["top_criticos"]:
            linhas.append(f"  - {c['id']} ({c['pkg']}): {c['titulo'][:60]}")
    else:
        linhas.append(f"\n✅ {imagem_b} não tem CVEs CRITICAL!")

    return "\n".join(linhas)


def analisar_com_ia(comparacao: str, imagem_a: str, imagem_b: str) -> str:
    """Envia a comparação para análise via OpenRouter."""
    if not OPENROUTER_API_KEY:
        print("[ERRO] OPENROUTER_API_KEY não configurada.")
        sys.exit(1)

    prompt = f"""Você é um especialista em segurança de containers e Kubernetes.
Compare as seguintes imagens do ponto de vista de segurança:

{comparacao}

## Sua análise deve incluir:

1. **Resumo da comparação** — qual imagem é mais segura e por quê
2. **Impacto da migração** — o que se ganha em segurança ao trocar {imagem_a} por {imagem_b}
3. **Risco dos CVEs eliminados** — quais eram os mais perigosos e que foram resolvidos
4. **Recomendação final** — vale migrar? Quais cuidados ao migrar?
5. **Nota de segurança** — dê uma nota de 0 a 10 para cada imagem

Responda em português brasileiro de forma objetiva e prática.
Destaque o ganho percentual de segurança com a migração.
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
            "HTTP-Referer": "https://lab-trivy-compare",
            "X-Title": "Trivy Compare IA K8s"
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


def salvar_relatorio(imagem_a: str, imagem_b: str,
                     comparacao: str, analise: str):
    """Salva o relatório de comparação em Markdown."""
    nome_a = imagem_a.replace("/", "_").replace(":", "_")
    nome_b = imagem_b.replace("/", "_").replace(":", "_")
    caminho = f"comparacao_{nome_a}_vs_{nome_b}.md"

    conteudo = f"""# Comparação de Segurança — Trivy + IA
## {imagem_a}  vs  {imagem_b}

---

## Dados do Scan

```
{comparacao}
```

---

## Análise da IA

{analise}
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"\n[OK] Relatório salvo em: {caminho}")
    return caminho


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 trivy-compare.py IMAGEM_A IMAGEM_B")
        print("")
        print("Exemplos:")
        print("  python3 trivy-compare.py nginx:1.21 nginx:alpine")
        print("  python3 trivy-compare.py python:3.9 python:3.11-slim")
        print("  python3 trivy-compare.py node:14 node:20-alpine")
        sys.exit(1)

    imagem_a = sys.argv[1]
    imagem_b = sys.argv[2]

    print("=" * 60)
    print("  Trivy Compare — Comparação de Segurança entre Imagens")
    print("=" * 60)
    print(f"\nComparando:")
    print(f"  A: {imagem_a}")
    print(f"  B: {imagem_b}")

    print("\n[1/4] Escaneando imagens com Trivy...")
    dados_a = rodar_trivy(imagem_a)
    dados_b = rodar_trivy(imagem_b)

    print("\n[2/4] Extraindo estatísticas...")
    stats_a = extrair_stats(dados_a)
    stats_b = extrair_stats(dados_b)

    print("\n[3/4] Comparando resultados...\n")
    comparacao = formatar_comparacao(imagem_a, stats_a, imagem_b, stats_b)
    print(comparacao)

    print("\n[4/4] Analisando com IA...")
    analise = analisar_com_ia(comparacao, imagem_a, imagem_b)
    print("\n--- Análise da IA ---")
    print(analise)

    salvar_relatorio(imagem_a, imagem_b, comparacao, analise)
    print("\n[CONCLUÍDO]")


if __name__ == "__main__":
    main()