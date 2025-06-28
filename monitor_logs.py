#!/usr/bin/env python3
"""
Script para monitorar logs em tempo real
"""
import os
import time
import subprocess
from datetime import datetime

def monitor_logs():
    """Monitora os logs em tempo real"""
    log_file = "logs/firewall_login.log"
    
    if not os.path.exists(log_file):
        print(f"Arquivo de log não encontrado: {log_file}")
        return
    
    print(f"=== Monitorando logs: {log_file} ===")
    print("Pressione Ctrl+C para parar")
    print("-" * 80)
    
    try:
        # Usar tail -f para monitorar em tempo real
        process = subprocess.Popen(
            ['tail', '-f', log_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        for line in process.stdout:
            print(line.strip())
            
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido.")
        process.terminate()
    except Exception as e:
        print(f"Erro ao monitorar logs: {e}")

def show_log_stats():
    """Mostra estatísticas dos logs"""
    log_file = "logs/firewall_login.log"
    
    if not os.path.exists(log_file):
        print(f"Arquivo de log não encontrado: {log_file}")
        return
    
    print(f"=== Estatísticas dos logs: {log_file} ===")
    
    # Tamanho do arquivo
    size = os.path.getsize(log_file)
    print(f"Tamanho: {size / 1024:.2f} KB")
    
    # Número de linhas
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Total de linhas: {len(lines)}")
    
    # Contar por nível
    levels = {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0}
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            for level in levels:
                if f'[{level}]' in line:
                    levels[level] += 1
                    break
    
    print("\nLogs por nível:")
    for level, count in levels.items():
        print(f"  {level}: {count}")
    
    # Últimas 5 linhas
    print(f"\nÚltimas 5 linhas:")
    with open(log_file, 'r', encoding='utf-8') as f:
        last_lines = f.readlines()[-5:]
        for line in last_lines:
            print(f"  {line.strip()}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        show_log_stats()
    else:
        monitor_logs() 