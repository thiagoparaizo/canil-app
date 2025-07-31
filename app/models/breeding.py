from app import db
from datetime import date, timedelta
from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship


# Association table for Many-to-Many relationship between Cruzamento and Animals
cruzamento_animal_association = db.Table('cruzamento_animal', db.Model.metadata,
    Column('cruzamento_id', Integer, ForeignKey('cruzamentos.id')),
    Column('animal_id', Integer, ForeignKey('animais.id'))
)

class Ninhada(db.Model):
    __tablename__ = 'ninhadas'

    id = Column(Integer, primary_key=True)
    numero = Column(Integer)
    data_cruzamento = Column(Date)
    data_previsao_parto = Column(Date)
    data_parto = Column(Date)
    qtd_filhotes = Column(Integer)
    qtd_vivos = Column(Integer)
    qtd_mortos = Column(Integer)
    observacoes = Column(Text)

    # Relationships
    filhotes = relationship('Filhote', backref='ninhada_obj', lazy=True)
    cruzamento_id = Column(Integer, ForeignKey('cruzamentos.id'), nullable=False)
    cruzamento = relationship('Cruzamento', backref='ninhadas')
    matriz_id = Column(Integer, ForeignKey('matrizes.id'), nullable=False) # Added relationship to Matriz
    matriz = relationship('Matriz', backref='ninhadas_matriz')


    def calcular_taxa_fertilidade(self) -> float:
        """
        Calculates the fertility rate of the litter.
        Requires access to the 'filhotes' relationship to count total vs. alive.
        """
        if self.qtd_filhotes is not None and self.qtd_filhotes > 0:
            # Simple calculation based on recorded counts
            return (self.qtd_vivos / self.qtd_filhotes) * 100 if self.qtd_vivos is not None else 0.0
        # More advanced calculation might involve analyzing individual filhote status
        return 0.0 # Return 0 if no filhotes recorded or total is zero


    def registrar_parto(self, data_parto, qtd_vivos, qtd_mortos):
        """Registers the details of the litter's birth."""
        self.data_parto = data_parto
        self.qtd_vivos = qtd_vivos
        self.qtd_mortos = qtd_mortos
        self.qtd_filhotes = qtd_vivos + qtd_mortos


class Cruzamento(db.Model):
    __tablename__ = 'cruzamentos'

    id = Column(Integer, primary_key=True)
    data_acasalamento = Column(Date, nullable=False)
    tipo = Column(String(64))
    confirmado = Column(Boolean, default=False)
    coeficiente_consanguinidade = Column(Float)
    observacoes = Column(Text)
    data_confirmacao = Column(Date, nullable=True)

    # Relationships (Many-to-Many with Animal using association table)
    animais = relationship('Animal', secondary=cruzamento_animal_association, backref='cruzamentos')
    # Relationships to Matriz and Reprodutor should come from the animals relationship

    def confirmar_prenhez(self, data_confirmacao):
        """Confirms pregnancy and sets the confirmation date."""
        self.confirmado = True
        self.data_confirmacao = data_confirmacao

    def calcular_previsao_parto(self, gestacao_dias: int):
        """Calculates the estimated birth date based on mating date and gestation period."""
        if self.data_acasalamento:
            self.data_previsao_parto = self.data_acasalamento + timedelta(days=gestacao_dias)

    def validar_compatibilidade(self) -> bool:
        """
        Validates the reproductive compatibility of the parent animals in the crossing.
        Logic depends on analyzing animal lineage (ArvoreGenealogica) and genetic data (ExameGenetico)
        to identify potential risks or undesirable traits.
        """
        # Placeholder for compatibility logic
        # Requires accessing self.animais (the parent animals)
        # and potentially their related ArvoreGenealogica and ExameGenetico records.
        # Return True if compatible, False otherwise.
        return True # Defaulting to compatible for now


class ArvoreGenealogica(db.Model):
    __tablename__ = 'arvores_genealogicas'

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey('animais.id'), unique=True, nullable=False)
    animal = relationship('Animal', backref='arvore_genealogica_obj')
    geracao = Column(Integer)
    tipo = Column(String(64))
    genealogia_data = Column(Text) # Consider JSON or a more structured approach later

    def gerar_arvore(self):
        """
        Generates the genealogical tree structure for the associated animal.
        Involves recursively traversing the 'mother' and 'father' relationships
        up through generations and structuring the data.
        The output could be stored in 'genealogia_data' (e.g., as JSON).
        """
        # Placeholder for generating the tree structure
        pass

    def calcular_consanguinidade(self) -> float:
        """
        Calculates the inbreeding coefficient for the associated animal.
        Requires traversing the genealogical tree (similar to gerar_arvore)
        to identify common ancestors and apply the appropriate calculation algorithm.
        Could utilize the 'genealogia_data' or traverse relationships directly.
        """
        # Placeholder for calculating the inbreeding coefficient
        return 0.0 # Defaulting to 0 for now

    def validar_linhagem(self) -> bool:
        """
        Validates the animal's lineage against specific breed standards or desired traits.
        Could involve checking for presence/absence of certain ancestors,
        confirming breed purity, or assessing conformity to lineage characteristics.
        Depends on the genealogical data and potentially external standards.
        """
        # Placeholder for validating lineage against standards
        return True # Defaulting to valid for now

    def obter_ancestral_comum(self, other_animal_id: int):
        """
        Finds and returns common ancestors between the associated animal and another specified animal.
        Requires traversing the genealogical trees of both animals and identifying shared individuals.
        """
        # Placeholder for finding common ancestors
        pass