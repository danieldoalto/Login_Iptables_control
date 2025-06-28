"""
Módulo para gerenciamento do firewall iptables
"""
import subprocess
import logging
import ipaddress
from typing import List, Tuple, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class FirewallManager:
    """Gerenciador do firewall iptables"""
    
    def __init__(self):
        self.chain_name = 'FIREWALL_LOGIN_ALLOW'
        self.iptables_path = '/sbin/iptables'
        self.ip6tables_path = '/sbin/ip6tables'
    
    def configure(self, app):
        """Configura o gerenciador com as configurações da aplicação"""
        self.chain_name = app.config.get('FIREWALL_CHAIN', 'FIREWALL_LOGIN_ALLOW')
        self.iptables_path = app.config.get('IPTABLES_PATH', '/sbin/iptables')
        self.ip6tables_path = app.config.get('IP6TABLES_PATH', '/sbin/ip6tables')
    
    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """Executa comando do sistema e retorna resultado"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"Comando executado com sucesso: {' '.join(command)}")
                return True, result.stdout.strip()
            else:
                logger.error(f"Erro ao executar comando: {' '.join(command)} - {result.stderr}")
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao executar comando: {' '.join(command)}")
            return False, "Timeout na execução do comando"
        except Exception as e:
            logger.error(f"Exceção ao executar comando: {' '.join(command)} - {str(e)}")
            return False, str(e)
    
    def _get_iptables_binary(self, ip_address: str) -> str:
        """Retorna o binário correto do iptables baseado no tipo de IP"""
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            if ip_obj.version == 6:
                return self.ip6tables_path
            else:
                return self.iptables_path
        except ValueError:
            logger.error(f"Endereço IP inválido: {ip_address}")
            return self.iptables_path
    
    def setup_firewall_base(self) -> bool:
        """Configura as regras base do firewall"""
        logger.info("Configurando regras base do firewall")
        
        # Comandos para configurar firewall base
        commands = [
            # Criar chain personalizada se não existir
            [self.iptables_path, '-t', 'filter', '-N', self.chain_name],
            [self.ip6tables_path, '-t', 'filter', '-N', self.chain_name],
            
            # Permitir tráfego de loopback
            [self.iptables_path, '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'],
            [self.ip6tables_path, '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'],
            
            # Permitir conexões estabelecidas e relacionadas
            [self.iptables_path, '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'],
            [self.ip6tables_path, '-A', 'INPUT', '-m', 'state', '--state', 'ESTABLISHED,RELATED', '-j', 'ACCEPT'],
            
            # Permitir HTTPS (443) para todos (necessário para login)
            [self.iptables_path, '-A', 'INPUT', '-p', 'tcp', '--dport', '443', '-j', 'ACCEPT'],
            [self.ip6tables_path, '-A', 'INPUT', '-p', 'tcp', '--dport', '443', '-j', 'ACCEPT'],
            
            # Permitir SSH apenas de IPs autorizados (opcional - configure conforme necessário)
            # [self.iptables_path, '-A', 'INPUT', '-p', 'tcp', '--dport', '22', '-s', 'SEU_IP_ADMIN', '-j', 'ACCEPT'],
            
            # Usar nossa chain personalizada
            [self.iptables_path, '-A', 'INPUT', '-j', self.chain_name],
            [self.ip6tables_path, '-A', 'INPUT', '-j', self.chain_name],
            
            # Bloquear todo o resto por padrão
            [self.iptables_path, '-A', 'INPUT', '-j', 'DROP'],
            [self.ip6tables_path, '-A', 'INPUT', '-j', 'DROP'],
        ]
        
        success = True
        for command in commands:
            result, output = self._run_command(command)
            # Ignorar erro se chain já existir
            if not result and "Chain already exists" not in output:
                logger.warning(f"Falha ao executar comando de configuração base: {' '.join(command)}")
                # Não marcar como falha total, algumas regras podem já existir
        
        logger.info("Configuração base do firewall concluída")
        return success
    
    def add_ip_to_firewall(self, ip_address: str) -> bool:
        """Adiciona IP às regras de permissão do firewall"""
        logger.info(f"Adicionando IP {ip_address} ao firewall")
        
        try:
            # Validar IP
            ip_obj = ipaddress.ip_address(ip_address)
            iptables_bin = self._get_iptables_binary(ip_address)
            
            # Comando para adicionar IP
            command = [
                iptables_bin, '-A', self.chain_name,
                '-s', ip_address,
                '-j', 'ACCEPT'
            ]
            
            success, output = self._run_command(command)
            
            if success:
                logger.info(f"IP {ip_address} adicionado com sucesso ao firewall")
                self._save_iptables_rules()
                return True
            else:
                logger.error(f"Falha ao adicionar IP {ip_address}: {output}")
                return False
                
        except ValueError as e:
            logger.error(f"IP inválido {ip_address}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao adicionar IP {ip_address}: {str(e)}")
            return False
    
    def remove_ip_from_firewall(self, ip_address: str) -> bool:
        """Remove IP das regras de permissão do firewall"""
        logger.info(f"Removendo IP {ip_address} do firewall")
        
        try:
            # Validar IP
            ip_obj = ipaddress.ip_address(ip_address)
            iptables_bin = self._get_iptables_binary(ip_address)
            
            # Comando para remover IP
            command = [
                iptables_bin, '-D', self.chain_name,
                '-s', ip_address,
                '-j', 'ACCEPT'
            ]
            
            success, output = self._run_command(command)
            
            if success:
                logger.info(f"IP {ip_address} removido com sucesso do firewall")
                self._save_iptables_rules()
                return True
            else:
                # Verificar se regra não existe (não é erro crítico)
                if "No chain/target/match" in output or "does not exist" in output:
                    logger.warning(f"Regra para IP {ip_address} não encontrada no firewall")
                    return True
                else:
                    logger.error(f"Falha ao remover IP {ip_address}: {output}")
                    return False
                    
        except ValueError as e:
            logger.error(f"IP inválido {ip_address}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao remover IP {ip_address}: {str(e)}")
            return False
    
    def list_allowed_ips(self) -> List[str]:
        """Lista todos os IPs permitidos no firewall"""
        try:
            allowed_ips = []
            
            # Listar regras IPv4
            command_v4 = [self.iptables_path, '-L', self.chain_name, '-n']
            success, output = self._run_command(command_v4)
            
            if success:
                allowed_ips.extend(self._parse_iptables_output(output))
            
            # Listar regras IPv6
            command_v6 = [self.ip6tables_path, '-L', self.chain_name, '-n']
            success, output = self._run_command(command_v6)
            
            if success:
                allowed_ips.extend(self._parse_iptables_output(output))
            
            return allowed_ips
            
        except Exception as e:
            logger.error(f"Erro ao listar IPs permitidos: {str(e)}")
            return []
    
    def _parse_iptables_output(self, output: str) -> List[str]:
        """Extrai IPs das regras do iptables"""
        ips = []
        lines = output.split('\n')
        
        for line in lines:
            if 'ACCEPT' in line and line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    source = parts[3]  # Campo source
                    if source != '0.0.0.0/0' and source != '::/0' and source != 'anywhere':
                        ips.append(source)
        
        return ips
    
    def _save_iptables_rules(self) -> bool:
        """Salva as regras do iptables para persistir após reboot"""
        try:
            # Para Ubuntu/Debian, usar iptables-save
            commands = [
                'iptables-save > /etc/iptables/rules.v4',
                'ip6tables-save > /etc/iptables/rules.v6'
            ]
            
            for command in commands:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    logger.warning(f"Falha ao salvar regras: {command} - {result.stderr}")
            
            logger.info("Regras do firewall salvas")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar regras do firewall: {str(e)}")
            return False
    
    def sync_database_with_firewall(self):
        """Sincroniza regras do banco de dados com o firewall"""
        from app.models import FirewallRule, db
        
        logger.info("Sincronizando regras do banco com firewall")
        
        try:
            # Buscar regras ativas no banco
            active_rules = FirewallRule.query.filter_by(is_active=True).all()
            firewall_ips = set(self.list_allowed_ips())
            database_ips = set(rule.ip_address for rule in active_rules)
            
            # IPs no firewall mas não no banco - remover
            orphaned_ips = firewall_ips - database_ips
            for ip in orphaned_ips:
                logger.info(f"Removendo IP órfão do firewall: {ip}")
                self.remove_ip_from_firewall(ip)
            
            # IPs no banco mas não no firewall - adicionar
            missing_ips = database_ips - firewall_ips
            for ip in missing_ips:
                logger.info(f"Adicionando IP ausente no firewall: {ip}")
                if self.add_ip_to_firewall(ip):
                    # Marcar como adicionado no banco
                    rule = FirewallRule.query.filter_by(ip_address=ip, is_active=True).first()
                    if rule:
                        rule.iptables_rule_added = True
            
            db.session.commit()
            logger.info("Sincronização concluída")
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {str(e)}")
            db.session.rollback()
    
    def cleanup_all_rules(self) -> bool:
        """Remove todas as regras da chain personalizada (usar com cuidado)"""
        logger.warning("Limpando todas as regras da chain personalizada")
        
        commands = [
            [self.iptables_path, '-F', self.chain_name],
            [self.ip6tables_path, '-F', self.chain_name]
        ]
        
        success = True
        for command in commands:
            result, output = self._run_command(command)
            if not result:
                success = False
                logger.error(f"Falha ao limpar chain: {' '.join(command)}")
        
        if success:
            self._save_iptables_rules()
            logger.info("Todas as regras da chain foram removidas")
        
        return success
