# 🐕 API de Animais - Documentação Completa

## 🎯 Visão Geral

A API de animais oferece um CRUD completo com isolamento por tenant, paginação, filtros e funcionalidades avançadas.

**Base URL:** `http://localhost:5000/api/v1/animals/`

**Autenticação:** Bearer Token (JWT) obrigatório para todos os endpoints

## 🔐 Autenticação

Primeiro, obtenha o token de acesso:

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin@canil.com", "senha": "admin123"}'

# Resposta: {"access_token": "eyJ..."}
```

Use o token em todas as requisições:
```bash
-H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 📋 Endpoints Disponíveis

### 1. **Listar Animais** - `GET /animals/`

Lista todos os animais do tenant atual com paginação e filtros.

**Parâmetros de Query:**
- `page` (int): Número da página (padrão: 1)
- `per_page` (int): Itens por página (padrão: 10, máx: 100)
- `search` (string): Busca por nome, microchip, pedigree, cor, origem
- `sexo` (string): Filtrar por sexo ('M' ou 'F')
- `status` (string): Filtrar por status
- `ativo` (boolean): Filtrar por animais ativos/inativos

**Exemplo:**
```bash
# Listar todos
curl -X GET "http://localhost:5000/api/v1/animals/" \
  -H "Authorization: Bearer SEU_TOKEN"

# Com filtros
curl -X GET "http://localhost:5000/api/v1/animals/?sexo=M&page=1&per_page=5" \
  -H "Authorization: Bearer SEU_TOKEN"

# Buscar por nome
curl -X GET "http://localhost:5000/api/v1/animals/?search=Rex" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:**
```json
{
  "items": [
    {
      "id": 1,
      "nome": "Rex",
      "microchip": "123456789012345",
      "data_nascimento": "2023-01-15",
      "sexo": "M",
      "cor": "Dourado",
      "peso": 25.5,
      "status": "Ativo",
      "ativo": true,
      "tipo_animal": "Reprodutor",
      "tenant_id": 1
    }
  ],
  "_meta": {
    "total": 5,
    "pages": 1,
    "page": 1,
    "per_page": 10,
    "has_next": false,
    "has_prev": false
  }
}
```

### 2. **Criar Animal** - `POST /animals/`

Cria um novo animal para o tenant atual.

**Campos Obrigatórios:**
- `nome` (string): Nome do animal
- `data_nascimento` (string): Data no formato YYYY-MM-DD
- `sexo` (string): 'M' ou 'F'

**Campos Opcionais:**
- `microchip` (string): ID do microchip (único)
- `pedigree` (string): Número do pedigree
- `cor` (string): Cor do animal
- `peso` (float): Peso em kg
- `altura` (float): Altura em cm
- `status` (string): Status (padrão: 'Ativo')
- `origem` (string): Origem do animal
- `data_aquisicao` (string): Data de aquisição (YYYY-MM-DD)
- `valor_aquisicao` (float): Valor de aquisição
- `observacoes` (string): Observações gerais
- `tipo_animal` (string): 'Animal', 'Matriz', 'Reprodutor', 'Filhote'
- `raca_id`, `especie_id`, `linhagem_id` (int): IDs de relacionamentos
- `mother_id`, `father_id` (int): IDs dos pais

**Exemplo:**
```bash
curl -X POST "http://localhost:5000/api/v1/animals/" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Buddy",
    "data_nascimento": "2023-06-15",
    "sexo": "M",
    "cor": "Marrom",
    "peso": 15.2,
    "microchip": "999888777666555",
    "status": "Ativo",
    "tipo_animal": "Animal",
    "observacoes": "Animal muito dócil"
  }'
```

**Resposta:** Status 201 + dados do animal criado

### 3. **Buscar Animal** - `GET /animals/{id}`

Obtém um animal específico por ID (apenas do tenant atual).

**Exemplo:**
```bash
curl -X GET "http://localhost:5000/api/v1/animals/1" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:** Status 200 + dados do animal ou 404 se não encontrado

### 4. **Atualizar Animal** - `PUT /animals/{id}`

Atualiza um animal específico (apenas do tenant atual).

**Exemplo:**
```bash
curl -X PUT "http://localhost:5000/api/v1/animals/1" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "peso": 26.0,
    "observacoes": "Peso atualizado após consulta veterinária"
  }'
```

**Resposta:** Status 200 + dados atualizados

### 5. **Deletar Animal** - `DELETE /animals/{id}`

Remove um animal específico (apenas do tenant atual).

