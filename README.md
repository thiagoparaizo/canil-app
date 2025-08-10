# 🐕 Sistema de Gerenciamento de Canil

Um sistema SaaS completo para gerenciamento de canis, incluindo controle de animais, reprodução, saúde, vendas e multi-tenancy.

## 🚀 Quick Start

### 1. Pré-requisitos

- Python 3.9+
- PostgreSQL 12+
- Redis (para cache e tasks)
- Git

### 2. Instalação

```bash
# Clone o repositório
git clone <repository-url>
cd canil-management-system

# Crie o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração do Banco de Dados

```bash
# Acesse o PostgreSQL
sudo -u postgres psql

# Crie o banco de dados
CREATE DATABASE canil_db;
CREATE USER canil_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE canil_db TO canil_user;
\q
```

### 4. Configuração do Ambiente

```bash
# Copie o template de variáveis de ambiente
cp .env.example .env

# Edite o arquivo .env com suas configurações
nano .env
```

### 5. Inicialização

```bash
# Execute as migrações do banco
flask db upgrade

# Ou inicialize o banco (primeira vez)
flask init-db

# Crie um usuário admin
flask create-admin

# Inicie o servidor de desenvolvimento
python wsgi.py
```

## 📁 Estrutura do Projeto

```
canil-management-system/
├── app/                          # Aplicação principal
│   ├── __init__.py              # Application Factory
│   ├── config.py                # Configurações
│   ├── models/                  # Modelos do banco de dados
│   │   ├── animal.py           # Modelos de animais
│   │   ├── breeding.py         # Modelos de reprodução
│   │   ├── health.py           # Modelos de saúde
│   │   ├── person.py           # Modelos de pessoas
│   │   ├── transaction.py      # Modelos de transações
│   │   ├── tenant.py           # Modelo de tenant
│   │   ├── system.py           # Modelos do sistema
│   │   ├── media.py            # Modelos de mídia
│   │   └── saas.py             # Modelos SaaS
│   ├── resources/              # APIs REST (Controllers)
│   │   ├── auth_resource.py    # Autenticação
│   │   ├── animal_resource.py  # Gestão de animais
│   │   ├── breeding_resource.py # Reprodução
│   │   ├── health_resource.py  # Saúde veterinária
│   │   └── ...
│   ├── services/               # Lógica de negócio
│   │   ├── tenant_service.py   # Gestão de tenants
│   │   ├── genealogy_service.py # Cálculos genéticos
│   │   ├── media_service.py    # Gestão de arquivos
│   │   └── payment_service.py  # Pagamentos
│   ├── middleware/             # Middlewares
│   │   └── tenant_middleware.py # Multi-tenancy
│   └── utils/                  # Utilitários
├── migrations/                  # Migrações do banco
├── logs/                       # Logs da aplicação
├── wsgi.py                     # Entry point principal
├── requirements.txt            # Dependências Python
├── .env.example               # Template de configuração
└── README.md                  # Esta documentação
```

## 🔧 Comandos Úteis

### Desenvolvimento

```bash
# Iniciar servidor de desenvolvimento
python wsgi.py

# Ou usando Flask CLI
flask run

# Executar com debug
FLASK_DEBUG=true python wsgi.py
```

### Banco de Dados

```bash
# Criar nova migração
flask db migrate -m "Descrição da migração"

# Aplicar migrações
flask db upgrade

# Reverter migração
flask db downgrade

# Inicializar banco (primeira vez)
flask init-db

# Criar usuário admin
flask create-admin
```

### Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=app

# Executar testes específicos
pytest tests/test_animal.py

# Executar com verbose
pytest -v
```

### Celery (Tarefas Assíncronas)

```bash
# Iniciar worker do Celery
celery -A app.celery_worker worker --loglevel=info

# Iniciar Beat (scheduler)
celery -A app.celery_worker beat --loglevel=info

# Monitorar tarefas
celery -A app.celery_worker flower
```

## 🔐 Autenticação e Autorização

### Endpoints Públicos
- `POST /api/v1/auth/register` - Registro de usuário
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/reset-password/request` - Solicitar reset de senha
- `GET /health` - Health check

### Endpoints Protegidos (Requerem JWT)
- `GET /api/v1/auth/me` - Informações do usuário atual
- `GET /api/v1/animals/` - Listar animais
- `POST /api/v1/animals/` - Criar animal
- Todos os outros endpoints da API

### Como usar JWT

```bash
# 1. Fazer login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "user@example.com", "senha": "password123"}'

# Resposta contém o token:
# {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}

# 2. Usar o token nas requisições
curl -X GET http://localhost:5000/api/v1/animals/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## 🏢 Multi-tenancy

O sistema suporta múltiplos inquilinos (canis) através de:

### Detecção por Subdomínio
- `canil1.localhost` → Tenant ID 1
- `canil2.localhost` → Tenant ID 2
- `localhost` → Schema público

### Isolamento de Dados
- Cada tenant tem seus próprios dados
- Middleware automaticamente filtra por `tenant_id`
- Schemas PostgreSQL separados (futuro)

