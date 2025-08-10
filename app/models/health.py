from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app import db

class RegistroVeterinario(db.Model):
    __tablename__ = 'registros_veterinarios'

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False)
    data_consulta = Column(Date, nullable=False)
    motivo = Column(String(255))
    diagnostico = Column(Text)
    tratamento = Column(Text)
    peso = Column(Float)
    observacoes = Column(Text)
    status_saude = Column(String(64))
    emergencia = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    #tenant = relationship("Tenant", backref='registros_veterinarios')

    animal = relationship('Animal', backref='registros_veterinarios_list')

    # No specific methods mentioned in prompt for RegistroVeterinario beyond data fields

class Vacinacao(db.Model):
    __tablename__ = 'vacinacoes'

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False)
    tipo_vacina = Column(String(128), nullable=False)
    data_aplicacao = Column(Date, nullable=False)
    proxima_dose = Column(Date)
    lote = Column(String(128))
    laboratorio = Column(String(128))
    reacao = Column(Boolean, default=False)
    observacoes = Column(Text)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    #tenant = relationship("Tenant", backref='registros_veterinarios')
    animal = relationship('Animal', backref='vacinacoes_list')

    # No specific methods mentioned in prompt for Vacinacao beyond data fields

class Vermifugacao(db.Model):
    __tablename__ = 'vermifugacoes'

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False)
    medicamento = Column(String(128), nullable=False)
    data_aplicacao = Column(Date, nullable=False)
    dosagem = Column(Float)
    proxima_aplicacao = Column(Date)
    observacoes = Column(Text)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    #tenant = relationship("Tenant", backref='registros_veterinarios')

    animal = relationship('Animal', backref='vermifugacoes_list')

    # No specific methods mentioned in prompt for Vermifugacao beyond data fields

class ExameGenetico(db.Model):
    __tablename__ = 'exames_geneticos'

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False)
    tipo_exame = Column(String(128), nullable=False)
    data_coleta = Column(Date)
    data_resultado = Column(Date)
    resultado = Column(Text)
    laboratorio = Column(String(128))
    observacoes = Column(Text)
    aprovado = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    #tenant = relationship("Tenant", backref='registros_veterinarios')

    animal = relationship('Animal', backref='exames_geneticos_list')

    # No specific methods mentioned in prompt for ExameGenetico beyond data fields