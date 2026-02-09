import os
import re
import tempfile
import zipfile
from datetime import datetime, time
from pathlib import Path
from urllib.parse import urlencode

from django.http import FileResponse, HttpResponse, JsonResponse
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


def _type_color_key(extension: str, is_dir: bool) -> str:
    if is_dir:
        return "folder"
    ext = (extension or "").lower()
    if ext in {"xls", "xlsx", "csv"}:
        return "excel"
    if ext in {"doc", "docx"}:
        return "word"
    if ext in {"ppt", "pptx"}:
        return "powerpoint"
    if ext in {"pdf"}:
        return "pdf"
    if ext in {"txt", "log"}:
        return "text"
    if ext in {"md"}:
        return "markdown"
    if ext in {"png", "jpg", "jpeg", "gif", "bmp"}:
        return "image"
    return "default"


def _parse_date_range(date_from: str, date_to: str):
    tz = timezone.get_current_timezone()
    start_dt = None
    end_dt = None
    error = None

    if date_from:
        try:
            start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
        except ValueError:
            error = "更新日のFromが不正です。"

    if date_to:
        try:
            end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            end_dt = timezone.make_aware(datetime.combine(end_date, time.max), tz)
        except ValueError:
            error = "更新日のToが不正です。"

    return start_dt, end_dt, error


def _parse_extensions(free_text: str, selected: list[str]) -> set[str]:
    values = set()
    for item in selected:
        value = item.strip().lstrip(".")
        if value:
            values.add(value.lower())
    for part in re.split(r"[\s,]+", free_text or ""):
        value = part.strip().lstrip(".")
        if value:
            values.add(value.lower())
    return values


def _iter_zip_members(entries):
    storage_root = _storage_root().resolve()
    seen = set()
    for entry in entries:
        full_path = _resolve_path(entry.relative_path)
        if full_path is None:
            continue
        if entry.is_dir:
            if not full_path.exists():
                continue
            for dirpath, _, filenames in os.walk(full_path):
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    try:
                        rel = file_path.resolve().relative_to(storage_root)
                    except ValueError:
                        continue
                    arcname = rel.as_posix()
                    if arcname in seen:
                        continue
                    seen.add(arcname)
                    yield file_path, arcname
        else:
            if not full_path.exists():
                continue
            arcname = entry.relative_path
            if arcname in seen:
                continue
            seen.add(arcname)
            yield full_path, arcname


def _zip_response(entries, filename: str):
    temp = tempfile.SpooledTemporaryFile(max_size=10 * 1024 * 1024)
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path, arcname in _iter_zip_members(entries):
            archive.write(file_path, arcname)
    temp.seek(0)
    return FileResponse(temp, as_attachment=True, filename=filename)


def _apply_filters(
    entries,
    name_query,
    folder_query,
    regex_query,
    bulk_query,
    date_from,
    date_to,
    ext_values,
):
    error = None
    start_dt, end_dt, date_error = _parse_date_range(date_from, date_to)
    if date_error:
        error = date_error

    if name_query:
        entries = entries.filter(name__icontains=name_query)
    if folder_query:
        entries = entries.filter(is_dir=True, name__icontains=folder_query)
    if ext_values:
        entries = entries.filter(extension__in=sorted(ext_values))
    if start_dt and end_dt:
        entries = entries.filter(modified_at__range=(start_dt, end_dt))
    elif start_dt:
        entries = entries.filter(modified_at__gte=start_dt)
    elif end_dt:
        entries = entries.filter(modified_at__lte=end_dt)

    filtered = list(entries)

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
            ]

    return filtered, error


def _storage_root() -> Path:
    root = os.getenv("APP_LOCAL_STORAGE_ROOT", "C:\\data\\public")
    return Path(root)


def _resolve_path(relative_path: str) -> Path | None:
    storage_root = _storage_root().resolve()
    full_path = (storage_root / relative_path).resolve()
    try:
        full_path.relative_to(storage_root)
    except ValueError:
        return None
    return full_path


def preview(request):
    rel_path = _normalize_path(request.GET.get("path", ""))
    if not rel_path:
        return JsonResponse({"error": "path is required"}, status=400)

    entry = FileEntry.objects.filter(relative_path=rel_path).first()
    if entry is None or entry.is_dir:
        return JsonResponse({"error": "file not found"}, status=404)

    full_path = _resolve_path(rel_path)
    if full_path is None or not full_path.exists():
        return JsonResponse({"error": "file not found"}, status=404)

    if entry.extension.lower() == "pdf":
        return FileResponse(
            full_path.open("rb"),
            content_type="application/pdf",
        )

    max_bytes = 200 * 1024
    with full_path.open("rb") as handle:
        data = handle.read(max_bytes + 1)

    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]

    content = data.decode("utf-8", errors="replace")
    if truncated:
        content += "\n\n--- ここまで表示しました ---"

    return HttpResponse(content, content_type="text/plain; charset=utf-8")


