from flask_restx import Namespace, Resource, fields
from app import db
from app.models.identity import Raca, Especie, Linhagem # Assuming these models are defined in app.models.identity

identity_ns = Namespace('identity', description='Identity related operations (Races, Species, Lineages)')

# Define models for API representation
raca_model = identity_ns.model('Raca', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'padrao': fields.String,
    'caracteristicas': fields.String,
    'peso_medio': fields.Float,
    'altura_media': fields.Float,
    'temperamento': fields.String,
    'origem_geografica': fields.String,
})

especie_model = identity_ns.model('Especie', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'nome_cientifico': fields.String,
    'familia': fields.String,
})

linhagem_model = identity_ns.model('Linhagem', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'origem': fields.String,
    'caracteristicas': fields.String,
    'tipo': fields.String,
    'genealogia': fields.String,
})

# --- Raca Resources ---

@identity_ns.route('/racas')
class RacaList(Resource):
    @identity_ns.doc('list_racas')
    @identity_ns.marshal_list_with(raca_model)
    def get(self):
        """List all races"""
        racas = Raca.query.all() # Interaction with SQLAlchemy model
        return racas

    @identity_ns.doc('create_raca')
    @identity_ns.expect(raca_model)
    @identity_ns.marshal_with(raca_model, code=201)
    def post(self):
        """Create a new race"""
        data = identity_ns.payload
        new_raca = Raca(**data) # Create model instance
        db.session.add(new_raca) # Add to session
        db.session.commit() # Commit to save
        return new_raca, 201

@identity_ns.route('/racas/<int:id>')
@identity_ns.param('id', 'The race identifier')
class RacaResource(Resource):
    @identity_ns.doc('get_raca')
    @identity_ns.marshal_with(raca_model)
    def get(self, id):
        """Get a race by its ID"""
        raca = Raca.query.get_or_404(id) # Interaction with SQLAlchemy model
        return raca

    @identity_ns.doc('update_raca')
    @identity_ns.expect(raca_model)
    @identity_ns.marshal_with(raca_model)
    def put(self, id):
        """Update a race by its ID"""
        raca = Raca.query.get_or_404(id)
        data = identity_ns.payload
        for key, value in data.items():
            setattr(raca, key, value)
        db.session.commit()
        return raca

    @identity_ns.doc('delete_raca')
    @identity_ns.response(204, 'Race deleted')
    def delete(self, id):
        """Delete a race by its ID"""
        raca = Raca.query.get_or_404(id)
        db.session.delete(raca)
        db.session.commit()
        return '', 204

# --- Especie Resources ---

@identity_ns.route('/especies')
class EspecieList(Resource):
    @identity_ns.doc('list_especies')
    @identity_ns.marshal_list_with(especie_model)
    def get(self):
        """List all species"""
        especies = Especie.query.all()
        return especies

    @identity_ns.doc('create_especie')
    @identity_ns.expect(especie_model)
    @identity_ns.marshal_with(especie_model, code=201)
    def post(self):
        """Create a new species"""
        data = identity_ns.payload
        new_especie = Especie(**data)
        db.session.add(new_especie)
        db.session.commit()
        return new_especie, 201

@identity_ns.route('/especies/<int:id>')
@identity_ns.param('id', 'The species identifier')
class EspecieResource(Resource):
    @identity_ns.doc('get_especie')
    @identity_ns.marshal_with(especie_model)
    def get(self, id):
        """Get a species by its ID"""
        especie = Especie.query.get_or_404(id)
        return especie

    @identity_ns.doc('update_especie')
    @identity_ns.expect(especie_model)
    @identity_ns.marshal_with(especie_model)
    def put(self, id):
        """Update a species by its ID"""
        especie = Especie.query.get_or_404(id)
        data = identity_ns.payload
        for key, value in data.items():
            setattr(especie, key, value)
        db.session.commit()
        return especie

    @identity_ns.doc('delete_especie')
    @identity_ns.response(204, 'Species deleted')
    def delete(self, id):
        """Delete a species by its ID"""
        especie = Especie.query.get_or_404(id)
        db.session.delete(especie)
        db.session.commit()
        return '', 204

