import shutil
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def check_database():
    try:
        connection.ensure_connection()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def check_migrations():
    try:
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            return False, f"Unapplied migrations: {len(plan)}"
        return True, "All migrations applied"
    except Exception as e:
        return False, f"Migration check failed: {str(e)}"


def check_disk_space():
    try:
        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024**3)
        if free_gb < 1:
            return False, f"Low disk space: {free_gb:.2f}GB free"
        return True, f"Disk space OK: {free_gb:.2f}GB free"
    except Exception as e:
        return False, f"Disk space check failed: {str(e)}"


def run_health_checks():
    checks = {
        "database": check_database(),
        "migrations": check_migrations(),
        "disk_space": check_disk_space(),
    }

    overall_status = all(status for status, _ in checks.values())

    return {
        "status": "healthy" if overall_status else "unhealthy",
        "checks": {
            name: {"status": "pass" if status else "fail", "message": message}
            for name, (status, message) in checks.items()
        },
    }
