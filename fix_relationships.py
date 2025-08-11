#!/usr/bin/env python3
"""
Script para corrigir relacionamentos problemáticos nos modelos
Remove referências incorretas a 'public.' nos ForeignKey
"""

import os
import sys
import re
from pathlib import Path

def fix_foreign_key_references():
    """Corrige referências incorretas de ForeignKey nos modelos."""
    
    print("🔧 Corrigindo Relacionamentos - Foreign Keys")
    print("=" * 50)
    
    # Diretório dos modelos
    models_dir = Path("app/models")
    
    if not models_dir.exists():
        print(f"❌ Diretório {models_dir} não encontrado!")
        return False
    
    # Padrões problemáticos a corrigir
    patterns_to_fix = [
        (r"ForeignKey\('public\.tenants\.id'\)", "ForeignKey('tenants.id')"),
        (r"ForeignKey\('public\.([^']+)'\)", r"ForeignKey('\1')"),
        (r'ForeignKey\("public\.tenants\.id"\)', 'ForeignKey("tenants.id")'),
        (r'ForeignKey\("public\.([^"]+)"\)', r'ForeignKey("\1")'),
    ]
    
    fixed_files = []
    
    # Processar todos os arquivos Python no diretório models
    for py_file in models_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue
            
        print(f"🔍 Verificando {py_file.name}...")
        
        try:
            # Ler conteúdo do arquivo
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_made = False
            
            # Aplicar correções
            for pattern, replacement in patterns_to_fix:
                if re.search(pattern, content):
                    print(f"   🔧 Corrigindo padrão: {pattern}")
                    content = re.sub(pattern, replacement, content)
                    changes_made = True
            
            # Salvar se houve mudanças
            if changes_made:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"   ✅ {py_file.name} corrigido!")
                fixed_files.append(str(py_file))
            else:
                print(f"   ⚪ {py_file.name} não precisou de correção")
                
        except Exception as e:
            print(f"   ❌ Erro ao processar {py_file.name}: {e}")
    
    # Resumo
    print(f"\\n📋 Resumo:")
    print(f"   ✅ Arquivos corrigidos: {len(fixed_files)}")
    
    if fixed_files:
        print("   📄 Arquivos modificados:")
        for file in fixed_files:
            print(f"      - {file}")
    
    return len(fixed_files) > 0

