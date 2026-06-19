# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# 547 — IA no Universo Kubernetes
# VM de lab: Ubuntu 22.04, Docker + kind + ferramentas de IA

Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "k8s-ai-lab"

  # ── Recursos da VM ────────────────────────────────────────────────────────────
  config.vm.provider "virtualbox" do |vb|
    vb.name   = "547-ia-kubernetes"
    vb.memory = 8192   # 8 GB — mínimo para kind com 3 nodes
    vb.cpus   = 4
    vb.customize ["modifyvm", :id, "--nested-hw-virt", "on"]
  end

  # ── Rede ──────────────────────────────────────────────────────────────────────
  # Dashboard do Goldilocks (port-forward manual dentro da VM)
  config.vm.network "forwarded_port", guest: 8080, host: 8080, auto_correct: true
  # Porta livre para outros serviços
  config.vm.network "forwarded_port", guest: 8443, host: 8443, auto_correct: true

  # ── Pasta sincronizada ────────────────────────────────────────────────────────
  # Os labs ficam disponíveis em /labs dentro da VM
  config.vm.synced_folder "./labs",     "/labs"
  config.vm.synced_folder "./ambiente", "/ambiente"

  # ── Provisionamento ───────────────────────────────────────────────────────────
  config.vm.provision "shell", path: "provision/setup.sh"

  # ── Mensagem pós-boot ─────────────────────────────────────────────────────────
  config.vm.post_up_message = <<~MSG
    ╔══════════════════════════════════════════════════════╗
    ║       547 — IA no Universo Kubernetes                ║
    ║       VM pronta!                                     ║
    ╠══════════════════════════════════════════════════════╣
    ║                                                      ║
    ║  1. Acesse a VM:                                     ║
    ║     vagrant ssh                                      ║
    ║                                                      ║
    ║  2. Configure suas chaves de API:                    ║
    ║     export OPENROUTER_API_KEY="sua_chave"            ║
    ║     export GEMINI_API_KEY="sua_chave"                ║
    ║     export OPENAI_API_KEY="sua_chave"                ║
    ║                                                      ║
    ║  3. Verifique o ambiente:                            ║
    ║     bash /labs/verificar.sh                          ║
    ║                                                      ║
    ║  4. Comece pelo Lab 01:                              ║
    ║     cd /labs/lab-01-k8sgpt && cat LAB.md             ║
    ║                                                      ║
    ╚══════════════════════════════════════════════════════╝
  MSG

end
