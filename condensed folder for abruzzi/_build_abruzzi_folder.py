# Created: 2026-02-23
"""
Build a condensed context folder for Abruzzi.
- Copies source code, docs, contracts, bot, frontend, SDK
- Skips sensitive files (.env, private keys, secrets)
- Skips large/irrelevant folders (node_modules, .git, models, renders)
- Targets ~2-2.5 GB max
"""

import os
import shutil
import sys

SOURCE_ROOT = r"k:\kerne mid feb"
DEST_ROOT = r"k:\kerne mid feb\condensed folder for abruzzi"
SIZE_LIMIT_BYTES = 2.5 * 1024 * 1024 * 1024  # 2.5 GB hard ceiling

# ── Directories to exclude entirely ──────────────────────────────────────────
EXCLUDED_DIRS = {
    # Bloat — node_modules everywhere
    "node_modules",
    ".git",
    ".next",
    "venv",
    ".venv",
    "__pycache__",
    ".cache",
    "cache",
    ".foundry",
    "out",               # foundry build artefacts
    "broadcast",         # foundry deployment transactions
    # Huge binary/data dirs (ML weights only — see extensions below)
    "models",
    # Already condensed
    "condensed folder for abruzzi",
    # High-security / ops dirs that Abruzzi doesn't need
    "bagwell_Autonomus_Outreach",
    "leads",
    "penetration testing",
    " penetration testing",
    "investor information",
    # Heavy artefact sub-dirs inside animations (rendered videos)
    "output",
    "example videos",
    # DefiLlama-Official is a massive mirror, skip it; New is our fork (include)
    "DefiLlama-Adapters-Official",
}

# ── File patterns to exclude (name or extension) ─────────────────────────────
EXCLUDED_EXTENSIONS = {
    # Secrets
    ".env",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".secret",
    # Large compiled / binary artefacts
    ".bin",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".wasm",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".lock",      # package-lock.json is noise; handled below
    # ML model weights (include Python source, exclude blobs)
    ".h5",
    ".pkl",
    ".pt",
    ".pth",
    ".onnx",
    ".safetensors",
    ".ckpt",
    ".npy",
    ".npz",
    # Video (too large, no context value for AI)
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    # Design files
    ".psd",
    ".ai",
    ".figma",
    # Animated GIF (usually big)
    ".gif",
    # Data dumps
    ".parquet",
    ".sqlite",
    ".db",
}

# Exact filenames to always skip (case-insensitive)
EXCLUDED_FILENAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.example",      # contains key names, omit to be safe
    "package-lock.json", # huge, not useful for context
    "package-lock.json.bak",
    ".DS_Store",
    "thumbs.db",
    # Private key material
    "keystore.json",
    "mnemonic.txt",
    "seed.txt",
}

# ── Directories to copy but with a file-count / size cap ─────────────────────
# (copy only source files, skip build artefacts inside)
PARTIAL_DIRS = {
    "bot",
    "frontend",
    "sdk",
    "yield-server",
    "src",
    "test",
    "script",
    "docs",
    "gitbook (docs)",
    "data-room",
    "api",
    "integrations",
    "kanban",
    "graphs",
    "white-label-template",
    "projects",
    "kerne for inference via openrouter",
    "Bagwell Kerne tour",
    "Euler_Bug_BountyINFO",
    "deployments",
    "pitch deck",
}

# ── Root-level files to always include ───────────────────────────────────────
ROOT_INCLUDE_EXTENSIONS = {
    ".md", ".txt", ".toml", ".json", ".yaml", ".yml",
    ".py", ".sh", ".bat", ".sol", ".ts", ".js", ".css",
    ".svg", ".png", ".jpg", ".jpeg", ".ico",
    ".gitignore", ".gitmodules", ".gitbook",
    ".code-workspace", ".clinerules",
}

ROOT_INCLUDE_FILENAMES = {
    "Makefile", "AGENTS.md", ".clinerules", "remappings.txt",
    "foundry.toml", "runtime.txt", "requirements-solver.txt",
}

