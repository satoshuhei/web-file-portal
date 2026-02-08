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


def _normalize_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    normalized = raw_path.strip().replace("\\", "/")
    return normalized.strip("/")


def _build_breadcrumbs(current_path: str):
    crumbs = [("ルート", "")]
    if not current_path:
        return crumbs
    parts = current_path.split("/")
    acc = []
    for part in parts:
        acc.append(part)
        crumbs.append((part, "/".join(acc)))
    return crumbs


def index(request):
    current_path = _normalize_path(request.GET.get("path", ""))
    prefix = f"{current_path}/" if current_path else ""
    entries = FileEntry.objects.all()

    top_level = set()
    for entry in entries:
        top_segment = entry.relative_path.split("/")[0]
        if top_segment:
            top_level.add(top_segment)
    folders = sorted(top_level)

    rows = []
    for entry in entries:
        if not entry.relative_path.startswith(prefix):
            continue
        remainder = entry.relative_path[len(prefix) :]
        if not remainder or "/" in remainder:
            continue
        is_dir = entry.is_dir
        file_type = "フォルダ" if is_dir else (entry.extension.upper() or "ファイル")
        modified_at = timezone.localtime(entry.modified_at)
        next_path = (
            f"{current_path}/{remainder}" if current_path else remainder
        )
        rows.append(
            {
                "name": entry.name,
                "type": file_type,
                "modified_at": modified_at.strftime("%Y-%m-%d %H:%M"),
                "size": "-" if is_dir else _format_size(entry.size_bytes),
                "status": "読み取り専用",
                "is_dir": is_dir,
                "path": next_path,
            }
        )

    rows.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))

    return render(
        request,
        "files/index.html",
        {
            "entries": rows,
            "folders": folders,
            "current_path": current_path,
            "breadcrumbs": _build_breadcrumbs(current_path),
        },
    )