def _is_search_active(name_query, folder_query, regex_query, bulk_query):
    return any([name_query, folder_query, regex_query, bulk_query])


def index(request):
    current_path = _normalize_path(request.GET.get("path", ""))
    name_query = request.GET.get("name", "").strip()
    folder_query = request.GET.get("folder", "").strip()
    regex_query = request.GET.get("regex", "").strip()
    bulk_query = request.GET.get("bulk", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    selected_ext = request.GET.getlist("ext")
    free_ext = request.GET.get("ext_free", "").strip()
    ext_values = _parse_extensions(free_ext, selected_ext)
    prefix = f"{current_path}/" if current_path else ""
    entries = FileEntry.objects.all()
    if current_path:
        entries = entries.filter(relative_path__startswith=prefix)

    search_active = _is_search_active(
        name_query,
        folder_query,
        regex_query,
        bulk_query,
    ) or any([date_from, date_to, ext_values])

    error = None
    rows = []

    if search_active:
        filtered, error = _apply_filters(
            entries,
            name_query,
            folder_query,
            regex_query,
            bulk_query,
            date_from,
            date_to,
            ext_values,
        )

        for entry in filtered:
            is_dir = entry.is_dir
            file_type = "フォルダ" if is_dir else (entry.extension.upper() or "ファイル")
            modified_at = timezone.localtime(entry.modified_at)
            rows.append(
                {
                    "name": entry.name,
                    "type": file_type,
                    "extension": entry.extension.lower(),
                    "type_color": _type_color_key(entry.extension, is_dir),
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
                    "extension": entry.extension.lower(),
                    "type_color": _type_color_key(entry.extension, is_dir),
                    "modified_at": modified_at.strftime("%Y-%m-%d %H:%M"),
                    "size": "-" if is_dir else _format_size(entry.size_bytes),
                    "status": "読み取り専用",
                    "is_dir": is_dir,
                    "path": next_path,
                }
            )

    rows.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))

    ext_display = ", ".join(sorted(ext_values)) if ext_values else ""
    download_query = request.GET.urlencode()

    return render(
        request,
        "files/index.html",
        {
            "entries": rows,
            "current_path": current_path,
            "breadcrumbs": _build_breadcrumbs(current_path),
            "search_active": search_active,
            "name_query": name_query,
            "folder_query": folder_query,
            "regex_query": regex_query,
            "bulk_query": bulk_query,
            "date_from": date_from,
            "date_to": date_to,
            "ext_free": free_ext,
            "ext_display": ext_display,
            "selected_ext": set(ext_values),
            "download_query": download_query,
            "ext_options": [
                "pdf",
                "docx",
                "xlsx",
                "pptx",
                "txt",
                "csv",
                "md",
                "png",
                "jpg",
            ],
            "error": error,
        },
    )


def download(request):
    rel_path = _normalize_path(request.GET.get("path", ""))
    if not rel_path:
        return JsonResponse({"error": "path is required"}, status=400)

    entry = FileEntry.objects.filter(relative_path=rel_path).first()
    if entry is None:
        return JsonResponse({"error": "file not found"}, status=404)

    full_path = _resolve_path(rel_path)
    if full_path is None or not full_path.exists():
        return JsonResponse({"error": "file not found"}, status=404)

    if entry.is_dir:
        filename = f"{entry.name}.zip"
        return _zip_response([entry], filename)

    return FileResponse(
        full_path.open("rb"),
        as_attachment=True,
        filename=entry.name,
    )


def download_bulk(request):
    name_query = request.GET.get("name", "").strip()
    folder_query = request.GET.get("folder", "").strip()
    regex_query = request.GET.get("regex", "").strip()
    bulk_query = request.GET.get("bulk", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    selected_ext = request.GET.getlist("ext")
    free_ext = request.GET.get("ext_free", "").strip()
    ext_values = _parse_extensions(free_ext, selected_ext)

    search_active = _is_search_active(
        name_query,
        folder_query,
        regex_query,
        bulk_query,
    ) or any([date_from, date_to, ext_values])

    if not search_active:
        return JsonResponse({"error": "search query required"}, status=400)

    entries = FileEntry.objects.all()
    filtered, error = _apply_filters(
        entries,
        name_query,
        folder_query,
        regex_query,
        bulk_query,
        date_from,
        date_to,
        ext_values,
    )
    if error:
        return JsonResponse({"error": error}, status=400)

    if not filtered:
        return JsonResponse({"error": "no files"}, status=404)

    return _zip_response(filtered, "search-results.zip")


def download_selected(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)

    selected = request.POST.getlist("selected")
    if not selected:
        return JsonResponse({"error": "no files selected"}, status=400)

    entries = list(FileEntry.objects.filter(relative_path__in=selected))
    if not entries:
        return JsonResponse({"error": "file not found"}, status=404)

    return _zip_response(entries, "selected-results.zip")
