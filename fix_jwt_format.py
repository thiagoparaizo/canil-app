#!/usr/bin/env python3
"""
Script para corrigir o formato do JWT nos recursos
O Flask-JWT-Extended espera identity como string, não dicionário
"""

import os
import re
from pathlib import Path

def fix_auth_resource():
    """Corrige o auth_resource.py para usar JWT corretamente."""
    
    print("🔧 Corrigindo auth_resource.py...")
    
    auth_file = Path("app/resources/auth_resource.py")
    
    if not auth_file.exists():
        print("❌ auth_resource.py não encontrado!")
        return False
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substituir a criação do JWT para usar string simples
        old_jwt_creation = "access_token = create_access_token(identity={'user_id': user.id, 'tenant_id': user.tenant_id})"
        new_jwt_creation = "access_token = create_access_token(identity=str(user.id))"
        
        if old_jwt_creation in content:
            content = content.replace(old_jwt_creation, new_jwt_creation)
            print("   ✅ JWT creation corrigido no login")
        
        # Corrigir também no registro se existir
        old_register_jwt = "access_token = create_access_token(identity={'user_id': new_user.id, 'tenant_id': new_user.tenant_id})"
        new_register_jwt = "access_token = create_access_token(identity=str(new_user.id))"
        
        if old_register_jwt in content:
            content = content.replace(old_register_jwt, new_register_jwt)
            print("   ✅ JWT creation corrigido no registro")
        
        # Corrigir o endpoint /me para buscar o usuário pelo ID
        old_me_endpoint = '''@auth_ns.route('/me')
class UserInfo(Resource):
    @auth_ns.doc('get_user_info')
    @jwt_required() # Protect this endpoint
    @auth_ns.marshal_with(user_info_model)
    def get(self):
        """
        Get information about the currently logged-in user.
        """
        current_user_identity = get_jwt_identity()
        # current_user_identity contains the dictionary payload we put in create_access_token

        return {'user_id': current_user_identity['user_id'], 'tenant_id': current_user_identity['tenant_id']}, 200'''
        
        new_me_endpoint = '''@auth_ns.route('/me')
class UserInfo(Resource):
    @auth_ns.doc('get_user_info')
    @jwt_required() # Protect this endpoint
    @auth_ns.marshal_with(user_info_model)
    def get(self):
        """
        Get information about the currently logged-in user.
        """
        current_user_id = get_jwt_identity()
        
        # Buscar o usuário no banco de dados
        user = db.session.query(Usuario).filter_by(id=int(current_user_id)).first()
        
        if not user:
            auth_ns.abort(404, message='User not found')

        return {'user_id': user.id, 'tenant_id': user.tenant_id}, 200'''
        
        if '@auth_ns.route(\'/me\')' in content:
            # Substituir todo o bloco do endpoint /me
            pattern = r'@auth_ns\.route\(\'/me\'\).*?return.*?, 200'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = content.replace(match.group(0), new_me_endpoint)
                print("   ✅ Endpoint /me corrigido")
        
        # Salvar arquivo corrigido
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ auth_resource.py corrigido!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir auth_resource.py: {e}")
        return False

