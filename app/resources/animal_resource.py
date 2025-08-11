"""
Recursos REST para gerenciamento de animais
CRUD completo com isolamento por tenant
"""

from flask import request, current_app
from flask_restx import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from sqlalchemy import or_
from datetime import date, datetime

from app import db

# Função auxiliar para obter tenant_id do JWT
def get_current_tenant_id():
    """Obtém o tenant_id do JWT token."""
    try:
        user_id = get_jwt_identity()
        if user_id:
            # Buscar o usuário no banco para obter o tenant_id
            from app.models.system import Usuario
            user = db.session.query(Usuario).filter_by(id=int(user_id)).first()
            if user:
                return user.tenant_id
        return 1  # Fallback para tenant padrão
    except Exception as e:
        print(f"Erro ao obter tenant_id: {e}")
        return 1  # Fallback para tenant padrão
    except:
        return 1

# Namespace para animais
animal_ns = Namespace('animals', description='Operações relacionadas aos animais')

# Modelo para serialização/validação
animal_model = animal_ns.model('Animal', {
    'id': fields.Integer(readOnly=True, description='ID único do animal'),
    'nome': fields.String(required=True, description='Nome do animal', example='Rex'),
    'microchip': fields.String(description='ID do microchip', example='123456789012345'),
    'pedigree': fields.String(description='Número do pedigree', example='CBKC-123456'),
    'data_nascimento': fields.Date(required=True, description='Data de nascimento (YYYY-MM-DD)', example='2023-01-15'),
    'sexo': fields.String(required=True, description='Sexo do animal (M/F)', example='M', enum=['M', 'F']),
    'cor': fields.String(description='Cor do animal', example='Dourado'),
    'peso': fields.Float(description='Peso em kg', example=25.5),
    'altura': fields.Float(description='Altura em cm', example=60.0),
    'status': fields.String(description='Status do animal', example='Ativo', enum=['Ativo', 'Vendido', 'Reservado', 'Falecido']),
    'origem': fields.String(description='Origem do animal', example='Nascimento próprio'),
    'data_aquisicao': fields.Date(description='Data de aquisição (YYYY-MM-DD)', example='2023-01-15'),
    'valor_aquisicao': fields.Float(description='Valor de aquisição', example=1500.00),
    'observacoes': fields.String(description='Observações gerais', example='Animal dócil e saudável'),
    'ativo': fields.Boolean(description='Animal ativo no sistema', default=True),
    'tipo_animal': fields.String(description='Tipo específico do animal', enum=['Animal', 'Matriz', 'Reprodutor', 'Filhote']),
    'raca_id': fields.Integer(description='ID da raça'),
    'especie_id': fields.Integer(description='ID da espécie'),
    'linhagem_id': fields.Integer(description='ID da linhagem'),
    'mother_id': fields.Integer(description='ID da mãe'),
    'father_id': fields.Integer(description='ID do pai'),
    'tenant_id': fields.Integer(readOnly=True, description='ID do tenant')
})

# Modelo para listagem com metadados
animal_list_model = animal_ns.model('AnimalList', {
    'items': fields.List(fields.Nested(animal_model)),
    '_meta': fields.Raw(description='Metadados da paginação')
})

# Parser para parâmetros de consulta
list_parser = reqparse.RequestParser()
list_parser.add_argument('page', type=int, default=1, help='Número da página')
list_parser.add_argument('per_page', type=int, default=10, help='Itens por página (máx. 100)')
list_parser.add_argument('search', type=str, help='Buscar por nome, microchip, pedigree, etc.')
list_parser.add_argument('sexo', type=str, choices=['M', 'F'], help='Filtrar por sexo')
list_parser.add_argument('status', type=str, help='Filtrar por status')
list_parser.add_argument('ativo', type=bool, help='Filtrar por animais ativos/inativos')

