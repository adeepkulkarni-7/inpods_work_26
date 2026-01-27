"""
Inpods Curriculum Mapping System - Integration Package

This package provides everything needed to integrate the curriculum mapping
system into an existing platform as a microservice.

Usage:
    from integration import CurriculumMappingService, create_app

    # Option 1: Use as standalone microservice
    app = create_app(config)
    app.run()

    # Option 2: Import engine directly into existing backend
    from integration.engine import AuditEngine, LibraryManager

    engine = AuditEngine(azure_config)
    result = engine.run_audit_batched(...)

Components:
    - engine: Core AI mapping logic (AuditEngine, LibraryManager)
    - visualization: Chart generation (VisualizationEngine)
    - api: Flask API endpoints
    - auth: Authentication middleware
    - database: Database models and integration
    - config: Configuration management
"""

__version__ = "2.0.0"
__author__ = "Inpods"

from .engine import AuditEngine, LibraryManager
from .visualization import VisualizationEngine
from .app import create_app
from .config import Config, get_config

__all__ = [
    'AuditEngine',
    'LibraryManager',
    'VisualizationEngine',
    'create_app',
    'Config',
    'get_config'
]
