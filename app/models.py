"""
Models do banco de dados para o sistema de login com firewall
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import secrets

db = SQLAlchemy()

class User(db.Model):
    """Model para usuários do sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'admin' ou 'user'
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    confirmation_token = db.Column(db.String(255), unique=True)
    confirmation_sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected, inactive, blocked
    
    # Relacionamentos
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Define a senha do usuário com hash seguro"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def generate_confirmation_token(self):
        """Gera token único para confirmação de email"""
        self.confirmation_token = secrets.token_urlsafe(32)
        self.confirmation_sent_at = datetime.utcnow()
    
    def is_confirmation_token_valid(self):
        """Verifica se o token de confirmação ainda é válido (1 hora)"""
        if not self.confirmation_sent_at:
            return False
        return datetime.utcnow() - self.confirmation_sent_at < timedelta(hours=1)
    
    def confirm_email(self):
        """Confirma o email do usuário"""
        self.confirmed = True
        self.confirmation_token = None
        self.confirmation_sent_at = None
    
    def is_locked(self):
        """Verifica se a conta está bloqueada por tentativas de login"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def lock_account(self, minutes=30):
        """Bloqueia a conta por um período"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.failed_login_attempts = 0
    
    def record_failed_login(self):
        """Registra tentativa de login falhada"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
    
    def record_successful_login(self):
        """Registra login bem-sucedido"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.role == 'admin' or self.role == 'administrator'
    
    def is_user(self):
        """Verifica se o usuário é comum"""
        return self.role == 'user'
    
    def can_access_admin_panel(self):
        """Verifica se o usuário pode acessar o painel administrativo"""
        return self.is_admin() and self.confirmed and self.is_active
    
    def is_pending(self):
        return self.status == 'pending'

    def is_approved(self):
        return self.status == 'approved'

    def is_rejected(self):
        return self.status == 'rejected'

    def is_inactive(self):
        return self.status == 'inactive'

    def is_blocked(self):
        return self.status == 'blocked'
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class UserSession(db.Model):
    """Model para sessões ativas de usuários"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IPv4 e IPv6
    user_agent = db.Column(db.Text)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    ended_at = db.Column(db.DateTime)
    
    def __init__(self, user_id, ip_address, user_agent=None):
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
    
    def is_expired(self):
        """Verifica se a sessão expirou"""
        return datetime.utcnow() > self.expires_at
    
    def end_session(self):
        """Encerra a sessão"""
        self.is_active = False
        self.ended_at = datetime.utcnow()
    
    def extend_session(self, hours=24):
        """Estende o tempo da sessão"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    @classmethod
    def cleanup_expired(cls):
        """Remove sessões expiradas do banco"""
        expired_sessions = cls.query.filter(
            cls.expires_at < datetime.utcnow(),
            cls.is_active == True
        ).all()
        
        for session in expired_sessions:
            session.end_session()
        
        db.session.commit()
        return len(expired_sessions)
    
    def __repr__(self):
        return f'<UserSession {self.user.email} - {self.ip_address}>'

class FirewallRule(db.Model):
    """Model para rastrear regras do firewall"""
    __tablename__ = 'firewall_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('user_sessions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    removed_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    iptables_rule_added = db.Column(db.Boolean, default=False)
    tipo = db.Column(db.String(20), default='whitelist', nullable=False)  # whitelist ou blacklist
    chain = db.Column(db.String(50), default='WHITELIST', nullable=False)
    
    # Relacionamentos
    user = db.relationship('User', backref='firewall_rules')
    session = db.relationship('UserSession', backref='firewall_rule', uselist=False)
    
    def mark_as_removed(self):
        """Marca a regra como removida"""
        self.is_active = False
        self.removed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<FirewallRule {self.ip_address} - {self.user.email}>'

class SystemLog(db.Model):
    """Model para logs do sistema"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamento
    user = db.relationship('User', backref='system_logs')
    
    @classmethod
    def log(cls, level, message, module, user_id=None, ip_address=None):
        """Método para criar log no sistema"""
        log_entry = cls(
            level=level,
            message=message,
            module=module,
            user_id=user_id,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def __repr__(self):
        return f'<SystemLog {self.level} - {self.module}>'
