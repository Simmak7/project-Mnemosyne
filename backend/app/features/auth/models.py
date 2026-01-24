"""
Auth Feature - SQLAlchemy Models

Re-exports User model from the main models module.
This is a transitional approach during fractal migration - the User model
stays in models.py because other features depend on it.

NOTE: During full migration, this would contain the actual model definition.
For now, we re-export to avoid circular imports and model conflicts.
"""

# Re-export User from main models
# This allows features/auth to be self-contained in its API
# while avoiding SQLAlchemy table definition conflicts
from models import User

__all__ = ["User"]
