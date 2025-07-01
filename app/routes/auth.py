"""
Rotas de autenticação
"""
import logging
from flask import Blueprint, render_template, session, request, redirect, url_for, flash, current_app, abort
from app import limiter
from app.models import User, UserSession, FirewallRule, SystemLog, db
from app.forms import LoginForm, RegistrationForm, ResendConfirmationForm
from app.email import send_confirmation_email, send_welcome_email, send_login_notification, send_registration_received_email, send_admin_new_registration_email, send_blacklist_email_user, send_blacklist_email_admin
from app.logging_config import log_user_action, log_security_event, log_error
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    """Registro de novo usuário"""
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Criar novo usuário
            user = User(email=form.email.data.lower())
            user.set_password(form.password.data)
            user.generate_confirmation_token()
            user.status = 'pending'  # Usuário pendente de aprovação
            db.session.add(user)
            db.session.commit()
            
            # Enviar email para o usuário
            send_registration_received_email(user)
            
            # Enviar email para o admin
            send_admin_new_registration_email(user)
            
            # Log do registro
            log_user_action(
                action="Registro de usuário",
                user_id=user.id,
                ip_address=request.remote_addr,
                details=f"Email: {user.email}"
            )
            
            SystemLog.log(
                level='INFO',
                message=f'Novo usuário registrado: {user.email}',
                module='auth_register',
                user_id=user.id,
                ip_address=request.remote_addr
            )
            
            flash('Registro realizado com sucesso! Verifique seu email para confirmar sua conta.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f"Erro no registro - Email: {form.email.data}")
            flash('Erro interno. Tente novamente.', 'error')
    
    return render_template('auth/register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Login do usuário"""
    form = LoginForm()
    current_app.logger.info(f"Formulário validado? {form.validate_on_submit()} - Erros: {form.errors}")
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            # Verificar se usuário está bloqueado
            if user.is_locked():
                log_security_event(
                    event_type="Tentativa de login em conta bloqueada",
                    details=f"Email: {user.email}",
                    ip_address=request.remote_addr,
                    user_id=user.id
                )
                flash('Conta temporariamente bloqueada devido a múltiplas tentativas de login. Tente novamente mais tarde.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Verificar se email foi confirmado
            if not user.confirmed:
                log_security_event(
                    event_type="Tentativa de login sem confirmação de email",
                    details=f"Email: {user.email}",
                    ip_address=request.remote_addr,
                    user_id=user.id
                )
                flash('Você precisa confirmar seu email antes de fazer login.', 'warning')
                return redirect(url_for('auth.resend_confirmation'))
            
            try:
                # Obter IP do cliente
                client_ip = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')
                
                # Criar sessão
                user_session = UserSession(
                    user_id=user.id,
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                db.session.add(user_session)
                db.session.commit()  # Agora user_session.id está disponível!

                # Criar regra de firewall (whitelist)
                firewall_chain = current_app.config.get('FIREWALL_CHAIN', 'WHITELIST')
                ipv6_raw = current_app.config.get('IPV6', 'False')
                ipv6_enabled = str(ipv6_raw).lower() in ['true', 'on', '1', 'yes']
                firewall_rule = FirewallRule(
                    ip_address=client_ip,
                    user_id=user.id,
                    session_id=user_session.id,
                    iptables_rule_added=False,
                    tipo='whitelist',
                    chain=firewall_chain
                )
                db.session.add(firewall_rule)
                # Se IPV6 estiver ativado e client_ip for string, registrar também para IPv6 (simulação)
                if ipv6_enabled and isinstance(client_ip, str) and ':' in client_ip:
                    firewall_rule_v6 = FirewallRule(
                        ip_address=client_ip,
                        user_id=user.id,
                        session_id=user_session.id,
                        iptables_rule_added=False,
                        tipo='whitelist',
                        chain=firewall_chain
                    )
                    db.session.add(firewall_rule_v6)
                user.record_successful_login()
                db.session.commit()
                session['user_id'] = user.id
                session['session_token'] = user_session.session_token
                session['user_email'] = user.email
                session.permanent = True
                log_user_action(
                    action="Login bem-sucedido",
                    user_id=user.id,
                    ip_address=client_ip,
                    details=f"User-Agent: {user_agent[:100]}"
                )
                SystemLog.log(
                    level='INFO',
                    message=f'Login bem-sucedido - IP: {client_ip}',
                    module='auth_login',
                    user_id=user.id,
                    ip_address=client_ip
                )
                send_login_notification(user, client_ip, user_agent)
                flash(f'Login realizado com sucesso!', 'success')
                return redirect(url_for('main.dashboard'))

            except Exception as e:
                db.session.rollback()
                log_error(e, f"Erro interno no login - Usuário: {user.id}, IP: {request.remote_addr}")
                flash('Erro interno durante login. Tente novamente.', 'error')
                
                SystemLog.log(
                    level='ERROR',
                    message=f'Erro interno no login: {str(e)}',
                    module='auth_login',
                    user_id=user.id if user else None,
                    ip_address=request.remote_addr
                )
        else:
            # Login falhou
            if user:
                user.record_failed_login()
                db.session.commit()

                # Se atingiu 5 tentativas, bloquear usuário e IP (exceto admin)
                if user.failed_login_attempts >= 5 and not user.is_admin():
                    user.status = 'blacklist'
                    db.session.commit()
                    # Criar regra de blacklist
                    firewall_black_chain = current_app.config.get('FIREWALL_BLACK', 'BLACKLIST')
                    blacklist_rule = FirewallRule(
                        ip_address=request.remote_addr,
                        user_id=user.id,
                        session_id=None,
                        iptables_rule_added=False,
                        tipo='blacklist',
                        chain=firewall_black_chain
                    )
                    db.session.add(blacklist_rule)
                    db.session.commit()
                    # Enviar emails
                    send_blacklist_email_user(user, request.remote_addr)
                    send_blacklist_email_admin(user, request.remote_addr)
                
                log_security_event(
                    event_type="Tentativa de login falhada",
                    details=f"Email: {form.email.data}",
                    ip_address=request.remote_addr,
                    user_id=user.id
                )
                
                SystemLog.log(
                    level='WARNING',
                    message=f'Tentativa de login falhada - email: {form.email.data}',
                    module='auth_login',
                    user_id=user.id,
                    ip_address=request.remote_addr
                )
            else:
                log_security_event(
                    event_type="Tentativa de login com email inexistente",
                    details=f"Email: {form.email.data}",
                    ip_address=request.remote_addr
                )
            
            flash('Email ou senha incorretos.', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
def logout():
    """Logout do usuário"""
    if 'user_id' in session and 'session_token' in session:
        try:
            # Buscar sessão atual
            user_session = UserSession.query.filter_by(
                user_id=session['user_id'],
                session_token=session['session_token'],
                is_active=True
            ).first()
            
            if user_session:
                # Encerrar sessão
                user_session.end_session()
                
                # Marcar regra do firewall como removida
                firewall_rule = FirewallRule.query.filter_by(
                    session_id=user_session.id,
                    is_active=True
                ).first()
                
                if firewall_rule:
                    firewall_rule.mark_as_removed()
                
                db.session.commit()
                
                # Log do logout
                log_user_action(
                    action="Logout",
                    user_id=user_session.user_id,
                    ip_address=user_session.ip_address,
                    details="Sessão encerrada e IP removido do firewall"
                )
                
                SystemLog.log(
                    level='INFO',
                    message=f'Logout realizado - IP: {user_session.ip_address}',
                    module='auth_logout',
                    user_id=user_session.user_id,
                    ip_address=user_session.ip_address
                )
                
                flash(f'Logout realizado com sucesso! Seu IP {user_session.ip_address} foi removido do firewall.', 'success')
            
        except Exception as e:
            log_error(e, f"Erro no logout - Usuário: {session.get('user_id')}")
            db.session.rollback()
            flash('Erro durante logout, mas você foi desconectado.', 'warning')
    
    # Limpar sessão
    session.clear()
    return redirect(url_for('main.index'))

@bp.route('/confirm/<token>')
def confirm_email(token):
    """Confirma email do usuário"""
    user = User.query.filter_by(confirmation_token=token).first()
    
    if not user:
        log_security_event(
            event_type="Tentativa de confirmação com token inválido",
            details=f"Token: {token[:20]}...",
            ip_address=request.remote_addr
        )
        flash('Link de confirmação inválido.', 'error')
        return redirect(url_for('main.index'))
    
    if user.confirmed:
        flash('Sua conta já foi confirmada.', 'info')
        return redirect(url_for('auth.login'))
    
    if not user.is_confirmation_token_valid():
        log_security_event(
            event_type="Tentativa de confirmação com token expirado",
            details=f"Email: {user.email}",
            ip_address=request.remote_addr,
            user_id=user.id
        )
        flash('Link de confirmação expirado. Solicite um novo link.', 'error')
        return redirect(url_for('auth.resend_confirmation'))
    
    try:
        # Confirmar email
        user.confirm_email()
        db.session.commit()
        
        # Enviar email de boas-vindas
        send_welcome_email(user)
        
        # Log da confirmação
        log_user_action(
            action="Confirmação de email",
            user_id=user.id,
            ip_address=request.remote_addr,
            details=f"Email: {user.email}"
        )
        
        SystemLog.log(
            level='INFO',
            message=f'Email confirmado: {user.email}',
            module='auth_confirm',
            user_id=user.id,
            ip_address=request.remote_addr
        )
        
        flash('Email confirmado com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        log_error(e, f"Erro na confirmação de email - Usuário: {user.id}")
        flash('Erro interno. Tente novamente.', 'error')
        return redirect(url_for('main.index'))

@bp.route('/resend-confirmation', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def resend_confirmation():
    """Reenviar confirmação de email"""
    form = ResendConfirmationForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and not user.confirmed:
            try:
                # Gerar novo token
                user.generate_confirmation_token()
                db.session.commit()
                
                # Enviar email
                send_confirmation_email(user)
                
                # Log do reenvio
                log_user_action(
                    action="Reenvio de confirmação",
                    user_id=user.id,
                    ip_address=request.remote_addr,
                    details=f"Email: {user.email}"
                )
                
                SystemLog.log(
                    level='INFO',
                    message=f'Confirmação reenviada para: {user.email}',
                    module='auth_resend',
                    user_id=user.id,
                    ip_address=request.remote_addr
                )
                
                flash('Nova confirmação enviada para seu email.', 'success')
                return redirect(url_for('auth.login'))
                
            except Exception as e:
                db.session.rollback()
                log_error(e, f"Erro ao reenviar confirmação - Usuário: {user.id}")
                flash('Erro interno. Tente novamente.', 'error')
        else:
            log_security_event(
                event_type="Tentativa de reenvio para email inexistente ou já confirmado",
                details=f"Email: {form.email.data}",
                ip_address=request.remote_addr
            )
    
    return render_template('auth/resend_confirmation.html', form=form)

@bp.route('/account')
def account():
    """Página da conta do usuário"""
    if 'user_id' not in session:
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Sessão inválida. Faça login novamente.', 'error')
        return redirect(url_for('auth.login'))
    
    # Buscar sessões do usuário
    user_sessions = UserSession.query.filter_by(
        user_id=user.id
    ).order_by(UserSession.created_at.desc()).limit(20).all()
    
    return render_template('auth/account.html', user=user, user_sessions=user_sessions)

@bp.route('/end-session/<int:session_id>')
def end_session(session_id):
    """Encerra uma sessão específica"""
    if 'user_id' not in session:
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=session['user_id'],
        is_active=True
    ).first()
    
    if not user_session:
        flash('Sessão não encontrada.', 'error')
        return redirect(url_for('auth.account'))
    
    try:
        # Se for a sessão atual, fazer logout completo
        if user_session.session_token == session.get('session_token'):
            return redirect(url_for('auth.logout'))
        
        # Encerrar sessão
        user_session.end_session()
        
        # Marcar regra do firewall como removida
        firewall_rule = FirewallRule.query.filter_by(
            session_id=user_session.id,
            is_active=True
        ).first()
        
        if firewall_rule:
            firewall_rule.mark_as_removed()
        
        db.session.commit()
        
        # Log da ação
        SystemLog.log(
            level='INFO',
            message=f'Sessão encerrada manualmente - IP: {user_session.ip_address}',
            module='auth_end_session',
            user_id=user_session.user_id,
            ip_address=user_session.ip_address
        )
        
        flash(f'Sessão encerrada com sucesso! IP {user_session.ip_address} removido do firewall.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao encerrar sessão: {str(e)}")
        flash('Erro ao encerrar sessão.', 'error')
    
    return redirect(url_for('auth.account'))
