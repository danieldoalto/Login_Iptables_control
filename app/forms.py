"""
Formulários da aplicação usando Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from app.models import User
from app.captcha import generate_captcha, validate_captcha

class RegistrationForm(FlaskForm):
    """Formulário de registro de usuário"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=120, message='Email deve ter no máximo 120 caracteres')
    ])
    
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=8, max=128, message='Senha deve ter entre 8 e 128 caracteres')
    ])
    
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('password', message='Senhas devem ser iguais')
    ])
    
    # Campos para verificação humana simples
    captcha_question = HiddenField()
    captcha_answer = IntegerField('Verificação Humana', validators=[
        NumberRange(min=0, max=1000, message='Resposta inválida')
    ])
    
    submit = SubmitField('Registrar')
    
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.generate_captcha()
        # Se captcha estiver desabilitado, remove validadores
        if self.captcha_question.data == "Captcha desabilitado":
            self.captcha_answer.validators = []
    
    def generate_captcha(self):
        """Gera pergunta matemática simples para verificação humana"""
        question, answer = generate_captcha()
        if question and answer:
            self.captcha_question.data = question
            self.correct_answer = answer
        else:
            # Fallback se captcha estiver desabilitado
            self.captcha_question.data = "Captcha desabilitado"
            self.correct_answer = 0
    
    def validate_email(self, email):
        """Valida se email já não está cadastrado"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Este email já está cadastrado.')
    
    def validate_captcha_answer(self, captcha_answer):
        """Valida resposta da verificação humana"""
        # Pular validação se captcha estiver desabilitado
        if self.captcha_question.data == "Captcha desabilitado":
            return
        
        if hasattr(self, 'correct_answer'):
            if not validate_captcha(captcha_answer.data, self.correct_answer):
                raise ValidationError('Resposta incorreta. Tente novamente.')

class LoginForm(FlaskForm):
    """Formulário de login"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ])
    
    remember_me = BooleanField('Lembrar de mim')
    
    # Campos para verificação humana simples
    captcha_question = HiddenField()
    captcha_answer = IntegerField('Verificação Humana', validators=[
        NumberRange(min=0, max=1000, message='Resposta inválida')
    ])
    
    submit = SubmitField('Entrar')
    
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.generate_captcha()
        # Se captcha estiver desabilitado, remove validadores
        if self.captcha_question.data == "Captcha desabilitado":
            self.captcha_answer.validators = []
    
    def generate_captcha(self):
        """Gera pergunta matemática simples para verificação humana"""
        question, answer = generate_captcha()
        if question and answer:
            self.captcha_question.data = question
            self.correct_answer = answer
        else:
            # Fallback se captcha estiver desabilitado
            self.captcha_question.data = "Captcha desabilitado"
            self.correct_answer = 0
    
    def validate_captcha_answer(self, captcha_answer):
        """Valida resposta da verificação humana"""
        # Pular validação se captcha estiver desabilitado
        if self.captcha_question.data == "Captcha desabilitado":
            return
        
        if hasattr(self, 'correct_answer'):
            if not validate_captcha(captcha_answer.data, self.correct_answer):
                raise ValidationError('Resposta incorreta. Tente novamente.')

class RequestPasswordResetForm(FlaskForm):
    """Formulário para solicitar reset de senha"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    
    submit = SubmitField('Solicitar Reset de Senha')

class PasswordResetForm(FlaskForm):
    """Formulário para redefinir senha"""
    password = PasswordField('Nova Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=8, max=128, message='Senha deve ter entre 8 e 128 caracteres')
    ])
    
    password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('password', message='Senhas devem ser iguais')
    ])
    
    submit = SubmitField('Redefinir Senha')

class ResendConfirmationForm(FlaskForm):
    """Formulário para reenviar confirmação de email"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    
    submit = SubmitField('Reenviar Confirmação')
    
    def validate_email(self, email):
        """Valida se email existe e não está confirmado"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if not user:
            raise ValidationError('Email não encontrado.')
        if user.confirmed:
            raise ValidationError('Este email já foi confirmado.')

class ChangePasswordForm(FlaskForm):
    """Formulário para alterar senha quando logado"""
    current_password = PasswordField('Senha Atual', validators=[
        DataRequired(message='Senha atual é obrigatória')
    ])
    
    new_password = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=8, max=128, message='Senha deve ter entre 8 e 128 caracteres')
    ])
    
    new_password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('new_password', message='Senhas devem ser iguais')
    ])
    
    submit = SubmitField('Alterar Senha')
