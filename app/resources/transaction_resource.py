from flask_restx import Namespace, Resource, fields, abort
from app import db
from app.models.transaction import Venda, Adocao, Reserva # Assuming these models are defined
from app.models.person import Cliente # Assuming Cliente model is needed
from app.models.animal import Filhote, Animal # Assuming Animal and Filhote models are needed
from sqlalchemy.exc import SQLAlchemyError
from datetime import date # Import date for date validations

transaction_ns = Namespace('transactions', description='Transaction related operations (Sales, Adoptions, Reservations)')

# Define models for API representation
venta_model = transaction_ns.model('Venda', {
    'id': fields.Integer(readOnly=True),
    'data_venda': fields.Date(required=True),
    'valor': fields.Float(required=True),
    'forma_pagamento': fields.String,
    'contrato_venda': fields.String,
    'garantias': fields.String,
    'entregue': fields.Boolean,
    'observacoes': fields.String,
    'cliente_id': fields.Integer(required=True), # Foreign key
    'filhote_id': fields.Integer(required=True), # Foreign key
    # Relationships to Cliente and Filhote can be handled by nested models or IDs
})

adocao_model = transaction_ns.model('Adocao', {
    'id': fields.Integer(readOnly=True),
    'data_adocao': fields.Date(required=True),
    'motivo': fields.String(required=True),
    'termo_adocao': fields.String,
    'acompanhamento': fields.Boolean,
    'observacoes': fields.String,
    'cliente_id': fields.Integer(required=True), # Foreign key (Adopter)
    'animal_id': fields.Integer(required=True), # Foreign key (Animal being adopted)
    # Relationships to Cliente and Animal can be handled by nested models or IDs
})

reserva_model = transaction_ns.model('Reserva', {
    'id': fields.Integer(readOnly=True),
    'data_reserva': fields.Date(required=True),
    'valor_sinal': fields.Float(required=True),
    'data_vencimento': fields.Date,
    'status': fields.String(required=True),
    'observacoes': fields.String,
    'cliente_id': fields.Integer(required=True), # Foreign key
    'filhote_id': fields.Integer(required=True), # Foreign key
    # Relationships to Cliente and Filhote can be handled by nested models or IDs
})

# --- Venda Resources ---

@transaction_ns.route('/vendas')
class VendaList(Resource):
    @transaction_ns.doc('list_vendas')
# TODO: Apply @tenant_required decorator
    @transaction_ns.marshal_list_with(venta_model)
    def get(self):
        """List all sales"""
        # tenant_id = 1 # TODO: Get tenant_id from context/middleware
        # vendas = Venda.query.filter_by(tenant_id=tenant_id).all() # Simulate tenant filtering
        vendas = Venda.query.all()
        return vendas

    @transaction_ns.doc('create_venda')
    @transaction_ns.expect(venta_model)
    @transaction_ns.marshal_with(venta_model, code=201)
    def post(self):
        """Create a new sale record"""
        # TODO: Apply @tenant_required decorator
        try:
            data = transaction_ns.payload
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware

            # Basic validation for required fields
            required_fields = ['data_venda', 'valor', 'cliente_id', 'filhote_id']
            if not all(field in data for field in required_fields):
                abort(400, message='Missing required fields')

            # Validate data types and formats (basic)
            if not isinstance(data['data_venda'], date):
                 # Consider using Flask-RESTX fields for automatic date parsing
                 abort(400, message='Invalid data_venda format. Use YYYY-MM-DD')
            if not isinstance(data['valor'], (int, float)) or data['valor'] < 0:
                 abort(400, message='Valor must be a non-negative number')

            # Validate existence of Cliente and Filhote for the current tenant
            # cliente = Cliente.query.filter_by(id=data['cliente_id'], tenant_id=tenant_id).first() # Simulate tenant filtering
            # filhote = Filhote.query.filter_by(id=data['filhote_id'], tenant_id=tenant_id).first() # Simulate tenant filtering
            # if not cliente: abort(404, message='Cliente not found for this tenant')
            # if not filhote: abort(404, message='Filhote not found for this tenant')

            new_venda = Venda(**data)
            # new_venda.tenant_id = tenant_id # Assign tenant ID
            db.session.add(new_venda)
            db.session.commit()
            return new_venda, 201
        except SQLAlchemyError as e: db.session.rollback(); abort(500, message=f'Database error: {e}')
        except Exception as e: db.session.rollback(); abort(500, message=f'An error occurred: {e}')

