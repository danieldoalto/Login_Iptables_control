#!/usr/bin/env python3
"""
Script para testar o sistema de logging
"""
import os
import sys
import logging
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.logging_config import log_user_action, log_security_event, log_system_event, log_error

def test_logging():
    """Testa o sistema de logging"""
    print("=== Teste do Sistema de Logging ===")
    
    # Criar aplicação
    app = create_app('development')
    
    with app.app_context():
        # Testar logs básicos
        app.logger.info("Teste de log INFO")
        app.logger.warning("Teste de log WARNING")
        app.logger.error("Teste de log ERROR")
        
        # Testar funções de logging específicas
        log_user_action(
            action="Teste de ação de usuário",
            user_id=1,
            ip_address="192.168.1.100",
            details="Teste do sistema de logging"
        )
        
        log_security_event(
            event_type="Teste de evento de segurança",
            details="Teste de segurança",
            ip_address="192.168.1.100",
            user_id=1
        )
        
        log_system_event(
            event_type="Teste de evento do sistema",
            details="Teste do sistema"
        )
        
        # Testar log de erro
        try:
            raise ValueError("Erro de teste para logging")
        except Exception as e:
            log_error(e, "Teste de log de erro")
        
        print("✓ Logs de teste criados com sucesso!")
        print(f"✓ Arquivo de log: {app.config.get('LOG_FILE', 'logs/firewall_login.log')}")
        
        # Verificar se o arquivo foi criado
        log_file = app.config.get('LOG_FILE', 'logs/firewall_login.log')
        if os.path.exists(log_file):
            print(f"✓ Arquivo de log criado: {log_file}")
            
            # Mostrar últimas linhas do log
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n=== Últimas {min(10, len(lines))} linhas do log ===")
                for line in lines[-10:]:
                    print(line.strip())
        else:
            print(f"✗ Arquivo de log não encontrado: {log_file}")

if __name__ == '__main__':
    test_logging() 