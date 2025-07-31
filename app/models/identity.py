from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship

from app import db

class Raca(db.Model):
    __tablename__ = 'racas'

    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False, unique=True)
    especie_id = Column(Integer, ForeignKey('especies.id'), nullable=False)
    padrao = Column(Text)
    caracteristicas = Column(Text)
    peso_medio = Column(Float)
    altura_media = Column(Float)
    temperamento = Column(Text)
    origem_geografica = Column(String(128))

    especie = relationship('Especie', backref='racas')
    animais = relationship('Animal', backref='raca', lazy=True)

    def __repr__(self):
        return f"<Raca {self.nome}>"

class Especie(db.Model):
    __tablename__ = 'especies'

    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False, unique=True)
    nome_cientifico = Column(String(128))
    familia = Column(String(128))

    racas = relationship('Raca', backref='especie_obj', lazy=True)

    def __repr__(self):
        return f"<Especie {self.nome}>"

class Linhagem(db.Model):
    __tablename__ = 'linhagens'

    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False, unique=True)
    raca_id = Column(Integer, ForeignKey('racas.id'), nullable=True)
    origem = Column(String(128))
    caracteristicas = Column(Text)
    tipo = Column(String(64)) # e.g., "Trabalho", "Exposição"
    # genealogy could be represented via relationships on the Animal model

    raca = relationship('Raca', backref='linhagens')
    animais = relationship('Animal', backref='linhagem', lazy=True)

    def __repr__(self):
        return f"<Linhagem {self.nome}>"