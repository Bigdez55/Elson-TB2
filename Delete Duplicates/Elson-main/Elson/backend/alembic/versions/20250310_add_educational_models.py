"""add educational models

Revision ID: 20250310_add_educational_models
Revises: 20250306_add_subscription_plans
Create Date: 2025-03-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250310_add_educational_models'
down_revision: str = '20250306_add_subscription_plans'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ContentLevel enum type
    op.execute("CREATE TYPE contentlevel AS ENUM ('beginner', 'intermediate', 'advanced')")
    
    # Create ContentType enum type
    op.execute("CREATE TYPE contenttype AS ENUM ('module', 'quiz', 'article', 'interactive', 'video')")
    
    # Create CompletionRequirement enum type
    op.execute("CREATE TYPE completionrequirement AS ENUM ('none', 'quiz', 'time', 'interaction')")
    
    # Create educational_content table
    op.create_table(
        'educational_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', sa.Enum('module', 'quiz', 'article', 'interactive', 'video', name='contenttype'), nullable=False),
        sa.Column('level', sa.Enum('beginner', 'intermediate', 'advanced', name='contentlevel'), nullable=False),
        sa.Column('completion_requirement', sa.Enum('none', 'quiz', 'time', 'interaction', name='completionrequirement'), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=True),
        sa.Column('min_age', sa.Integer(), nullable=True),
        sa.Column('max_age', sa.Integer(), nullable=True),
        sa.Column('importance_level', sa.Integer(), nullable=True),
        sa.Column('content_path', sa.String(length=255), nullable=True),
        sa.Column('associated_quiz_id', sa.Integer(), nullable=True),
        sa.Column('passing_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['associated_quiz_id'], ['educational_content.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_educational_content_id'), 'educational_content', ['id'], unique=False)
    op.create_index(op.f('ix_educational_content_slug'), 'educational_content', ['slug'], unique=True)
    
    # Create content_prerequisites table
    op.create_table(
        'content_prerequisites',
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('prerequisite_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['content_id'], ['educational_content.id'], ),
        sa.ForeignKeyConstraint(['prerequisite_id'], ['educational_content.id'], ),
        sa.PrimaryKeyConstraint('content_id', 'prerequisite_id')
    )
    
    # Create learning_paths table
    op.create_table(
        'learning_paths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('min_age', sa.Integer(), nullable=True),
        sa.Column('max_age', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_learning_paths_id'), 'learning_paths', ['id'], unique=False)
    op.create_index(op.f('ix_learning_paths_slug'), 'learning_paths', ['slug'], unique=True)
    
    # Create learning_path_items table
    op.create_table(
        'learning_path_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learning_path_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['educational_content.id'], ),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_path_items_id'), 'learning_path_items', ['id'], unique=False)
    
    # Create trading_permissions table
    op.create_table(
        'trading_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permission_type', sa.String(length=50), nullable=False),
        sa.Column('requires_guardian_approval', sa.Boolean(), nullable=True),
        sa.Column('min_age', sa.Integer(), nullable=True),
        sa.Column('required_learning_path_id', sa.Integer(), nullable=True),
        sa.Column('required_content_id', sa.Integer(), nullable=True),
        sa.Column('required_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['required_content_id'], ['educational_content.id'], ),
        sa.ForeignKeyConstraint(['required_learning_path_id'], ['learning_paths.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_permissions_id'), 'trading_permissions', ['id'], unique=False)
    
    # Create user_progress table
    op.create_table(
        'user_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('is_started', sa.Boolean(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('progress_percent', sa.Float(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['educational_content.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_progress_id'), 'user_progress', ['id'], unique=False)
    
    # Create user_permissions table
    op.create_table(
        'user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('is_granted', sa.Boolean(), nullable=True),
        sa.Column('granted_by_user_id', sa.Integer(), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['trading_permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_permissions_id'), 'user_permissions', ['id'], unique=False)


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_index(op.f('ix_user_permissions_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    
    op.drop_index(op.f('ix_user_progress_id'), table_name='user_progress')
    op.drop_table('user_progress')
    
    op.drop_index(op.f('ix_trading_permissions_id'), table_name='trading_permissions')
    op.drop_table('trading_permissions')
    
    op.drop_index(op.f('ix_learning_path_items_id'), table_name='learning_path_items')
    op.drop_table('learning_path_items')
    
    op.drop_index(op.f('ix_learning_paths_slug'), table_name='learning_paths')
    op.drop_index(op.f('ix_learning_paths_id'), table_name='learning_paths')
    op.drop_table('learning_paths')
    
    op.drop_table('content_prerequisites')
    
    op.drop_index(op.f('ix_educational_content_slug'), table_name='educational_content')
    op.drop_index(op.f('ix_educational_content_id'), table_name='educational_content')
    op.drop_table('educational_content')
    
    # Drop enum types
    op.execute("DROP TYPE contentlevel")
    op.execute("DROP TYPE contenttype")
    op.execute("DROP TYPE completionrequirement")