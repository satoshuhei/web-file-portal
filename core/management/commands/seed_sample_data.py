import os
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from audit.models import AuditLog
from files.models import FileEntry
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Seed sample data for development"

    def handle(self, *args, **options):
        storage_root = Path(os.getenv("APP_LOCAL_STORAGE_ROOT", "C:\\data\\public"))
        storage_root.mkdir(parents=True, exist_ok=True)

        tenants = []
        for index in range(1, 6):
            name = f"Tenant {index}"
            slug = f"tenant-{index}"
            tenant, _ = Tenant.objects.get_or_create(slug=slug, defaults={"name": name})
            tenants.append(tenant)

        base_time = timezone.now()
        sample_entries = [
            ("Project-Overview.pdf", False, 24000),
            ("Design-Assets", True, 0),
            ("Release-Notes.txt", False, 1200),
            ("Roadmap.xlsx", False, 18000),
            ("Team-Notes.md", False, 900),
        ]

        for index, (name, is_dir, size_bytes) in enumerate(sample_entries):
            tenant = tenants[index % len(tenants)]
            relative_path = name
            extension = Path(name).suffix.lstrip(".")
            modified_at = base_time - timedelta(days=index)

            FileEntry.objects.get_or_create(
                tenant=tenant,
                relative_path=relative_path,
                defaults={
                    "name": name,
                    "extension": extension,
                    "size_bytes": size_bytes,
                    "modified_at": modified_at,
                    "is_dir": is_dir,
                    "owner": "system",
                },
            )

            full_path = storage_root / relative_path
            if is_dir:
                full_path.mkdir(parents=True, exist_ok=True)
                continue

            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not full_path.exists():
                with full_path.open("wb") as handle:
                    handle.write(b"0" * max(size_bytes, 1))

        audit_actions = [
            ("view", "admin_user", "Project-Overview.pdf"),
            ("view", "admin_user", "Design-Assets"),
            ("list", "admin_user", "Files"),
            ("view", "admin_user", "Release-Notes.txt"),
            ("health_check", "system", "/healthz"),
        ]

        for index, (action, actor, target) in enumerate(audit_actions):
            tenant = tenants[index % len(tenants)]
            AuditLog.objects.get_or_create(
                tenant=tenant,
                action=action,
                actor=actor,
                target=target,
                defaults={"detail": "seeded"},
            )

        self.stdout.write(self.style.SUCCESS("Sample data created."))
