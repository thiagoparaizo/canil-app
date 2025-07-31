from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app import db
from datetime import date

class PlanoAssinatura(db.Model):
    __tablename__ = 'planos_assinatura'

    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False)
    descricao = Column(Text)
    valor = Column(Float, nullable=False)
    limite_funcionarios = Column(Integer)
    limite_animais = Column(Integer)
    backup_automatico = Column(Boolean)
    suporte_premium = Column(Boolean)
    recursos = Column(Text) # Could be a JSON field later
    ativo = Column(Boolean, default=True)

    # Relationships (One-to-Many with Assinatura)
    assinaturas = relationship('Assinatura', backref='plano_assinatura', lazy=True)


class Assinatura(db.Model):
    __tablename__ = 'assinaturas'

    id = Column(Integer, primary_key=True)
    plano_id = Column(Integer, ForeignKey('planos_assinatura.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    valor = Column(Float, nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_vencimento = Column(Date)
    status = Column(String(64), nullable=False) # e.g., 'Ativa', 'Inativa', 'Cancelada', 'Em teste'
    forma_pagamento = Column(String(64))
    renovacao_automatica = Column(Boolean, default=True)
    observacoes = Column(Text)

    # Relationships
    plano = relationship('PlanoAssinatura') # Many-to-One with PlanoAssinatura
    tenant = relationship('Tenant', backref='assinaturas_list') # Many-to-One with Tenant
    pagamentos = relationship('Pagamento', backref='assinatura_obj', lazy=True) # One-to-Many with Pagamento


    def renovar(self):
        # Logic for renewing the subscription.
        # This would involve updating data_inicio, data_vencimento, status,
        # and potentially interacting with a payment gateway to process renewal payment.
        pass

    def cancelar(self):
        # Logic for cancelling the subscription.
        # This would involve updating the status to 'Cancelada' and potentially
        # handling prorated refunds or service degradation based on the plan.
        pass

    def alterar_plano(self, novo_plano_id):
        # Logic for changing the subscription plan.
        # This involves updating the plano_id, valor, and potentially adjusting
        # limits or features. May also involve prorated charges/credits and payment gateway interaction.
        pass

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'

    id = Column(Integer, primary_key=True)
    assinatura_id = Column(Integer, ForeignKey('assinaturas.id'), nullable=False)
    valor = Column(Float, nullable=False)
    data_pagamento = Column(Date, nullable=False)
    data_vencimento = Column(Date) # Due date
    status = Column(String(64), nullable=False) # e.g., 'Pendente', 'Confirmado', 'Recusado', 'Estornado'
    metodo_pagamento = Column(String(64))
    transacao_id = Column(String(128))
    observacoes = Column(Text)

    # Relationship
    assinatura = relationship('Assinatura') # Many-to-One with Assinatura

    def confirmar_pagamento(self):
        # Logic for confirming a payment.
        # This would involve updating the status to 'Confirmado' and potentially
        # activating/extending the associated subscription.
        pass

    def estornar(self):
        # Logic for refunding a payment.
        # This would involve updating the status to 'Estornado' and interacting
        # with the payment gateway to process the refund.
        pass