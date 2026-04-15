# HomeSense Migration Notes

Schema changes now use Alembic.

Existing databases created before Alembic should be stamped to the baseline revision first:

```bash
alembic stamp 0001_existing_schema_baseline
alembic upgrade head
```

New environments can either:

```bash
alembic upgrade head
```

or continue using `DATABASE_AUTO_CREATE=true` for local-only development bootstrap.

Recommended workflow:

```bash
alembic revision -m "describe change"
alembic upgrade head
```

For production, set `DATABASE_AUTO_CREATE=false` and run migrations explicitly during deploy.
