from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB # Assuming PostgreSQL for JSONB type

from app import db
from datetime import datetime, date

# Base class for files
class Arquivo(db.Model):
    __tablename__ = 'arquivos'

    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=False)
    nome_original = Column(String(255), nullable=False)
    caminho = Column(String(512), nullable=False) # Path to the file in Dropbox or storage
    tipo = Column(String(50), nullable=False) # Discriminator for polymorphic inheritance (e.g., 'imagem', 'video', 'documento')
    tamanho = Column(Float) # File size in bytes or KB/MB
    data_upload = Column(DateTime, default=datetime.utcnow)
    descricao = Column(Text)
    publico = Column(Boolean, default=False)
    hash = Column(String(64)) # File hash for integrity checks

    # Relationships
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=True) # Files can be associated with an animal
    animal = relationship('Animal', backref='arquivos_list')
    album_id = Column(Integer, ForeignKey('albuns_animais.id'), nullable=True) # Files can be part of an album
    album = relationship('AlbumAnimal', backref='arquivos_list')

    # Tenant ID for multi-tenancy
    tenant_id = Column(Integer, ForeignKey('public.tenants.id'), nullable=False)
    #tenant = relationship("Tenant", backref='arquivos_list')


    __mapper_args__ = {
        'polymorphic_identity': 'arquivo',
        'polymorphic_on': tipo
    }

    def upload(self):
        # Placeholder for file upload logic (e.g., to Dropbox) - Logic is in MediaService
        pass

    def excluir(self):
        # Placeholder for file deletion logic - Logic is in MediaService
        pass

    def obter_url(self):
        # Placeholder for generating a public or temporary URL - Logic is in MediaService
        pass


class ImagemAnimal(Arquivo):
    __tablename__ = 'imagens_animais'

    id = Column(Integer, ForeignKey('arquivos.id'), primary_key=True)
    categoria = Column(String(64))
    ordem = Column(Integer)
    principal = Column(Boolean, default=False)
    observacoes = Column(Text)
    data_foto = Column(Date)

    __mapper_args__ = {
        'polymorphic_identity': 'imagem',
    }

    def definir_como_principal(self):
        # Logic to set this image as the principal one for its associated animal or album.
        # This might involve updating the 'principal' flag on other images for the same animal/album
        # and saving the changes to the database session.
        pass

    def ordenar(self, ordem):
        # Logic to set the display order of the image within its album or for the animal.
        # This might involve updating the 'ordem' field and saving to the database session.
        self.ordem = ordem
        pass # Keep the field update, add session commit logic


class VideoAnimal(Arquivo):
    __tablename__ = 'videos_animais'

    id = Column(Integer, ForeignKey('arquivos.id'), primary_key=True)
    categoria = Column(String(64))
    duracao = Column(Integer) # Duration in seconds
    qualidade = Column(String(64)) # e.g., 'SD', 'HD', 'FullHD'
    observacoes = Column(Text)
    data_video = Column(Date)

    __mapper_args__ = {
        'polymorphic_identity': 'video',
    }

    def processar(self):
        # Logic for video processing (e.g., transcoding to different formats, extracting metadata).
        # This would likely involve using a background worker (Celery) and potentially external libraries.
        pass

    def gerar_thumbnail(self):
        # Logic for generating a thumbnail image from a video file.
        # This would also likely involve a background worker and video processing libraries.
        pass


class DocumentoAnimal(Arquivo):
    __tablename__ = 'documentos_animais'

    id = Column(Integer, ForeignKey('arquivos.id'), primary_key=True)
    tipo_documento = Column(String(64))
    data_emissao = Column(Date)
    data_validade = Column(Date)
    orgao_emissor = Column(String(128))
    verificado = Column(Boolean, default=False)

    __mapper_args__ = {
        'polymorphic_identity': 'documento',
    }

    def verificar(self):
        # Logic for verifying the authenticity or validity of the document.
        # This might be a manual process reflected in the 'verificado' field or interaction with an external service.
        pass

    def renovar(self):
        # Logic for marking the document as renewed or updating its validity date.
        pass


class AlbumAnimal(db.Model):
    __tablename__ = 'albuns_animais'

    id = Column(Integer, primary_key=True)
    nome = Column(String(128), nullable=False)
    descricao = Column(Text)
    data_criacao = Column(Date, default=date.today)
    publico = Column(Boolean, default=False)
    visualizacoes = Column(Integer, default=0)

    # Relationships
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False) # An album belongs to an animal
    animal = relationship('Animal', backref='albuns_list')
    # arquivos = relationship('Arquivo', backref='album_obj') # Relationship is defined on the Arquivo side

    # Tenant ID for multi-tenancy
    tenant_id = Column(Integer, ForeignKey('public.tenants.id'), nullable=False)
    #tenant = relationship("Tenant", backref='albuns_list')


    def criar(self):
        # Logic for creating an album. This might just involve saving the instance to the database.
        # Additional logic could be creating a corresponding folder structure in Dropbox via MediaService.
        pass

    def compartilhar(self):
        # Logic for generating shareable links for the album or its contents.
        # This might involve iterating through associated Arquivo objects and getting their shareable links via MediaService.
        pass

    def definir_privacidade(self, publico: bool):
        self.publico = publico
        # Logic to update the public status in the database session.
        pass # Keep the field update, add session commit logic


class RegistroEvolucao(db.Model):
    __tablename__ = 'registros_evolucao'

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animais.id'), nullable=False) # A record belongs to an animal
    animal = relationship('Animal', backref='registros_evolucao_list')
    data_registro = Column(Date, default=date.today, nullable=False)
    peso = Column(Float)
    altura = Column(Float)
    observacoes = Column(Text)
    milestone = Column(String(128))
    fase = Column(String(64))

    # Tenant ID for multi-tenancy
    tenant_id = Column(Integer, ForeignKey('public.tenants.id'), nullable=False)
    tenant = relationship("Tenant", backref='registros_evolucao_list')

    def registrar_marco(self, milestone: str):
        self.milestone = milestone
        # Logic to update the milestone in the database session.
        pass # Keep the field update, add session commit logic

    def comparar_evolucao(self):
        # Logic for comparing this record with previous RegistroEvolucao records for the same animal.
        # This would involve querying the database for past records filtered by animal_id and ordered by date,
        # and then performing comparisons on weight, height, etc.
        pass