**Exemplo:**
```bash
curl -X DELETE "http://localhost:5000/api/v1/animals/1" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:** Status 204 (sem conteúdo) ou 409 se há dependências

### 6. **Alternar Status** - `PATCH /animals/{id}/toggle-status`

Alterna o status ativo/inativo do animal.

**Exemplo:**
```bash
curl -X PATCH "http://localhost:5000/api/v1/animals/1/toggle-status" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:** Status 200 + dados do animal com status alterado

### 7. **Estatísticas** - `GET /animals/stats`

Obtém estatísticas dos animais do tenant atual.

**Exemplo:**
```bash
curl -X GET "http://localhost:5000/api/v1/animals/stats" \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:**
```json
{
  "total": 5,
  "ativos": 4,
  "inativos": 1,
  "machos": 3,
  "femeas": 2,
  "por_status": {
    "Ativo": 4,
    "Reservado": 1
  },
  "tenant_id": 1
}
```

## 🛡️ Segurança e Isolamento

### **Isolamento por Tenant**
- Todos os endpoints filtram automaticamente por `tenant_id`
- Impossível acessar animais de outros tenants
- Token JWT contém informações do tenant

### **Validações**
- Campos obrigatórios validados
- Formatos de data validados (YYYY-MM-DD)
- Sexo deve ser 'M' ou 'F'
- Microchip deve ser único
- Peso e altura devem ser números positivos

### **Tratamento de Erros**
- **400**: Dados inválidos ou faltando
- **401**: Token inválido ou expirado
- **403**: Sem permissão
- **404**: Animal não encontrado
- **409**: Conflito (ex: microchip duplicado)
- **500**: Erro interno do servidor

## 🧪 Testando a API

### **1. Script Automatizado**
```bash
# Execute após configurar o banco
python create_animal_tables.py

# Execute após iniciar o servidor
python test_animal_endpoints.py
```

### **2. Teste Manual Completo**
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin@canil.com", "senha": "admin123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# 2. Listar animais
curl -X GET "http://localhost:5000/api/v1/animals/" \
  -H "Authorization: Bearer $TOKEN"

# 3. Criar animal
curl -X POST "http://localhost:5000/api/v1/animals/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Test Dog",
    "data_nascimento": "2023-01-01",
    "sexo": "M",
    "cor": "Preto"
  }'

# 4. Estatísticas
curl -X GET "http://localhost:5000/api/v1/animals/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Casos de Uso Comuns

### **Buscar animais disponíveis para venda**
```bash
curl -X GET "http://localhost:5000/api/v1/animals/?status=Ativo&ativo=true" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### **Listar apenas reprodutores machos**
```bash
curl -X GET "http://localhost:5000/api/v1/animals/?sexo=M&search=Reprodutor" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### **Buscar por microchip específico**
```bash
curl -X GET "http://localhost:5000/api/v1/animals/?search=123456789012345" \
  -H "Authorization: Bearer SEU_TOKEN"
```

### **Paginação para muitos animais**
```bash
curl -X GET "http://localhost:5000/api/v1/animals/?page=2&per_page=20" \
  -H "Authorization: Bearer SEU_TOKEN"
```

## 🚀 Setup Rápido

### **1. Configurar estrutura do banco:**
```bash
python create_animal_tables.py
```

### **2. Iniciar servidor:**
```bash
python run_dev.py
```

### **3. Testar endpoints:**
```bash
python test_animal_endpoints.py
```

## 📝 Notas de Desenvolvimento

### **Estrutura da Tabela `animais`**
A tabela foi expandida com as seguintes colunas:
- Dados básicos: nome, data_nascimento, sexo, tenant_id
- Identificação: microchip (único), pedigree
- Físico: cor, peso, altura
- Status: status, ativo, tipo_animal
- Comercial: origem, data_aquisicao, valor_aquisicao
- Relacionamentos: raca_id, especie_id, linhagem_id, mother_id, father_id
- Metadados: observacoes, data_criacao, data_atualizacao

### **Índices Criados**
- `idx_animais_tenant_id`: Performance para isolamento
- `idx_animais_nome`: Busca por nome
- `idx_animais_sexo`: Filtro por sexo
- `idx_animais_status`: Filtro por status
- `idx_animais_ativo`: Filtro por animais ativos
- `idx_animais_microchip`: Busca por microchip
- `idx_animais_data_nascimento`: Ordenação por idade

### **Próximas Funcionalidades**
- Upload de fotos dos animais
- Histórico de mudanças
- Relatórios em PDF
- Integração com sistema de reprodução
- APIs para mobile

---

**🎉 CRUD de Animais implementado com sucesso!**

*Isolamento por tenant ✅ | Validações ✅ | Paginação ✅ | Filtros ✅ | Testes ✅*