# INFOS.md

## Visão Geral do Sistema

Sistema de Login com Firewall desenvolvido em Flask, com autenticação web, controle de acesso via iptables, aprovação de usuários, envio de emails, logs robustos e painel administrativo. Utiliza SQLAlchemy, Flask-Mail, Flask-Limiter, APScheduler, Bootstrap e padrão Factory/Blueprints.

---

## Novidades e Customização do Dashboard

- O dashboard agora é **dinâmico e configurável** via o arquivo `config.yml` na raiz do projeto.
- As seções exibidas para o **administrador** e para o **usuário comum** são definidas neste arquivo, sem necessidade de alterar código Python ou HTML.
- Os nomes das seções do dashboard agora correspondem aos nomes dos cards/janelas exibidos na interface. Os nomes padrão são:
  - `status_do_sistema`
  - `sua_sessao_atual`
  - `logs_recentes`
  - `acoes_rapidas`
- Para alterar o que aparece no dashboard de cada perfil, edite o arquivo `config.yml`:

```yaml
admin:
  sections:
    - status_do_sistema
    - sua_sessao_atual
    - logs_recentes
    - acoes_rapidas
usuario:
  sections:
    - status_do_sistema
    - sua_sessao_atual
```
- O sistema carrega essas configurações automaticamente ao iniciar. Basta adicionar ou remover nomes de cards no `config.yml` para personalizar o dashboard.
- O template `dashboard.html` e o código Python usam esses nomes diretamente para exibir os cards.

---

## Novidade: Card "Firewall Manager" no Dashboard do Admin

- Agora o dashboard do administrador conta com o card **Firewall Manager**.
- Permite visualizar todos os IPs liberados (whitelist) e bloqueados (blacklist), com informações detalhadas de cada regra (IP, tipo, usuário, data, chain).
- Permite **adicionar** novos IPs à whitelist ou blacklist, escolhendo o tipo e a chain (opcional).
- Permite **remover** IPs da whitelist ou blacklist, removendo também a regra correspondente do iptables.
- Todas as ações são refletidas imediatamente no banco de dados e no firewall real (iptables), respeitando o modo simulação se o firewall estiver desativado.
- O card só aparece para administradores e pode ser ativado/desativado no dashboard editando o `config.yml`.

### Exemplo de config.yml atualizado

```yaml
admin:
  sections:
    - status_do_sistema
    - sua_sessao_atual
    - logs_recentes
    - acoes_rapidas
    - firewall_manager
usuario:
  sections:
    - status_do_sistema
    - sua_sessao_atual
```

### Como acessar e usar o Firewall Manager

1. Faça login como administrador.
2. No dashboard, clique em **Acessar Gerenciador de Firewall** no card "Firewall Manager".
3. Na página do gerenciador:
   - Veja a lista de todos os IPs ativos (liberados/bloqueados), com dados do usuário, data e tipo.
   - Para remover um IP, clique no botão "Remover" ao lado do registro desejado.
   - Para adicionar um novo IP, preencha o formulário na parte inferior, escolhendo o tipo (liberar/bloquear) e, se necessário, a chain.
   - As ações são aplicadas imediatamente no banco e no iptables.

### Fluxo de uso do Firewall Manager

- **Adicionar IP**: Preencha o IP, selecione o tipo (liberar/bloquear) e clique em "Adicionar". O IP será registrado no banco e a regra criada no iptables.
- **Remover IP**: Clique em "Remover" ao lado do IP desejado. O registro será marcado como removido no banco e a regra excluída do iptables.
- **Visualização**: Todos os registros ativos aparecem em uma tabela, com destaque visual para whitelist (verde) e blacklist (vermelho).

---

## Estrutura de Pastas e Arquivos

```
firewall_login_system/
├── app/                  # Código principal da aplicação Flask
│   ├── __init__.py       # Factory da aplicação, inicialização de extensões, blueprints
│   ├── models.py         # Modelos do banco de dados (User, UserSession, FirewallRule, SystemLog, etc)
│   ├── routes/           # Blueprints de rotas (auth, main, api)
│   ├── forms.py          # Formulários Flask-WTF (login, registro, captcha, etc)
│   ├── email.py          # Funções de envio de email
│   ├── captcha.py        # Lógica do captcha matemático
│   ├── firewall.py       # Lógica de integração com iptables
│   ├── logging_config.py # Configuração avançada de logging
│   ├── tasks.py          # Tarefas agendadas (APScheduler)
│   └── ...
├── templates/            # Templates HTML (Bootstrap, Jinja2)
│   ├── base.html         # Template base
│   ├── auth/             # Templates de autenticação (login, registro, etc)
│   ├── main/             # Templates do dashboard e páginas principais
│   └── emails/           # Templates de emails (confirmação, boas-vindas, notificação, etc)
├── static/               # Arquivos estáticos (CSS, JS, imagens)
├── instance/             # Arquivos sensíveis e banco de dados SQLite
│   └── firewall_login.db # Banco de dados principal
├── logs/                 # Arquivos de log rotacionados
│   └── firewall_login.log
├── config/               # Configurações da aplicação
│   └── config.py         # Classes de configuração (dev, prod, test)
├── config.yml            # Configuração dinâmica do dashboard (seções por perfil)
├── .env                  # Variáveis de ambiente (senhas, email, configs)
├── requirements.txt      # Dependências do projeto
├── run.py                # Script para rodar a aplicação Flask
├── init_admin.py         # Script para criar/atualizar o administrador
├── test_logging.py       # Script de teste do sistema de logging
├── monitor_logs.py       # Script para monitorar e analisar logs
├── README_LOGGING.md     # Documentação detalhada do sistema de logging
├── INFOS.md              # (Este arquivo) Documentação técnica geral
└── ...
```

