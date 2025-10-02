#!/usr/bin/env python3
"""
Deface the specific T1w images flagged in OpenNeuro ds004021 and write them
to a separate output directory while preserving BIDS structure and filenames.

Example:
  python deface_ds004021_separate_out.py \
      --dataset-root /path/to/ds004021 \
      --output-root  /path/to/ds004021_defaced \
      --copy-sidecars \
      --workers 8

Then you can replace originals with:
  rsync -av --progress /path/to/ds004021_defaced/ /path/to/ds004021/

Requirements:
  pip install pydeface
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
import concurrent.futures as cf

REL_FILES = [
    "sub-06/ses-01/anat/sub-06_ses-01_T1w.nii.gz",
    "sub-06/ses-02/anat/sub-06_ses-02_T1w.nii.gz",
    "sub-07/ses-01/anat/sub-07_ses-01_T1w.nii.gz",
    "sub-07/ses-02/anat/sub-07_ses-02_T1w.nii.gz",
    "sub-10/ses-01/anat/sub-10_ses-01_T1w.nii.gz",
    "sub-10/ses-02/anat/sub-10_ses-02_T1w.nii.gz",
    "sub-11/ses-01/anat/sub-11_ses-01_T1w.nii.gz",
    "sub-11/ses-02/anat/sub-11_ses-02_T1w.nii.gz",
    "sub-12/ses-01/anat/sub-12_ses-01_T1w.nii.gz",
    "sub-12/ses-02/anat/sub-12_ses-02_T1w.nii.gz",
    "sub-14/ses-01/anat/sub-14_ses-01_T1w.nii.gz",
    "sub-14/ses-02/anat/sub-14_ses-02_T1w.nii.gz",
    "sub-18/ses-01/anat/sub-18_ses-01_T1w.nii.gz",
    "sub-18/ses-02/anat/sub-18_ses-02_T1w.nii.gz",
    "sub-19/ses-01/anat/sub-19_ses-01_T1w.nii.gz",
    "sub-19/ses-02/anat/sub-19_ses-02_T1w.nii.gz",
    "sub-22/ses-01/anat/sub-22_ses-01_T1w.nii.gz",
    "sub-22/ses-02/anat/sub-22_ses-02_T1w.nii.gz",
    "sub-24/ses-01/anat/sub-24_ses-01_T1w.nii.gz",
    "sub-24/ses-02/anat/sub-24_ses-02_T1w.nii.gz",
    "sub-27/ses-01/anat/sub-27_ses-01_T1w.nii.gz",
    "sub-28/ses-01/anat/sub-28_ses-01_T1w.nii.gz",
    "sub-28/ses-02/anat/sub-28_ses-02_T1w.nii.gz",
    "sub-29/ses-01/anat/sub-29_ses-01_T1w.nii.gz",
    "sub-29/ses-02/anat/sub-29_ses-02_T1w.nii.gz",
    "sub-39/ses-01/anat/sub-39_ses-01_T1w.nii.gz",
    "sub-39/ses-02/anat/sub-39_ses-02_T1w.nii.gz",
]

def run_pydeface(in_file: Path, out_file: Path) -> tuple[bool, str]:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["pydeface", str(in_file), "--outfile", str(out_file)]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             check=True, text=True)
        return True, (res.stdout or "").strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stdout or str(e)).strip()

def copy_sidecar_if_present(in_nii: Path, out_nii: Path) -> None:
    # Copy matching sidecar JSON if exists (e.g., sub-XX_ses-YY_T1w.json)
    src_json = in_nii.with_suffix("").with_suffix(".json")  # handles .nii.gz -> .json
    if src_json.exists():
        dst_json = out_nii.with_suffix("").with_suffix(".json")
        dst_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_json, dst_json)

def process_one(src_root: Path, dst_root: Path, rel: str,
                copy_sidecars: bool = False, skip_existing: bool = False) -> tuple[str, bool, str]:
    src = (src_root / rel).resolve()
    dst = (dst_root / rel).resolve()

    if not src.exists():
        return rel, False, f"Missing source file: {src}"

    if skip_existing and dst.exists():
        if copy_sidecars:
            copy_sidecar_if_present(src, dst)
        return rel, True, "Skipped (already exists)"

    ok, msg = run_pydeface(src, dst)
    if ok and copy_sidecars:
        copy_sidecar_if_present(src, dst)
    return rel, ok, ("defaced" if ok else msg)

def main():
    ap = argparse.ArgumentParser(description="Deface ds004021 flagged T1w images into a separate BIDS folder.")
    ap.add_argument("--dataset-root", required=True, type=Path, help="Path to local ds004021 (source).")
    ap.add_argument("--output-root", required=True, type=Path, help="Path to write defaced BIDS tree (destination).")
    ap.add_argument("--copy-sidecars", action="store_true", help="Also copy matching T1w sidecar .json files if present.")
    ap.add_argument("--skip-existing", action="store_true", help="Skip if output NIfTI already exists.")
    ap.add_argument("--workers", type=int, default=4, help="Number of parallel workers (default: 4).")
    args = ap.parse_args()

    if shutil.which("pydeface") is None:
        print("ERROR: pydeface not found. Install with: pip install pydeface", file=sys.stderr)
        sys.exit(2)

    src_root = args.dataset_root.resolve()
    dst_root = args.output_root.resolve()

    if not src_root.exists():
        print(f"ERROR: dataset root not found: {src_root}", file=sys.stderr)
        sys.exit(2)

    # Basic safety for output path
    if str(dst_root) == "/" or not os.access(dst_root.parent, os.W_OK):
        print(f"ERROR: Output root '{dst_root}' is not writable. Use a path in your home dir.", file=sys.stderr)
        sys.exit(2)
    dst_root.mkdir(parents=True, exist_ok=True)

    print(f"Source: {src_root}")
    print(f"Output: {dst_root}")
    print(f"Workers: {args.workers}")
    print("-" * 72)

    ok_count, err_count = 0, 0
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = [
            ex.submit(process_one, src_root, dst_root, rel,
                      copy_sidecars=args.copy_sidecars, skip_existing=args.skip_existing)
            for rel in REL_FILES
        ]
        for fut in cf.as_completed(futures):
            rel, ok, msg = fut.result()
            print(f"[{'OK' if ok else 'ERR'}] {rel} -> {msg}")
            if ok:
                ok_count += 1
            else:
                err_count += 1

    print("-" * 72)
    print(f"Summary: {ok_count} succeeded, {err_count} failed")
    if err_count:
        sys.exit(1)

if __name__ == "__main__":
    main()
