# 🔐 Sistema de Login com Firewall

Um sistema de autenticação web que integra controle de firewall (iptables) para gerenciar acesso baseado em login.

## 🚀 Características

- ✅ **Autenticação segura** com confirmação por email
- ✅ **Integração com iptables** para controle de IPs
- ✅ **Proteção contra força bruta** (bloqueio após 5 tentativas)
- ✅ **Sessões persistentes** com tokens únicos
- ✅ **Rate limiting** para prevenir ataques
- ✅ **Logs detalhados** de todas as ações
- ✅ **Interface web moderna** com Bootstrap
- ✅ **Tarefas em background** para limpeza automática

## 📋 Pré-requisitos

- Python 3.8+
- iptables/ip6tables
- Privilégios sudo para gerenciar firewall
- Conta de email para envio de confirmações

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd firewall_login_system
```

### 2. Crie e ative o ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Configure permissões do sudo (opcional)
Para evitar digitar senha a cada operação do firewall:
```bash
sudo visudo
# Adicione a linha:
# seu_usuario ALL=(ALL) NOPASSWD: /sbin/iptables, /sbin/ip6tables
```

## 🚀 Execução

### Método 1: Script automático (recomendado)
```bash
./start.sh
```

### Método 2: Execução manual
```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute a aplicação
python run.py
```

### Método 3: Produção com Gunicorn
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```bash
# Ambiente
FLASK_ENV=development

# Chave secreta (ALTERE EM PRODUÇÃO!)
SECRET_KEY=sua-chave-secreta-muito-segura

# Banco de dados
DATABASE_URL=sqlite:///firewall_login.db

# Email (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=seu-email@gmail.com

# Administrador
ADMIN_EMAIL=admin@localhost

# Logging
LOG_LEVEL=INFO
LOG_FILE=firewall_login.log

# Firewall
FIREWALL_CHAIN=FIREWALL_LOGIN_ALLOW
IPTABLES_PATH=/sbin/iptables
IP6TABLES_PATH=/sbin/ip6tables
```

### Configuração de Email (Gmail)

1. Ative a verificação em duas etapas
2. Gere uma senha de app
3. Use essa senha no campo `MAIL_PASSWORD`

## 🌐 Uso

### 1. Acesse a aplicação
```
http://localhost:5000
```

### 2. Registre uma conta
- Preencha email e senha
- Confirme o email recebido

### 3. Faça login
- Após login bem-sucedido, seu IP será liberado no firewall
- Você terá acesso ao dashboard

### 4. Logout
- Ao fazer logout, seu IP será removido do firewall

## 📊 Funcionalidades

### Dashboard
- Visualização de sessões ativas
- Logs do sistema
- Status do firewall
- Gerenciamento de conta

### Segurança
- Hash de senhas com bcrypt
- Tokens de confirmação seguros
- Proteção CSRF
- Rate limiting por IP
- Captcha matemático
- Sessões seguras

### Firewall
- Adição automática de IPs no login
- Remoção automática no logout
- Suporte a IPv4 e IPv6
- Sincronização com banco de dados

## 🔧 Manutenção

### Limpeza automática
O sistema executa tarefas em background:
- Limpeza de sessões expiradas (a cada 5 min)
- Sincronização de regras do firewall (a cada 10 min)
- Health check do sistema

### Logs
- Logs de aplicação: `firewall_login.log`
- Logs do sistema: Banco de dados
- Logs do firewall: `/var/log/iptables.log`

### Backup
```bash
# Backup do banco
cp firewall_login.db backup_$(date +%Y%m%d_%H%M%S).db

# Backup das regras do firewall
sudo iptables-save > firewall_rules_$(date +%Y%m%d_%H%M%S).txt
```

## 🚨 Troubleshooting

### Erro de permissão do iptables
```bash
sudo chmod +s /sbin/iptables
sudo chmod +s /sbin/ip6tables
```

### Email não enviado
- Verifique as configurações SMTP
- Confirme se a verificação em duas etapas está ativa
- Use senha de app, não a senha normal

### Banco de dados corrompido
```bash
rm firewall_login.db
python run.py  # Recria o banco automaticamente
```

### Firewall não funciona
```bash
# Verificar se iptables está instalado
sudo apt-get install iptables

# Verificar regras
sudo iptables -L FIREWALL_LOGIN_ALLOW
```

## 🔒 Segurança

### Em Produção
1. **Altere a SECRET_KEY**
2. **Use HTTPS**
3. **Configure firewall adequadamente**
4. **Monitore logs regularmente**
5. **Faça backups frequentes**
6. **Use banco PostgreSQL/MySQL**

### Recomendações
- Implemente 2FA
- Use captcha mais robusto
- Configure whitelist de IPs
- Implemente monitoramento
- Use proxy reverso (nginx)

## 📝 Licença

Este projeto é de código aberto. Use com responsabilidade.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Consulte os logs do sistema
- Verifique a documentação

---

**⚠️ AVISO**: Este sistema manipula regras de firewall. Use apenas em ambientes controlados e teste adequadamente antes de usar em produção. 