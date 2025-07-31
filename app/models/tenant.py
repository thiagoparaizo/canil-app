from . import db
from datetime import date

class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), unique=True, nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    data_criacao = db.Column(db.Date, default=date.today, nullable=False)
    plano = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='ativo', nullable=False)
    limite_funcionarios = db.Column(db.Integer, default=0)
    limite_animais = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    schema_name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tenant {self.name}>"

    def create_schema(self):
        """Creates the database schema for the tenant."""
        # This needs to be implemented using raw SQL or a schema management tool
        # based on your specific database setup and privileges.
        # Example (for PostgreSQL):
        # db.engine.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}")
        pass # Placeholder

    def suspend(self):
        self.status = 'suspenso'
        self.ativo = False

    def reativar(self):
        self.status = 'ativo'
        self.ativo = True