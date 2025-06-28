"""
API routes para o sistema
"""
import logging
from flask import Blueprint, jsonify, session, request, current_app
from app import limiter
from app.models import User, UserSession, FirewallRule, SystemLog, db
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)

@bp.route('/status')
@limiter.limit("30 per minute")
def api_status():
    """Status da API"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@bp.route('/user/session')
@limiter.limit("60 per minute")
def user_session_info():
    """Informações da sessão atual do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Buscar sessão atual
    current_session = UserSession.query.filter_by(
        user_id=user.id,
        session_token=session.get('session_token'),
        is_active=True
    ).first()
    
    if not current_session:
        return jsonify({'error': 'Sessão não encontrada'}), 404
    
    if current_session.is_expired():
        return jsonify({'error': 'Sessão expirada'}), 401
    
    return jsonify({
        'user_id': user.id,
        'email': user.email,
        'ip_address': current_session.ip_address,
        'login_time': current_session.created_at.isoformat(),
        'expires_at': current_session.expires_at.isoformat(),
        'session_duration_hours': 24,
        'time_remaining': (current_session.expires_at - datetime.utcnow()).total_seconds()
    })

@bp.route('/user/sessions')
@limiter.limit("30 per minute")
def user_sessions():
    """Lista todas as sessões do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Buscar sessões ativas
    active_sessions = UserSession.query.filter_by(
        user_id=user.id,
        is_active=True
    ).filter(UserSession.expires_at > datetime.utcnow()).all()
    
    sessions_data = []
    for sess in active_sessions:
        sessions_data.append({
            'id': sess.id,
            'ip_address': sess.ip_address,
            'user_agent': sess.user_agent,
            'created_at': sess.created_at.isoformat(),
            'expires_at': sess.expires_at.isoformat(),
            'is_current': sess.session_token == session.get('session_token'),
            'time_remaining': (sess.expires_at - datetime.utcnow()).total_seconds()
        })
    
    return jsonify({
        'active_sessions': sessions_data,
        'total_active': len(sessions_data)
    })

@bp.route('/firewall/allowed-ips')
@limiter.limit("10 per minute")
def firewall_allowed_ips():
    """Lista IPs permitidos no firewall (apenas para usuários logados)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        firewall_manager = current_app.firewall_manager
        allowed_ips = firewall_manager.list_allowed_ips()
        
        return jsonify({
            'allowed_ips': allowed_ips,
            'count': len(allowed_ips),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar IPs permitidos: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/system/stats')
@limiter.limit("5 per minute")
def system_stats():
    """Estatísticas do sistema (apenas para usuários logados)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    try:
        stats = {
            'users': {
                'total': User.query.count(),
                'confirmed': User.query.filter_by(confirmed=True).count(),
                'active_sessions': UserSession.query.filter_by(is_active=True).count()
            },
            'firewall': {
                'active_rules': FirewallRule.query.filter_by(is_active=True).count(),
                'total_rules': FirewallRule.query.count()
            },
            'logs': {
                'total': SystemLog.query.count(),
                'today': SystemLog.query.filter(
                    SystemLog.created_at >= datetime.utcnow().date()
                ).count()
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/session/extend', methods=['POST'])
@limiter.limit("3 per minute")
def extend_session():
    """Estende a sessão atual do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Buscar sessão atual
    current_session = UserSession.query.filter_by(
        user_id=user.id,
        session_token=session.get('session_token'),
        is_active=True
    ).first()
    
    if not current_session:
        return jsonify({'error': 'Sessão não encontrada'}), 404
    
    if current_session.is_expired():
        return jsonify({'error': 'Sessão já expirada'}), 401
    
    try:
        # Estender sessão por mais 24 horas
        current_session.extend_session(hours=24)
        db.session.commit()
        
        # Log da extensão
        SystemLog.log(
            level='INFO',
            message=f'Sessão estendida - IP: {current_session.ip_address}',
            module='api_extend',
            user_id=user.id,
            ip_address=current_session.ip_address
        )
        
        return jsonify({
            'message': 'Sessão estendida com sucesso',
            'new_expires_at': current_session.expires_at.isoformat(),
            'time_remaining': (current_session.expires_at - datetime.utcnow()).total_seconds()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao estender sessão: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.route('/user/activity')
@limiter.limit("10 per minute")
def user_activity():
    """Atividade recente do usuário"""
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Buscar logs recentes do usuário
    recent_logs = SystemLog.query.filter_by(
        user_id=user.id
    ).order_by(SystemLog.created_at.desc()).limit(20).all()
    
    activity_data = []
    for log in recent_logs:
        activity_data.append({
            'id': log.id,
            'level': log.level,
            'message': log.message,
            'module': log.module,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat()
        })
    
    return jsonify({
        'activity': activity_data,
        'total_records': len(activity_data)
    })

@bp.errorhandler(404)
def api_not_found(error):
    """Erro 404 da API"""
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@bp.errorhandler(500)
def api_internal_error(error):
    """Erro 500 da API"""
    logger.error(f"Erro interno da API: {str(error)}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

@bp.errorhandler(429)
def api_rate_limit_exceeded(error):
    """Erro de rate limit da API"""
    return jsonify({'error': 'Limite de requisições excedido. Tente novamente mais tarde.'}), 429

@bp.before_request
def api_before_request():
    """Executado antes de cada requisição da API"""
    # Log da requisição da API
    SystemLog.log(
        level='DEBUG',
        message=f'API: {request.method} {request.path}',
        module='api_request',
        user_id=session.get('user_id'),
        ip_address=request.remote_addr
    )
