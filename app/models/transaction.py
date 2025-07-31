from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app import db

class Venda(db.Model):
    __tablename__ = 'vendas'

    id = Column(Integer, primary_key=True)
    data_venda = Column(Date, nullable=False)
    valor = Column(Float, nullable=False)
    forma_pagamento = Column(String(64))
    contrato_venda = Column(Text)
    garantias = Column(Text)
    entregue = Column(Boolean, default=False)
    observacoes = Column(Text)

    # Relationships
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    cliente = relationship('Cliente', backref='vendas_list')
    filhote_id = Column(Integer, ForeignKey('filhotes.id'), nullable=False) # Assuming a sale is for a Filhote
    filhote = relationship('Filhote', backref='venda', uselist=False)

    def emitir_contrato(self):
        # Placeholder for generating a sales contract document
        pass

    def registrar_entrega(self):
        # Placeholder for marking the animal as delivered and updating status
        self.entregue = True


class Adocao(db.Model):
    __tablename__ = 'adocoes'

    id = Column(Integer, primary_key=True)
    data_adocao = Column(Date, nullable=False)
    motivo = Column(Text, nullable=False)
    termo_adocao = Column(Text)
    acompanhamento = Column(Boolean, default=False)
    observacoes = Column(Text)

    # Relationships
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False) # Adopter is a Cliente
    cliente = relationship('Cliente', backref='adocoes_list')
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False) # Adopting an Animal
    animal = relationship('Animal', backref='adocao', uselist=False)

    def emitir_termo(self):
        # Placeholder for generating the adoption term document
        pass

    def agendar_visita(self):
        # Placeholder for scheduling a follow-up visit
        pass


class Reserva(db.Model):
    __tablename__ = 'reservas'

    id = Column(Integer, primary_key=True)
    data_reserva = Column(Date, nullable=False)
    valor_sinal = Column(Float, nullable=False)
    data_vencimento = Column(Date)
    status = Column(String(64), nullable=False) # e.g., 'Pending', 'Confirmed', 'Cancelled'
    observacoes = Column(Text)

    # Relationships
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    cliente = relationship('Cliente', backref='reservas_list')
    filhote_id = Column(Integer, ForeignKey('filhotes.id'), nullable=False) # Reserving a Filhote
    filhote = relationship('Filhote', backref='reserva', uselist=False)

    def confirmar(self):
        # Placeholder for updating status to Confirmed and potentially affecting Filhote availability
        self.status = 'Confirmed'
        # Logic to update Filhote status to 'Reservado' might go here or in a service
        pass

    def cancelar(self):
        # Placeholder for updating status to Cancelled and freeing up Filhote
        self.status = 'Cancelled'
        # Logic to update Filhote status (e.g., back to 'Disponível') might go here or in a service
        pass