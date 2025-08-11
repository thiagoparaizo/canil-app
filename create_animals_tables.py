#!/usr/bin/env python3
"""
Script para adicionar colunas faltantes na tabela animais
e criar estrutura completa para CRUD
"""

import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuração direta
DATABASE_URI = 'postgresql://canil_user:canil123@localhost:5432/canil_db'

def add_animal_columns():
    """Adiciona colunas faltantes na tabela animais."""
    
    print("🐕 Adicionando Colunas na Tabela Animais...")
    print("=" * 50)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                print("🔌 Conectado ao banco!")
                
                # Verificar estrutura atual
                print("🔍 Verificando estrutura atual da tabela animais...")
                
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                columns = inspector.get_columns('animais')
                
                existing_columns = [col['name'] for col in columns]
                print(f"📋 Colunas existentes: {existing_columns}")
                
                # Colunas que precisamos adicionar
                new_columns = [
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS microchip VARCHAR(20) UNIQUE",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS pedigree VARCHAR(50)",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS cor VARCHAR(50)",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS peso DECIMAL(5,2)",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS altura DECIMAL(5,2)",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'Ativo'",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS origem VARCHAR(100)",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS data_aquisicao DATE",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS valor_aquisicao DECIMAL(10,2)",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS observacoes TEXT",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT true",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS tipo_animal VARCHAR(20) DEFAULT 'Animal'",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS raca_id INTEGER",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS especie_id INTEGER",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS linhagem_id INTEGER",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS mother_id INTEGER",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS father_id INTEGER",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "ALTER TABLE animais ADD COLUMN IF NOT EXISTS data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                ]
                
                print("🔧 Adicionando colunas...")
                
                for sql in new_columns:
                    try:
                        conn.execute(db.text(sql))
                        column_name = sql.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0]
                        print(f"   ✅ {column_name}")
                    except Exception as e:
                        if "already exists" not in str(e):
                            print(f"   ⚠️  Erro em {sql}: {e}")
                
                # Commit das alterações
                conn.commit()
                
                # Criar índices para performance
                print("\\n📊 Criando índices para performance...")
                
                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_animais_tenant_id ON animais(tenant_id)",
                    "CREATE INDEX IF NOT EXISTS idx_animais_nome ON animais(nome)",
                    "CREATE INDEX IF NOT EXISTS idx_animais_sexo ON animais(sexo)",
                    "CREATE INDEX IF NOT EXISTS idx_animais_status ON animais(status)",
                    "CREATE INDEX IF NOT EXISTS idx_animais_ativo ON animais(ativo)",
                    "CREATE INDEX IF NOT EXISTS idx_animais_microchip ON animais(microchip)",
                    "CREATE INDEX IF NOT EXISTS idx_animais_data_nascimento ON animais(data_nascimento)"
                ]
                
                for sql in indices:
                    try:
                        conn.execute(db.text(sql))
                        index_name = sql.split('idx_')[1].split(' ')[0]
                        print(f"   ✅ idx_{index_name}")
                    except Exception as e:
                        if "already exists" not in str(e):
                            print(f"   ⚠️  Erro no índice: {e}")
                
                conn.commit()
                
                # Verificar estrutura final
                print("\\n🔍 Estrutura final da tabela animais:")
                columns_final = inspector.get_columns('animais')
                for col in columns_final:
                    print(f"   📋 {col['name']} ({col['type']})")
                
                return True
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_animals():
    """Cria alguns animais de exemplo para teste."""
    
    print("\\n🧪 Criando Animais de Exemplo...")
    print("=" * 30)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # Modelo simples para inserção
            class Animal(db.Model):
                __tablename__ = 'animais'
                id = db.Column(db.Integer, primary_key=True)
                nome = db.Column(db.String(128), nullable=False)
                data_nascimento = db.Column(db.Date, nullable=False)
                sexo = db.Column(db.String(10), nullable=False)
                tenant_id = db.Column(db.Integer, nullable=False)
                microchip = db.Column(db.String(20))
                cor = db.Column(db.String(50))
                peso = db.Column(db.Numeric(5,2))
                status = db.Column(db.String(20), default='Ativo')
                ativo = db.Column(db.Boolean, default=True)
                tipo_animal = db.Column(db.String(20), default='Animal')
            
            from datetime import date
            
            # Verificar se já existem animais
            count = db.session.query(Animal).count()
            if count > 0:
                print(f"⚠️  Já existem {count} animais no sistema")
                resposta = input("Deseja criar mais animais de exemplo? (s/N): ").lower().strip()
                if resposta != 's':
                    return True
            
            # Animais de exemplo
            animais_exemplo = [
                {
                    'nome': 'Rex',
                    'data_nascimento': date(2023, 1, 15),
                    'sexo': 'M',
                    'tenant_id': 1,
                    'microchip': '123456789012345',
                    'cor': 'Dourado',
                    'peso': 25.5,
                    'status': 'Ativo',
                    'tipo_animal': 'Reprodutor'
                },
                {
                    'nome': 'Luna',
                    'data_nascimento': date(2022, 8, 20),
                    'sexo': 'F',
                    'tenant_id': 1,
                    'microchip': '123456789012346',
                    'cor': 'Caramelo',
                    'peso': 22.0,
                    'status': 'Ativo',
                    'tipo_animal': 'Matriz'
                },
                {
                    'nome': 'Thor',
                    'data_nascimento': date(2023, 12, 10),
                    'sexo': 'M',
                    'tenant_id': 1,
                    'microchip': '123456789012347',
                    'cor': 'Preto',
                    'peso': 8.5,
                    'status': 'Ativo',
                    'tipo_animal': 'Filhote'
                },
                {
                    'nome': 'Mel',
                    'data_nascimento': date(2021, 5, 3),
                    'sexo': 'F',
                    'tenant_id': 1,
                    'microchip': '123456789012348',
                    'cor': 'Mel',
                    'peso': 20.8,
                    'status': 'Reservado',
                    'tipo_animal': 'Animal'
                },
                {
                    'nome': 'Zeus',
                    'data_nascimento': date(2020, 11, 12),
                    'sexo': 'M',
                    'tenant_id': 1,
                    'microchip': '123456789012349',
                    'cor': 'Chocolate',
                    'peso': 28.3,
                    'status': 'Ativo',
                    'tipo_animal': 'Reprodutor'
                }
            ]
            
            print("🐕 Criando animais de exemplo...")
            
            for animal_data in animais_exemplo:
                try:
                    # Verificar se já existe por microchip
                    existing = db.session.query(Animal).filter_by(
                        microchip=animal_data['microchip']
                    ).first()
                    
                    if existing:
                        print(f"   ⚠️  {animal_data['nome']} já existe (microchip: {animal_data['microchip']})")
                        continue
                    
                    animal = Animal(**animal_data)
                    db.session.add(animal)
                    print(f"   ✅ {animal_data['nome']} ({animal_data['sexo']}, {animal_data['tipo_animal']})")
                    
                except Exception as e:
                    print(f"   ❌ Erro ao criar {animal_data['nome']}: {e}")
                    db.session.rollback()
                    continue
            
            # Commit todas as inserções
            db.session.commit()
            
            # Verificar resultado
            total = db.session.query(Animal).filter_by(tenant_id=1).count()
            print(f"\\n📊 Total de animais no tenant 1: {total}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_animal_endpoints():
    """Cria um script de teste para os endpoints de animais."""
    
    print("\\n🧪 Criando Script de Teste...")
    print("=" * 30)
    
    test_script = '''#!/usr/bin/env python3
"""
Script de teste para endpoints de animais
Execute após iniciar o servidor com: python run_dev.py
"""

import requests
import json
from datetime import date

# Configuração
BASE_URL = "http://localhost:5000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
ANIMALS_URL = f"{BASE_URL}/animals/"

def get_auth_token():
    """Obtém token de autenticação."""
    login_data = {
        "login": "admin@canil.com",
        "senha": "admin123"
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Erro no login: {response.text}")
        return None

def test_list_animals(token):
    """Testa listagem de animais."""
    print("\\n📋 Testando Listagem de Animais...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Listar todos
    response = requests.get(ANIMALS_URL, headers=headers)
    print(f"GET /animals/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   📊 Total: {data['_meta']['total']} animais")
        for animal in data['items'][:3]:  # Mostrar apenas 3
            print(f"   🐕 {animal['nome']} ({animal['sexo']}, {animal['tipo_animal']})")
    
    # Testar filtros
    response = requests.get(f"{ANIMALS_URL}?sexo=M", headers=headers)
    print(f"GET /animals/?sexo=M - Status: {response.status_code}")
    
    response = requests.get(f"{ANIMALS_URL}?search=Rex", headers=headers)
    print(f"GET /animals/?search=Rex - Status: {response.status_code}")

def test_create_animal(token):
    """Testa criação de animal."""
    print("\\n➕ Testando Criação de Animal...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    new_animal = {
        "nome": "Buddy",
        "data_nascimento": "2023-06-15",
        "sexo": "M",
        "cor": "Marrom",
        "peso": 15.2,
        "microchip": "999888777666555",
        "status": "Ativo",
        "tipo_animal": "Animal"
    }
    
    response = requests.post(ANIMALS_URL, json=new_animal, headers=headers)
    print(f"POST /animals/ - Status: {response.status_code}")
    
    if response.status_code == 201:
        animal = response.json()
        print(f"   ✅ Animal criado: ID {animal['id']}, Nome: {animal['nome']}")
        return animal['id']
    else:
        print(f"   ❌ Erro: {response.text}")
        return None

def test_get_animal(token, animal_id):
    """Testa busca de animal específico."""
    print(f"\\n🔍 Testando Busca do Animal ID {animal_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{ANIMALS_URL}{animal_id}", headers=headers)
    print(f"GET /animals/{animal_id} - Status: {response.status_code}")
    
    if response.status_code == 200:
        animal = response.json()
        print(f"   ✅ Animal encontrado: {animal['nome']}")
        return animal
    else:
        print(f"   ❌ Erro: {response.text}")
        return None

def test_update_animal(token, animal_id):
    """Testa atualização de animal."""
    print(f"\\n✏️ Testando Atualização do Animal ID {animal_id}...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    update_data = {
        "peso": 16.5,
        "observacoes": "Animal muito dócil e brincalhão"
    }
    
    response = requests.put(f"{ANIMALS_URL}{animal_id}", json=update_data, headers=headers)
    print(f"PUT /animals/{animal_id} - Status: {response.status_code}")
    
    if response.status_code == 200:
        animal = response.json()
        print(f"   ✅ Animal atualizado: Peso {animal['peso']}kg")
        return animal
    else:
        print(f"   ❌ Erro: {response.text}")
        return None

def test_animal_stats(token):
    """Testa estatísticas de animais."""
    print("\\n📊 Testando Estatísticas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{ANIMALS_URL}stats", headers=headers)
    print(f"GET /animals/stats - Status: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"   📊 Total: {stats['total']}")
        print(f"   📊 Ativos: {stats['ativos']}")
        print(f"   📊 Machos: {stats['machos']}")
        print(f"   📊 Fêmeas: {stats['femeas']}")
        print(f"   📊 Por status: {stats['por_status']}")

def test_toggle_status(token, animal_id):
    """Testa alteração de status."""
    print(f"\\n🔄 Testando Toggle Status do Animal ID {animal_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.patch(f"{ANIMALS_URL}{animal_id}/toggle-status", headers=headers)
    print(f"PATCH /animals/{animal_id}/toggle-status - Status: {response.status_code}")
    
    if response.status_code == 200:
        animal = response.json()
        status = "ativo" if animal['ativo'] else "inativo"
        print(f"   ✅ Status alterado para: {status}")

def test_delete_animal(token, animal_id):
    """Testa exclusão de animal."""
    print(f"\\n🗑️ Testando Exclusão do Animal ID {animal_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.delete(f"{ANIMALS_URL}{animal_id}", headers=headers)
    print(f"DELETE /animals/{animal_id} - Status: {response.status_code}")
    
    if response.status_code == 204:
        print("   ✅ Animal deletado com sucesso")
    else:
        print(f"   ❌ Erro: {response.text}")

def main():
    """Executa todos os testes."""
    print("🧪 Teste Completo dos Endpoints de Animais")
    print("=" * 50)
    
    # 1. Autenticação
    print("🔐 Fazendo login...")
    token = get_auth_token()
    if not token:
        print("❌ Falha na autenticação. Verifique se o servidor está rodando.")
        return
    
    print("✅ Login realizado com sucesso!")
    
    # 2. Listar animais
    test_list_animals(token)
    
    # 3. Criar animal
    animal_id = test_create_animal(token)
    
    if animal_id:
        # 4. Buscar animal
        test_get_animal(token, animal_id)
        
        # 5. Atualizar animal
        test_update_animal(token, animal_id)
        
        # 6. Toggle status
        test_toggle_status(token, animal_id)
        
        # 7. Estatísticas
        test_animal_stats(token)
        
        # 8. Deletar animal (opcional)
        print("\\n❓ Deseja deletar o animal de teste?")
        resposta = input("Digite 's' para deletar: ").lower().strip()
        if resposta == 's':
            test_delete_animal(token, animal_id)
    
    print("\\n🎉 Testes concluídos!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n👋 Testes interrompidos!")
    except Exception as e:
        print(f"\\n❌ Erro durante os testes: {e}")
'''
    
    try:
        with open('test_animal_endpoints.py', 'w', encoding='utf-8') as f:
            f.write(test_script)
        print("✅ Script de teste criado: test_animal_endpoints.py")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        return False

def main():
    """Função principal."""
    
    print("🐕 CanilApp - Configuração de Animais")
    print("=" * 50)
    
    success = True
    
    # 1. Adicionar colunas na tabela animais
    print("\\n🔧 Etapa 1: Estrutura da Tabela")
    if not add_animal_columns():
        success = False
    
    # 2. Criar animais de exemplo
    print("\\n🧪 Etapa 2: Dados de Exemplo")
    if not create_sample_animals():
        print("⚠️  Falha ao criar animais de exemplo")
    
    # 3. Criar script de teste
    print("\\n🧪 Etapa 3: Script de Testes")
    if not test_animal_endpoints():
        print("⚠️  Falha ao criar script de teste")
    
    if success:
        print("\\n🎉 Configuração de animais concluída!")
        print("\\n📋 Próximos passos:")
        print("1. Execute: python run_dev.py")
        print("2. Teste: python test_animal_endpoints.py")
        print("3. Ou use curl para testar manualmente")
        
        print("\\n🧪 Exemplos de teste manual:")
        print("# Listar animais")
        print("curl -X GET http://localhost:5000/api/v1/animals/ \\\\")
        print('  -H "Authorization: Bearer SEU_TOKEN"')
        
        print("\\n# Criar animal")
        print("curl -X POST http://localhost:5000/api/v1/animals/ \\\\")
        print('  -H "Authorization: Bearer SEU_TOKEN" \\\\')
        print('  -H "Content-Type: application/json" \\\\')
        print('  -d \'{"nome": "Bolt", "data_nascimento": "2023-01-01", "sexo": "M"}\'')
    else:
        print("\\n💥 Algumas etapas falharam!")
    
    return success

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n\\n👋 Script interrompido!")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)