@transaction_ns.route('/vendas/<int:id>')
@transaction_ns.param('id', 'The sale identifier')
class VendaResource(Resource):
    @transaction_ns.doc('get_venda')
    @transaction_ns.marshal_with(venta_model)
    def get(self, id):
        """Get a sale record by its ID"""
        # TODO: Apply @tenant_required decorator
        try:
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware
            # venda = Venda.query.filter_by(id=id, tenant_id=tenant_id).first() # Simulate tenant filtering
            venda = Venda.query.get(id) # Placeholder without tenant filtering
            if not venda:
                abort(404, message='Sale not found') # Needs tenant-specific not found
            # TODO: Add check for tenant ownership if not using filter_by
            return venda
        except SQLAlchemyError as e: abort(500, message=f'Database error: {e}')
        except Exception as e: abort(500, message=f'An error occurred: {e}')

    @transaction_ns.doc('update_venda')
    @transaction_ns.expect(venta_model)
    @transaction_ns.marshal_with(venta_model)
    def put(self, id):
        # TODO: Apply @tenant_required decorator
        try:

        """Update a sale by its ID"""
        venda = Venda.query.get_or_404(id)
        data = transaction_ns.payload

        # Prevent updating foreign keys directly if not intended, or add logic to handle it
        data.pop('cliente_id', None)
        data.pop('filhote_id', None)

        for key, value in data.items():
            setattr(venda, key, value)

        db.session.commit()
        return venda # Needs tenant check before updating and returning
        except SQLAlchemyError as e: db.session.rollback(); abort(500, message=f'Database error: {e}')
        except Exception as e: db.session.rollback(); abort(500, message=f'An error occurred: {e}')

    @transaction_ns.doc('delete_venda')
    @transaction_ns.response(204, 'Sale deleted')
    def delete(self, id):
        """Delete a sale by its ID"""
        # TODO: Apply @tenant_required decorator
        try:
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware
            # venda = Venda.query.filter_by(id=id, tenant_id=tenant_id).first() # Simulate tenant filtering
            venda = Venda.query.get(id) # Placeholder without tenant filtering
            if not venda: abort(404, message='Sale not found') # Needs tenant-specific not found
        db.session.delete(venda)
        db.session.commit()
        return '', 204

# --- Adocao Resources ---

@transaction_ns.route('/adocoes')
class AdocaoList(Resource):
    @transaction_ns.doc('list_adocoes')
# TODO: Apply @tenant_required decorator
    @transaction_ns.marshal_list_with(adocao_model)
    def get(self):
        """List all adoptions"""
        # tenant_id = 1 # TODO: Get tenant_id from context/middleware
        # adocoes = Adocao.query.filter_by(tenant_id=tenant_id).all() # Simulate tenant filtering
        adocoes = Adocao.query.all()
        return adocoes

    @transaction_ns.doc('create_adocao')
    @transaction_ns.expect(adocao_model)
    @transaction_ns.marshal_with(adocao_model, code=201)
    def post(self):
        """Create a new adoption record"""
        # TODO: Apply @tenant_required decorator
        try:
            data = transaction_ns.payload
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware

            # Basic validation for required fields
            required_fields = ['data_adocao', 'motivo', 'cliente_id', 'animal_id']
            if not all(field in data for field in required_fields):
                abort(400, message='Missing required fields')

            # Validate data format (basic)
            if not isinstance(data['data_adocao'], date):
                 abort(400, message='Invalid data_adocao format. Use YYYY-MM-DD')

            # Validate existence of Cliente and Animal for the current tenant
            # cliente = Cliente.query.filter_by(id=data['cliente_id'], tenant_id=tenant_id).first() # Simulate tenant filtering
            # animal = Animal.query.filter_by(id=data['animal_id'], tenant_id=tenant_id).first() # Simulate tenant filtering
            # if not cliente: abort(404, message='Cliente not found for this tenant')
            # if not animal: abort(404, message='Animal not found for this tenant')

            new_adocao = Adocao(**data)
            db.session.add(new_adocao)
            db.session.commit()
            return new_adocao, 201
        except SQLAlchemyError as e: db.session.rollback(); abort(500, message=f'Database error: {e}')
        except Exception as e: db.session.rollback(); abort(500, message=f'An error occurred: {e}')

