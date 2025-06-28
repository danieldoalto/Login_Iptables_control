#!/bin/bash

# Script de inicialização do Sistema de Login com Firewall
# =======================================================

echo "🚀 Sistema de Login com Firewall"
echo "================================="

# Verificar se o ambiente virtual está ativo
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Ambiente virtual não está ativo!"
    echo "Execute: source venv/bin/activate"
    exit 1
fi

# Verificar se as dependências estão instaladas
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Instalando dependências..."
    pip install -r requirements.txt
fi

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env a partir do exemplo..."
    cp env.example .env
    echo "⚠️  IMPORTANTE: Configure o arquivo .env com suas credenciais de email!"
fi

# Verificar permissões para iptables
if ! sudo -n true 2>/dev/null; then
    echo "⚠️  ATENÇÃO: O sistema precisa de privilégios sudo para gerenciar o firewall"
    echo "   Execute: sudo visudo"
    echo "   Adicione: $(whoami) ALL=(ALL) NOPASSWD: /sbin/iptables, /sbin/ip6tables"
fi

# Inicializar a aplicação
echo "🌐 Iniciando aplicação..."
echo "   URL: http://localhost:5000"
echo "   Pressione Ctrl+C para parar"
echo ""

python run.py 