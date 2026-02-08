from django.shortcuts import render
from django.utils import timezone

from files.models import FileEntry


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def index(request):
    entries = FileEntry.objects.all()
    rows = []
    for entry in entries:
        is_dir = entry.is_dir
        file_type = "フォルダ" if is_dir else (entry.extension.upper() or "ファイル")
        modified_at = timezone.localtime(entry.modified_at)
        rows.append(
            {
                "name": entry.name,
                "type": file_type,
                "modified_at": modified_at.strftime("%Y-%m-%d %H:%M"),
                "size": "-" if is_dir else _format_size(entry.size_bytes),
                "status": "読み取り専用",
            }
        )

    return render(request, "files/index.html", {"entries": rows})