## 📊 API Documentation

### Swagger/OpenAPI
Acesse a documentação interativa em: `http://localhost:5000/docs/`

### Principais Recursos

#### 🐕 Animais
```
GET    /api/v1/animals/          # Listar animais
POST   /api/v1/animals/          # Criar animal
GET    /api/v1/animals/{id}      # Obter animal
PUT    /api/v1/animals/{id}      # Atualizar animal
DELETE /api/v1/animals/{id}      # Deletar animal
```

#### 🧬 Reprodução
```
GET    /api/v1/breeding/ninhadas/        # Listar ninhadas
POST   /api/v1/breeding/ninhadas/        # Criar ninhada
GET    /api/v1/breeding/cruzamentos/     # Listar cruzamentos
POST   /api/v1/breeding/cruzamentos/     # Criar cruzamento
```

#### 🏥 Saúde
```
GET    /api/v1/health/registros_veterinarios/  # Registros veterinários
GET    /api/v1/health/vacinacoes/              # Vacinações
GET    /api/v1/health/vermifugacoes/           # Vermifugações
```

#### 💰 Transações
```
GET    /api/v1/transactions/vendas/      # Vendas
GET    /api/v1/transactions/adocoes/     # Adoções
GET    /api/v1/transactions/reservas/    # Reservas
```

## 🔧 Configuração Detalhada

### Variáveis de Ambiente Obrigatórias

```bash
# Segurança
SECRET_KEY=sua-chave-secreta-muito-forte
JWT_SECRET_KEY=sua-chave-jwt-muito-forte

# Banco de dados
DB_USER=canil_user
DB_PASSWORD=sua-senha-forte
DB_HOST=localhost
DB_PORT=5432
DB_NAME=canil_db
```

### Variáveis Opcionais

```bash
# Dropbox (para arquivos)
DROPBOX_ACCESS_TOKEN=seu-token-dropbox
DROPBOX_APP_KEY=sua-app-key
DROPBOX_APP_SECRET=seu-app-secret

# Mercado Pago (para pagamentos)
MERCADO_PAGO_ACCESS_TOKEN=seu-token-mp

# Email (para notificações)
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-app
```

## 🚀 Deploy em Produção

### Usando Gunicorn

```bash
# Instalar gunicorn
pip install gunicorn

# Executar em produção
gunicorn --bind 0.0.0.0:8000 wsgi:app

# Com workers
gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
```

### Usando Docker

```bash
# Build da imagem
docker build -t canil-app .

# Executar container
docker run -p 8000:8000 canil-app
```

### Configurações de Produção

```bash
# Definir ambiente
export FLASK_ENV=production

# Usar configuração segura
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
export JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')

# Configurar banco em produção
export DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🔍 Troubleshooting

### Problemas Comuns

#### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar conexão
psql -h localhost -U canil_user -d canil_db
```

#### Erro de Migração
```bash
# Resetar migrações (CUIDADO: perde dados)
flask db stamp head
flask db migrate
flask db upgrade
```

#### Erro de JWT
```bash
# Verificar se JWT_SECRET_KEY está definido
echo $JWT_SECRET_KEY

# Recriar token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "seu-usuario", "senha": "sua-senha"}'
```

#### Erro de Tenant
```bash
# Verificar configuração de domínio
echo $MAIN_DOMAIN

# Testar com subdomínio
curl -H "Host: canil1.localhost" http://localhost:5000/api/v1/animals/
```

## 📈 Monitoramento

### Logs
```bash
# Ver logs em tempo real
tail -f logs/canil_app.log

# Ver logs específicos
grep "ERROR" logs/canil_app.log
```

### Health Check
```bash
# Verificar saúde da aplicação
curl http://localhost:5000/health
```

### Métricas
- CPU, Memória: Use ferramentas como htop, free
- Banco de dados: pg_stat_activity
- Redis: redis-cli info

## 🤝 Contribuição

### Setup para Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Configurar pre-commit hooks
pre-commit install

# Executar linters
flake8 app/
black app/
```

### Estrutura de Commits
```
feat: adiciona nova funcionalidade
fix: corrige bug
docs: atualiza documentação
test: adiciona testes
refactor: refatora código
```

## 📝 TODO / Roadmap

### Fase 1 - Correções Críticas ✅
- [x] Corrigir Application Factory
- [x] Configurar entry points
- [ ] Corrigir modelos Tenant
- [ ] Implementar middleware seguro

### Fase 2 - Funcionalidades Core 🔄
- [ ] Implementar cálculos genéticos
- [ ] Sistema completo de arquivos
- [ ] Integrações com APIs externas
- [ ] Sistema de notificações

### Fase 3 - Funcionalidades Avançadas 📋
- [ ] Dashboard analytics
- [ ] Relatórios PDF
- [ ] API mobile
- [ ] Sistema de backup automático

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação
2. Consulte os logs de erro
3. Abra uma issue no repositório

**Versão:** 1.0.0  
**Última atualização:** Dezembro 2024