def fix_animal_resource():
    """Corrige a função get_current_tenant_id no animal_resource.py."""
    
    print("\\n🔧 Corrigindo animal_resource.py...")
    
    animal_file = Path("app/resources/animal_resource.py")
    
    if not animal_file.exists():
        print("❌ animal_resource.py não encontrado!")
        return False
    
    try:
        with open(animal_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Substituir a função get_current_tenant_id
        old_function = '''def get_current_tenant_id():
    """Obtém o tenant_id do JWT token."""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            return identity.get('tenant_id', 1)
        return 1  # Fallback para tenant padrão
    except:
        return 1'''
        
        new_function = '''def get_current_tenant_id():
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
        return 1'''
        
        if 'def get_current_tenant_id():' in content:
            # Encontrar e substituir a função completa
            pattern = r'def get_current_tenant_id\(\):.*?return 1'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = content.replace(match.group(0), new_function)
                print("   ✅ Função get_current_tenant_id corrigida")
        
        # Salvar arquivo corrigido
        with open(animal_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ animal_resource.py corrigido!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir animal_resource.py: {e}")
        return False

def create_jwt_test_script():
    """Cria um script para testar o JWT corrigido."""
    
    print("\\n🧪 Criando script de teste JWT...")
    
    test_script = '''#!/usr/bin/env python3
"""
Script para testar JWT após correções
"""

import requests
import json

BASE_URL = "http://localhost:5000/api/v1"

def test_jwt_flow():
    """Testa o fluxo completo de JWT."""
    
    print("🧪 Testando Fluxo JWT Corrigido")
    print("=" * 40)
    
    # 1. Login
    print("\\n🔐 Fazendo login...")
    login_data = {
        "login": "admin@canil.com",
        "senha": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Erro no login: {response.text}")
        return False
    
    token_data = response.json()
    token = token_data["access_token"]
    print("✅ Login realizado com sucesso!")
    print(f"Token: {token[:50]}...")
    
    # 2. Testar endpoint /me
    print("\\n👤 Testando endpoint /me...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ Endpoint /me funcionando!")
        print(f"User ID: {user_info['user_id']}")
        print(f"Tenant ID: {user_info['tenant_id']}")
        
        # 3. Testar endpoint de animais
        print("\\n🐕 Testando endpoint de animais...")
        response = requests.get(f"{BASE_URL}/animals/", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            animals_data = response.json()
            print("✅ Endpoint de animais funcionando!")
            print(f"Total de animais: {animals_data['_meta']['total']}")
            return True
        else:
            print(f"❌ Erro no endpoint de animais: {response.text}")
            return False
    else:
        print(f"❌ Erro no endpoint /me: {response.text}")
        return False

def test_animal_creation():
    """Testa criação de animal."""
    
    print("\\n➕ Testando criação de animal...")
    
    # Login
    login_data = {"login": "admin@canil.com", "senha": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Falha no login")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Dados do animal
    animal_data = {
        "nome": "TestDog JWT",
        "data_nascimento": "2023-08-01",
        "sexo": "M",
        "cor": "Teste",
        "peso": 10.5,
        "microchip": "TEST" + str(hash("jwt_test"))[-10:],
        "status": "Ativo"
    }
    
    response = requests.post(f"{BASE_URL}/animals/", json=animal_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        animal = response.json()
        print("✅ Animal criado com sucesso!")
        print(f"ID: {animal['id']}, Nome: {animal['nome']}")
        return animal['id']
    else:
        print(f"❌ Erro ao criar animal: {response.text}")
        return None

if __name__ == "__main__":
    try:
        success = test_jwt_flow()
        if success:
            animal_id = test_animal_creation()
            if animal_id:
                print("\\n🎉 Todos os testes passaram!")
            else:
                print("\\n⚠️  JWT funcionando, mas criação de animal falhou")
        else:
            print("\\n💥 Falha nos testes de JWT")
    except Exception as e:
        print(f"\\n❌ Erro durante os testes: {e}")
'''
    
    try:
        with open('test_jwt_fixed.py', 'w', encoding='utf-8') as f:
            f.write(test_script)
        print("✅ Script de teste criado: test_jwt_fixed.py")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar script: {e}")
        return False

def main():
    """Função principal."""
    
    print("🔧 CanilApp - Correção de JWT")
    print("=" * 40)
    
    success = True
    
    # 1. Corrigir auth_resource.py
    if not fix_auth_resource():
        success = False
    
    # 2. Corrigir animal_resource.py
    if not fix_animal_resource():
        success = False
    
    # 3. Criar script de teste
    if not create_jwt_test_script():
        print("⚠️  Falha ao criar script de teste")
    
    if success:
        print("\\n🎉 Correções de JWT aplicadas!")
        print("\\n📋 Próximos passos:")
        print("1. Reinicie o servidor: python run_dev.py")
        print("2. Execute os testes: python test_jwt_fixed.py")
        print("3. Execute os testes de animais: python test_animal_endpoints.py")
        
        print("\\n🧪 Teste manual rápido:")
        print("# 1. Login")
        print("curl -X POST http://localhost:5000/api/v1/auth/login \\\\")
        print('  -H "Content-Type: application/json" \\\\')
        print("  -d '{\"login\": \"admin@canil.com\", \"senha\": \"admin123\"}'")
        print("\\n# 2. Usar token nos animais")
        print("curl -X GET http://localhost:5000/api/v1/animals/ \\\\")
        print('  -H "Authorization: Bearer SEU_TOKEN"')
    else:
        print("\\n💥 Algumas correções falharam!")
    
    return success

if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n\\n👋 Script interrompido!")
        exit(0)
    except Exception as e:
        print(f"\\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)