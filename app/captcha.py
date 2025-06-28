"""
Módulo para gerenciamento de captcha
"""
import random
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class CaptchaManager:
    """Gerenciador de captcha"""
    
    def __init__(self):
        self.enabled = True
        self.difficulty = 'easy'
    
    def configure(self, app):
        """Configura o captcha baseado nas configurações da aplicação"""
        self.enabled = app.config.get('CAPTCHA_ENABLED', True)
        self.difficulty = app.config.get('CAPTCHA_DIFFICULTY', 'easy')
        
        logger.info(f"Captcha configurado: enabled={self.enabled}, difficulty={self.difficulty}")
    
    def is_enabled(self):
        """Verifica se o captcha está habilitado"""
        return self.enabled
    
    def generate_question(self):
        """Gera uma pergunta de captcha baseada na dificuldade"""
        if not self.is_enabled():
            return None, None
        
        if self.difficulty == 'easy':
            return self._generate_easy_question()
        elif self.difficulty == 'medium':
            return self._generate_medium_question()
        elif self.difficulty == 'hard':
            return self._generate_hard_question()
        else:
            return self._generate_easy_question()
    
    def _generate_easy_question(self):
        """Gera pergunta fácil (adição e subtração simples)"""
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"Quanto é {num1} + {num2}?"
        else:
            # Garantir que resultado seja positivo
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"Quanto é {num1} - {num2}?"
        
        return question, answer
    
    def _generate_medium_question(self):
        """Gera pergunta média (adição, subtração e multiplicação)"""
        num1 = random.randint(1, 15)
        num2 = random.randint(1, 15)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"Quanto é {num1} + {num2}?"
        elif operation == '-':
            # Garantir que resultado seja positivo
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"Quanto é {num1} - {num2}?"
        else:  # multiplicação
            # Usar números menores para multiplicação
            num1 = random.randint(2, 10)
            num2 = random.randint(2, 10)
            answer = num1 * num2
            question = f"Quanto é {num1} × {num2}?"
        
        return question, answer
    
    def _generate_hard_question(self):
        """Gera pergunta difícil (operações mais complexas)"""
        operation_type = random.choice(['math', 'sequence', 'word'])
        
        if operation_type == 'math':
            # Operações matemáticas mais complexas
            num1 = random.randint(10, 50)
            num2 = random.randint(2, 10)
            operation = random.choice(['+', '-', '*'])
            
            if operation == '+':
                answer = num1 + num2
                question = f"Quanto é {num1} + {num2}?"
            elif operation == '-':
                answer = num1 - num2
                question = f"Quanto é {num1} - {num2}?"
            else:  # multiplicação
                answer = num1 * num2
                question = f"Quanto é {num1} × {num2}?"
        
        elif operation_type == 'sequence':
            # Sequências numéricas
            start = random.randint(1, 10)
            step = random.randint(2, 5)
            position = random.randint(3, 6)
            answer = start + (step * (position - 1))
            question = f"Complete a sequência: {start}, {start + step}, {start + step * 2}, ..., {answer}?"
        
        else:  # word
            # Perguntas de palavras simples
            questions = [
                ("Quantas letras tem a palavra 'SISTEMA'?", 7),
                ("Quantas vogais tem a palavra 'COMPUTADOR'?", 4),
                ("Quantas consoantes tem a palavra 'INTERNET'?", 6),
                ("Quantas letras tem a palavra 'SEGURANCA'?", 9),
                ("Quantas vogais tem a palavra 'FIREWALL'?", 3)
            ]
            question, answer = random.choice(questions)
        
        return question, answer
    
    def validate_answer(self, user_answer, correct_answer):
        """Valida a resposta do usuário"""
        if not self.is_enabled():
            return True
        
        try:
            # Converter para inteiro se possível
            if isinstance(user_answer, str):
                user_answer = int(user_answer.strip())
            elif user_answer is None:
                return False
            
            return user_answer == correct_answer
        except (ValueError, TypeError):
            return False

# Instância global do gerenciador de captcha
captcha_manager = CaptchaManager()

def get_captcha_manager():
    """Retorna a instância global do gerenciador de captcha"""
    return captcha_manager

def generate_captcha():
    """Função helper para gerar captcha"""
    return captcha_manager.generate_question()

def validate_captcha(user_answer, correct_answer):
    """Função helper para validar captcha"""
    return captcha_manager.validate_answer(user_answer, correct_answer) 