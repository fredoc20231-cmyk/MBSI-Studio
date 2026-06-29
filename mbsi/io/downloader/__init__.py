"""Real-time dataset download, inspection, and progressive analysis."""

from mbsi.io.downloader.archive import extract_archive, is_archive, list_archive_contents
from mbsi.io.downloader.inspector import (
    build_required_file_checklist,
    inspect_downloaded_files,
    update_ingestion_readiness,
)
from mbsi.io.downloader.manager import (
    cancel_download_job,
    create_download_job,
    download_file,
    run_download_job,
    start_download_job_async,
)
from mbsi.io.downloader.manifest import (
    DownloadManifest,
    load_manifest,
    save_manifest,
)
from mbsi.io.downloader.parse_commands import (
    classify_download_url,
    extract_urls_from_text,
    infer_filename_from_url,
)
from mbsi.io.downloader.patch_analyzer import (
    run_incremental_patch_analysis,
    run_patch_preview_analysis,
    select_preview_patch,
)
from mbsi.io.downloader.progress import ProgressTracker, make_progress_callback

__all__ = [
    "extract_archive",
    "is_archive",
    "list_archive_contents",
    "build_required_file_checklist",
    "inspect_downloaded_files",
    "update_ingestion_readiness",
    "cancel_download_job",
    "create_download_job",
    "download_file",
    "run_download_job",
    "start_download_job_async",
    "DownloadManifest",
    "load_manifest",
    "save_manifest",
    "classify_download_url",
    "extract_urls_from_text",
    "infer_filename_from_url",
    "run_incremental_patch_analysis",
    "run_patch_preview_analysis",
    "select_preview_patch",
    "ProgressTracker",
    "make_progress_callback",
]
