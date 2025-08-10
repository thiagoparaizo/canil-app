from app import db
from datetime import date, timedelta
from sqlalchemy import Column, Integer, String, Date, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

# Assume these models exist for relationship and functionality
# from app.models.breeding import Cruzamento
# from app.models.transaction import Venda
# from app.models.person import Cliente # Assuming Cliente is a type of Pessoa


class Animal(db.Model):
    __tablename__ = 'animais'  # Removido __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    microchip = db.Column(db.String(128), unique=True, nullable=True)
    pedigree = db.Column(db.String(128), unique=True, nullable=True)
    data_nascimento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)
    cor = db.Column(db.String(64), nullable=True)
    peso = db.Column(db.Float, nullable=True)
    altura = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(64), nullable=True)
    origem = db.Column(db.String(128), nullable=True)
    data_aquisicao = db.Column(db.Date, nullable=True)
    valor_aquisicao = db.Column(db.Float, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    tipo_animal = db.Column(db.String(50))  # Discriminator

    # Relacionamentos corrigidos
    mother_id = db.Column(db.Integer, db.ForeignKey('animais.id'), nullable=True)
    father_id = db.Column(db.Integer, db.ForeignKey('animais.id'), nullable=True)

    mother = db.relationship('Animal', remote_side=[id], backref='filhos_mae', foreign_keys=[mother_id])
    father = db.relationship('Animal', remote_side=[id], backref='filhos_pai', foreign_keys=[father_id])

    __mapper_args__ = {
        'polymorphic_identity': 'animal',
        'polymorphic_on': tipo_animal
    }

    def calcular_idade(self):
        from datetime import date
        today = date.today()
        return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))

    def calcular_coeficiente_consanguinidade(self):
        return 0.0

    def obter_arvore_genealogica(self):
        return {'animal': self.nome, 'id': self.id, 'mother': None, 'father': None}


class Matriz(Animal):
    __tablename__ = 'matrizes'

    id = db.Column(db.Integer, db.ForeignKey('animais.id'), primary_key=True)
    proximo_cio = db.Column(db.Date, nullable=True)
    status_reprodutivo = db.Column(db.String(64), nullable=True) # e.g., 'Em ciclo', 'Prenha', 'Lactante', 'Descanso'
    qtd_cruzamentos = db.Column(db.Integer, default=0)
    qtd_filhotes = db.Column(db.Integer, default=0)
    aposentada = db.Column(db.Boolean, default=False)
    data_aposentadoria = db.Column(db.Date, nullable=True)

    # Relationships
    # ninhadas = db.relationship('Ninhada', backref='matriz', lazy=True)


    def __repr__(self):
        return f"<Matriz {self.nome} ({self.id})>"

    def programar_cruzamento(self, reprodutor_id, data_prevista):
        # Requires importing the Cruzamento model: from app.models.breeding import Cruzamento
        # Create a new Cruzamento record
        # Assumes reprodutor_id is the ID of the Reprodutor animal
        try:
            # Assuming Cruzamento model has these fields
            # new_cruzamento = Cruzamento(
            #     matriz_id=self.id,
            #     reprodutor_id=reprodutor_id,
            #     data_prevista=data_prevista,
            #     tenant_id=self.tenant_id,
            #     status='Programado' # Example status
            # )
            # db.session.add(new_cruzamento)
            # db.session.commit()
            self.qtd_cruzamentos += 1 # Increment crossing count
            db.session.commit()
            print(f"Cruzamento programado para Matriz {self.nome} com Reprodutor ID {reprodutor_id} em {data_prevista}") # Placeholder success message
            # return new_cruzamento # Return the created object
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao programar cruzamento: {e}") # Placeholder error handling
            # raise e # Re-raise the exception

    def registrar_cio(self, data_inicio, data_fim):
        # Update status and calculate next heat based on a simplified rule (e.g., ~6 months after end date)
        self.status_reprodutivo = 'Em ciclo'
        # Simplified calculation for next heat: assume 6 months (approx 180 days)
        self.proximo_cio = data_fim + timedelta(days=180)
        # Update general animal status if needed
        self.status = 'Ativo Reprodutivo' # Example status
        db.session.commit()
        print(f"Cio registrado para Matriz {self.nome}. Próximo cio previsto em {self.proximo_cio}") # Placeholder success message


