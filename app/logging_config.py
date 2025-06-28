"""
Configuração de logging para o sistema
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logging(app):
    """Configura o sistema de logging da aplicação"""
    
    # Obter configurações
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE', 'logs/firewall_login.log')
    log_max_size = app.config.get('LOG_MAX_SIZE', '10MB')
    log_backup_count = app.config.get('LOG_BACKUP_COUNT', 5)
    
    # Converter tamanho máximo para bytes
    if isinstance(log_max_size, str):
        if log_max_size.endswith('MB'):
            max_bytes = int(log_max_size[:-2]) * 1024 * 1024
        elif log_max_size.endswith('KB'):
            max_bytes = int(log_max_size[:-2]) * 1024
        else:
            max_bytes = int(log_max_size)
    else:
        max_bytes = log_max_size
    
    # Garantir que o diretório de logs existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar formato do log
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(filename)s:%(lineno)d]'
    )
    
    # Configurar handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=log_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Configurar handler para console (apenas em desenvolvimento)
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.INFO)
        app.logger.addHandler(console_handler)
    
    # Adicionar handler de arquivo
    app.logger.addHandler(file_handler)
    
    # Configurar nível do logger principal
    app.logger.setLevel(getattr(logging, log_level.upper()))
    
    # Configurar loggers específicos
    loggers_to_configure = [
        'app',
        'app.auth',
        'app.firewall',
        'app.email',
        'app.models',
        'werkzeug',
        'sqlalchemy'
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = False  # Evitar duplicação de logs
    
    # Log inicial
    app.logger.info(f'Sistema de logging configurado - Arquivo: {log_file}, Nível: {log_level}')
    app.logger.info(f'Rotacionamento: {log_max_size} máximo, {log_backup_count} backups')

def log_user_action(action, user_id=None, ip_address=None, details=None):
    """Função helper para logar ações de usuário"""
    logger = logging.getLogger('app.user_actions')
    
    message_parts = [f"Ação: {action}"]
    if user_id:
        message_parts.append(f"Usuário: {user_id}")
    if ip_address:
        message_parts.append(f"IP: {ip_address}")
    if details:
        message_parts.append(f"Detalhes: {details}")
    
    logger.info(" | ".join(message_parts))

def log_security_event(event_type, details, ip_address=None, user_id=None):
    """Função helper para logar eventos de segurança"""
    logger = logging.getLogger('app.security')
    
    message_parts = [f"Evento de Segurança: {event_type}"]
    if ip_address:
        message_parts.append(f"IP: {ip_address}")
    if user_id:
        message_parts.append(f"Usuário: {user_id}")
    if details:
        message_parts.append(f"Detalhes: {details}")
    
    logger.warning(" | ".join(message_parts))

def log_system_event(event_type, details):
    """Função helper para logar eventos do sistema"""
    logger = logging.getLogger('app.system')
    logger.info(f"Evento do Sistema: {event_type} - {details}")

def log_error(error, context=None):
    """Função helper para logar erros"""
    logger = logging.getLogger('app.errors')
    
    message_parts = [f"Erro: {str(error)}"]
    if context:
        message_parts.append(f"Contexto: {context}")
    
    logger.error(" | ".join(message_parts), exc_info=True) 