@animal_ns.route('/')
class AnimalList(Resource):
    @jwt_required()
    @animal_ns.doc('list_animals')
    @animal_ns.expect(list_parser)
    @animal_ns.marshal_with(animal_list_model)
    def get(self):
        """
        Lista todos os animais do tenant atual com paginação e filtros
        """
        try:
            # Obter tenant atual
            current_tenant_id = get_current_tenant_id()
            
            # Obter parâmetros da query
            args = list_parser.parse_args()
            page = args['page']
            per_page = min(args['per_page'], 100)  # Limitar a 100 itens por página
            search = args['search']
            sexo = args['sexo']
            status = args['status']
            ativo = args['ativo']
            
            # Importar modelos dinamicamente para evitar imports circulares
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            # Query base com filtro de tenant
            query = Animal.query.filter_by(tenant_id=current_tenant_id)
            
            # Aplicar filtros
            if search:
                search_pattern = f'%{search}%'
                query = query.filter(or_(
                    Animal.nome.ilike(search_pattern),
                    Animal.microchip.ilike(search_pattern),
                    Animal.pedigree.ilike(search_pattern),
                    Animal.cor.ilike(search_pattern),
                    Animal.origem.ilike(search_pattern)
                ))
            
            if sexo:
                query = query.filter_by(sexo=sexo)
            
            if status:
                query = query.filter_by(status=status)
            
            if ativo is not None:
                query = query.filter_by(ativo=ativo)
            
            # Ordenar por ID decrescente (mais recentes primeiro)
            query = query.order_by(Animal.id.desc())
            
            # Paginação
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # Resposta com metadados
            response = {
                'items': pagination.items,
                '_meta': {
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
            
            return response, 200
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"Erro de banco ao listar animais: {e}")
            animal_ns.abort(500, message='Erro de banco de dados')
        except Exception as e:
            current_app.logger.error(f"Erro inesperado ao listar animais: {e}")
            animal_ns.abort(500, message='Erro interno do servidor')

    @jwt_required()
    @animal_ns.doc('create_animal')
    @animal_ns.expect(animal_model)
    @animal_ns.marshal_with(animal_model, code=201)
    def post(self):
        """
        Cria um novo animal para o tenant atual
        """
        try:
            # Obter tenant atual
            current_tenant_id = get_current_tenant_id()
            
            # Obter dados do payload
            data = animal_ns.payload
            
            # Validações básicas
            if not data.get('nome'):
                animal_ns.abort(400, message='Nome é obrigatório')
            
            if not data.get('data_nascimento'):
                animal_ns.abort(400, message='Data de nascimento é obrigatória')
            
            if not data.get('sexo') or data.get('sexo') not in ['M', 'F']:
                animal_ns.abort(400, message='Sexo deve ser M ou F')
            
            # Converter data se necessário
            if isinstance(data.get('data_nascimento'), str):
                try:
                    data['data_nascimento'] = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
                except ValueError:
                    animal_ns.abort(400, message='Formato de data inválido. Use YYYY-MM-DD')
            
            if data.get('data_aquisicao') and isinstance(data.get('data_aquisicao'), str):
                try:
                    data['data_aquisicao'] = datetime.strptime(data['data_aquisicao'], '%Y-%m-%d').date()
                except ValueError:
                    animal_ns.abort(400, message='Formato de data de aquisição inválido. Use YYYY-MM-DD')
            
            # Importar modelo
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            # Remover campos que não devem ser definidos pelo usuário
            data.pop('id', None)
            data.pop('tenant_id', None)
            
            # Definir valores padrão
            data.setdefault('status', 'Ativo')
            data.setdefault('ativo', True)
            
            # Criar animal
            animal = Animal(
                tenant_id=current_tenant_id,
                **data
            )
            
            db.session.add(animal)
            db.session.commit()
            
            current_app.logger.info(f"Animal criado: ID {animal.id}, Nome: {animal.nome}, Tenant: {current_tenant_id}")
            
            return animal, 201
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de integridade ao criar animal: {e}")
            if 'microchip' in str(e):
                animal_ns.abort(409, message='Microchip já está em uso')
            animal_ns.abort(409, message='Violação de restrição única')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de dados ao criar animal: {e}")
            animal_ns.abort(400, message='Formato de dados inválido')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de banco ao criar animal: {e}")
            animal_ns.abort(500, message='Erro de banco de dados')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao criar animal: {e}")
            animal_ns.abort(500, message='Erro interno do servidor')

@animal_ns.route('/<int:id>')
@animal_ns.param('id', 'ID do animal')
class AnimalResource(Resource):
    @jwt_required()
    @animal_ns.doc('get_animal')
    @animal_ns.marshal_with(animal_model)
    def get(self, id):
        """
        Obtém um animal específico por ID (apenas do tenant atual)
        """
        try:
            # Obter tenant atual
            current_tenant_id = get_current_tenant_id()
            
            # Importar modelo
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            # Buscar animal com filtro de tenant
            animal = Animal.query.filter_by(
                id=id, 
                tenant_id=current_tenant_id
            ).first()
            
            if not animal:
                animal_ns.abort(404, message=f'Animal {id} não encontrado ou não pertence ao seu tenant')
            
            return animal, 200
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"Erro de banco ao buscar animal {id}: {e}")
            animal_ns.abort(500, message='Erro de banco de dados')
        except Exception as e:
            current_app.logger.error(f"Erro inesperado ao buscar animal {id}: {e}")
            animal_ns.abort(500, message='Erro interno do servidor')

    @jwt_required()
    @animal_ns.doc('update_animal')
    @animal_ns.expect(animal_model)
    @animal_ns.marshal_with(animal_model)
    def put(self, id):
        """
        Atualiza um animal específico (apenas do tenant atual)
        """
        try:
            # Obter tenant atual
            current_tenant_id = get_current_tenant_id()
            
            # Importar modelo
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            # Buscar animal
            animal = Animal.query.filter_by(
                id=id, 
                tenant_id=current_tenant_id
            ).first()
            
            if not animal:
                animal_ns.abort(404, message=f'Animal {id} não encontrado ou não pertence ao seu tenant')
            
            # Obter dados de atualização
            data = animal_ns.payload
            
            # Remover campos que não devem ser alterados
            data.pop('id', None)
            data.pop('tenant_id', None)
            
            # Validações
            if 'sexo' in data and data['sexo'] not in ['M', 'F']:
                animal_ns.abort(400, message='Sexo deve ser M ou F')
            
            # Converter datas se necessário
            if data.get('data_nascimento') and isinstance(data.get('data_nascimento'), str):
                try:
                    data['data_nascimento'] = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
                except ValueError:
                    animal_ns.abort(400, message='Formato de data inválido. Use YYYY-MM-DD')
            
            if data.get('data_aquisicao') and isinstance(data.get('data_aquisicao'), str):
                try:
                    data['data_aquisicao'] = datetime.strptime(data['data_aquisicao'], '%Y-%m-%d').date()
                except ValueError:
                    animal_ns.abort(400, message='Formato de data de aquisição inválido. Use YYYY-MM-DD')
            
            # Atualizar campos
            for field, value in data.items():
                if hasattr(animal, field):
                    setattr(animal, field, value)
            
            db.session.commit()
            
            current_app.logger.info(f"Animal atualizado: ID {animal.id}, Nome: {animal.nome}, Tenant: {current_tenant_id}")
            
            return animal, 200
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de integridade ao atualizar animal {id}: {e}")
            if 'microchip' in str(e):
                animal_ns.abort(409, message='Microchip já está em uso')
            animal_ns.abort(409, message='Violação de restrição única')
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de dados ao atualizar animal {id}: {e}")
            animal_ns.abort(400, message='Formato de dados inválido')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de banco ao atualizar animal {id}: {e}")
            animal_ns.abort(500, message='Erro de banco de dados')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao atualizar animal {id}: {e}")
            animal_ns.abort(500, message='Erro interno do servidor')

    @jwt_required()
    @animal_ns.doc('delete_animal')
    @animal_ns.response(204, 'Animal deletado com sucesso')
    def delete(self, id):
        """
        Deleta um animal específico (apenas do tenant atual)
        """
        try:
            # Obter tenant atual
            current_tenant_id = get_current_tenant_id()
            
            # Importar modelo
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            # Buscar animal
            animal = Animal.query.filter_by(
                id=id, 
                tenant_id=current_tenant_id
            ).first()
            
            if not animal:
                animal_ns.abort(404, message=f'Animal {id} não encontrado ou não pertence ao seu tenant')
            
            # Salvar info para log
            nome_animal = animal.nome
            
            # Deletar animal
            db.session.delete(animal)
            db.session.commit()
            
            current_app.logger.info(f"Animal deletado: ID {id}, Nome: {nome_animal}, Tenant: {current_tenant_id}")
            
            return '', 204
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de banco ao deletar animal {id}: {e}")
            
            # Verificar se há dependências (ex: animal tem filhotes)
            if 'foreign key constraint' in str(e).lower():
                animal_ns.abort(409, message='Não é possível deletar: animal possui dependências (filhotes, registros, etc.)')
            
            animal_ns.abort(500, message='Erro de banco de dados')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado ao deletar animal {id}: {e}")
            animal_ns.abort(500, message='Erro interno do servidor')

