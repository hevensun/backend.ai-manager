"""vfolder-and-kernel

Revision ID: 7ea324d0535b
Revises: 5de06da3c2b5
Create Date: 2017-08-08 16:25:59.553570

"""
from alembic import op
import sqlalchemy as sa
from ai.backend.manager.models.base import GUID
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7ea324d0535b'
down_revision = '5de06da3c2b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'agents',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('mem_slots', sa.Integer(), nullable=False),
        sa.Column('cpu_slots', sa.Integer(), nullable=False),
        sa.Column('gpu_slots', sa.Integer(), nullable=False),
        sa.Column('used_mem_slots', sa.Integer(), nullable=False),
        sa.Column('used_cpu_slots', sa.Integer(), nullable=False),
        sa.Column('used_gpu_slots', sa.Integer(), nullable=False),
        sa.Column('addr', sa.String(length=128), nullable=False),
        sa.Column('first_contact', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_agents'))
    )
    op.create_table(
        'vfolders',
        sa.Column('id', GUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('host', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('max_files', sa.Integer(), nullable=True),
        sa.Column('max_size', sa.Integer(), nullable=True),
        sa.Column('num_files', sa.Integer(), nullable=True),
        sa.Column('cur_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('belongs_to', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['belongs_to'], ['keypairs.access_key'], name=op.f('fk_vfolders_belongs_to_keypairs')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_vfolders'))
    )
    op.create_table(
        'vfolder_attachment',
        sa.Column('vfolder', GUID(), nullable=False),
        sa.Column('kernel', GUID(), nullable=False),
        sa.ForeignKeyConstraint(['kernel'], ['kernels.sess_id'], name=op.f('fk_vfolder_attachment_kernel_kernels')),
        sa.ForeignKeyConstraint(['vfolder'], ['vfolders.id'], name=op.f('fk_vfolder_attachment_vfolder_vfolders')),
        sa.PrimaryKeyConstraint('vfolder', 'kernel', name=op.f('pk_vfolder_attachment'))
    )
    op.drop_table('usage')
    op.add_column('kernels', sa.Column('agent', sa.String(length=64), nullable=True))
    op.add_column('kernels', sa.Column('allocated_cores', sa.ARRAY(sa.Integer()), nullable=True))
    op.add_column('kernels', sa.Column('cpu_used', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('cur_mem_bytes', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('io_read_bytes', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('io_write_bytes', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('max_mem_bytes', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('net_rx_bytes', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('net_tx_bytes', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('num_queries', sa.BigInteger(), nullable=True))
    op.add_column('kernels', sa.Column('status_info', sa.Unicode(), nullable=True))
    op.create_index(op.f('ix_kernels_created_at'), 'kernels', ['created_at'], unique=False)
    op.create_index(op.f('ix_kernels_status'), 'kernels', ['status'], unique=False)
    op.create_index(op.f('ix_kernels_terminated_at'), 'kernels', ['terminated_at'], unique=False)
    op.create_foreign_key(op.f('fk_kernels_agent_agents'), 'kernels', 'agents', ['agent'], ['id'])
    op.drop_column('kernels', 'agent_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('kernels', sa.Column('agent_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(op.f('fk_kernels_agent_agents'), 'kernels', type_='foreignkey')
    op.drop_index(op.f('ix_kernels_terminated_at'), table_name='kernels')
    op.drop_index(op.f('ix_kernels_status'), table_name='kernels')
    op.drop_index(op.f('ix_kernels_created_at'), table_name='kernels')
    op.drop_column('kernels', 'status_info')
    op.drop_column('kernels', 'num_queries')
    op.drop_column('kernels', 'net_tx_bytes')
    op.drop_column('kernels', 'net_rx_bytes')
    op.drop_column('kernels', 'max_mem_bytes')
    op.drop_column('kernels', 'io_write_bytes')
    op.drop_column('kernels', 'io_read_bytes')
    op.drop_column('kernels', 'cur_mem_bytes')
    op.drop_column('kernels', 'cpu_used')
    op.drop_column('kernels', 'allocated_cores')
    op.drop_column('kernels', 'agent')
    op.create_table(
        'usage',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('uuid_generate_v4()'), autoincrement=False, nullable=False),
        sa.Column('access_key_id', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
        sa.Column('kernel_type', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('kernel_id', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('started_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column('terminated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column('cpu_used', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True),
        sa.Column('mem_used', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True),
        sa.Column('io_used', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True),
        sa.Column('net_used', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['access_key_id'], ['keypairs.access_key'], name='fk_usage_access_key_id_keypairs'),
        sa.PrimaryKeyConstraint('id', name='pk_usage')
    )
    op.drop_table('vfolder_attachment')
    op.drop_table('vfolders')
    op.drop_table('agents')
    # ### end Alembic commands ###
