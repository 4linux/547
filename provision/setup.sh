#!/usr/bin/env bash
# provision/setup.sh — Provisionamento da VM para o curso 547
# IA no Universo Kubernetes
# Ubuntu 22.04 (ubuntu/jammy64)

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
err()  { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }
step() { echo -e "\n${YELLOW}==>${NC} $1"; }

echo "=============================================="
echo "  547 — IA no Universo Kubernetes"
echo "  Provisionando VM..."
echo "=============================================="

# ── Sistema base ──────────────────────────────────────────────────────────────
step "Atualizando sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  curl wget git unzip \
  python3 python3-pip pipx \
  ca-certificates gnupg \
  apt-transport-https software-properties-common \
  build-essential
ok "Sistema atualizado"

# ── Docker ────────────────────────────────────────────────────────────────────
step "Instalando Docker"
if command -v docker &>/dev/null; then
  ok "Docker já instalado: $(docker --version)"
else
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null

  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

  systemctl enable --now docker
  ok "Docker instalado"
fi

# Adicionar usuário vagrant ao grupo docker
usermod -aG docker vagrant
ok "vagrant adicionado ao grupo docker"

# ── Go (necessário para kube-copilot) ─────────────────────────────────────────
step "Instalando Go"
if command -v go &>/dev/null; then
  ok "Go já instalado: $(go version)"
else
  GO_VERSION="1.22.3"
  curl -sSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tar.gz
  rm -rf /usr/local/go
  tar -C /usr/local -xzf /tmp/go.tar.gz
  rm /tmp/go.tar.gz

  echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile.d/go.sh
  echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> /etc/profile.d/go.sh
  chmod +x /etc/profile.d/go.sh

  # Para o vagrant user
  echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> /home/vagrant/.bashrc
  ok "Go ${GO_VERSION} instalado"
fi

export PATH=$PATH:/usr/local/go/bin
export GOPATH=/home/vagrant/go

# ── kubectl ───────────────────────────────────────────────────────────────────
step "Instalando kubectl"
if command -v kubectl &>/dev/null; then
  ok "kubectl já instalado"
else
  curl -sSLO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
  chmod +x kubectl
  mv kubectl /usr/local/bin/
  ok "kubectl instalado"
fi

# ── kind ──────────────────────────────────────────────────────────────────────
step "Instalando kind"
if command -v kind &>/dev/null; then
  ok "kind já instalado: $(kind version)"
else
  curl -sSLo kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
  chmod +x kind
  mv kind /usr/local/bin/
  ok "kind instalado"
fi

# ── Helm ──────────────────────────────────────────────────────────────────────
step "Instalando Helm"
if command -v helm &>/dev/null; then
  ok "Helm já instalado: $(helm version --short)"
else
  curl -sSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  ok "Helm instalado"
fi

# ── Trivy ─────────────────────────────────────────────────────────────────────
step "Instalando Trivy"
if command -v trivy &>/dev/null; then
  ok "Trivy já instalado"
else
  curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin
  ok "Trivy instalado"
fi

# ── K8sGPT ────────────────────────────────────────────────────────────────────
step "Instalando k8sgpt"
if command -v k8sgpt &>/dev/null; then
  ok "k8sgpt já instalado"
else
  curl -sSLO https://github.com/k8sgpt-ai/k8sgpt/releases/latest/download/k8sgpt_linux_amd64.tar.gz
  tar -xzf k8sgpt_linux_amd64.tar.gz
  mv k8sgpt /usr/local/bin/
  rm -f k8sgpt_linux_amd64.tar.gz
  ok "k8sgpt instalado"
fi

# ── HolmesGPT ─────────────────────────────────────────────────────────────────
step "Instalando holmesgpt"
if pip3 show holmesgpt &>/dev/null 2>&1; then
  ok "holmesgpt já instalado"
else
  pip3 install holmesgpt --quiet
  ok "holmesgpt instalado"
fi

# ── kubectl-ai ────────────────────────────────────────────────────────────────
step "Instalando kubectl-ai"
if command -v kubectl-ai &>/dev/null; then
  ok "kubectl-ai já instalado"
