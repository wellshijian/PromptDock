# -*- coding: utf-8 -*-
"""PromptDock 自动化构建与版本发布辅助脚本（支持版本递增、编译、SHA-256 校验与便携包生成）"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_SCRIPT = os.path.join(ROOT_DIR, "prompt_dock.py")
SPEC_FILE = os.path.join(ROOT_DIR, "PromptDock.spec")
VERSION_FILE = os.path.join(ROOT_DIR, "version.json")
DIST_EXE = os.path.join(ROOT_DIR, "dist", "PromptDock.exe")
PORTABLE_ZIP = os.path.join(ROOT_DIR, "PromptDock_绿色便携版.zip")
ISS_FILE = os.path.join(ROOT_DIR, "installer.iss")
SETUP_EXE = os.path.join(ROOT_DIR, "PromptDock_Setup.exe")
GITHUB_REPO = "wellshijian/PromptDock"


def read_current_version() -> str:
    with open(MAIN_SCRIPT, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.M)
    if m:
        return m.group(1).strip()
    return "1.0.0"


def bump_patch(version: str) -> str:
    parts = [int(x) for x in re.findall(r"\d+", version)[:3]]
    while len(parts) < 3:
        parts.append(0)
    parts[2] += 1
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def sync_app_version(version: str):
    with open(MAIN_SCRIPT, "r", encoding="utf-8") as f:
        text = f.read()
    new_text, count = re.subn(
        r'^(APP_VERSION\s*=\s*)"[^"]+"',
        rf'\g<1>"{version}"',
        text,
        count=1,
        flags=re.M,
    )
    if count == 0:
        raise RuntimeError("未在 prompt_dock.py 中找到 APP_VERSION 常量")
    with open(MAIN_SCRIPT, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)


def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def build_executable():
    print(f"[build] Running PyInstaller with {SPEC_FILE}...")
    res = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", SPEC_FILE],
        cwd=ROOT_DIR,
    )
    if res.returncode != 0 or not os.path.exists(DIST_EXE):
        raise RuntimeError("PyInstaller 打包失败")
    print(f"[build] Built: {DIST_EXE} ({os.path.getsize(DIST_EXE)} bytes)")


def build_portable_zip():
    with zipfile.ZipFile(PORTABLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(DIST_EXE, arcname="PromptDock.exe")
        readme = os.path.join(ROOT_DIR, "README.md")
        if os.path.exists(readme):
            zf.write(readme, arcname="README.md")
    print(f"[build] Portable zip created: {PORTABLE_ZIP} ({os.path.getsize(PORTABLE_ZIP)} bytes)")


def build_setup_installer(version: str):
    candidates = [
        shutil.which("ISCC"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Inno Setup 6\ISCC.exe"),
    ]
    iscc = next((p for p in candidates if p and os.path.exists(p)), None)
    if not iscc or not os.path.exists(ISS_FILE):
        print("[build] ISCC.exe not found, skipping Setup installer build.")
        return False
    print(f"[build] Building Setup installer via {iscc}...")
    res = subprocess.run([iscc, f"/DMyAppVersion={version}", ISS_FILE], cwd=ROOT_DIR)
    if res.returncode != 0 or not os.path.exists(SETUP_EXE):
        raise RuntimeError("Inno Setup 安装包编译失败")
    print(f"[build] Setup installer created: {SETUP_EXE} ({os.path.getsize(SETUP_EXE)} bytes)")
    return True


def update_version_json(version: str, sha256: str, notes: str = None):
    existing = {}
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    data = {
        "version": version,
        "notes": notes if notes is not None else existing.get("notes", f"PromptDock v{version} 更新发布"),
        "sha256": sha256,
        "download_url": f"https://github.com/{GITHUB_REPO}/releases/latest/download/PromptDock.exe",
        "published_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds"),
    }
    with open(VERSION_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[build] Updated {VERSION_FILE} (v{version}, sha256={sha256[:12]}...)")


def main():
    parser = argparse.ArgumentParser(description="PromptDock 自动化构建与版本同步脚本")
    parser.add_argument("--version", help="显式指定版本号，例如 1.0.1")
    parser.add_argument("--bump", action="store_true", help="自动递增补丁版本号")
    parser.add_argument("--notes", help="本次发布更新说明")
    parser.add_argument("--skip-build", action="store_true", help="仅同步版本号与元数据，不执行 PyInstaller 编译")
    args = parser.parse_args()

    cur_ver = read_current_version()
    target_ver = args.version.lstrip("vV") if args.version else (bump_patch(cur_ver) if args.bump else cur_ver)

    sync_app_version(target_ver)
    print(f"[build] Version synced: {target_ver}")

    if not args.skip_build:
        build_executable()
        build_portable_zip()
        build_setup_installer(target_ver)
        sha = compute_sha256(DIST_EXE)
        update_version_json(target_ver, sha, notes=args.notes)
    else:
        sha = compute_sha256(DIST_EXE) if os.path.exists(DIST_EXE) else ""
        update_version_json(target_ver, sha, notes=args.notes)


if __name__ == "__main__":
    main()
