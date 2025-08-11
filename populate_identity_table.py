#!/usr/bin/env python3
"""
Script para popular tabelas de identidade (Espécie, Raça, Linhagem)
e atualizar animais existentes com essas informações
"""

import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuração direta
DATABASE_URI = 'postgresql://canil_user:canil123@localhost:5432/canil_db'

def create_identity_tables():
    """Cria as tabelas de identidade se não existirem."""
    
    print("🏗️ Criando Tabelas de Identidade...")
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
                
                # Criar tabela especies
                especies_sql = """
                CREATE TABLE IF NOT EXISTS especies (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(128) UNIQUE NOT NULL,
                    nome_cientifico VARCHAR(128),
                    familia VARCHAR(128)
                )
                """
                
                # Criar tabela racas
                racas_sql = """
                CREATE TABLE IF NOT EXISTS racas (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(128) UNIQUE NOT NULL,
                    especie_id INTEGER REFERENCES especies(id),
                    padrao TEXT,
                    caracteristicas TEXT,
                    peso_medio FLOAT,
                    altura_media FLOAT,
                    temperamento TEXT,
                    origem_geografica VARCHAR(128)
                )
                """
                
                # Criar tabela linhagens
                linhagens_sql = """
                CREATE TABLE IF NOT EXISTS linhagens (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(128) UNIQUE NOT NULL,
                    raca_id INTEGER REFERENCES racas(id),
                    origem VARCHAR(128),
                    caracteristicas TEXT,
                    tipo VARCHAR(64)
                )
                """
                
                # Executar SQLs
                conn.execute(db.text(especies_sql))
                print("   ✅ Tabela especies criada/verificada")
                
                conn.execute(db.text(racas_sql))
                print("   ✅ Tabela racas criada/verificada")
                
                conn.execute(db.text(linhagens_sql))
                print("   ✅ Tabela linhagens criada/verificada")
                
                conn.commit()
                
                return True
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def populate_especies():
    """Popula a tabela de espécies."""
    
    print("\\n🐾 Populando Espécies...")
    print("=" * 30)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    # Definir modelo simples
    class Especie(db.Model):
        __tablename__ = 'especies'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128), nullable=False, unique=True)
        nome_cientifico = db.Column(db.String(128))
        familia = db.Column(db.String(128))
    
    especies_data = [
        {
            'nome': 'Cão',
            'nome_cientifico': 'Canis lupus familiaris',
            'familia': 'Canidae'
        },
        {
            'nome': 'Gato',
            'nome_cientifico': 'Felis catus',
            'familia': 'Felidae'
        },
        {
            'nome': 'Cavalo',
            'nome_cientifico': 'Equus caballus',
            'familia': 'Equidae'
        },
        {
            'nome': 'Coelho',
            'nome_cientifico': 'Oryctolagus cuniculus',
            'familia': 'Leporidae'
        }
    ]
    
    try:
        with app.app_context():
            created_count = 0
            
            for especie_info in especies_data:
                # Verificar se já existe
                existing = db.session.query(Especie).filter_by(nome=especie_info['nome']).first()
                
                if not existing:
                    especie = Especie(**especie_info)
                    db.session.add(especie)
                    created_count += 1
                    print(f"   ✅ {especie_info['nome']} ({especie_info['nome_cientifico']})")
                else:
                    print(f"   ⚠️  {especie_info['nome']} já existe")
            
            db.session.commit()
            print(f"\\n📊 {created_count} espécies criadas")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def populate_racas():
    """Popula a tabela de raças."""
    
    print("\\n🐕 Populando Raças...")
    print("=" * 30)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    # Modelos simples
    class Especie(db.Model):
        __tablename__ = 'especies'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128))
    
    class Raca(db.Model):
        __tablename__ = 'racas'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128), nullable=False, unique=True)
        especie_id = db.Column(db.Integer, db.ForeignKey('especies.id'))
        padrao = db.Column(db.Text)
        caracteristicas = db.Column(db.Text)
        peso_medio = db.Column(db.Float)
        altura_media = db.Column(db.Float)
        temperamento = db.Column(db.Text)
        origem_geografica = db.Column(db.String(128))
    
    # Dados de raças de cães (mais comuns no Brasil)
    racas_data = [
        # Raças de Cães
        {
            'nome': 'Golden Retriever',
            'especie': 'Cão',
            'peso_medio': 32.0,
            'altura_media': 58.0,
            'temperamento': 'Amigável, confiável, inteligente',
            'origem_geografica': 'Escócia',
            'caracteristicas': 'Pelagem dourada, porte médio a grande, excelente para famílias'
        },
        {
            'nome': 'Labrador',
            'especie': 'Cão',
            'peso_medio': 30.0,
            'altura_media': 57.0,
            'temperamento': 'Amigável, ativo, extrovertido',
            'origem_geografica': 'Canadá',
            'caracteristicas': 'Pelagem curta, excelente nadador, muito popular como pet'
        },
        {
            'nome': 'Pastor Alemão',
            'especie': 'Cão',
            'peso_medio': 35.0,
            'altura_media': 62.0,
            'temperamento': 'Corajoso, confiante, versátil',
            'origem_geografica': 'Alemanha',
            'caracteristicas': 'Porte grande, muito inteligente, usado em trabalhos policiais'
        },
        {
            'nome': 'Bulldog Francês',
            'especie': 'Cão',
            'peso_medio': 12.0,
            'altura_media': 32.0,
            'temperamento': 'Adaptável, brincalhão, inteligente',
            'origem_geografica': 'França',
            'caracteristicas': 'Porte pequeno, orelhas de morcego, focinho achatado'
        },
        {
            'nome': 'Poodle',
            'especie': 'Cão',
            'peso_medio': 25.0,
            'altura_media': 45.0,
            'temperamento': 'Inteligente, ativo, elegante',
            'origem_geografica': 'França/Alemanha',
            'caracteristicas': 'Pelagem crespa, hipoalergênico, diversos tamanhos'
        },
        {
            'nome': 'Rottweiler',
            'especie': 'Cão',
            'peso_medio': 50.0,
            'altura_media': 65.0,
            'temperamento': 'Confiante, corajoso, calmo',
            'origem_geografica': 'Alemanha',
            'caracteristicas': 'Porte grande, muito forte, excelente guardião'
        },
        {
            'nome': 'Border Collie',
            'especie': 'Cão',
            'peso_medio': 20.0,
            'altura_media': 50.0,
            'temperamento': 'Inteligente, enérgico, alerta',
            'origem_geografica': 'Reino Unido',
            'caracteristicas': 'Excelente pastor, muito ativo, precisa de estímulo mental'
        },
        {
            'nome': 'Shih Tzu',
            'especie': 'Cão',
            'peso_medio': 6.0,
            'altura_media': 25.0,
            'temperamento': 'Amigável, extrovertido, afetuoso',
            'origem_geografica': 'Tibet/China',
            'caracteristicas': 'Porte pequeno, pelagem longa, excelente companhia'
        },
        {
            'nome': 'Vira-lata',
            'especie': 'Cão',
            'peso_medio': 20.0,
            'altura_media': 45.0,
            'temperamento': 'Variável, geralmente amigável e adaptável',
            'origem_geografica': 'Brasil',
            'caracteristicas': 'Sem raça definida, muito resistente, características variadas'
        },
        
        # Raças de Gatos
        {
            'nome': 'Persa',
            'especie': 'Gato',
            'peso_medio': 4.5,
            'altura_media': 25.0,
            'temperamento': 'Calmo, doce, quieto',
            'origem_geografica': 'Irã',
            'caracteristicas': 'Pelagem longa, focinho achatado, muito elegante'
        },
        {
            'nome': 'Siamês',
            'especie': 'Gato',
            'peso_medio': 4.0,
            'altura_media': 30.0,
            'temperamento': 'Vocal, inteligente, social',
            'origem_geografica': 'Tailândia',
            'caracteristicas': 'Pontos coloridos, olhos azuis, muito comunicativo'
        },
        {
            'nome': 'SRD Gato',
            'especie': 'Gato',
            'peso_medio': 4.0,
            'altura_media': 25.0,
            'temperamento': 'Variável, independente',
            'origem_geografica': 'Brasil',
            'caracteristicas': 'Sem raça definida, muito adaptável'
        }
    ]
    
    try:
        with app.app_context():
            created_count = 0
            
            for raca_info in racas_data:
                # Buscar espécie
                especie = db.session.query(Especie).filter_by(nome=raca_info['especie']).first()
                if not especie:
                    print(f"   ❌ Espécie {raca_info['especie']} não encontrada para {raca_info['nome']}")
                    continue
                
                # Verificar se raça já existe
                existing = db.session.query(Raca).filter_by(nome=raca_info['nome']).first()
                
                if not existing:
                    # Criar raça
                    raca_data = raca_info.copy()
                    raca_data.pop('especie')  # Remover campo especie
                    raca_data['especie_id'] = especie.id
                    
                    raca = Raca(**raca_data)
                    db.session.add(raca)
                    created_count += 1
                    print(f"   ✅ {raca_info['nome']} ({raca_info['especie']})")
                else:
                    print(f"   ⚠️  {raca_info['nome']} já existe")
            
            db.session.commit()
            print(f"\\n📊 {created_count} raças criadas")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def populate_linhagens():
    """Popula a tabela de linhagens."""
    
    print("\\n🧬 Populando Linhagens...")
    print("=" * 30)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    # Modelos simples
    class Raca(db.Model):
        __tablename__ = 'racas'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128))
    
    class Linhagem(db.Model):
        __tablename__ = 'linhagens'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128), nullable=False, unique=True)
        raca_id = db.Column(db.Integer, db.ForeignKey('racas.id'))
        origem = db.Column(db.String(128))
        caracteristicas = db.Column(db.Text)
        tipo = db.Column(db.String(64))
    
    linhagens_data = [
        # Linhagens de Golden Retriever
        {
            'nome': 'Golden Americano',
            'raca': 'Golden Retriever',
            'origem': 'Estados Unidos',
            'tipo': 'Show/Pet',
            'caracteristicas': 'Pelagem mais clara, estrutura mais atlética'
        },
        {
            'nome': 'Golden Inglês',
            'raca': 'Golden Retriever',
            'origem': 'Reino Unido',
            'tipo': 'Show/Working',
            'caracteristicas': 'Pelagem mais escura, estrutura mais robusta'
        },
        
        # Linhagens de Labrador
        {
            'nome': 'Labrador Inglês',
            'raca': 'Labrador',
            'origem': 'Reino Unido',
            'tipo': 'Show',
            'caracteristicas': 'Mais compacto, cabeça mais larga'
        },
        {
            'nome': 'Labrador Americano',
            'raca': 'Labrador',
            'origem': 'Estados Unidos',
            'tipo': 'Working/Field',
            'caracteristicas': 'Mais atlético, focado no trabalho'
        },
        
        # Linhagens de Pastor Alemão
        {
            'nome': 'Pastor Alemão Europeu',
            'raca': 'Pastor Alemão',
            'origem': 'Europa',
            'tipo': 'Working',
            'caracteristicas': 'Foco no trabalho, temperamento equilibrado'
        },
        {
            'nome': 'Pastor Alemão Americano',
            'raca': 'Pastor Alemão',
            'origem': 'Estados Unidos',
            'tipo': 'Show',
            'caracteristicas': 'Mais angulado, foco na beleza'
        },
        
        # Linhagens gerais
        {
            'nome': 'Linhagem Nacional',
            'raca': 'Vira-lata',
            'origem': 'Brasil',
            'tipo': 'Pet',
            'caracteristicas': 'Adaptado ao clima brasileiro, muito resistente'
        },
        {
            'nome': 'Working Line',
            'raca': 'Border Collie',
            'origem': 'Reino Unido',
            'tipo': 'Working',
            'caracteristicas': 'Foco no pastoreio, alta energia'
        },
        {
            'nome': 'Show Line',
            'raca': 'Poodle',
            'origem': 'França',
            'tipo': 'Show',
            'caracteristicas': 'Foco na conformação, pelagem exemplar'
        }
    ]
    
    try:
        with app.app_context():
            created_count = 0
            
            for linhagem_info in linhagens_data:
                # Buscar raça
                raca = db.session.query(Raca).filter_by(nome=linhagem_info['raca']).first()
                if not raca:
                    print(f"   ❌ Raça {linhagem_info['raca']} não encontrada para {linhagem_info['nome']}")
                    continue
                
                # Verificar se linhagem já existe
                existing = db.session.query(Linhagem).filter_by(nome=linhagem_info['nome']).first()
                
                if not existing:
                    # Criar linhagem
                    linhagem_data = linhagem_info.copy()
                    linhagem_data.pop('raca')  # Remover campo raca
                    linhagem_data['raca_id'] = raca.id
                    
                    linhagem = Linhagem(**linhagem_data)
                    db.session.add(linhagem)
                    created_count += 1
                    print(f"   ✅ {linhagem_info['nome']} ({linhagem_info['raca']})")
                else:
                    print(f"   ⚠️  {linhagem_info['nome']} já existe")
            
            db.session.commit()
            print(f"\\n📊 {created_count} linhagens criadas")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def update_animals_with_identity():
    """Atualiza animais existentes com informações de raça, espécie e linhagem."""
    
    print("\\n🔄 Atualizando Animais com Informações de Identidade...")
    print("=" * 50)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    # Modelos simples
    class Especie(db.Model):
        __tablename__ = 'especies'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128))
    
    class Raca(db.Model):
        __tablename__ = 'racas'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128))
        especie_id = db.Column(db.Integer)
    
    class Linhagem(db.Model):
        __tablename__ = 'linhagens'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128))
        raca_id = db.Column(db.Integer)
    
    class Animal(db.Model):
        __tablename__ = 'animais'
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(128))
        cor = db.Column(db.String(64))
        raca_id = db.Column(db.Integer)
        especie_id = db.Column(db.Integer)
        linhagem_id = db.Column(db.Integer)
    
    # Mapeamento baseado na cor/características dos animais existentes
    cor_to_raca_mapping = {
        'Dourado': 'Golden Retriever',
        'Caramelo': 'Labrador',
        'Preto': 'Labrador',
        'Mel': 'Golden Retriever',
        'Chocolate': 'Labrador',
        'Marrom': 'Vira-lata'
    }
    
    try:
        with app.app_context():
            # Buscar espécie cão (assumindo que todos os animais atuais são cães)
            especie_cao = db.session.query(Especie).filter_by(nome='Cão').first()
            if not especie_cao:
                print("❌ Espécie 'Cão' não encontrada!")
                return False
            
            # Buscar todos os animais sem raça definida
            animais = db.session.query(Animal).filter(
                (Animal.raca_id.is_(None)) | (Animal.especie_id.is_(None))
            ).all()
            
            updated_count = 0
            
            for animal in animais:
                print(f"\\n🐕 Processando: {animal.nome} (cor: {animal.cor})")
                
                # Definir espécie como cão
                animal.especie_id = especie_cao.id
                print(f"   📝 Espécie: Cão")
                
                # Definir raça baseada na cor
                raca_nome = cor_to_raca_mapping.get(animal.cor, 'Vira-lata')
                raca = db.session.query(Raca).filter_by(nome=raca_nome).first()
                
                if raca:
                    animal.raca_id = raca.id
                    print(f"   📝 Raça: {raca_nome}")
                    
                    # Definir linhagem padrão baseada na raça
                    if raca_nome == 'Golden Retriever':
                        linhagem = db.session.query(Linhagem).filter_by(nome='Golden Americano').first()
                    elif raca_nome == 'Labrador':
                        linhagem = db.session.query(Linhagem).filter_by(nome='Labrador Inglês').first()
                    elif raca_nome == 'Vira-lata':
                        linhagem = db.session.query(Linhagem).filter_by(nome='Linhagem Nacional').first()
                    else:
                        linhagem = None
                    
                    if linhagem:
                        animal.linhagem_id = linhagem.id
                        print(f"   📝 Linhagem: {linhagem.nome}")
                
                updated_count += 1
            
            db.session.commit()
            print(f"\\n📊 {updated_count} animais atualizados com informações de identidade")
            
            # Mostrar resumo
            print("\\n📋 Resumo dos animais:")
            animais_final = db.session.query(Animal).all()
            for animal in animais_final:
                raca = db.session.query(Raca).filter_by(id=animal.raca_id).first()
                raca_nome = raca.nome if raca else 'Não definida'
                print(f"   🐕 {animal.nome}: {raca_nome}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_summary():
    """Mostra um resumo dos dados criados."""
    
    print("\\n📊 Resumo dos Dados Criados")
    print("=" * 40)
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'temp-key'
    
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                # Contar registros
                especies_count = conn.execute(db.text("SELECT COUNT(*) FROM especies")).scalar()
                racas_count = conn.execute(db.text("SELECT COUNT(*) FROM racas")).scalar()
                linhagens_count = conn.execute(db.text("SELECT COUNT(*) FROM linhagens")).scalar()
                animais_count = conn.execute(db.text("SELECT COUNT(*) FROM animais")).scalar()
                
                print(f"🐾 Espécies: {especies_count}")
                print(f"🐕 Raças: {racas_count}")
                print(f"🧬 Linhagens: {linhagens_count}")
                print(f"🐕 Animais: {animais_count}")
                
                # Mostrar algumas raças por espécie
                print("\\n📋 Raças por Espécie:")
                racas_por_especie = conn.execute(db.text("""
                    SELECT e.nome as especie, r.nome as raca 
                    FROM especies e 
                    JOIN racas r ON e.id = r.especie_id 
                    ORDER BY e.nome, r.nome
                """)).fetchall()
                
                current_especie = None
                for row in racas_por_especie:
                    if row[0] != current_especie:
                        current_especie = row[0]
                        print(f"\\n   🐾 {current_especie}:")
                    print(f"      • {row[1]}")
                
    except Exception as e:
        print(f"❌ Erro ao gerar resumo: {e}")

def main():
    """Função principal."""
    
    print("🐕 CanilApp - População de Dados de Identidade")
    print("=" * 50)
    
    success = True
    
    # 1. Criar tabelas
    print("\\n🔧 Etapa 1: Criar Tabelas")
    if not create_identity_tables():
        success = False
    
    # 2. Popular espécies
    print("\\n🔧 Etapa 2: Popular Espécies")
    if not populate_especies():
        success = False
    
    # 3. Popular raças
    print("\\n🔧 Etapa 3: Popular Raças")
    if not populate_racas():
        success = False
    
    # 4. Popular linhagens
    print("\\n🔧 Etapa 4: Popular Linhagens")
    if not populate_linhagens():
        success = False
    
    # 5. Atualizar animais
    print("\\n🔧 Etapa 5: Atualizar Animais")
    if not update_animals_with_identity():
        print("⚠️  Falha ao atualizar animais")
    
    # 6. Mostrar resumo
    show_summary()
    
    if success:
        print("\\n🎉 População de dados concluída!")
        print("\\n📋 Próximos passos:")
        print("1. Teste os endpoints: /api/v1/identity/especies/")
        print("2. Teste os endpoints: /api/v1/identity/racas/")
        print("3. Teste os endpoints: /api/v1/identity/linhagens/")
        print("4. Verifique animais atualizados: /api/v1/animals/")
        
        print("\\n🧪 Exemplos de teste:")
        print("curl -H 'Authorization: Bearer TOKEN' http://localhost:5000/api/v1/identity/racas/")
        print("curl -H 'Authorization: Bearer TOKEN' http://localhost:5000/api/v1/animals/")
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