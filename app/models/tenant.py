from sqlalchemy import Column, Integer, String, Date, Boolean, text
from sqlalchemy.orm import relationship
from datetime import date

from app import db


class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)  # Changed from 'name' to 'nome'
    dominio = Column(String(100), unique=True, nullable=False)  # Changed from 'domain' to 'dominio'
    cnpj = Column(String(18), unique=True, nullable=False)
    data_criacao = Column(Date, default=date.today, nullable=False)
    plano = Column(String(50), nullable=False)
    status = Column(String(20), default='ativo', nullable=False)
    limite_funcionarios = Column(Integer, default=0)
    limite_animais = Column(Integer, default=0)
    ativo = Column(Boolean, default=True)
    schema_name = Column(String(100), unique=True, nullable=False)

    # Relationships - these will be added by other models using backref
    # usuarios = relationship back-referenced from Usuario
    # configuracoes = relationship back-referenced from Configuracao
    # logs_sistema = relationship back-referenced from LogSistema
    # backups = relationship back-referenced from Backup
    # enderecos = relationship back-referenced from Endereco
    # canis = relationship back-referenced from Canil
    # assinaturas_list = relationship back-referenced from Assinatura
    # arquivos_list = relationship back-referenced from Arquivo
    # albuns_list = relationship back-referenced from AlbumAnimal
    # registros_evolucao_list = relationship back-referenced from RegistroEvolucao

    def __repr__(self):
        return f"<Tenant {self.nome}>"

    def criar_schema(self):
        """Creates the database schema for the tenant."""
        # This needs to be implemented using raw SQL or a schema management tool
        # based on your specific database setup and privileges.
        try:
            # Use SQLAlchemy's text() for raw SQL execution
            db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}"))
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating schema {self.schema_name}: {e}")
            return False

    def suspender(self):
        """Suspend the tenant."""
        self.status = 'suspenso'
        self.ativo = False
        db.session.commit()

    def reativar(self):
        """Reactivate the tenant."""
        self.status = 'ativo'
        self.ativo = True
        db.session.commit()

    def verificar_limite_funcionarios(self, quantidade_atual: int) -> bool:
        """Check if the tenant is within the employee limit."""
        if self.limite_funcionarios <= 0:  # No limit
            return True
        return quantidade_atual < self.limite_funcionarios

    def verificar_limite_animais(self, quantidade_atual: int) -> bool:
        """Check if the tenant is within the animal limit."""
        if self.limite_animais <= 0:  # No limit
            return True
        return quantidade_atual < self.limite_animais

    @classmethod
    def buscar_por_dominio(cls, dominio: str):
        """Find tenant by domain."""
        return cls.query.filter_by(dominio=dominio, ativo=True).first()

    @classmethod
    def buscar_ativos(cls):
        """Get all active tenants."""
        return cls.query.filter_by(ativo=True).all()

    def to_dict(self):
        """Convert tenant to dictionary for API responses."""
        return {
            'id': self.id,
            'nome': self.nome,
            'dominio': self.dominio,
            'cnpj': self.cnpj,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'plano': self.plano,
            'status': self.status,
            'limite_funcionarios': self.limite_funcionarios,
            'limite_animais': self.limite_animais,
            'ativo': self.ativo,
            'schema_name': self.schema_name
        }