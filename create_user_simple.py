#!/usr/bin/env python3
"""
Script para criar usuários - método direto (bypass da configuração)
Baseado na mesma lógica do create_db_simple.py
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime

# Configuração direta (mesma do create_db_simple.py)
DATABASE_URI = 'postgresql://canil_user:canil123@localhost:5432/canil_db'

def create_user_direct():
    """Criar usuário usando configuração direta."""
    
    print("👤 Método Direto - Criando Usuários...")
    print("=" * 50)
    
    # Criar app Flask simples (mesma estrutura do create_db_simple.py)
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    # Criar nova instância SQLAlchemy (não importar do app)
    db = SQLAlchemy(app)
    
    print(f"🔌 Conectando: {DATABASE_URI}")
    
    try:
        with app.app_context():
            # Testar conexão
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT 1'))
                print("✅ Conexão estabelecida!")
            
            # Definir modelos necessários (mesmo padrão do create_db_simple.py)
            print("📦 Definindo modelos...")
            
            class Tenant(db.Model):
                __tablename__ = 'tenants'
                id = db.Column(db.Integer, primary_key=True)
                nome = db.Column(db.String(100), nullable=False)
                dominio = db.Column(db.String(100), unique=True, nullable=False)
                cnpj = db.Column(db.String(18), unique=True, nullable=False)
                ativo = db.Column(db.Boolean, default=True)
                data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
                plano = db.Column(db.String(50), default='basico')
                status = db.Column(db.String(20), default='ativo')
            
            class Usuario(db.Model):
                __tablename__ = 'usuarios'
                id = db.Column(db.Integer, primary_key=True)
                login = db.Column(db.String(128), unique=True, nullable=False)
                senha = db.Column(db.String(255), nullable=False)
                perfil = db.Column(db.String(50), default='admin')
                ativo = db.Column(db.Boolean, default=True)
                ultimo_acesso = db.Column(db.DateTime)
                tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
                data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
            
            print("✅ Modelos definidos!")
            
            # 1. Verificar se já existe tenant padrão, se não, criar
            print("🏢 Verificando tenant padrão...")
            tenant = db.session.query(Tenant).filter_by(id=1).first()
            
            if not tenant:
                print("📝 Criando tenant padrão...")
                tenant = Tenant(
                    id=1,
                    nome='Canil Principal',
                    dominio='localhost',
                    cnpj='00.000.000/0001-00',
                    ativo=True,
                    plano='premium',
                    status='ativo'
                )
                db.session.add(tenant)
                db.session.commit()
                print("✅ Tenant padrão criado!")
            else:
                print("✅ Tenant padrão já existe!")
            
            # 2. Criar usuário admin
            print("👤 Criando usuário administrador...")
            
            # Verificar se admin já existe
            admin_existente = db.session.query(Usuario).filter_by(login='admin@canil.com').first()
            
            if admin_existente:
                print("⚠️  Usuário admin já existe!")
                resposta = input("Deseja recriar? (s/N): ").lower().strip()
                if resposta != 's':
                    print("❌ Operação cancelada!")
                    return False
                else:
                    db.session.delete(admin_existente)
                    db.session.commit()
                    print("🗑️  Usuário admin removido!")
            
            # Criar novo admin
            senha_hash = generate_password_hash('admin123')
            
            admin = Usuario(
                login='admin@canil.com',
                senha=senha_hash,
                perfil='admin',
                ativo=True,
                tenant_id=tenant.id,
                ultimo_acesso=None  # Será definido no primeiro login
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário administrador criado com sucesso!")
            print(f"📧 Login: admin@canil.com")
            print(f"🔑 Senha: admin123")
            print(f"🏢 Tenant: {tenant.nome} (ID: {tenant.id})")
            
            # 3. Criar usuário de teste (opcional)
            print("\\n🧪 Criando usuário de teste...")
            
            usuario_teste = db.session.query(Usuario).filter_by(login='teste@canil.com').first()
            if not usuario_teste:
                senha_teste_hash = generate_password_hash('teste123')
                
                teste = Usuario(
                    login='teste@canil.com',
                    senha=senha_teste_hash,
                    perfil='operador',
                    ativo=True,
                    tenant_id=tenant.id
                )
                
                db.session.add(teste)
                db.session.commit()
                
                print("✅ Usuário de teste criado!")
                print(f"📧 Login: teste@canil.com")
                print(f"🔑 Senha: teste123")
                print(f"👤 Perfil: operador")
            else:
                print("⚠️  Usuário de teste já existe!")
            
            # 4. Listar usuários criados
            print("\\n📋 Usuários no sistema:")
            usuarios = db.session.query(Usuario).all()
            for i, user in enumerate(usuarios, 1):
                print(f"   {i}. {user.login} - {user.perfil} (Tenant: {user.tenant_id}) - {'Ativo' if user.ativo else 'Inativo'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_custom_user():
    """Criar usuário personalizado."""
    
    print("\\n👤 Criar Usuário Personalizado")
    print("=" * 30)
    
    login = input("📧 Login (email): ").strip()
    if not login:
        print("❌ Login é obrigatório!")
        return False
    
    senha = input("🔑 Senha: ").strip()
    if not senha:
        print("❌ Senha é obrigatória!")
        return False
    
    perfil = input("👤 Perfil (admin/operador/veterinario) [operador]: ").strip() or 'operador'
    
    # Usar a mesma estrutura de conexão
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # Definir modelos novamente (necessário para este contexto)
            class Tenant(db.Model):
                __tablename__ = 'tenants'
                id = db.Column(db.Integer, primary_key=True)
                nome = db.Column(db.String(100), nullable=False)
            
            class Usuario(db.Model):
                __tablename__ = 'usuarios'
                id = db.Column(db.Integer, primary_key=True)
                login = db.Column(db.String(128), unique=True, nullable=False)
                senha = db.Column(db.String(255), nullable=False)
                perfil = db.Column(db.String(50), default='operador')
                ativo = db.Column(db.Boolean, default=True)
                tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
                data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
            
            # Verificar se usuário já existe
            usuario_existente = db.session.query(Usuario).filter_by(login=login).first()
            if usuario_existente:
                print(f"❌ Usuário {login} já existe!")
                return False
            
            # Verificar tenant padrão
            tenant = db.session.query(Tenant).filter_by(id=1).first()
            if not tenant:
                print("❌ Tenant padrão não encontrado! Execute create_user_direct() primeiro.")
                return False
            
            # Criar usuário
            senha_hash = generate_password_hash(senha)
            
            novo_usuario = Usuario(
                login=login,
                senha=senha_hash,
                perfil=perfil,
                ativo=True,
                tenant_id=tenant.id
            )
            
            db.session.add(novo_usuario)
            db.session.commit()
            
            print(f"✅ Usuário {login} criado com sucesso!")
            print(f"👤 Perfil: {perfil}")
            print(f"🏢 Tenant: {tenant.id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return False

def menu_principal():
    """Menu principal do script."""
    
    print("\\n🐕 CanilApp - Gerenciador de Usuários")
    print("=" * 40)
    print("1. Criar usuários padrão (admin + teste)")
    print("2. Criar usuário personalizado")
    print("3. Sair")
    print("=" * 40)
    
    opcao = input("Escolha uma opção (1-3): ").strip()
    
    if opcao == '1':
        sucesso = create_user_direct()
        if sucesso:
            print("\\n🎉 Usuários padrão criados com sucesso!")
        else:
            print("\\n💥 Falha na criação dos usuários!")
    
    elif opcao == '2':
        create_custom_user()
    
    elif opcao == '3':
        print("👋 Até logo!")
        sys.exit(0)
    
    else:
        print("❌ Opção inválida!")

if __name__ == '__main__':
    try:
        # Se executado com argumentos, executar criação direta
        if len(sys.argv) > 1 and sys.argv[1] == '--direct':
            success = create_user_direct()
            if success:
                print("\\n🎉 Usuários criados com sucesso!")
                print("🚀 Agora execute: python run_dev.py")
            else:
                print("\\n💥 Falha na criação")
                sys.exit(1)
        else:
            # Menu interativo
            while True:
                menu_principal()
                print("\\n" + "="*40)
                continuar = input("Deseja continuar? (S/n): ").lower().strip()
                if continuar == 'n':
                    break
            
            print("\\n👋 Script finalizado!")
    
    except KeyboardInterrupt:
        print("\\n\\n👋 Script interrompido pelo usuário!")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ Erro inesperado: {e}")
        sys.exit(1)