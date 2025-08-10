from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app import db
from datetime import date, datetime

# Assume RegistroVeterinario and Tratamento models exist and are imported
# from app.models.health import RegistroVeterinario, Tratamento

class Pessoa(db.Model):
    __tablename__ = 'pessoas'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False)
    cpf = Column(String(11), unique=True, nullable=True)
    telefone = Column(String(20))
    email = Column(String(120), unique=True)
    data_nascimento = Column(Date, nullable=True)
    ativo = Column(Boolean, default=True)
    tipo_pessoa = Column(String(50))
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Endereco relationship
    endereco_id = Column(Integer, ForeignKey('enderecos.id'), nullable=True)
    endereco = relationship('Endereco', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'pessoa',
        'polymorphic_on': tipo_pessoa
    }

    def calcular_idade(self):
        if self.data_nascimento:
            from datetime import date
            today = date.today()
            return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))
        return None

class Cliente(Pessoa):
    __tablename__ = 'clientes'
    __mapper_args__ = {
        'polymorphic_identity': 'cliente',
    }

    id = Column(Integer, ForeignKey('pessoas.id'), primary_key=True)
    profissao = Column(String(128))  # Relationships to Transactions (One-to-Many)\n    vendas = relationship('Venda', backref='cliente_obj', lazy=True)\n    adocoes = relationship('Adocao', backref='cliente_obj', lazy=True)\n    reservas = relationship('Reserva', backref='cliente_obj', lazy=True)

    def validar_documentos(self):
        # TODO: Implement proper document validation logic (e.g., CPF format, existence checks)
        """
        Performs document validation for the client.
        Returns True if documents are valid, False otherwise.
        """
        # Basic placeholder implementation
        return True

class Funcionario(Pessoa):
    __tablename__ = 'funcionarios'
    __mapper_args__ = {
        'polymorphic_identity': 'funcionario',
    }

    id = Column(Integer, ForeignKey('pessoas.id'), primary_key=True)
    cargo = Column(String(128))
    salario = Column(Float)
    data_admissao = Column(Date, nullable=False)
    especialidade = Column(String(128), nullable=True)


class Veterinario(Funcionario):
    __tablename__ = 'veterinarios'
    __mapper_args__ = {
        'polymorphic_identity': 'veterinario'
    }

    id = Column(Integer, ForeignKey('funcionarios.id'), primary_key=True)
    crmv = Column(String(64), unique=True, nullable=False)
    # especialidade is inherited from Funcionario

    def realizar_consulta(self, animal_id, diagnostico=None, observacoes=None):
        # TODO: Import RegistroVeterinario model and capture full consultation details.
        """
        Records a veterinary consultation for a given animal.

        Args:
            animal_id (int): The ID of the animal being consulted.
            diagnostico (str, optional): The diagnosis from the consultation. Defaults to None.
            observacoes (str, optional): Any additional observations. Defaults to None.

        Returns:
            RegistroVeterinario: The created consultation record.
        """
        # Assuming RegistroVeterinario model exists
        # from app.models.health import RegistroVeterinario # Import needed
        #
        # new_consulta = RegistroVeterinario(
        #     veterinario_id=self.id,
        #     animal_id=animal_id,
        #     data_consulta=datetime.utcnow(), # Or appropriate timezone aware datetime
        #     diagnostico=diagnostico,
        #     observacoes=observacoes,
        #     tenant_id=self.tenant_id # Assuming tenant_id is available on Pessoa/Funcionario
        # )
        # db.session.add(new_consulta)
        # return new_consulta
        print(f"Placeholder: Realizar consulta para animal {animal_id} pelo veterinário {self.nome}. Diagnóstico: {diagnostico}")
        return None # Placeholder return


    def prescrever_tratamento(self, registro_consulta_id, descricao, data_inicio, data_fim=None):
        # TODO: Import Tratamento model and link correctly to a consultation.
        """
        Prescribes a treatment linked to a veterinary consultation.

        Args:
            registro_consulta_id (int): The ID of the consultation record.
            descricao (str): Description of the treatment.
            data_inicio (date): Start date of the treatment.
            data_fim (date, optional): End date of the treatment. Defaults to None.

        Returns:
            Tratamento: The created treatment record.
        """
        # Assuming Tratamento model exists
        # from app.models.health import Tratamento # Import needed
        # from app.models.health import RegistroVeterinario # Import needed to get tenant_id from consultation
        #
        # consulta = RegistroVeterinario.query.get(registro_consulta_id)
        # if not consulta:
        #     raise ValueError("Consulta not found")
        #
        # new_tratamento = Tratamento(
        #     registro_consulta_id=registro_consulta_id,
        #     descricao=descricao,
        #     data_inicio=data_inicio,
        #     data_fim=data_fim,
        #     tenant_id=consulta.tenant_id # Get tenant_id from the associated consultation
        # )
        # db.session.add(new_tratamento)
        # return new_tratamento
        print(f"Placeholder: Prescrever tratamento para consulta {registro_consulta_id}: {descricao}")
        return None # Placeholder return


    def emitir_atestado(self, animal_id, motivo, data_emissao=None):
        # TODO: Implement real document generation (e.g., PDF).
        """
        Generates a veterinary certificate (atestado) for an animal.

        Args:
            animal_id (int): The ID of the animal.
            motivo (str): The reason for the certificate.
            data_emissao (date, optional): The date of issuance. Defaults to today.

        Returns:
            dict or str: A representation of the certificate.
        """
        atestado_data = {
            "veterinario": self.nome,
            "crmv": self.crmv,
            "animal_id": animal_id,
            "motivo": motivo,
            "data_emissao": data_emissao if data_emissao else date.today(),
            "tenant_id": self.tenant_id # Assuming tenant_id is available
        }
        print(f"Placeholder: Emitir atestado para animal {animal_id}. Motivo: {motivo}")
        return atestado_data # Placeholder return

# Note: The Endereco model is assumed to be defined elsewhere (e.g., app/models/system.py)