#!/usr/bin/env python3
"""
Script corrigido para criar usuário admin
Usa EXATAMENTE a mesma estrutura do create_db_simple.py
"""

import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Configuração direta (igual ao create_db_simple.py)
DATABASE_URI = 'postgresql://canil_user:canil123@localhost:5432/canil_db'

def create_admin_fixed():
    """Criar usuário admin com estrutura correta."""
    
    print("🔧 Criação Admin - Estrutura Corrigida...")
    print("=" * 40)
    
    # Configuração Flask (mesmo padrão)
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    print(f"🔌 Conectando...")
    
    try:
        with app.app_context():
            # Testar conexão
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
                print("✅ Conectado!")
            
            # Usar EXATAMENTE os mesmos modelos do create_db_simple.py
            print("📦 Definindo modelos (estrutura original)...")
            
            class Tenant(db.Model):
                __tablename__ = 'tenants'
                id = db.Column(db.Integer, primary_key=True)
                nome = db.Column(db.String(100), nullable=False)
                dominio = db.Column(db.String(100), unique=True, nullable=False)
                cnpj = db.Column(db.String(18), unique=True, nullable=False)
                ativo = db.Column(db.Boolean, default=True)
            
            # IMPORTANTE: Usar exatamente a mesma estrutura que foi criada
            class Usuario(db.Model):
                __tablename__ = 'usuarios'
                id = db.Column(db.Integer, primary_key=True)
                login = db.Column(db.String(128), unique=True, nullable=False)
                senha = db.Column(db.String(255), nullable=False)
                tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
                # NÃO incluir 'perfil' porque não foi criado no create_db_simple.py
            
            print("✅ Modelos definidos!")
            
            # Verificar estrutura da tabela
            print("🔍 Verificando estrutura da tabela usuarios...")
            
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('usuarios')
            
            print("📋 Colunas existentes:")
            for col in columns:
                print(f"   ✓ {col['name']} ({col['type']})")
            
            # Verificar se tenant existe
            tenant = db.session.query(Tenant).filter_by(id=1).first()
            if not tenant:
                print("🏢 Criando tenant...")
                tenant = Tenant(
                    id=1,
                    nome='Canil Principal',
                    dominio='localhost',
                    cnpj='00.000.000/0001-00',
                    ativo=True
                )
                db.session.add(tenant)
                db.session.commit()
                print("✅ Tenant criado!")
            else:
                print("✅ Tenant já existe!")
            
            # Verificar se admin existe
            admin = db.session.query(Usuario).filter_by(login='admin@canil.com').first()
            if admin:
                print("⚠️  Admin já existe! Removendo...")
                db.session.delete(admin)
                db.session.commit()
            
            # Criar admin (SEM campo perfil)
            print("👤 Criando admin...")
            senha_hash = generate_password_hash('admin123')
            
            admin = Usuario(
                login='admin@canil.com',
                senha=senha_hash,
                tenant_id=1
                # NÃO incluir perfil, ativo, etc. porque não existem na tabela
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin criado!")
            print("📧 Login: admin@canil.com")
            print("🔑 Senha: admin123")
            print("🏢 Tenant ID: 1")
            
            # Verificar usuários criados
            print("\\n📋 Usuários no sistema:")
            usuarios = db.session.query(Usuario).all()
            for i, user in enumerate(usuarios, 1):
                print(f"   {i}. {user.login} (Tenant: {user.tenant_id})")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def add_missing_columns():
    """Adicionar colunas que faltam na tabela usuarios."""
    
    print("\\n🔧 Adicionando Colunas Faltantes...")
    print("=" * 40)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                print("🔌 Conectado!")
                
                # Adicionar colunas faltantes usando SQL direto
                print("📝 Adicionando coluna 'perfil'...")
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN perfil VARCHAR(64) DEFAULT 'admin'"))
                    conn.commit()
                    print("✅ Coluna 'perfil' adicionada!")
                except Exception as e:
                    if "already exists" in str(e):
                        print("⚠️  Coluna 'perfil' já existe!")
                    else:
                        print(f"❌ Erro ao adicionar 'perfil': {e}")
                
                print("📝 Adicionando coluna 'ativo'...")
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN DEFAULT true"))
                    conn.commit()
                    print("✅ Coluna 'ativo' adicionada!")
                except Exception as e:
                    if "already exists" in str(e):
                        print("⚠️  Coluna 'ativo' já existe!")
                    else:
                        print(f"❌ Erro ao adicionar 'ativo': {e}")
                
                print("📝 Adicionando coluna 'ultimo_acesso'...")
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN ultimo_acesso TIMESTAMP"))
                    conn.commit()
                    print("✅ Coluna 'ultimo_acesso' adicionada!")
                except Exception as e:
                    if "already exists" in str(e):
                        print("⚠️  Coluna 'ultimo_acesso' já existe!")
                    else:
                        print(f"❌ Erro ao adicionar 'ultimo_acesso': {e}")
                
                print("📝 Adicionando coluna 'permissoes'...")
                try:
                    conn.execute(db.text("ALTER TABLE usuarios ADD COLUMN permissoes JSONB"))
                    conn.commit()
                    print("✅ Coluna 'permissoes' adicionada!")
                except Exception as e:
                    if "already exists" in str(e):
                        print("⚠️  Coluna 'permissoes' já existe!")
                    else:
                        print(f"❌ Erro ao adicionar 'permissoes': {e}")
                
                # Atualizar usuários existentes
                print("🔄 Atualizando usuários existentes...")
                conn.execute(db.text("UPDATE usuarios SET perfil = 'admin' WHERE perfil IS NULL"))
                conn.execute(db.text("UPDATE usuarios SET ativo = true WHERE ativo IS NULL"))
                conn.commit()
                print("✅ Usuários atualizados!")
                
                return True
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def menu_opcoes():
    """Menu de opções."""
    
    print("\\n🐕 CanilApp - Correção de Usuários")
    print("=" * 40)
    print("1. Criar admin (estrutura original)")
    print("2. Adicionar colunas faltantes")
    print("3. Fazer ambos (recomendado)")
    print("4. Sair")
    print("=" * 40)
    
    opcao = input("Escolha uma opção (1-4): ").strip()
    
    if opcao == '1':
        return create_admin_fixed()
    
    elif opcao == '2':
        return add_missing_columns()
    
    elif opcao == '3':
        print("🔧 Executando correção completa...")
        resultado1 = create_admin_fixed()
        resultado2 = add_missing_columns()
        return resultado1 and resultado2
    
    elif opcao == '4':
        print("👋 Até logo!")
        return True
    
    else:
        print("❌ Opção inválida!")
        return False

if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == '--simple':
                success = create_admin_fixed()
            elif sys.argv[1] == '--columns':
                success = add_missing_columns()
            elif sys.argv[1] == '--full':
                success1 = create_admin_fixed()
                success2 = add_missing_columns()
                success = success1 and success2
            else:
                print("Opções: --simple, --columns, --full")
                sys.exit(1)
        else:
            success = menu_opcoes()
        
        if success:
            print("\\n🎉 Operação concluída com sucesso!")
            print("🚀 Teste com: python run_dev.py")
        else:
            print("\\n💥 Falha na operação!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n\\n👋 Script interrompido!")
        sys.exit(0)