# Endpoints adicionais para funcionalidades específicas

@animal_ns.route('/<int:id>/toggle-status')
@animal_ns.param('id', 'ID do animal')
class AnimalToggleStatus(Resource):
    @jwt_required()
    @animal_ns.doc('toggle_animal_status')
    @animal_ns.marshal_with(animal_model)
    def patch(self, id):
        """
        Alterna o status ativo/inativo do animal
        """
        try:
            current_tenant_id = get_current_tenant_id()
            
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            animal = Animal.query.filter_by(
                id=id, 
                tenant_id=current_tenant_id
            ).first()
            
            if not animal:
                animal_ns.abort(404, message=f'Animal {id} não encontrado')
            
            # Alternar status
            animal.ativo = not animal.ativo
            db.session.commit()
            
            status_text = "ativado" if animal.ativo else "desativado"
            current_app.logger.info(f"Animal {status_text}: ID {id}, Nome: {animal.nome}")
            
            return animal, 200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao alterar status do animal {id}: {e}")
            animal_ns.abort(500, message='Erro de banco de dados')

@animal_ns.route('/stats')
class AnimalStats(Resource):
    @jwt_required()
    @animal_ns.doc('get_animal_stats')
    def get(self):
        """
        Obtém estatísticas dos animais do tenant atual
        """
        try:
            current_tenant_id = get_current_tenant_id()
            
            try:
                from app.models.animal import Animal
            except ImportError:
                animal_ns.abort(500, message='Modelo Animal não disponível')
            
            # Consultas de estatísticas
            total = Animal.query.filter_by(tenant_id=current_tenant_id).count()
            ativos = Animal.query.filter_by(tenant_id=current_tenant_id, ativo=True).count()
            machos = Animal.query.filter_by(tenant_id=current_tenant_id, sexo='M').count()
            femeas = Animal.query.filter_by(tenant_id=current_tenant_id, sexo='F').count()
            
            # Estatísticas por status
            stats_status = {}
            status_query = db.session.query(
                Animal.status, 
                db.func.count(Animal.id)
            ).filter_by(tenant_id=current_tenant_id).group_by(Animal.status).all()
            
            for status, count in status_query:
                stats_status[status or 'Sem status'] = count
            
            response = {
                'total': total,
                'ativos': ativos,
                'inativos': total - ativos,
                'machos': machos,
                'femeas': femeas,
                'por_status': stats_status,
                'tenant_id': current_tenant_id
            }
            
            return response, 200
            
        except SQLAlchemyError as e:
            current_app.logger.error(f"Erro ao obter estatísticas: {e}")
            animal_ns.abort(500, message='Erro de banco de dados')
        except Exception as e:
            current_app.logger.error(f"Erro inesperado ao obter estatísticas: {e}")
            animal_ns.abort(500, message='Erro interno do servidor')