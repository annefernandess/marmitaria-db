#!/bin/bash
set -e

# Detecta a arquitetura da máquina
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)         LG_ARCH="x86_64" ;;
  aarch64 | arm64) LG_ARCH="arm64" ;;
  *)
    echo "Arquitetura não suportada: $ARCH"
    exit 1
    ;;
esac

# ── lazygit ────────────────────────────────────────────────────────────────────
echo ">>> Instalando lazygit..."
LAZYGIT_VERSION=$(curl -fsSL "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" \
  | grep -Po '"tag_name": "v\K[^"]*')
curl -fsSL \
  "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_${LG_ARCH}.tar.gz" \
  | tar -xz -C /tmp lazygit
sudo install /tmp/lazygit /usr/local/bin/lazygit
rm -f /tmp/lazygit
echo "    lazygit v${LAZYGIT_VERSION} instalado em /usr/local/bin/lazygit"

# ── uv ────────────────────────────────────────────────────────────────────────
echo ">>> Instalando uv..."
curl -LsSf https://astral.sh/uv/install.sh | sudo UV_INSTALL_DIR=/usr/local/bin sh
echo "    uv $(uv --version) instalado em /usr/local/bin/uv"

echo ""
echo ">>> Ferramentas instaladas com sucesso!"