# ─────────────────────────────────────────────────────────────────────────────

total_copied = 0
files_copied = 0
files_skipped = 0


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def should_skip_file(filepath: str) -> bool:
    name = os.path.basename(filepath).lower()
    _, ext = os.path.splitext(name)
    if name in {n.lower() for n in EXCLUDED_FILENAMES}:
        return True
    if ext in EXCLUDED_EXTENSIONS:
        return True
    # Skip very large individual files (> 150 MB) — likely binaries / dumps
    try:
        if os.path.getsize(filepath) > 150 * 1024 * 1024:
            return True
    except OSError:
        return True
    return False


def copy_file(src: str, dest: str):
    global total_copied, files_copied
    size = os.path.getsize(src)
    if total_copied + size > SIZE_LIMIT_BYTES:
        return False  # stop
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    total_copied += size
    files_copied += 1
    if files_copied % 200 == 0:
        print(f"  [{files_copied} files | {human_size(total_copied)}] ...", flush=True)
    return True


def walk_and_copy(src_dir: str, dest_dir: str) -> bool:
    """Returns False when the size limit is hit."""
    global files_skipped
    for entry in sorted(os.scandir(src_dir), key=lambda e: e.name.lower()):
        if entry.is_symlink():
            continue
        rel = os.path.relpath(entry.path, SOURCE_ROOT)
        dest_path = os.path.join(DEST_ROOT, rel)

        if entry.is_dir():
            if entry.name in EXCLUDED_DIRS:
                continue
            # Recurse
            ok = walk_and_copy(entry.path, dest_dir)
            if not ok:
                return False
        else:
            if should_skip_file(entry.path):
                files_skipped += 1
                continue
            ok = copy_file(entry.path, dest_path)
            if not ok:
                print(f"\n⚠  Size limit reached at {human_size(total_copied)} — stopping.")
                return False
    return True


def main():
    print("=" * 60)
    print("Kerne → Condensed Context Folder Builder")
    print(f"Destination: {DEST_ROOT}")
    print(f"Size limit: {human_size(SIZE_LIMIT_BYTES)}")
    print("=" * 60)

    # Clear destination first
    if os.path.exists(DEST_ROOT):
        print("Clearing existing destination folder...")
        shutil.rmtree(DEST_ROOT)
    os.makedirs(DEST_ROOT, exist_ok=True)

    # ── 1. Root-level files ───────────────────────────────────────────────────
    print("\n[1/2] Copying root-level files...")
    for entry in sorted(os.scandir(SOURCE_ROOT), key=lambda e: e.name.lower()):
        if entry.is_dir():
            continue
        name = entry.name
        _, ext = os.path.splitext(name)
        if name in ROOT_INCLUDE_FILENAMES or ext.lower() in ROOT_INCLUDE_EXTENSIONS:
            if not should_skip_file(entry.path):
                dest = os.path.join(DEST_ROOT, name)
                ok = copy_file(entry.path, dest)
                if not ok:
                    print("Size limit hit on root files.")
                    break

    # ── 2. Walk all subdirectories ────────────────────────────────────────────
    print(f"\n[2/2] Walking subdirectories...")
    for entry in sorted(os.scandir(SOURCE_ROOT), key=lambda e: e.name.lower()):
        if not entry.is_dir():
            continue
        if entry.name in EXCLUDED_DIRS:
            print(f"  SKIP (excluded): {entry.name}/")
            continue
        print(f"  Copying: {entry.name}/")
        ok = walk_and_copy(entry.path, DEST_ROOT)
        if not ok:
            break

    print("\n" + "=" * 60)
    print(f"✅ Done!")
    print(f"   Files copied : {files_copied:,}")
    print(f"   Files skipped: {files_skipped:,}")
    print(f"   Total size   : {human_size(total_copied)}")
    print(f"   Destination  : {DEST_ROOT}")
    print("=" * 60)


if __name__ == "__main__":
    main()