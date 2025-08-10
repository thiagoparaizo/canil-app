#!/usr/bin/env python3
"""
Método alternativo para criar tabelas - bypass da configuração
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuração direta
DATABASE_URI = 'postgresql://canil_user:canil123@localhost:5432/canil_db'

def create_db_direct():
    """Criar banco usando configuração direta."""
    
    print("🐕 Método Direto - Criando Tabelas...")
    print("=" * 50)
    
    # Criar app Flask simples
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    # Criar nova instância SQLAlchemy (não importar do app)
    db = SQLAlchemy(app)
    
    print(f"🔌 Conectando: {DATABASE_URI}")
    
    try:
        with app.app_context():
            # Testar conexão (SQLAlchemy 2.0+)
            with db.engine.connect() as conn:
                result = conn.execute(db.text('SELECT 1'))
                print("✅ Conexão estabelecida!")
            
            # Agora definir modelos diretamente aqui
            print("📦 Criando modelos...")
            
            class Tenant(db.Model):
                __tablename__ = 'tenants'
                id = db.Column(db.Integer, primary_key=True)
                nome = db.Column(db.String(100), nullable=False)
                dominio = db.Column(db.String(100), unique=True, nullable=False)
                cnpj = db.Column(db.String(18), unique=True, nullable=False)
                ativo = db.Column(db.Boolean, default=True)
            
            class Animal(db.Model):
                __tablename__ = 'animais'
                id = db.Column(db.Integer, primary_key=True)
                nome = db.Column(db.String(128), nullable=False)
                data_nascimento = db.Column(db.Date, nullable=False)
                sexo = db.Column(db.String(10), nullable=False)
                tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
            
            class Usuario(db.Model):
                __tablename__ = 'usuarios'
                id = db.Column(db.Integer, primary_key=True)
                login = db.Column(db.String(128), unique=True, nullable=False)
                senha = db.Column(db.String(255), nullable=False)
                tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
            
            print("✅ Modelos criados!")
            print(f"🔍 Tabelas no metadata: {list(db.metadata.tables.keys())}")
            
            # Criar todas as tabelas
            print("🔨 Criando tabelas...")
            db.create_all()
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if tables:
                print("✅ Tabelas criadas com sucesso!")
                print(f"\n📋 {len(tables)} tabelas:")
                for table in sorted(tables):
                    print(f"   ✓ {table}")
            else:
                print("⚠️  Nenhuma tabela foi criada!")
                
            return len(tables) > 0
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_db_direct()
    if success:
        print("\n🎉 Banco configurado com sucesso!")
        print("🚀 Execute: python run_dev.py")
    else:
        print("\n💥 Falha na configuração")
        sys.exit(1)