@transaction_ns.route('/adocoes/<int:id>')
@transaction_ns.param('id', 'The adoption identifier')
class AdocaoResource(Resource):
    @transaction_ns.doc('get_adocao')
    @transaction_ns.marshal_with(adocao_model)
    def get(self, id):
        """Get an adoption record by its ID""" # TODO: Apply @tenant_required decorator
        try:
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware
            # adocao = Adocao.query.filter_by(id=id, tenant_id=tenant_id).first() # Simulate tenant filtering
            adocao = Adocao.query.get(id) # Placeholder without tenant filtering
            if not adocao:
                abort(404, message='Adoption record not found') # Needs tenant-specific not found
            # TODO: Add check for tenant ownership if not using filter_by
            return adocao
        except SQLAlchemyError as e: abort(500, message=f'Database error: {e}')
        except Exception as e: abort(500, message=f'An error occurred: {e}')


    @transaction_ns.doc('update_adocao')
    @transaction_ns.expect(adocao_model)
    @transaction_ns.marshal_with(adocao_model)
    # TODO: Apply @tenant_required decorator
    # TODO: Validate fields being updated
    # TODO: Prevent changing cliente_id, animal_id, and tenant_id via PUT
    def put(self, id):
        """Update an adoption record by its ID"""
        adocao = Adocao.query.get_or_404(id)
        data = transaction_ns.payload

        data.pop('cliente_id', None)
        data.pop('animal_id', None)

        for key, value in data.items():
            setattr(adocao, key, value)

        db.session.commit()
        return adocao # Needs tenant check before updating and returning

    @transaction_ns.doc('delete_adocao')
    @transaction_ns.response(204, 'Adoption record deleted')
    def delete(self, id):
        """Delete an adoption record by its ID"""
        # TODO: Apply @tenant_required decorator
        try:
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware
            # adocao = Adocao.query.filter_by(id=id, tenant_id=tenant_id).first() # Simulate tenant filtering
            adocao = Adocao.query.get(id) # Placeholder without tenant filtering
            if not adocao:
                abort(404, message='Adoption record not found') # Needs tenant-specific not found

        db.session.delete(adocao)
        db.session.commit()
        return '', 204

# --- Reserva Resources ---

@transaction_ns.route('/reservas')
class ReservaList(Resource):
    @transaction_ns.doc('list_reservas')