---

## Principais Arquivos e Funcionalidades

### app/__init__.py
- Cria a aplicação Flask (factory pattern)
- Inicializa extensões: SQLAlchemy, Mail, Limiter, APScheduler
- Registra blueprints (rotas)
- Configura logging, captcha, firewall
- Carrega configurações do .env
- **Carrega configurações do dashboard a partir do config.yml**

### app/models.py
- Define os modelos do banco:
  - **User**: Usuário do sistema (campos: email, senha, role, confirmado, aprovado, etc)
  - **UserSession**: Sessões de login dos usuários
  - **FirewallRule**: Regras de firewall associadas a sessões/IPs
  - **SystemLog**: Logs de eventos do sistema
- Métodos utilitários para autenticação, aprovação, bloqueio, etc.

### app/routes/
- **auth.py**: Rotas de autenticação (login, logout, registro, confirmação, aprovação)
- **main.py**: Rotas principais (dashboard, painel admin, etc)
- **api.py**: Rotas de API (se houver)

### app/forms.py
- Formulários Flask-WTF para login, registro, captcha, reset de senha, etc.
- Validações customizadas (captcha, email único, etc)

### app/email.py
- Funções para envio de emails (confirmação, boas-vindas, notificação de login, aprovação, etc)
- Usa Flask-Mail e templates HTML

### app/captcha.py
- Geração e validação de captcha matemático
- Configuração dinâmica via .env (habilitar/desabilitar, dificuldade)

### app/firewall.py
- Integração com iptables (adicionar/remover IPs)
- Pode ser desabilitado para testes
- Lida com permissões e logs de firewall

### app/logging_config.py
- Configuração avançada de logging (rotação, múltiplos níveis, logs por categoria)
- Funções utilitárias para logar ações de usuário, eventos de segurança, sistema e erros

### app/tasks.py
- Tarefas agendadas com APScheduler (limpeza de sessões, sincronização de firewall)

### config/config.py
- Classes de configuração (Development, Production, Testing)
- Lê variáveis do .env
- Define caminhos de banco, email, logging, captcha, firewall, etc.

### config.yml
- Define as seções do dashboard para cada tipo de usuário (admin e comum)
- Permite customização rápida da interface sem alterar código

### requirements.txt
- Lista todas as dependências do projeto
- **Inclui agora o pacote PyYAML** para leitura do config.yml:
  - `PyYAML==6.0.1`

### run.py
- Script principal para rodar a aplicação Flask
- Usa a factory do `app/__init__.py`

### init_admin.py
- Script para criar ou atualizar o usuário administrador a partir do .env
- Garante que sempre existe um admin válido

### test_logging.py
- Testa o sistema de logging, gera logs de todos os tipos

### monitor_logs.py
- Permite monitorar logs em tempo real ou gerar estatísticas dos logs

### README_LOGGING.md
- Documentação detalhada do sistema de logging, exemplos, dicas de manutenção

### INFOS.md
- (Este arquivo) Documentação técnica geral do sistema

---

## Fluxos Importantes

### Registro de Usuário
- Usuário preenche formulário de registro
- Usuário é criado com status "pendente" (`is_approved=False`)
- Email enviado ao usuário: "Recebemos seu pedido de registro"
- Email enviado ao admin: "Novo pedido de registro"
- Admin aprova/rejeita pelo dashboard
- Ao aprovar, email de confirmação é enviado ao usuário

### Login
- Validação de email/senha
- Se aprovado e confirmado, cria sessão (`UserSession`), registra IP (se firewall ativo)
- Sessão salva no banco e cookie enviado ao navegador
- Logs detalhados de cada etapa

### Sessão
- Cada login cria um registro em `user_sessions`
- Sessão pode ser encerrada manualmente ou por expiração
- Logout remove IP do firewall (se ativo) e encerra sessão

### Firewall
- Integração opcional com iptables
- Adiciona IP do usuário ao fazer login, remove ao fazer logout
- Pode ser desabilitado para testes/desenvolvimento

### Logging
- Logs rotacionados, detalhados por categoria
- Logs de ações de usuário, eventos de segurança, sistema e erros
- Scripts para monitorar e analisar logs

---

## Pontos Técnicos Importantes

- **Factory Pattern**: Facilita testes, múltiplas configurações e extensibilidade
- **Blueprints**: Organização modular das rotas
- **SQLAlchemy**: ORM robusto, fácil de migrar para outros bancos
- **Flask-Mail**: Envio de emails com templates HTML
- **Flask-Limiter**: Protege contra brute-force e abuso
- **APScheduler**: Tarefas agendadas para manutenção
- **Captcha**: Proteção contra bots, configurável via .env
- **Firewall**: Segurança extra, integração com iptables
- **Logging**: Diagnóstico e auditoria completos
- **.env**: Centraliza configurações sensíveis e variáveis de ambiente
- **instance/**: Armazena arquivos sensíveis fora do versionamento

---

## Como Rodar o Sistema

1. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Configure o arquivo `.env` com as variáveis necessárias (veja `env.example`)
3. Inicialize o banco e o admin:
   ```bash
   python3 init_admin.py
   ```
4. Rode a aplicação:
   ```bash
   python3 run.py
   ```
5. Acesse em `http://localhost:5001`

---

## Dicas de Manutenção
- Use os scripts de logging para monitorar o sistema
- Consulte os logs para depurar problemas de login, email, firewall
- Use o dashboard admin para aprovar/rejeitar usuários
- Faça backup regular do banco em `instance/`
- Mantenha o `.env` seguro e fora do versionamento

---

## Contato e Suporte
Para dúvidas técnicas, consulte este arquivo, o README principal e os comentários no código. Para suporte avançado, entre em contato com o desenvolvedor responsável. 