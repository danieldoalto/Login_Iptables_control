# Sistema de Logging

Este documento descreve o sistema de logging implementado no projeto de Firewall Login System.

## Configuração

### Variáveis de Ambiente (.env)

```bash
# Configurações de Log
LOG_LEVEL=INFO                    # Nível de log (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=logs/firewall_login.log  # Arquivo de log
LOG_MAX_SIZE=10MB                 # Tamanho máximo antes de rotacionar
LOG_BACKUP_COUNT=5                # Número de backups a manter
```

### Níveis de Log

- **DEBUG**: Informações detalhadas para desenvolvimento
- **INFO**: Informações gerais do sistema
- **WARNING**: Avisos sobre situações que merecem atenção
- **ERROR**: Erros que não impedem o funcionamento
- **CRITICAL**: Erros críticos que podem afetar o sistema

## Estrutura dos Logs

### Formato Padrão

```
2025-06-28 11:46:32,055 [INFO] app: Mensagem do log [arquivo.py:linha]
```

### Categorias de Log

1. **app**: Logs gerais da aplicação
2. **app.user_actions**: Ações de usuários (login, logout, registro)
3. **app.security**: Eventos de segurança (tentativas de login, tokens inválidos)
4. **app.system**: Eventos do sistema (inicialização, configuração)
5. **app.errors**: Erros da aplicação
6. **app.auth**: Logs específicos de autenticação
7. **app.firewall**: Logs do sistema de firewall
8. **app.email**: Logs de envio de emails

## Funções de Logging

### log_user_action()
Registra ações de usuários com contexto detalhado.

```python
from app.logging_config import log_user_action

log_user_action(
    action="Login bem-sucedido",
    user_id=user.id,
    ip_address=request.remote_addr,
    details="User-Agent: Mozilla/5.0..."
)
```

### log_security_event()
Registra eventos de segurança.

```python
from app.logging_config import log_security_event

log_security_event(
    event_type="Tentativa de login falhada",
    details="Email: user@example.com",
    ip_address=request.remote_addr,
    user_id=user.id
)
```

### log_system_event()
Registra eventos do sistema.

```python
from app.logging_config import log_system_event

log_system_event(
    event_type="Inicialização do sistema",
    details="Configuração carregada com sucesso"
)
```

### log_error()
Registra erros com stack trace completo.

```python
from app.logging_config import log_error

try:
    # código que pode gerar erro
    pass
except Exception as e:
    log_error(e, "Contexto do erro")
```

## Rotação de Arquivos

O sistema implementa rotação automática de logs:

- **Tamanho máximo**: 10MB (configurável)
- **Backups**: 5 arquivos (configurável)
- **Nomenclatura**: `firewall_login.log.1`, `firewall_login.log.2`, etc.

## Scripts de Utilidade

### test_logging.py
Testa o sistema de logging criando logs de exemplo.

```bash
python3 test_logging.py
```

### monitor_logs.py
Monitora logs em tempo real ou mostra estatísticas.

```bash
# Monitorar em tempo real
python3 monitor_logs.py

# Mostrar estatísticas
python3 monitor_logs.py stats
```

## Localização dos Logs

- **Arquivo principal**: `logs/firewall_login.log`
- **Backups**: `logs/firewall_login.log.1`, `logs/firewall_login.log.2`, etc.

## Exemplos de Logs

### Login Bem-sucedido
```
2025-06-28 11:46:32,055 [INFO] app.user_actions: Ação: Login bem-sucedido | Usuário: 1 | IP: 192.168.1.100 | Detalhes: User-Agent: Mozilla/5.0... [auth.py:120]
```

### Evento de Segurança
```
2025-06-28 11:46:32,056 [WARNING] app.security: Evento de Segurança: Tentativa de login falhada | IP: 192.168.1.100 | Usuário: 1 | Detalhes: Email: user@example.com [auth.py:180]
```

### Erro do Sistema
```
2025-06-28 11:46:32,056 [ERROR] app.errors: Erro: Connection timeout | Contexto: Envio de email [email.py:45]
Traceback (most recent call last):
  File "app/email.py", line 45, in send_email
    smtp.send_message(msg)
TimeoutError: Connection timeout
```

## Monitoramento

### Comandos Úteis

```bash
# Ver últimas 20 linhas
tail -20 logs/firewall_login.log

# Monitorar em tempo real
tail -f logs/firewall_login.log

# Filtrar por nível
grep "\[ERROR\]" logs/firewall_login.log

# Filtrar por usuário
grep "Usuário: 1" logs/firewall_login.log

# Contar eventos de segurança
grep "app.security" logs/firewall_login.log | wc -l
```

### Alertas

Configure alertas para:
- Múltiplas tentativas de login falhadas
- Erros críticos do sistema
- Tentativas de acesso não autorizado
- Problemas de conectividade

## Manutenção

### Limpeza de Logs Antigos

```bash
# Remover logs com mais de 30 dias
find logs/ -name "*.log*" -mtime +30 -delete

# Comprimir logs antigos
gzip logs/firewall_login.log.5
```

### Backup

```bash
# Backup diário
cp logs/firewall_login.log logs/backup/firewall_login_$(date +%Y%m%d).log
```

## Troubleshooting

### Problemas Comuns

1. **Logs não aparecem**: Verificar permissões da pasta `logs/`
2. **Arquivo muito grande**: Verificar configuração de rotação
3. **Logs duplicados**: Verificar se `propagate=False` está configurado
4. **Erro de encoding**: Verificar se o arquivo está em UTF-8

### Verificações

```bash
# Verificar permissões
ls -la logs/

# Verificar tamanho
du -h logs/firewall_login.log

# Verificar encoding
file logs/firewall_login.log
``` 