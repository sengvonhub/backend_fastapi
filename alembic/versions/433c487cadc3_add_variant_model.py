"""add variant model

Revision ID: 433c487cadc3
Revises: 65d9e55a98e8
Create Date: 2026-06-20 02:43:23.340772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '433c487cadc3'
down_revision: Union[str, Sequence[str], None] = '65d9e55a98e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ///////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 1 — create product_variants
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    op.create_table('product_variants',
        sa.Column('variant_id',     sa.Integer(),                              autoincrement=True, nullable=False),
        sa.Column('product_id',     sa.Integer(),                              nullable=False),
        sa.Column('sku',            sa.String(length=100),                     nullable=True),
        sa.Column('specs',          postgresql.JSONB(astext_type=sa.Text()),   nullable=False),
        sa.Column('price',          sa.Numeric(precision=12, scale=2),         nullable=False),
        sa.Column('stock_quantity', sa.Integer(),                              nullable=False),
        sa.Column('created_at',     sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',     sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ),
        sa.PrimaryKeyConstraint('variant_id'),
        sa.UniqueConstraint('product_id', 'sku', name='uq_variant_product_sku'),
    )
    op.create_index(op.f('ix_product_variants_product_id'), 'product_variants', ['product_id'], unique=False)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 2 — seed default variant per product (must run before dropping product columns)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.execute("""
        INSERT INTO product_variants (product_id, specs, price, stock_quantity, created_at, updated_at)
        SELECT
            product_id,
            jsonb_strip_nulls(jsonb_build_object('unit', unit, 'size', length_width)),
            price,
            stock_quantity,
            created_at,
            updated_at
        FROM products
    """)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 3 — create supplier_product_prices
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.create_table('supplier_product_prices',
        sa.Column('price_id',    sa.Integer(),                          autoincrement=True, nullable=False),
        sa.Column('supplier_id', sa.Integer(),                          nullable=False),
        sa.Column('variant_id',  sa.Integer(),                          nullable=False),
        sa.Column('unit_price',  sa.Numeric(precision=12, scale=2),    nullable=False),
        sa.Column('note',        sa.String(length=255),                 nullable=True),
        sa.Column('created_at',  sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at',  sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.supplier_id'], ),
        sa.ForeignKeyConstraint(['variant_id'],  ['product_variants.variant_id'], ),
        sa.PrimaryKeyConstraint('price_id'),
        sa.UniqueConstraint('supplier_id', 'variant_id', name='uq_supplier_variant'),
    )
    op.create_index(op.f('ix_supplier_product_prices_supplier_id'), 'supplier_product_prices', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_supplier_product_prices_variant_id'),  'supplier_product_prices', ['variant_id'],  unique=False)

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 4 — invoice_items: add variant_id (nullable → fill → enforce)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.add_column('invoice_items', sa.Column('variant_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_invoice_items_variant_id'), 'invoice_items', ['variant_id'], unique=False)
    op.create_foreign_key(None, 'invoice_items', 'product_variants', ['variant_id'], ['variant_id'])
    op.execute("""
        UPDATE invoice_items ii
        SET variant_id = pv.variant_id
        FROM product_variants pv
        WHERE pv.product_id = ii.product_id
    """)
    op.alter_column('invoice_items', 'variant_id', nullable=False)

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 5 — product_images: add variant_id (stays nullable — NULL = product-level image)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.add_column('product_images', sa.Column('variant_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_product_images_variant_id'), 'product_images', ['variant_id'], unique=False)
    op.create_foreign_key(None, 'product_images', 'product_variants', ['variant_id'], ['variant_id'])

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 6 — drop migrated columns from products (safe — variant seed already captured them)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    
    op.drop_column('products', 'price')
    op.drop_column('products', 'unit')
    op.drop_column('products', 'length_width')
    op.drop_column('products', 'stock_quantity')

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 7 — stock_movements: add variant_id (nullable → fill → enforce → drop old)
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.add_column('stock_movements', sa.Column('variant_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_stock_movements_variant_id'), 'stock_movements', ['variant_id'], unique=False)
    op.create_foreign_key(None, 'stock_movements', 'product_variants', ['variant_id'], ['variant_id'])
    op.execute("""
        UPDATE stock_movements sm
        SET variant_id = pv.variant_id
        FROM product_variants pv
        WHERE pv.product_id = sm.product_id
    """)
    op.alter_column('stock_movements', 'variant_id', nullable=False)
    op.drop_constraint('stock_movements_product_id_fkey', 'stock_movements', type_='foreignkey')
    op.drop_column('stock_movements', 'product_id')

    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # STEP 8 — suppliers: add phone2
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.add_column('suppliers', sa.Column('phone2', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # ### commands auto generated by Alembic - please adjust! ###
    # //////////////////////////////////////////////////////////////////////////////////////////////////////////

    op.drop_column('suppliers', 'phone2')
    op.add_column('stock_movements', sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'stock_movements', type_='foreignkey')
    op.create_foreign_key(op.f('stock_movements_product_id_fkey'), 'stock_movements', 'products', ['product_id'], ['product_id'])
    op.drop_index(op.f('ix_stock_movements_variant_id'), table_name='stock_movements')
    op.drop_column('stock_movements', 'variant_id')
    op.add_column('products', sa.Column('stock_quantity', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('products', sa.Column('length_width', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('products', sa.Column('unit', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('products', sa.Column('price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'product_images', type_='foreignkey')
    op.drop_index(op.f('ix_product_images_variant_id'), table_name='product_images')
    op.drop_column('product_images', 'variant_id')
    op.drop_constraint(None, 'invoice_items', type_='foreignkey')
    op.drop_index(op.f('ix_invoice_items_variant_id'), table_name='invoice_items')
    op.drop_column('invoice_items', 'variant_id')
    op.drop_index(op.f('ix_supplier_product_prices_variant_id'), table_name='supplier_product_prices')
    op.drop_index(op.f('ix_supplier_product_prices_supplier_id'), table_name='supplier_product_prices')
    op.drop_table('supplier_product_prices')
    op.drop_index(op.f('ix_product_variants_product_id'), table_name='product_variants')
    op.drop_table('product_variants')
    # ### end Alembic commands ###
