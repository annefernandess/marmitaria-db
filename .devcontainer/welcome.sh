#!/bin/bash
# Exibe orientações apenas se o gh ainda não estiver autenticado

if ! gh auth status &>/dev/null; then
  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║              Bem-vindo ao devcontainer marmitaria!           ║"
  echo "╠══════════════════════════════════════════════════════════════╣"
  echo "║  GitHub CLI detectado, mas você ainda não está autenticado.  ║"
  echo "║                                                              ║"
  echo "║  Para configurar o GitHub, execute:                          ║"
  echo "║                                                              ║"
  echo "║    gh auth login                                             ║"
  echo "║                                                              ║"
  echo "║  Siga as instruções e escolha:                               ║"
  echo "║    • GitHub.com                                              ║"
  echo "║    • HTTPS  (recomendado)  ou  SSH                           ║"
  echo "║    • Login via browser  (mais fácil)                         ║"
  echo "╚══════════════════════════════════════════════════════════════╝"
  echo ""
fi