# TODO: Apply @tenant_required decorator
    @transaction_ns.marshal_list_with(reserva_model)
    def get(self):
        """List all reservations"""
        # tenant_id = 1 # TODO: Get tenant_id from context/middleware
        # reservas = Reserva.query.filter_by(tenant_id=tenant_id).all() # Simulate tenant filtering
        reservas = Reserva.query.all()
        return reservas

    @transaction_ns.doc('create_reserva')
    @transaction_ns.expect(reserva_model)
    @transaction_ns.marshal_with(reserva_model, code=201)
    def post(self):
        """Create a new reservation"""# TODO: Apply @tenant_required decorator
        try:
            data = transaction_ns.payload
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware

            # Basic validation for required fields
            required_fields = ['data_reserva', 'valor_sinal', 'status', 'cliente_id', 'filhote_id']
            if not all(field in data for field in required_fields):
                abort(400, message='Missing required fields')

            # Validate data types and formats (basic)
            if not isinstance(data['data_reserva'], date):
                 abort(400, message='Invalid data_reserva format. Use YYYY-MM-DD')
            if 'data_vencimento' in data and not isinstance(data['data_vencimento'], date):
                 abort(400, message='Invalid data_vencimento format. Use YYYY-MM-DD')
            if not isinstance(data['valor_sinal'], (int, float)) or data['valor_sinal'] < 0:
                 abort(400, message='Valor_sinal must be a non-negative number')
            # TODO: Validate status against allowed values
            # allowed_statuses = ['Pendente', 'Confirmada', 'Cancelada'] # Example
            # if data['status'] not in allowed_statuses:
            #     abort(400, message=f'Invalid status. Allowed values are: {", ".join(allowed_statuses)}')

            # Validate existence of Cliente and Filhote for the current tenant
            # cliente = Cliente.query.filter_by(id=data['cliente_id'], tenant_id=tenant_id).first() # Simulate tenant filtering
            # filhote = Filhote.query.filter_by(id=data['filhote_id'], tenant_id=tenant_id).first() # Simulate tenant filtering
            # if not cliente: abort(404, message='Cliente not found for this tenant')
            # if not filhote: abort(404, message='Filhote not found for this tenant')

            new_reserva = Reserva(**data)
            db.session.add(new_reserva)
            db.session.commit()
            return new_reserva, 201
        except SQLAlchemyError as e: db.session.rollback(); abort(500, message=f'Database error: {e}')
        except Exception as e: db.session.rollback(); abort(500, message=f'An error occurred: {e}')

@transaction_ns.route('/reservas/<int:id>')
@transaction_ns.param('id', 'The reservation identifier')
class ReservaResource(Resource):
    @transaction_ns.doc('get_reserva')
    @transaction_ns.marshal_with(reserva_model)
    def get(self, id):
        """Get a reservation by its ID"""# TODO: Apply @tenant_required decorator
        try:
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware
            # reserva = Reserva.query.filter_by(id=id, tenant_id=tenant_id).first() # Simulate tenant filtering
            reserva = Reserva.query.get(id) # Placeholder without tenant filtering
            if not reserva:
                abort(404, message='Reservation not found') # Needs tenant-specific not found
            # TODO: Add check for tenant ownership if not using filter_by
            return reserva
        except SQLAlchemyError as e: abort(500, message=f'Database error: {e}')
        except Exception as e: abort(500, message=f'An error occurred: {e}')


    @transaction_ns.doc('update_reserva')
    @transaction_ns.expect(reserva_model)
    @transaction_ns.marshal_with(reserva_model)
    # TODO: Apply @tenant_required decorator
    # TODO: Validate fields being updated
    # TODO: Prevent changing cliente_id, filhote_id, and tenant_id via PUT
    def put(self, id):
        """Update a reservation by its ID"""
        reserva = Reserva.query.get_or_404(id)
        data = transaction_ns.payload

        data.pop('cliente_id', None)
        data.pop('filhote_id', None)

        for key, value in data.items():
            setattr(reserva, key, value)

        db.session.commit()
        return reserva # Needs tenant check before updating and returning

    @transaction_ns.doc('delete_reserva')
    @transaction_ns.response(204, 'Reservation deleted')
    def delete(self, id):
        """Delete a reservation by its ID"""
        # TODO: Apply @tenant_required decorator
        try:
            # tenant_id = 1 # TODO: Get tenant_id from context/middleware
            # reserva = Reserva.query.filter_by(id=id, tenant_id=tenant_id).first() # Simulate tenant filtering
            reserva = Reserva.query.get(id) # Placeholder without tenant filtering
            if not reserva:
                abort(404, message='Reservation not found') # Needs tenant-specific not found

        db.session.delete(reserva)
        db.session.commit()
        return '', 204