class Reprodutor(Animal):
    __tablename__ = 'reprodutores'

    id = db.Column(db.Integer, db.ForeignKey('animais.id'), primary_key=True)
    qtd_cruzamentos = db.Column(db.Integer, default=0)
    qtd_filhotes = db.Column(db.Integer, default=0)
    qualidade_esperma = db.Column(db.String(64), nullable=True)
    ultima_coleta = db.Column(db.Date, nullable=True)
    ativo_reprodutivo = db.Column(db.Boolean, default=True)
    taxa_fertilidade = db.Column(db.Float, nullable=True)

    # Relationships
    # cruzamentos = db.relationship('Cruzamento', backref='reprodutor', lazy=True)


    def __repr__(self):
        return f"<Reprodutor {self.nome} ({self.id})>"

    def programar_cruzamento(self, matriz_id, data_prevista):
        # Requires importing the Cruzamento model: from app.models.breeding import Cruzamento
        # Create a new Cruzamento record
        # Assumes matriz_id is the ID of the Matriz animal
        try:
            # Assuming Cruzamento model has these fields
            # new_cruzamento = Cruzamento(
            #     matriz_id=matriz_id,
            #     reprodutor_id=self.id,
            #     data_prevista=data_prevista,
            #     tenant_id=self.tenant_id,
            #     status='Programado' # Example status
            # )
            # db.session.add(new_cruzamento)
            # db.session.commit()
            self.qtd_cruzamentos += 1 # Increment crossing count
            db.session.commit()
            print(f"Cruzamento programado para Reprodutor {self.nome} com Matriz ID {matriz_id} em {data_prevista}") # Placeholder success message
            # return new_cruzamento # Return the created object
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao programar cruzamento: {e}") # Placeholder error handling
            # raise e # Re-raise the exception

    def avaliar_fertilidade(self, data_avaliacao, resultado):
        # Update fertility details
        self.qualidade_esperma = resultado # Assuming resultado is a string like 'Boa', 'Regular', etc.
        self.ultima_coleta = data_avaliacao
        # Updating taxa_fertilidade would require more complex logic
        db.session.commit()
        print(f"Avaliação de fertilidade registrada para Reprodutor {self.nome} em {data_avaliacao}") # Placeholder success message


class Filhote(Animal):
    __tablename__ = 'filhotes'

    id = db.Column(db.Integer, db.ForeignKey('animais.id'), primary_key=True)
    ordem_nascimento = db.Column(db.Integer, nullable=True)
    peso_nascimento = db.Column(db.Float, nullable=True)
    status_venda = db.Column(db.String(64), nullable=True) # e.g., 'Disponível', 'Reservado', 'Vendido', 'Em observação'
    preco_venda = db.Column(db.Float, nullable=True)
    data_venda = db.Column(db.Date, nullable=True)
    reservado = db.Column(db.Boolean, default=False)
    ninhada_id = db.Column(db.Integer, db.ForeignKey('ninhadas.id'), nullable=True)

    def reservar(self):
        # Update status to 'Reservado' and set reserved to True.
        if not self.reservado:
            self.reservado = True
            self.status_venda = 'Reservado'
            self.status = 'Reservado' # Update general animal status
            db.session.commit()
            print(f"Filhote {self.nome} reservado.") # Placeholder success message
        else:
            print(f"Filhote {self.nome} já está reservado.") # Placeholder message


    def vender(self, valor_venda, cliente_id):
        # Requires importing Venda and possibly Cliente models:
        # from app.models.transaction import Venda
        # from app.models.person import Cliente # Assuming Cliente is a type of Pessoa
        # Update status to 'Vendido', set sale details, and create a Venda record.
        try:
            # Assume Cliente model exists and can be retrieved by ID
            # cliente = Cliente.query.get(cliente_id)
            # if not cliente:
            #     raise ValueError(f"Cliente com ID {cliente_id} não encontrado.")

            self.status_venda = 'Vendido'
            self.data_venda = date.today()
            self.preco_venda = valor_venda
            self.reservado = False # No longer reserved once sold
            self.status = 'Vendido' # Update general animal status

            # Create a Venda record (requires importing Venda model)
            # new_venda = Venda(
            #     data_venda=self.data_venda,
            #     valor=self.preco_venda,
            #     cliente_id=cliente_id, # Or use the cliente object if relationship is set up
            #     filhote_id=self.id,
            #     tenant_id=self.tenant_id
            # )
            # db.session.add(new_venda)

            db.session.commit()
            print(f"Filhote {self.nome} vendido por {valor_venda} para Cliente ID {cliente_id}.") # Placeholder success message
            # return new_venda # Return the created object
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao vender filhote: {e}") # Placeholder error handling
            # raise e # Re-raise the exception


    def transferir_para_adulto(self):
        # Change the animal's status to 'Adulto'.
        # Note: In a system using SQLAlchemy's concrete or joined table inheritance,
        # transitioning between subclasses is complex and often involves creating a new
        # instance of the target class, copying data, and deleting the old instance.
        # A simpler approach here is just updating the general status.
        # If full polymorphic transition is needed, more advanced SQLAlchemy techniques
        # or a dedicated migration process would be required.
        if self.status != 'Vendido' and self.status != 'Aposentado': # Avoid changing status if already sold or retired
             self.status = 'Adulto'
             # Consider removing from Filhote-specific contexts or relationships if they exist.
             db.session.commit()
             print(f"Filhote {self.nome} transferido para status Adulto.") # Placeholder success message
        else:
            print(f"Não é possível transferir Filhote {self.nome} para Adulto. Status atual: {self.status}") # Placeholder message
