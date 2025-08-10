from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB # Assuming PostgreSQL for JSONB type
from datetime import datetime

from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    login = Column(String(128), unique=True, nullable=False)
    senha = Column(String(255), nullable=False) # Store hashed passwords
    perfil = Column(String(64), nullable=False) # e.g., 'admin', 'gerente', 'funcionario'
    ultimo_acesso = Column(DateTime)
    ativo = Column(Boolean, default=True)
    permissoes = Column(JSONB) # Using JSONB for flexible permissions structure

    # Relationships
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)  # Fixed: removed 'public.'
    #tenant = relationship("Tenant", backref='usuarios_list')
    logs_sistema = relationship('LogSistema', backref='usuario_obj', lazy=True) # One-to-Many with LogSistema


    def autenticar(self, senha):
        # Password hashing and verification logic
        return check_password_hash(self.senha, senha)

    def alterar_senha(self, nova_senha):
        # Password change logic
        self.senha = generate_password_hash(nova_senha)

    def definir_permissoes(self, permissoes: dict):
        """Sets the user's permissions."""
        self.permissoes = permissoes

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'

    id = Column(Integer, primary_key=True)
    chave = Column(String(128), unique=True, nullable=False)
    valor = Column(Text)
    descricao = Column(Text)
    tipo = Column(String(64))
    categoria = Column(String(64))

    # Relationships
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)  # Fixed: removed 'public.'
    #tenant = relationship("Tenant", backref='configuracoes_list')

    def atualizar(self, valor):  # Fixed: renamed from 'actualizar' to 'atualizar'
        """Updates the configuration value."""
        self.valor = valor

class LogSistema(db.Model):
    __tablename__ = 'logs_sistema'

    id = Column(Integer, primary_key=True)
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True) # Log might not always have a user (e.g., system events)
    usuario = relationship("Usuario")
    acao = Column(String(255), nullable=False)
    tabela = Column(String(128))
    dados_anteriores = Column(JSONB)
    dados_novos = Column(JSONB)
    ip = Column(String(45)) # IPv4 or IPv6 address

    # Relationships
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)  # Fixed: removed 'public.'
    #tenant = relationship("Tenant", backref='logs_sistema_list')

    def registrar_log(self, usuario_id: int = None, acao: str = None, tabela: str = None, dados_anteriores: dict = None, dados_novos: dict = None, ip: str = None):  # Fixed: added default values
        """Registers a system log entry."""
        # TODO: tenant_id needs to be obtained from the current request context or user
        new_log = LogSistema(
            data_hora=datetime.utcnow(),
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip=ip,
            tenant_id=self.tenant_id # Assuming tenant_id is available on the instance or can be passed
        )
        db.session.add(new_log)
        # db.session.commit() # Commit should likely happen outside this method

class Backup(db.Model):
    __tablename__ = 'backups'

    id = Column(Integer, primary_key=True)
    data_backup = Column(Date, nullable=False)
    tipo = Column(String(64))
    tamanho = Column(Float) # Size in MB or GB
    caminho = Column(String(512)) # Path to backup file in storage
    status = Column(String(64)) # e.g., 'Concluído', 'Falhou', 'Em andamento'
    observacoes = Column(Text)

    # Relationships
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)  # Fixed: removed 'public.'
    #tenant = relationship("Tenant", backref='backups_list')

    def executar(self):
        """Initiates a backup process."""
        self.status = 'Em andamento'
        # TODO: Trigger a Celery task for the actual backup process

    def restaurar(self):
        """Initiates a backup restoration process."""
        self.status = 'Restaurando'
        # TODO: Trigger a Celery task for the actual restoration process

    def verificar(self):
        """Verifies the integrity of the backup."""
        # TODO: Implement actual verification logic
        return 'Pendente' # Placeholder

class Endereco(db.Model):
    __tablename__ = 'enderecos'

    id = Column(Integer, primary_key=True)
    logradouro = Column(String(255), nullable=False)
    numero = Column(String(20))
    complemento = Column(String(128))
    bairro = Column(String(128))
    cidade = Column(String(128), nullable=False)
    estado = Column(String(128), nullable=False)
    cep = Column(String(10))
    pais = Column(String(64), default='Brasil')

    # Relationships (One-to-One - reciprocated in related models)
    cliente = relationship('Cliente', backref='endereco_obj', uselist=False)
    funcionario = relationship('Funcionario', backref='endereco_obj', uselist=False)
    canil = relationship('Canil', backref='endereco_obj', uselist=False)

    # Relationships
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)  # Fixed: removed 'public.'
    #tenant = relationship("Tenant", backref='enderecos_list')


class Canil(db.Model):
    __tablename__ = 'canis'

    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=True)
    registro_kennel = Column(String(128))
    site = Column(String(128))  # Fixed: removed backslash
    email = Column(String(128))
    telefone = Column(String(20))
    ativo = Column(Boolean, default=True)

    # Relationships
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)  # Fixed: removed 'public.'
    tenant = relationship("Tenant", backref='canis_list')
    # Relationship to Endereco (1:1)
    endereco_id = Column(Integer, ForeignKey('enderecos.id'), unique=True, nullable=True)
    # endereco relationship defined in Endereco model


    def gerar_relatorio_financeiro(self):
        """Generates a financial report for the tenant."""
        # TODO: Implement actual logic to aggregate financial data (sales, expenses, etc.) for this tenant.
        return {"report_type": "financial", "data": "placeholder"}

    def gerar_relatorio_reprodutivo(self):
        """Generates a reproductive report for the tenant."""
        # TODO: Implement actual logic to aggregate reproductive data (breedings, litters, etc.) for this tenant.
        return {"report_type": "reproductive", "data": "placeholder"}

    def gerar_relatorio_saude(self):
        """Generates a health report for the tenant."""
        # TODO: Implement actual logic to aggregate health data (vaccinations, consultations, etc.) for this tenant's animals.
        return {"report_type": "health", "data": "placeholder"}