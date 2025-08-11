#!/usr/bin/env python3
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
    print("\n📋 Testando Listagem de Animais...")
    
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
    print("\n➕ Testando Criação de Animal...")
    
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
    print(f"\n🔍 Testando Busca do Animal ID {animal_id}...")
    
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
    print(f"\n✏️ Testando Atualização do Animal ID {animal_id}...")
    
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
    print("\n📊 Testando Estatísticas...")
    
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
    print(f"\n🔄 Testando Toggle Status do Animal ID {animal_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.patch(f"{ANIMALS_URL}{animal_id}/toggle-status", headers=headers)
    print(f"PATCH /animals/{animal_id}/toggle-status - Status: {response.status_code}")
    
    if response.status_code == 200:
        animal = response.json()
        status = "ativo" if animal['ativo'] else "inativo"
        print(f"   ✅ Status alterado para: {status}")

def test_delete_animal(token, animal_id):
    """Testa exclusão de animal."""
    print(f"\n🗑️ Testando Exclusão do Animal ID {animal_id}...")
    
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
        print("\n❓ Deseja deletar o animal de teste?")
        resposta = input("Digite 's' para deletar: ").lower().strip()
        if resposta == 's':
            test_delete_animal(token, animal_id)
    
    print("\n🎉 Testes concluídos!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Testes interrompidos!")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
