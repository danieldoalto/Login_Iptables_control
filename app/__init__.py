"""
Aplicação Flask para sistema de login com gerenciamento de firewall
"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.config import config
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar extensões
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    """Factory para criar a aplicação Flask"""
    
    # Determinar configuração
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Especificar o caminho correto dos templates
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config[config_name])
    
    # Configurar logging primeiro
    from app.logging_config import setup_logging
    setup_logging(app)
    
    # Logs para debug
    app.logger.info(f"Template folder configurado: {app.template_folder}")
    app.logger.info(f"Template folder absoluto: {os.path.abspath(app.template_folder)}")
    app.logger.info(f"Template folder existe: {os.path.exists(app.template_folder)}")
    
    # Inicializar extensões
    from app.models import db
    db.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    
    # Configurar captcha
    from app.captcha import captcha_manager
    captcha_manager.configure(app)
    
    # Registrar blueprints
    from app.routes import auth, main, api
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(api.bp, url_prefix='/api')
    
    # Inicializar sistema de firewall
    from app.firewall import FirewallManager
    app.firewall_manager = FirewallManager()
    app.firewall_manager.configure(app)
    
    # Configurar tarefas em background
    setup_background_tasks(app)
    
    app.logger.info(f'Sistema de Login com Firewall iniciado - Configuração: {config_name}')
    
    return app

def setup_background_tasks(app):
    """Configura tarefas em background"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from app.tasks import cleanup_expired_sessions, sync_firewall_rules
    
    if not app.debug:  # Apenas em produção
        scheduler = BackgroundScheduler()
        
        # Limpar sessões expiradas a cada 5 minutos
        scheduler.add_job(
            func=cleanup_expired_sessions,
            trigger="interval",
            minutes=5,
            id='cleanup_sessions'
        )
        
        # Sincronizar regras do firewall a cada 10 minutos
        scheduler.add_job(
            func=sync_firewall_rules,
            trigger="interval",
            minutes=10,
            id='sync_firewall'
        )
        
        scheduler.start()
        app.scheduler = scheduler
        app.logger.info('Tarefas em background configuradas')