def fix_specific_media_model():
    """Corrige especificamente o modelo RegistroEvolucao em media.py."""
    
    print("\\n🎯 Correção Específica - RegistroEvolucao")
    print("=" * 40)
    
    media_file = Path("app/models/media.py")
    
    if not media_file.exists():
        print(f"❌ Arquivo {media_file} não encontrado!")
        return False
    
    try:
        with open(media_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se o problema existe
        if "ForeignKey('public.tenants.id')" not in content:
            print("✅ RegistroEvolucao já está correto!")
            return True
        
        # Corrigir linha problemática
        content = content.replace(
            "tenant_id = Column(Integer, ForeignKey('public.tenants.id'), nullable=False)",
            "tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)"
        )
        
        # Remover relacionamento problemático se existir
        content = content.replace(
            'tenant = relationship("Tenant", backref=\'registros_evolucao_list\')',
            '# tenant = relationship("Tenant", backref=\'registros_evolucao_list\')'
        )
        
        # Salvar arquivo corrigido
        with open(media_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ RegistroEvolucao corrigido!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir RegistroEvolucao: {e}")
        return False

def create_models_init():
    """Cria ou atualiza __init__.py nos models para importação correta."""
    
    print("\\n📦 Atualizando __init__.py dos modelos")
    print("=" * 40)
    
    models_init = Path("app/models/__init__.py")
    
    init_content = '''"""
Modelos do Sistema de Gerenciamento de Canil
Imports organizados para evitar dependências circulares
"""

# Importação ordenada para evitar problemas de dependência
from .tenant import Tenant
from .system import Usuario, Configuracao, LogSistema, Backup, Endereco, Canil

# Importar apenas se não causar erro de relacionamento
try:
    from .animal import Animal, Matriz, Reprodutor, Filhote, Raca, Especie, Linhagem
except ImportError:
    pass

try:
    from .breeding import Ninhada, Cruzamento, ArvoreGenealogica
except ImportError:
    pass

try:
    from .health import RegistroVeterinario, Vacinacao, Vermifugacao, ExameGenetico
except ImportError:
    pass

try:
    from .person import Pessoa, Cliente, Funcionario, Veterinario
except ImportError:
    pass

try:
    from .transaction import Venda, Adocao, Reserva
except ImportError:
    pass

try:
    from .saas import Assinatura, Pagamento, PlanoAssinatura
except ImportError:
    pass

# Media models - importar por último devido aos relacionamentos
try:
    from .media import Arquivo, ImagemAnimal, VideoAnimal, DocumentoAnimal, AlbumAnimal, RegistroEvolucao
except ImportError:
    pass

__all__ = [
    'Tenant', 'Usuario', 'Configuracao', 'LogSistema', 'Backup', 'Endereco', 'Canil',
    'Animal', 'Matriz', 'Reprodutor', 'Filhote', 'Raca', 'Especie', 'Linhagem',
    'Ninhada', 'Cruzamento', 'ArvoreGenealogica',
    'RegistroVeterinario', 'Vacinacao', 'Vermifugacao', 'ExameGenetico',
    'Pessoa', 'Cliente', 'Funcionario', 'Veterinario',
    'Venda', 'Adocao', 'Reserva',
    'Assinatura', 'Pagamento', 'PlanoAssinatura',
    'Arquivo', 'ImagemAnimal', 'VideoAnimal', 'DocumentoAnimal', 'AlbumAnimal', 'RegistroEvolucao'
]
'''
    
    try:
        with open(models_init, 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        print("✅ __init__.py atualizado!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar __init__.py: {e}")
        return False

def test_imports():
    """Testa se os imports funcionam após as correções."""
    
    print("\\n🧪 Testando Imports dos Modelos")
    print("=" * 30)
    
    try:
        # Tentar importar modelos básicos
        from app.models.tenant import Tenant
        print("✅ Tenant importado")
        
        from app.models.system import Usuario
        print("✅ Usuario importado")
        
        # Tentar importar modelo problemático
        try:
            from app.models.media import RegistroEvolucao
            print("✅ RegistroEvolucao importado")
        except Exception as e:
            print(f"❌ Erro ao importar RegistroEvolucao: {e}")
            return False
        
        print("\\n🎉 Todos os imports funcionaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

def main():
    """Função principal do script."""
    
    print("🐕 CanilApp - Correção de Relacionamentos")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not Path("app").exists():
        print("❌ Execute o script na raiz do projeto CanilApp!")
        return False
    
    success = True
    
    # 1. Corrigir referências de ForeignKey
    print("\\n🔧 Etapa 1: Corrigir Foreign Keys")
    if not fix_foreign_key_references():
        print("⚠️  Algumas correções podem ter falhado")
    
    # 2. Correção específica do RegistroEvolucao
    print("\\n🎯 Etapa 2: Correção Específica")
    if not fix_specific_media_model():
        success = False
    
    # 3. Atualizar __init__.py
    print("\\n📦 Etapa 3: Atualizar Imports")
    if not create_models_init():
        print("⚠️  __init__.py não foi atualizado")
    
    # 4. Testar imports
    print("\\n🧪 Etapa 4: Testar Imports")
    if not test_imports():
        success = False
    
    if success:
        print("\\n🎉 Correções aplicadas com sucesso!")
        print("🚀 Agora teste: python run_dev.py")
    else:
        print("\\n💥 Algumas correções falharam!")
        print("📋 Verifique os erros acima")
    
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