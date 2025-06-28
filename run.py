#!/usr/bin/env python3
"""
Arquivo de inicialização do Sistema de Login com Firewall
"""
import os
import sys
from app import create_app

def main():
    """Função principal para inicializar a aplicação"""
    
    # Configurar variáveis de ambiente padrão se não existirem
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    if not os.environ.get('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Criar aplicação Flask
    app = create_app()
    
    # Configurações para desenvolvimento
    if app.config.get('DEBUG', False):
        print("🚀 Iniciando Sistema de Login com Firewall em modo DESENVOLVIMENTO")
        print(f"📊 Configuração: {os.environ.get('FLASK_ENV', 'development')}")
        print(f"🌐 URL: http://localhost:5000")
        print(f"🔧 Debug: {app.config.get('DEBUG', False)}")
        print("=" * 60)
        
        # Executar em modo de desenvolvimento
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            use_reloader=True
        )
    else:
        print("🚀 Iniciando Sistema de Login com Firewall em modo PRODUÇÃO")
        print(f"📊 Configuração: {os.environ.get('FLASK_ENV', 'production')}")
        print("=" * 60)
        
        # Para produção, usar gunicorn
        from gunicorn.app.wsgiapp import WSGIApplication
        
        class StandaloneApplication(WSGIApplication):
            def __init__(self, app_uri, options=None):
                self.options = options or {}
                self.app_uri = app_uri
                super().__init__()
            
            def load_config(self):
                config = {
                    'bind': '0.0.0.0:5000',
                    'workers': 4,
                    'worker_class': 'sync',
                    'timeout': 120,
                    'keepalive': 2,
                    'max_requests': 1000,
                    'max_requests_jitter': 100,
                    'preload_app': True,
                    'access_logfile': '-',
                    'error_logfile': '-',
                    'loglevel': 'info'
                }
                for key, value in config.items():
                    self.cfg.set(key, value)
        
        StandaloneApplication(app, {}).run()

if __name__ == '__main__':
    main() 