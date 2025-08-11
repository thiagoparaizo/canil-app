#!/usr/bin/env python3
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
    print("\n🔐 Fazendo login...")
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
    print("\n👤 Testando endpoint /me...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ Endpoint /me funcionando!")
        print(f"User ID: {user_info['user_id']}")
        print(f"Tenant ID: {user_info['tenant_id']}")
        
        # 3. Testar endpoint de animais
        print("\n🐕 Testando endpoint de animais...")
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
    
    print("\n➕ Testando criação de animal...")
    
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
                print("\n🎉 Todos os testes passaram!")
            else:
                print("\n⚠️  JWT funcionando, mas criação de animal falhou")
        else:
            print("\n💥 Falha nos testes de JWT")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