# --- Linhagem Resources ---

@identity_ns.route('/linhagens')
class LinhagemList(Resource):
    @identity_ns.doc('list_linhagens')
    @identity_ns.marshal_list_with(linhagem_model)
    def get(self):
        """List all lineages"""
        linhagens = Linhagem.query.all()
        return linhagens

    @identity_ns.doc('create_linhagem')
    @identity_ns.expect(linhagem_model)
    @identity_ns.marshal_with(linhagem_model, code=201)
    def post(self):
        """Create a new lineage"""
        data = identity_ns.payload
        new_linhagem = Linhagem(**data)
        db.session.add(new_linhagem)
        db.session.commit()
        return new_linhagem, 201

@identity_ns.route('/linhagens/<int:id>')
@identity_ns.param('id', 'The lineage identifier')
class LinhagemResource(Resource):
    @identity_ns.doc('get_linhagem')
    @identity_ns.marshal_with(linhagem_model)
    def get(self, id):
        """Get a lineage by its ID"""
        linhagem = Linhagem.query.get_or_404(id)
        return linhagem

    @identity_ns.doc('update_linhagem')
    @identity_ns.expect(linhagem_model)
    @identity_ns.marshal_with(linhagem_model)
    def put(self, id):
        """Update a lineage by its ID"""
        linhagem = Linhagem.query.get_or_404(id)
        data = identity_ns.payload
        for key, value in data.items():
            setattr(linhagem, key, value)
        db.session.commit()
        return linhagem

    @identity_ns.doc('delete_linhagem')
    @identity_ns.response(204, 'Lineage deleted')
    def delete(self, id):
        """Delete a lineage by its ID"""
        linhagem = Linhagem.query.get_or_404(id)
        db.session.delete(linhagem)
        db.session.commit()
        return '', 204
from flask_restx import Namespace, Resource, fields
from app import db
from app.models.identity import Raca, Especie, Linhagem # Assuming these models are defined in app.models.identity

identity_ns = Namespace('identity', description='Identity related operations (Races, Species, Lineages)')

# Define models for API representation
raca_model = identity_ns.model('Raca', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'padrao': fields.String,
    'caracteristicas': fields.String,
    'peso_medio': fields.Float,
    'altura_media': fields.Float,
    'temperamento': fields.String,
    'origem_geografica': fields.String,
})

especie_model = identity_ns.model('Especie', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'nome_cientifico': fields.String,
    'familia': fields.String,
})

linhagem_model = identity_ns.model('Linhagem', {
    'id': fields.Integer(readOnly=True),
    'nome': fields.String(required=True),
    'origem': fields.String,
    'caracteristicas': fields.String,
    'tipo': fields.String,
    'genealogia': fields.String,
})

# --- Raca Resources ---

@identity_ns.route('/racas')
class RacaList(Resource):
    @identity_ns.doc('list_racas')
    @identity_ns.marshal_list_with(raca_model)
    def get(self):
        """List all races"""
        racas = Raca.query.all() # Interaction with SQLAlchemy model
        return racas

    @identity_ns.doc('create_raca')
    @identity_ns.expect(raca_model)
    @identity_ns.marshal_with(raca_model, code=201)
    def post(self):
        """Create a new race"""
        data = identity_ns.payload
        new_raca = Raca(**data) # Create model instance
        db.session.add(new_raca) # Add to session
        db.session.commit() # Commit to save
        return new_raca, 201

