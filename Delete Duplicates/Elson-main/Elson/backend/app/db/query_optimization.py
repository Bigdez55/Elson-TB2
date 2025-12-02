"""Database query optimization utilities.

This module provides optimized query functions and decorators to improve 
database performance, including select optimizations, lazy loading controls,
and query profiling.
"""

import logging
import time
import functools
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast
from sqlalchemy import Column, func, text
from sqlalchemy.orm import Query, Session, joinedload, contains_eager, aliased
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.expression import select

from app.core.config import settings
from app.core.metrics import record_metric
from app.core.caching import cached

logger = logging.getLogger(__name__)

# Type variables for generic models and functions
T = TypeVar('T')
M = TypeVar('M', bound=DeclarativeMeta)

def optimize_query(query: Query, 
                  model: Type[M], 
                  eager_load: Optional[List[str]] = None) -> Query:
    """Apply optimization techniques to a SQLAlchemy query.
    
    Args:
        query: The query to optimize
        model: The model class being queried
        eager_load: List of relationships to eager load
        
    Returns:
        Optimized query object
    """
    # Enable eager loading for specified relationships
    if eager_load:
        for relationship in eager_load:
            query = query.options(joinedload(getattr(model, relationship)))
    
    return query

def count_estimate(query: Query, session: Session) -> int:
    """Fast way to estimate count for large tables.
    
    This uses PostgreSQL's query planner to estimate the row count
    rather than actually counting all rows, which is much faster for large tables.
    
    Args:
        query: The query to count
        session: Database session
        
    Returns:
        Estimated count
    """
    # Get the query SQL
    sql = str(query.statement.compile(
        dialect=session.bind.dialect,
        compile_kwargs={"literal_binds": True}
    ))
    
    # Create an EXPLAIN query
    explain_sql = f"EXPLAIN {sql}"
    
    # Execute the EXPLAIN query
    result = session.execute(text(explain_sql)).fetchone()[0]
    
    # Extract the estimated row count using a simple parsing approach
    # Example: 'Seq Scan on users (cost=0.00..123.45 rows=1000 width=20)'
    for part in result.split():
        if part.startswith('rows='):
            return int(part[5:])
    
    # Fallback to actual count if we can't parse the EXPLAIN output
    logger.warning("Could not extract estimated count, falling back to actual count")
    return query.count()

@cached(ttl=settings.CACHE_TTL_MEDIUM, prefix="db")
def get_cached_entity(
    session: Session,
    model: Type[M],
    entity_id: int,
    eager_load: Optional[List[str]] = None
) -> Optional[M]:
    """Get an entity by ID with caching.
    
    Args:
        session: Database session
        model: The model class
        entity_id: The entity ID
        eager_load: List of relationships to eager load
        
    Returns:
        Entity instance or None if not found
    """
    query = session.query(model).filter(model.id == entity_id)
    query = optimize_query(query, model, eager_load)
    return query.first()

@cached(ttl=settings.CACHE_TTL_SHORT, prefix="db")
def get_cached_entities(
    session: Session,
    model: Type[M],
    filters: Optional[Dict[str, Any]] = None,
    eager_load: Optional[List[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[M]:
    """Get a list of entities with caching.
    
    Args:
        session: Database session
        model: The model class
        filters: Dictionary of column-value filters
        eager_load: List of relationships to eager load
        limit: Maximum number of entities to return
        offset: Offset for pagination
        
    Returns:
        List of entity instances
    """
    query = session.query(model)
    
    # Apply filters
    if filters:
        for column_name, value in filters.items():
            column = getattr(model, column_name)
            query = query.filter(column == value)
    
    # Apply optimization
    query = optimize_query(query, model, eager_load)
    
    # Apply limit and offset
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    
    return query.all()

def batch_load_relationships(
    session: Session,
    instances: List[M],
    relationship_names: List[str]
) -> None:
    """Efficiently load relationships for a list of instances in a single query.
    
    This is useful when you have many objects and want to avoid N+1 query problems.
    
    Args:
        session: Database session
        instances: List of model instances
        relationship_names: Names of relationships to load
    """
    if not instances:
        return
    
    # Get the model class from the first instance
    model = instances[0].__class__
    
    # Get the primary keys
    primary_keys = [instance.id for instance in instances]
    
    # Load each relationship
    for relationship_name in relationship_names:
        # Get the relationship attribute
        relationship_attr = getattr(model, relationship_name)
        
        # Get the related model
        related_model = relationship_attr.prop.mapper.class_
        
        # Get the foreign key that relates back to our model
        # This assumes a simple relationship with a single foreign key
        for prop in relationship_attr.prop.local_columns:
            fk_column = prop.key
            break
        else:
            logger.warning(f"Could not determine foreign key for {relationship_name}")
            continue
        
        # Load all related objects for all instances in a single query
        query = session.query(related_model).filter(
            getattr(related_model, fk_column).in_(primary_keys)
        )
        
        # Execute the query (the ORM will automatically populate the appropriate relationships)
        query.all()

def profile_query(query_name: str = "unnamed_query"):
    """Decorator to profile query execution time and record metrics.
    
    Args:
        query_name: Name to identify the query in metrics
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                
                # Log slow queries
                if elapsed_ms > 100:  # More than 100ms
                    logger.warning(f"Slow query {query_name}: {elapsed_ms:.2f}ms")
                
                # Record metrics
                record_metric("optimized_query_time", elapsed_ms, {"query": query_name})
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"Query error in {query_name}: {str(e)}")
                record_metric("query_error", 1, {"query": query_name, "error": str(e)[:100]})
                raise
        return wrapper
    return decorator

def paginate_query(
    query: Query, 
    page: int = 1, 
    page_size: int = 20
) -> Tuple[List[Any], int, int]:
    """Paginate a query with efficient count.
    
    Args:
        query: The query to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Tuple of (items, total_count, total_pages)
    """
    # Ensure positive values
    page = max(1, page)
    page_size = max(1, min(100, page_size))  # Limit page size to reasonable range
    
    # Get total count (or estimate for large tables)
    if hasattr(query, '_total_count'):
        total_count = query._total_count
    else:
        # For larger tables, we might want to use the estimate
        if settings.DB_ECHO_SQL:
            logger.debug(f"Counting rows for pagination...")
        
        # Use the query's session
        session = query.session
        
        # Use count estimate for large tables
        if hasattr(settings, 'USE_COUNT_ESTIMATE') and settings.USE_COUNT_ESTIMATE:
            total_count = count_estimate(query, session)
        else:
            # Use regular count() for smaller tables
            total_count = query.count()
    
    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get paginated items
    items = query.offset(offset).limit(page_size).all()
    
    return items, total_count, total_pages

def bulk_create(session: Session, 
               model: Type[M], 
               data: List[Dict[str, Any]], 
               chunk_size: int = 1000,
               return_instances: bool = False) -> Union[int, List[M]]:
    """Efficiently insert multiple records in chunks.
    
    Args:
        session: Database session
        model: Model class
        data: List of dictionaries containing the data to insert
        chunk_size: Number of records to insert in each chunk
        return_instances: Whether to return the created instances
        
    Returns:
        Count of created records, or list of instances if return_instances=True
    """
    created_instances = []
    total_count = 0
    
    # Process in chunks
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        instances = [model(**item) for item in chunk]
        
        if return_instances:
            created_instances.extend(instances)
        
        session.bulk_save_objects(instances)
        total_count += len(chunk)
    
    # Commit will be handled by the caller
    
    if return_instances:
        return created_instances
    return total_count