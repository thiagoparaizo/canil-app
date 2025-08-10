"""
Models package initialization
This module ensures all models are imported and available.
"""

# Import db from the main app package
from app import db

# Import all model modules to ensure they are registered with SQLAlchemy
try:
    from . import tenant
    print("✅ Tenant models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import tenant models: {e}")

try:
    from . import system
    print("✅ System models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import system models: {e}")

try:
    from . import animal
    print("✅ Animal models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import animal models: {e}")

try:
    from . import breeding
    print("✅ Breeding models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import breeding models: {e}")

try:
    from . import health
    print("✅ Health models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import health models: {e}")

try:
    from . import identity
    print("✅ Identity models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import identity models: {e}")

try:
    from . import person
    print("✅ Person models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import person models: {e}")

try:
    from . import transaction
    print("✅ Transaction models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import transaction models: {e}")

try:
    from . import media
    print("✅ Media models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import media models: {e}")

try:
    from . import saas
    print("✅ SaaS models imported")
except ImportError as e:
    print(f"⚠️  Warning: Could not import saas models: {e}")

# Make commonly used models available at package level
__all__ = [
    'db',
    'tenant',
    'system', 
    'animal',
    'breeding',
    'health',
    'identity',
    'person',
    'transaction',
    'media',
    'saas'
]