"""Alembic env."""
from alembic import context


def run_migrations_offline():
    context.configure(url=context.config.get_main_option("sqlalchemy.url"), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    pass

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
