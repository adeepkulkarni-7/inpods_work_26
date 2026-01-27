"""
Database Integration for Curriculum Mapping Service

Provides persistent storage for mapping sets using SQLAlchemy.
Supports PostgreSQL, MySQL, SQLite, and other SQL databases.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy imports (optional dependency)
try:
    from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey, JSON
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, scoped_session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not installed. Database features disabled. Install with: pip install sqlalchemy")

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class MappingSet(Base):
        """
        Stores a complete mapping session.

        Corresponds to the library JSON files in the file-based storage.
        """
        __tablename__ = 'curriculum_mapping_sets'

        id = Column(String(36), primary_key=True)
        user_id = Column(String(36), nullable=True, index=True)
        name = Column(String(255), nullable=False)
        dimension = Column(String(50), nullable=False)  # area_topics, competency, objective, skill, nmc_competency
        mode = Column(String(10), nullable=False)  # A (map), B (rate), C (insights)
        source_file = Column(String(255))
        question_count = Column(Integer, default=0)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relationships
        mappings = relationship("Mapping", back_populates="mapping_set", cascade="all, delete-orphan")

        def to_dict(self, include_mappings: bool = False) -> Dict[str, Any]:
            result = {
                'id': self.id,
                'user_id': self.user_id,
                'name': self.name,
                'dimension': self.dimension,
                'mode': self.mode,
                'source_file': self.source_file,
                'question_count': self.question_count,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None
            }

            if include_mappings:
                result['recommendations'] = [m.to_dict() for m in self.mappings]

            return result


    class Mapping(Base):
        """
        Individual question-to-curriculum mapping.
        """
        __tablename__ = 'curriculum_mappings'

        id = Column(String(36), primary_key=True)
        mapping_set_id = Column(String(36), ForeignKey('curriculum_mapping_sets.id'), nullable=False, index=True)
        question_number = Column(String(50))
        question_text = Column(Text)

        # Mapping details
        mapped_id = Column(String(50))  # For competency/objective/skill
        mapped_topic = Column(String(255))  # For area_topics
        mapped_subtopic = Column(String(255))  # For area_topics

        confidence = Column(Float, default=0.0)
        justification = Column(Text)

        # Rating details (Mode B)
        rating = Column(String(20))  # correct, partially_correct, incorrect
        agreement_score = Column(Float)
        status = Column(String(20), default='pending')  # pending, accepted, rejected

        created_at = Column(DateTime, default=datetime.utcnow)

        # Relationships
        mapping_set = relationship("MappingSet", back_populates="mappings")

        def to_dict(self) -> Dict[str, Any]:
            return {
                'id': self.id,
                'question_num': self.question_number,
                'question_text': self.question_text,
                'mapped_id': self.mapped_id,
                'mapped_topic': self.mapped_topic,
                'mapped_subtopic': self.mapped_subtopic,
                'recommended_mapping': self.mapped_id or f"{self.mapped_topic} / {self.mapped_subtopic}",
                'confidence': self.confidence,
                'justification': self.justification,
                'rating': self.rating,
                'agreement_score': self.agreement_score,
                'status': self.status
            }


    class AuditLog(Base):
        """
        Security audit log for tracking user actions.
        """
        __tablename__ = 'curriculum_audit_logs'

        id = Column(String(36), primary_key=True)
        user_id = Column(String(36), index=True)
        action = Column(String(100), nullable=False)
        resource_type = Column(String(50))
        resource_id = Column(String(36))
        details = Column(JSON)
        ip_address = Column(String(45))
        user_agent = Column(String(255))
        created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DatabaseManager:
    """
    Manages database connections and operations.

    Usage:
        db = DatabaseManager(config.database)

        # Save a mapping set
        db.save_mapping_set(mapping_data)

        # Query mapping sets
        sets = db.list_mapping_sets(user_id='user-123')

        # Get a specific mapping
        mapping = db.get_mapping_set('abc123')
    """

    def __init__(self, config):
        """
        Initialize database manager.

        Args:
            config: DatabaseConfig object
        """
        self.config = config
        self.engine = None
        self.Session = None

        if config.enabled and SQLALCHEMY_AVAILABLE:
            self._initialize_db()

    def _initialize_db(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(
                self.config.url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                echo=False
            )

            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)

            # Create session factory
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_session(self):
        """Get a database session"""
        if not self.Session:
            raise RuntimeError("Database not initialized")
        return self.Session()

    def close_session(self):
        """Close the current session"""
        if self.Session:
            self.Session.remove()

    # ==========================================
    # Mapping Set Operations
    # ==========================================

    def save_mapping_set(self, data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """
        Save a mapping set to the database.

        Args:
            data: Mapping set data (same format as library JSON)
            user_id: Optional user ID for ownership

        Returns:
            Saved mapping set data
        """
        import uuid

        session = self.get_session()

        try:
            mapping_set_id = data.get('id') or str(uuid.uuid4())[:8]

            mapping_set = MappingSet(
                id=mapping_set_id,
                user_id=user_id,
                name=data.get('name', f'Mapping_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
                dimension=data.get('dimension', 'area_topics'),
                mode=data.get('mode', 'A'),
                source_file=data.get('source_file', ''),
                question_count=len(data.get('recommendations', []))
            )

            session.add(mapping_set)

            # Add individual mappings
            for idx, rec in enumerate(data.get('recommendations', [])):
                mapping = Mapping(
                    id=str(uuid.uuid4()),
                    mapping_set_id=mapping_set_id,
                    question_number=rec.get('question_num', f'Q{idx+1}'),
                    question_text=rec.get('question_text', ''),
                    mapped_id=rec.get('mapped_id', ''),
                    mapped_topic=rec.get('mapped_topic', ''),
                    mapped_subtopic=rec.get('mapped_subtopic', ''),
                    confidence=rec.get('confidence', 0.0),
                    justification=rec.get('justification', ''),
                    rating=rec.get('rating'),
                    agreement_score=rec.get('agreement_score'),
                    status='pending'
                )
                session.add(mapping)

            session.commit()

            return mapping_set.to_dict()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save mapping set: {e}")
            raise

        finally:
            self.close_session()

    def list_mapping_sets(self, user_id: str = None, dimension: str = None,
                          limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List mapping sets with optional filtering.

        Args:
            user_id: Filter by user
            dimension: Filter by dimension
            limit: Max results
            offset: Pagination offset

        Returns:
            List of mapping set summaries
        """
        session = self.get_session()

        try:
            query = session.query(MappingSet)

            if user_id:
                query = query.filter(MappingSet.user_id == user_id)
            if dimension:
                query = query.filter(MappingSet.dimension == dimension)

            query = query.order_by(MappingSet.created_at.desc())
            query = query.offset(offset).limit(limit)

            results = query.all()

            return [ms.to_dict() for ms in results]

        finally:
            self.close_session()

    def get_mapping_set(self, mapping_set_id: str, include_mappings: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a specific mapping set.

        Args:
            mapping_set_id: The mapping set ID
            include_mappings: Whether to include individual mappings

        Returns:
            Mapping set data or None if not found
        """
        session = self.get_session()

        try:
            mapping_set = session.query(MappingSet).filter(MappingSet.id == mapping_set_id).first()

            if not mapping_set:
                return None

            return mapping_set.to_dict(include_mappings=include_mappings)

        finally:
            self.close_session()

    def delete_mapping_set(self, mapping_set_id: str) -> bool:
        """
        Delete a mapping set.

        Args:
            mapping_set_id: The mapping set ID

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()

        try:
            mapping_set = session.query(MappingSet).filter(MappingSet.id == mapping_set_id).first()

            if not mapping_set:
                return False

            session.delete(mapping_set)
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete mapping set: {e}")
            raise

        finally:
            self.close_session()

    def update_mapping_status(self, mapping_id: str, status: str) -> bool:
        """
        Update the status of an individual mapping.

        Args:
            mapping_id: The mapping ID
            status: New status (pending, accepted, rejected)

        Returns:
            True if updated, False if not found
        """
        session = self.get_session()

        try:
            mapping = session.query(Mapping).filter(Mapping.id == mapping_id).first()

            if not mapping:
                return False

            mapping.status = status
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update mapping status: {e}")
            raise

        finally:
            self.close_session()

    # ==========================================
    # Audit Log Operations
    # ==========================================

    def log_action(self, user_id: str, action: str, resource_type: str = None,
                   resource_id: str = None, details: Dict = None,
                   ip_address: str = None, user_agent: str = None):
        """
        Log an action for audit purposes.
        """
        import uuid

        session = self.get_session()

        try:
            log = AuditLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )

            session.add(log)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log action: {e}")

        finally:
            self.close_session()

    def get_audit_logs(self, user_id: str = None, action: str = None,
                       start_date: datetime = None, end_date: datetime = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query audit logs.
        """
        session = self.get_session()

        try:
            query = session.query(AuditLog)

            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if action:
                query = query.filter(AuditLog.action == action)
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            query = query.order_by(AuditLog.created_at.desc())
            query = query.limit(limit)

            results = query.all()

            return [{
                'id': log.id,
                'user_id': log.user_id,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'details': log.details,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat() if log.created_at else None
            } for log in results]

        finally:
            self.close_session()


# ==========================================
# Hybrid Storage Manager
# ==========================================

class HybridStorageManager:
    """
    Combines file-based and database storage.

    Uses database when available, falls back to file-based storage.
    Useful during migration or for platforms that want both options.
    """

    def __init__(self, database_manager: DatabaseManager = None, library_folder: str = None):
        self.db = database_manager
        self.file_manager = None

        if library_folder:
            # Import the file-based LibraryManager
            from .engine import LibraryManager
            self.file_manager = LibraryManager(library_folder)

    def save_mapping(self, name: str, recommendations: list, dimension: str,
                     mode: str, source_file: str = '', user_id: str = None) -> Dict[str, Any]:
        """Save mapping set (tries database first, falls back to file)"""

        data = {
            'name': name,
            'recommendations': recommendations,
            'dimension': dimension,
            'mode': mode,
            'source_file': source_file
        }

        # Try database first
        if self.db and self.db.config.enabled:
            try:
                return self.db.save_mapping_set(data, user_id=user_id)
            except Exception as e:
                logger.warning(f"Database save failed, falling back to file: {e}")

        # Fall back to file storage
        if self.file_manager:
            return self.file_manager.save_mapping(name, recommendations, dimension, mode, source_file)

        raise RuntimeError("No storage backend available")

    def list_mappings(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List all mapping sets"""

        # Try database first
        if self.db and self.db.config.enabled:
            try:
                return self.db.list_mapping_sets(user_id=user_id)
            except Exception as e:
                logger.warning(f"Database list failed, falling back to file: {e}")

        # Fall back to file storage
        if self.file_manager:
            return self.file_manager.list_mappings()

        return []

    def get_mapping(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific mapping set"""

        # Try database first
        if self.db and self.db.config.enabled:
            try:
                return self.db.get_mapping_set(mapping_id)
            except Exception as e:
                logger.warning(f"Database get failed, falling back to file: {e}")

        # Fall back to file storage
        if self.file_manager:
            return self.file_manager.get_mapping(mapping_id)

        return None

    def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a mapping set"""

        # Try database first
        if self.db and self.db.config.enabled:
            try:
                return self.db.delete_mapping_set(mapping_id)
            except Exception as e:
                logger.warning(f"Database delete failed, falling back to file: {e}")

        # Fall back to file storage
        if self.file_manager:
            return self.file_manager.delete_mapping(mapping_id)

        return False
