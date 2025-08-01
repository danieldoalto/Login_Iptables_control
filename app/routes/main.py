"""
Rotas principais da aplicação
"""
import logging
from flask import Blueprint, render_template, session, request, redirect, url_for, flash, current_app
from app import limiter
from app.models import User, UserSession, SystemLog, db, FirewallRule
from datetime import datetime
import os
from sqlalchemy import text

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Página inicial"""
    # Logs para debug
    logger.info(f"Tentando renderizar template 'index.html'")
    logger.info(f"Template folder: {current_app.template_folder}")
    logger.info(f"Templates disponíveis: {os.listdir(current_app.template_folder)}")
    
    # Verificar se o arquivo existe
    template_folder = current_app.template_folder or ''
    template_path = os.path.join(template_folder, 'index.html')
    logger.info(f"Template path: {template_path}")
    logger.info(f"Arquivo existe: {os.path.exists(template_path)}")
    
    return render_template('index.html')

@bp.route('/dashboard')
def dashboard():
    """Dashboard do usuário logado"""
    if 'user_id' not in session:
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Sessão inválida. Faça login novamente.', 'error')
        return redirect(url_for('auth.login'))
    
    # Buscar sessão atual
    current_session = UserSession.query.filter_by(
        user_id=user.id,
        session_token=session.get('session_token'),
        is_active=True
    ).first()
    
    if not current_session or current_session.is_expired():
        session.clear()
        flash('Sua sessão expirou. Faça login novamente.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Buscar sessões ativas do usuário
    active_sessions = UserSession.query.filter_by(
        user_id=user.id,
        is_active=True
    ).filter(UserSession.expires_at > datetime.utcnow()).all()
    
    # Buscar logs recentes do usuário
    recent_logs = SystemLog.query.filter_by(
        user_id=user.id
    ).order_by(SystemLog.created_at.desc()).limit(10).all()

    # Obter seções do dashboard a partir do config.yml
    dashboard_config = current_app.config.get('DASHBOARD_CONFIG', {})
    if hasattr(user, 'is_admin') and user.is_admin():
        sections = dashboard_config.get('admin', {}).get('sections', [])
    else:
        sections = dashboard_config.get('usuario', {}).get('sections', [])

    # Passar diretamente as seções como dashboard_sections
    dashboard_sections = sections

    return render_template('dashboard.html', 
                         user=user, 
                         current_session=current_session,
                         active_sessions=active_sessions,
                         recent_logs=recent_logs,
                         dashboard_sections=dashboard_sections,
                         dashboard_config=dashboard_config)

@bp.route('/status')
@limiter.limit("10 per minute")
def status():
    """Página de status do sistema"""
    try:
        # Verificar status do banco
        db.session.execute(text('SELECT 1'))
        db_status = 'OK'
    except Exception as e:
        db_status = f'Erro: {str(e)}'
    
    # Verificar status do firewall
    try:
        firewall_manager = current_app.firewall_manager  # type: ignore[attr-defined]
        allowed_ips = firewall_manager.list_allowed_ips()
        firewall_status = f'OK - {len(allowed_ips)} IPs permitidos'
    except Exception as e:
        firewall_status = f'Erro: {str(e)}'
    
    # Estatísticas básicas
    stats = {
        'total_users': User.query.count(),
        'confirmed_users': User.query.filter_by(confirmed=True).count(),
        'active_sessions': UserSession.query.filter_by(is_active=True).count(),
        'total_logs': SystemLog.query.count()
    }
    
    status_info = {
        'database': db_status,
        'firewall': firewall_status,
        'stats': stats,
        'timestamp': datetime.utcnow()
    }
    
    return render_template('status.html', status=status_info)

@bp.route('/help')
def help():
    """Página de ajuda"""
    return render_template('help.html')

@bp.route('/privacy')
def privacy():
    """Política de privacidade"""
    return render_template('privacy.html')

@bp.route('/terms')
def terms():
    """Termos de uso"""
    return render_template('terms.html')

@bp.route('/admin/pending-users', methods=['GET', 'POST'])
def admin_pending_users():
    """Painel admin: listar e aprovar/rejeitar usuários pendentes"""
    if 'user_id' not in session:
        flash('Você precisa fazer login como administrador.', 'warning')
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin():
        flash('Acesso restrito ao administrador.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Aprovação/rejeição via POST
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        target_user = User.query.get(user_id)
        if not target_user or not target_user.is_pending():
            flash('Usuário inválido ou já processado.', 'warning')
            return redirect(url_for('main.admin_pending_users'))
        if action == 'approve':
            target_user.status = 'approved'
            db.session.commit()
            # Enviar email de confirmação
            from app.email import send_confirmation_email
            send_confirmation_email(target_user)
            flash(f'Usuário {target_user.email} aprovado com sucesso!', 'success')
        elif action == 'reject':
            target_user.status = 'rejected'
            db.session.commit()
            from app.email import send_rejection_email
            send_rejection_email(target_user)
            flash(f'Usuário {target_user.email} rejeitado.', 'info')
        return redirect(url_for('main.admin_pending_users'))

    # Listar usuários pendentes
    pending_users = User.query.filter_by(status='pending').all()
    return render_template('admin/pending_users.html', user=user, pending_users=pending_users)

@bp.route('/firewall_manager', methods=['GET', 'POST'])
def firewall_manager():
    """Card Firewall Manager: listar, adicionar e remover IPs liberados/bloqueados"""
    if 'user_id' not in session:
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin():
        flash('Acesso restrito ao administrador.', 'danger')
        return redirect(url_for('main.dashboard'))

    firewall_manager = current_app.firewall_manager
    # Listar regras ativas
    regras = FirewallRule.query.filter_by(is_active=True).order_by(FirewallRule.created_at.desc()).all()

    if request.method == 'POST':
        acao = request.form.get('acao')
        ip = request.form.get('ip')
        tipo = request.form.get('tipo')  # whitelist ou blacklist
        chain = request.form.get('chain') or (firewall_manager.chain_name if tipo == 'whitelist' else current_app.config.get('FIREWALL_BLACK', 'BLACKLIST'))
        if acao == 'adicionar' and ip and tipo:
            # Adicionar IP
            nova_regra = FirewallRule(
                ip_address=ip,
                user_id=user.id,
                session_id=None,
                tipo=tipo,
                chain=chain,
                is_active=True
            )
            db.session.add(nova_regra)
            db.session.commit()
            # Adicionar no iptables
            if tipo == 'whitelist':
                firewall_manager.add_ip_to_firewall(ip)
            else:
                firewall_manager.add_ip_to_blacklist(ip)
            flash(f'IP {ip} adicionado à {tipo}.', 'success')
            return redirect(url_for('main.firewall_manager'))
        elif acao == 'remover' and ip:
            # Remover IP
            regra = FirewallRule.query.filter_by(ip_address=ip, is_active=True).first()
            if regra:
                regra.mark_as_removed()
                db.session.commit()
                # Remover do iptables
                if regra.tipo == 'whitelist':
                    firewall_manager.remove_ip_from_firewall(ip)
                else:
                    firewall_manager.remove_ip_from_blacklist(ip)
                flash(f'IP {ip} removido da {regra.tipo}.', 'info')
            else:
                flash('Regra não encontrada.', 'warning')
            return redirect(url_for('main.firewall_manager'))

    return render_template('firewall_manager.html', user=user, regras=regras)

@bp.errorhandler(404)
def not_found_error(error):
    """Página de erro 404"""
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """Página de erro 500"""
    db.session.rollback()
    logger.error(f"Erro interno do servidor: {str(error)}")
    return render_template('errors/500.html'), 500

@bp.errorhandler(403)
def forbidden_error(error):
    """Página de erro 403"""
    return render_template('errors/403.html'), 403

@bp.before_app_request
def before_request():
    """Executa antes de cada requisição"""
    # Log da requisição
    if request.endpoint and not request.endpoint.startswith('static'):
        SystemLog.log(
            level='DEBUG',
            message=f'Requisição: {request.method} {request.path}',
            module='request',
            user_id=session.get('user_id'),
            ip_address=request.remote_addr
        )
    
    # Verificar se usuário está logado e sessão é válida
    if 'user_id' in session and 'session_token' in session:
        user_session = UserSession.query.filter_by(
            user_id=session['user_id'],
            session_token=session['session_token'],
            is_active=True
        ).first()
        
        if not user_session or user_session.is_expired():
            # Sessão inválida ou expirada
            session.clear()
            if request.endpoint and request.endpoint != 'auth.login':
                flash('Sua sessão expirou. Faça login novamente.', 'warning')