else
  curl -sSLO "https://github.com/GoogleCloudPlatform/kubectl-ai/releases/download/v0.0.31/kubectl-ai_Linux_x86_64.tar.gz"
  tar -xzf kubectl-ai_Linux_x86_64.tar.gz
  mv kubectl-ai /usr/local/bin/
  rm -f kubectl-ai_Linux_x86_64.tar.gz
  ok "kubectl-ai instalado"
fi

# ── kube-copilot ──────────────────────────────────────────────────────────────
step "Instalando kube-copilot"
if command -v kube-copilot &>/dev/null; then
  ok "kube-copilot já instalado"
else
  GOPATH=/root/go /usr/local/go/bin/go install \
    github.com/feiskyer/kube-copilot/cmd/kube-copilot@latest 2>/dev/null || \
    warn "kube-copilot: falha na instalação — execute manualmente após o vagrant up"
  [ -f /root/go/bin/kube-copilot ] && cp /root/go/bin/kube-copilot /usr/local/bin/
  ok "kube-copilot instalado"
fi

# ── Python: dependências dos scripts ──────────────────────────────────────────
step "Instalando dependências Python"
pip3 install requests --quiet
ok "requests instalado"

# ── Cluster kind ──────────────────────────────────────────────────────────────
step "Criando cluster Kubernetes (kind)"
if su - vagrant -c "kind get clusters 2>/dev/null | grep -q k8s-ai-labs"; then
  ok "Cluster k8s-ai-labs já existe"
else
  # Rodar como vagrant para que o kubeconfig fique no home do usuário
  su - vagrant -c "docker info &>/dev/null && kind create cluster --config /ambiente/kind-cluster.yaml" || \
    warn "Cluster não pôde ser criado agora. Execute dentro da VM: kind create cluster --config /ambiente/kind-cluster.yaml"
fi

# ── kubeconfig para vagrant ───────────────────────────────────────────────────
step "Configurando kubeconfig"
su - vagrant -c "mkdir -p ~/.kube && kind get kubeconfig --name k8s-ai-labs > ~/.kube/config 2>/dev/null" || true
ok "kubeconfig configurado em /home/vagrant/.kube/config"

# ── Script de verificação ─────────────────────────────────────────────────────
cat > /labs/verificar.sh << 'VERIFY'
#!/usr/bin/env bash
echo "=== Ferramentas Base ==="
docker --version
kubectl version --client --short 2>/dev/null || kubectl version --client
kind version
helm version --short
trivy --version | head -1
python3 --version

echo ""
echo "=== Ferramentas de IA ==="
k8sgpt version
pip3 show holmesgpt | grep Version
kubectl-ai version 2>/dev/null || echo "kubectl-ai: ok"
kube-copilot --help 2>/dev/null | head -1 || echo "kube-copilot: ok"

echo ""
echo "=== Chaves de API ==="
[ -n "$OPENROUTER_API_KEY" ] && echo "OK  OPENROUTER_API_KEY" || echo "FALTA  OPENROUTER_API_KEY"
[ -n "$GEMINI_API_KEY" ]     && echo "OK  GEMINI_API_KEY"     || echo "FALTA  GEMINI_API_KEY"
[ -n "$OPENAI_API_KEY" ]     && echo "OK  OPENAI_API_KEY"     || echo "FALTA  OPENAI_API_KEY (necessária apenas para HolmesGPT)"

echo ""
echo "=== Cluster Kubernetes ==="
kubectl get nodes 2>/dev/null || echo "FALTA  Cluster nao encontrado — execute: kind create cluster --config /ambiente/kind-cluster.yaml"
VERIFY
chmod +x /labs/verificar.sh
ok "verificar.sh criado em /labs/verificar.sh"

# ── Finalização ───────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo "  Provisionamento concluído!"
echo "=============================================="
echo ""
echo "  Próximos passos:"
echo "  1. vagrant ssh"
echo "  2. export OPENROUTER_API_KEY='sua_chave'"
echo "  3. bash /labs/verificar.sh"
echo "  4. cd /labs/lab-01-k8sgpt && cat LAB.md"
echo ""