@identity_ns.route('/racas/<int:id>')
@identity_ns.param('id', 'The race identifier')
class RacaResource(Resource):
    @identity_ns.doc('get_raca')
    @identity_ns.marshal_with(raca_model)
    def get(self, id):
        """Get a race by its ID"""
        raca = Raca.query.get_or_404(id) # Interaction with SQLAlchemy model
        return raca

    @identity_ns.doc('update_raca')
    @identity_ns.expect(raca_model)
    @identity_ns.marshal_with(raca_model)
    def put(self, id):
        """Update a race by its ID"""
        raca = Raca.query.get_or_404(id)
        data = identity_ns.payload
        for key, value in data.items():
            setattr(raca, key, value)
        db.session.commit()
        return raca

    @identity_ns.doc('delete_raca')
    @identity_ns.response(204, 'Race deleted')
    def delete(self, id):
        """Delete a race by its ID"""
        raca = Raca.query.get_or_404(id)
        db.session.delete(raca)
        db.session.commit()
        return '', 204

# --- Especie Resources ---

@identity_ns.route('/especies')
class EspecieList(Resource):
    @identity_ns.doc('list_especies')
    @identity_ns.marshal_list_with(especie_model)
    def get(self):
        """List all species"""
        especies = Especie.query.all()
        return especies

    @identity_ns.doc('create_especie')
    @identity_ns.expect(especie_model)
    @identity_ns.marshal_with(especie_model, code=201)
    def post(self):
        """Create a new species"""
        data = identity_ns.payload
        new_especie = Especie(**data)
        db.session.add(new_especie)
        db.session.commit()
        return new_especie, 201

@identity_ns.route('/especies/<int:id>')
@identity_ns.param('id', 'The species identifier')
class EspecieResource(Resource):
    @identity_ns.doc('get_especie')
    @identity_ns.marshal_with(especie_model)
    def get(self, id):
        """Get a species by its ID"""
        especie = Especie.query.get_or_404(id)
        return especie

    @identity_ns.doc('update_especie')
    @identity_ns.expect(especie_model)
    @identity_ns.marshal_with(especie_model)
    def put(self, id):
        """Update a species by its ID"""
        especie = Especie.query.get_or_404(id)
        data = identity_ns.payload
        for key, value in data.items():
            setattr(especie, key, value)
        db.session.commit()
        return especie

    @identity_ns.doc('delete_especie')
    @identity_ns.response(204, 'Species deleted')
    def delete(self, id):
        """Delete a species by its ID"""
        especie = Especie.query.get_or_404(id)
        db.session.delete(especie)
        db.session.commit()
        return '', 204

# --- Linhagem Resources ---

@identity_ns.route('/linhagens')
class LinhagemList(Resource):
    @identity_ns.doc('list_linhagens')
    @identity_ns.marshal_list_with(linhagem_model)
    def get(self):
        """List all lineages"""
        linhagens = Linhagem.query.all()
        return linhagens

    @identity_ns.doc('create_linhagem')
    @identity_ns.expect(linhagem_model)
    @identity_ns.marshal_with(linhagem_model, code=201)
    def post(self):
        """Create a new lineage"""
        data = identity_ns.payload
        new_linhagem = Linhagem(**data)
        db.session.add(new_linhagem)
        db.session.commit()
        return new_linhagem, 201

@identity_ns.route('/linhagens/<int:id>')
@identity_ns.param('id', 'The lineage identifier')
class LinhagemResource(Resource):
    @identity_ns.doc('get_linhagem')
    @identity_ns.marshal_with(linhagem_model)
    def get(self, id):
        """Get a lineage by its ID"""
        linhagem = Linhagem.query.get_or_404(id)
        return linhagem

    @identity_ns.doc('update_linhagem')
    @identity_ns.expect(linhagem_model)
    @identity_ns.marshal_with(linhagem_model)
    def put(self, id):
        """Update a lineage by its ID"""
        linhagem = Linhagem.query.get_or_404(id)
        data = identity_ns.payload
        for key, value in data.items():
            setattr(linhagem, key, value)
        db.session.commit()
        return linhagem

    @identity_ns.doc('delete_linhagem')
    @identity_ns.response(204, 'Lineage deleted')
    def delete(self, id):
        """Delete a lineage by its ID"""
        linhagem = Linhagem.query.get_or_404(id)
        db.session.delete(linhagem)
        db.session.commit()
        return '', 204