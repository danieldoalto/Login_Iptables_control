"""
Tarefas em background para o sistema
"""
import logging
from datetime import datetime, timedelta
from flask import current_app
from app.models import UserSession, FirewallRule, SystemLog, db

logger = logging.getLogger(__name__)

def cleanup_expired_sessions():
    """Limpa sessões expiradas e remove IPs do firewall"""
    try:
        with current_app.app_context():
            logger.info("Iniciando limpeza de sessões expiradas")
            
            # Buscar sessões expiradas que ainda estão ativas
            expired_sessions = UserSession.query.filter(
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_active == True
            ).all()
            
            removed_count = 0
            
            for session in expired_sessions:
                try:
                    # Remover IP do firewall
                    firewall_manager = current_app.firewall_manager
                    success = firewall_manager.remove_ip_from_firewall(session.ip_address)
                    
                    # Atualizar sessão
                    session.end_session()
                    
                    # Atualizar regra do firewall no banco
                    firewall_rule = FirewallRule.query.filter_by(
                        session_id=session.id,
                        is_active=True
                    ).first()
                    
                    if firewall_rule:
                        firewall_rule.mark_as_removed()
                    
                    removed_count += 1
                    
                    # Log da ação
                    SystemLog.log(
                        level='INFO',
                        message=f'Sessão expirada removida - IP: {session.ip_address}, Usuário: {session.user.email}',
                        module='task_cleanup',
                        user_id=session.user_id,
                        ip_address=session.ip_address
                    )
                    
                    logger.info(f"Sessão expirada removida: {session.user.email} - {session.ip_address}")
                    
                except Exception as e:
                    logger.error(f"Erro ao remover sessão expirada {session.id}: {str(e)}")
                    SystemLog.log(
                        level='ERROR',
                        message=f'Erro ao remover sessão expirada: {str(e)}',
                        module='task_cleanup',
                        user_id=session.user_id if hasattr(session, 'user_id') else None,
                        ip_address=session.ip_address if hasattr(session, 'ip_address') else None
                    )
            
            # Commit das alterações
            db.session.commit()
            
            logger.info(f"Limpeza concluída: {removed_count} sessões expiradas removidas")
            
            # Log de sistema
            SystemLog.log(
                level='INFO',
                message=f'Limpeza automática concluída: {removed_count} sessões removidas',
                module='task_cleanup'
            )
            
            return removed_count
            
    except Exception as e:
        logger.error(f"Erro na limpeza de sessões expiradas: {str(e)}")
        db.session.rollback()
        
        SystemLog.log(
            level='ERROR',
            message=f'Erro na limpeza automática de sessões: {str(e)}',
            module='task_cleanup'
        )
        
        return 0

def sync_firewall_rules():
    """Sincroniza regras do banco de dados com o firewall"""
    try:
        with current_app.app_context():
            logger.info("Iniciando sincronização de regras do firewall")
            
            firewall_manager = current_app.firewall_manager
            firewall_manager.sync_database_with_firewall()
            
            SystemLog.log(
                level='INFO',
                message='Sincronização de regras do firewall concluída',
                module='task_sync'
            )
            
            logger.info("Sincronização de regras do firewall concluída")
            
    except Exception as e:
        logger.error(f"Erro na sincronização de regras do firewall: {str(e)}")
        
        SystemLog.log(
            level='ERROR',
            message=f'Erro na sincronização de regras do firewall: {str(e)}',
            module='task_sync'
        )

def cleanup_old_logs(days=30):
    """Remove logs antigos do sistema"""
    try:
        with current_app.app_context():
            logger.info(f"Iniciando limpeza de logs antigos (mais de {days} dias)")
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_logs = SystemLog.query.filter(
                SystemLog.created_at < cutoff_date
            ).all()
            
            removed_count = len(old_logs)
            
            for log in old_logs:
                db.session.delete(log)
            
            db.session.commit()
            
            logger.info(f"Limpeza de logs concluída: {removed_count} logs removidos")
            
            SystemLog.log(
                level='INFO',
                message=f'Limpeza automática de logs: {removed_count} registros removidos',
                module='task_cleanup'
            )
            
            return removed_count
            
    except Exception as e:
        logger.error(f"Erro na limpeza de logs antigos: {str(e)}")
        db.session.rollback()
        
        SystemLog.log(
            level='ERROR',
            message=f'Erro na limpeza de logs antigos: {str(e)}',
            module='task_cleanup'
        )
        
        return 0

def health_check():
    """Verifica saúde do sistema"""
    try:
        with current_app.app_context():
            health_status = {
                'database': False,
                'firewall': False,
                'email': False,
                'timestamp': datetime.utcnow()
            }
            
            # Teste do banco de dados
            try:
                db.session.execute('SELECT 1')
                health_status['database'] = True
            except Exception as e:
                logger.error(f"Erro no teste do banco de dados: {str(e)}")
            
            # Teste do firewall
            try:
                firewall_manager = current_app.firewall_manager
                allowed_ips = firewall_manager.list_allowed_ips()
                health_status['firewall'] = True
            except Exception as e:
                logger.error(f"Erro no teste do firewall: {str(e)}")
            
            # Teste do email (sem enviar email real)
            try:
                from flask_mail import mail
                # Apenas verificar se a configuração está válida
                if current_app.config.get('MAIL_SERVER'):
                    health_status['email'] = True
            except Exception as e:
                logger.error(f"Erro no teste do email: {str(e)}")
            
            # Log do health check
            status_msg = f"Health check - DB: {health_status['database']}, " \
                        f"Firewall: {health_status['firewall']}, " \
                        f"Email: {health_status['email']}"
            
            level = 'INFO' if all([health_status['database'], health_status['firewall']]) else 'WARNING'
            
            SystemLog.log(
                level=level,
                message=status_msg,
                module='task_health'
            )
            
            logger.info(status_msg)
            
            return health_status
            
    except Exception as e:
        logger.error(f"Erro no health check: {str(e)}")
        
        SystemLog.log(
            level='ERROR',
            message=f'Erro no health check do sistema: {str(e)}',
            module='task_health'
        )
        
        return {'error': str(e), 'timestamp': datetime.utcnow()}

def backup_database():
    """Cria backup do banco de dados"""
    try:
        with current_app.app_context():
            import sqlite3
            import shutil
            from datetime import datetime
            
            # Obter caminho do banco
            db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
            if db_url.startswith('sqlite:///'):
                db_path = db_url.replace('sqlite:///', '')
                
                # Criar nome do backup
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"backup/firewall_login_backup_{timestamp}.db"
                
                # Criar diretório de backup se não existir
                import os
                os.makedirs('backup', exist_ok=True)
                
                # Criar backup
                shutil.copy2(db_path, backup_path)
                
                logger.info(f"Backup do banco criado: {backup_path}")
                
                SystemLog.log(
                    level='INFO',
                    message=f'Backup automático criado: {backup_path}',
                    module='task_backup'
                )
                
                return backup_path
            else:
                logger.warning("Backup automático suporta apenas SQLite")
                return None
                
    except Exception as e:
        logger.error(f"Erro ao criar backup: {str(e)}")
        
        SystemLog.log(
            level='ERROR',
            message=f'Erro ao criar backup automático: {str(e)}',
            module='task_backup'
        )
        
        return None
