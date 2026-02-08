import re

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


def _is_search_active(name_query, folder_query, regex_query, bulk_query):
    return any([name_query, folder_query, regex_query, bulk_query])


def index(request):
    current_path = _normalize_path(request.GET.get("path", ""))
    name_query = request.GET.get("name", "").strip()
    folder_query = request.GET.get("folder", "").strip()
    regex_query = request.GET.get("regex", "").strip()
    bulk_query = request.GET.get("bulk", "").strip()
    prefix = f"{current_path}/" if current_path else ""
    entries = FileEntry.objects.all()
    if current_path:
        entries = entries.filter(relative_path__startswith=prefix)

    search_active = _is_search_active(
        name_query,
        folder_query,
        regex_query,
        bulk_query,
    )

    top_level = set()
    for entry in entries:
        top_segment = entry.relative_path.split("/")[0]
        if top_segment:
            top_level.add(top_segment)
    folders = sorted(top_level)

    error = None
    rows = []

    if search_active:
        filtered = list(entries)
        if name_query:
            filtered = [
                entry
                for entry in filtered
                if name_query.lower() in entry.name.lower()
            ]
        if folder_query:
            filtered = [
                entry
                for entry in filtered
                if entry.is_dir and folder_query.lower() in entry.name.lower()
            ]
        if bulk_query:
            terms = [term.strip() for term in bulk_query.splitlines() if term.strip()]
            if terms:
                filtered = [
                    entry
                    for entry in filtered
                    if any(term.lower() in entry.name.lower() for term in terms)
                ]
        if regex_query:
            try:
                pattern = re.compile(regex_query, re.IGNORECASE)
            except re.error:
                pattern = None
                error = "正規表現が無効です。"
            if pattern is not None:
                filtered = [
                    entry
                    for entry in filtered
                    if pattern.search(entry.name)
                    or pattern.search(entry.relative_path)
                ]

        for entry in filtered:
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
                    "is_dir": is_dir,
                    "path": entry.relative_path,
                    "display_path": entry.relative_path,
                }
            )
    else:
        for entry in entries:
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
            "search_active": search_active,
            "name_query": name_query,
            "folder_query": folder_query,
            "regex_query": regex_query,
            "bulk_query": bulk_query,
            "error": error,
        },
    )
