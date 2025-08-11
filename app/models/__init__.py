"""
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
