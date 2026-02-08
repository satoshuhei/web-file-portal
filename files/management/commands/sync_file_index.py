import os
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from files.models import FileEntry
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Sync file entries from local storage into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--root",
            default=None,
            help="Override APP_LOCAL_STORAGE_ROOT",
        )
        parser.add_argument(
            "--tenant",
            default=None,
            help="Tenant slug (default: APP_DEFAULT_TENANT)",
        )
        parser.add_argument(
            "--no-delete",
            action="store_true",
            help="Do not delete entries missing from disk",
        )

    def handle(self, *args, **options):
        root = options["root"] or os.getenv("APP_LOCAL_STORAGE_ROOT", "C:\\data\\public")
        tenant_slug = options["tenant"] or os.getenv("APP_DEFAULT_TENANT", "default")
        delete_missing = not options["no_delete"]
        default_owner = os.getenv("APP_DEFAULT_OWNER", "system")

        storage_root = Path(root)
        if not storage_root.exists():
            self.stderr.write(self.style.ERROR(f"Storage root not found: {storage_root}"))
            return

        tenant, _ = Tenant.objects.get_or_create(
            slug=tenant_slug,
            defaults={"name": tenant_slug},
        )

        existing = {
            entry.relative_path: entry
            for entry in FileEntry.objects.filter(tenant=tenant)
        }
        seen = set()
        created = 0
        updated = 0

        for dirpath, dirnames, filenames in os.walk(storage_root):
            dir_path = Path(dirpath)
            relative_dir = dir_path.relative_to(storage_root)
            if relative_dir != Path("."):
                rel_path = str(relative_dir).replace("\\", "/")
                seen.add(rel_path)
                created, updated = self._upsert_entry(
                    tenant=tenant,
                    rel_path=rel_path,
                    full_path=dir_path,
                    is_dir=True,
                    existing=existing,
                    default_owner=default_owner,
                    created=created,
                    updated=updated,
                )

            for name in filenames:
                full_path = dir_path / name
                relative_file = full_path.relative_to(storage_root)
                rel_path = str(relative_file).replace("\\", "/")
                seen.add(rel_path)
                created, updated = self._upsert_entry(
                    tenant=tenant,
                    rel_path=rel_path,
                    full_path=full_path,
                    is_dir=False,
                    existing=existing,
                    default_owner=default_owner,
                    created=created,
                    updated=updated,
                )

        deleted = 0
        if delete_missing:
            missing = [
                entry_id
                for path, entry_id in ((p, e.id) for p, e in existing.items())
                if path not in seen
            ]
            if missing:
                deleted, _ = FileEntry.objects.filter(id__in=missing).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete. Created: {created}, Updated: {updated}, Deleted: {deleted}."
            )
        )

    def _upsert_entry(
        self,
        tenant,
        rel_path,
        full_path,
        is_dir,
        existing,
        default_owner,
        created,
        updated,
    ):
        stat_info = full_path.stat()
        modified_at = datetime.fromtimestamp(
            stat_info.st_mtime,
            tz=timezone.get_current_timezone(),
        )
        extension = "" if is_dir else full_path.suffix.lstrip(".")
        size_bytes = 0 if is_dir else stat_info.st_size

        entry = existing.get(rel_path)
        if entry is None:
            FileEntry.objects.create(
                tenant=tenant,
                name=full_path.name,
                relative_path=rel_path,
                extension=extension,
                size_bytes=size_bytes,
                modified_at=modified_at,
                is_dir=is_dir,
                owner=default_owner,
            )
            created += 1
        else:
            changed = False
            if entry.name != full_path.name:
                entry.name = full_path.name
                changed = True
            if entry.extension != extension:
                entry.extension = extension
                changed = True
            if entry.size_bytes != size_bytes:
                entry.size_bytes = size_bytes
                changed = True
            if entry.modified_at != modified_at:
                entry.modified_at = modified_at
                changed = True
            if entry.is_dir != is_dir:
                entry.is_dir = is_dir
                changed = True
            if not entry.owner:
                entry.owner = default_owner
                changed = True

            if changed:
                entry.save()
                updated += 1

        return created, updated
