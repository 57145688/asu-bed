"""BED 流水线编排：一次跑完校验、DEXPI、三维、应力、LCA、HAZOP，并写清单。

用法（在 ammonia-bed 根目录）：
  python tools/run_pipeline.py            # 全部
  python tools/run_pipeline.py --skip-cad # 跳过 FreeCAD
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BED = ROOT / "bed"
PY = sys.executable
CHEME = shutil.which("cheme") or str(ROOT.parent / ".venv" / "Scripts" / "cheme.exe")
FREECAD = os.environ.get(
    "FREECAD_CMD", r"D:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe"
)


def run(name, cmd, cwd=ROOT, check=True, env=None):
    print(f"\n=== {name} ===", flush=True)
    print("$", " ".join(str(c) for c in cmd), flush=True)
    proc = subprocess.run(
        [str(c) for c in cmd], cwd=str(cwd), text=True, encoding="utf-8",
        errors="replace", env={**os.environ, **(env or {})},
    )
    print(f"[{name}] exit={proc.returncode}", flush=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"{name} failed with {proc.returncode}")
    return proc.returncode


def sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-cad", action="store_true")
    args = ap.parse_args()

    run("cheme validate", [CHEME, "validate"])
    run("DEXPI check", [PY, ROOT / "tools" / "dexpi_check.py"])
    (BED / "dwsim").mkdir(parents=True, exist_ok=True)
    with (BED / "dwsim" / "stream-table.csv").open("w", encoding="utf-8", newline="") as fp:
        subprocess.run([CHEME, "process", "streams", "--csv"], cwd=str(ROOT),
                       stdout=fp, text=True, encoding="utf-8")

    run("DWSIM summary", [PY, ROOT / "tools" / "dwsim_summary.py"])
    run("LCA (Brightway 2.5)", [PY, ROOT / "tools" / "brightway_lca.py"])
    run("LCA (cheme, open factors)", [CHEME, "assess", "lca", "--write"], check=False)
    run("PSI batch stress", [PY, ROOT / "tools" / "psi_batch.py"])
    run("HAZOP export", [PY, ROOT / "tools" / "hazop_export.py"])
    run("HAZOP report", [CHEME, "safety", "hazop", "report", "H-01"], check=False)
    if (ROOT / "build" / "hazop" / "H-01.md").exists():
        shutil.copy2(ROOT / "build" / "hazop" / "H-01.md", BED / "hazop" / "H-01-full-report.md")
        shutil.copy2(ROOT / "build" / "hazop" / "H-01.html", BED / "hazop" / "H-01-full-report.html")

    if not args.skip_cad:
        run("layout -> JSON", [PY, ROOT / "tools" / "model_to_json.py"])
        if Path(FREECAD).exists():
            run("FreeCAD STEP", [FREECAD, ROOT / "tools" / "freecad_build.py"],
                env={"BED_ROOT": str(ROOT)})
        else:
            print(f"FreeCAD not found at {FREECAD}; skipped", flush=True)

    for src, dst in [
        (ROOT / "process" / "design-basis.yaml", BED / "design-basis.yaml"),
        (ROOT / "process" / "simulation.yaml", BED / "dwsim" / "simulation-spec.yaml"),
        (ROOT / "process" / "simulation-run.json", BED / "dwsim" / "simulation-run-archived.json"),
        (ROOT / "lca" / "results.md", BED / "lca" / "cheme-lca-results.md"),
    ]:
        if src.exists():
            shutil.copy2(src, dst)

    artifacts = []
    for path in sorted(BED.rglob("*")):
        if path.is_file():
            artifacts.append(
                {"path": path.relative_to(BED).as_posix(), "bytes": path.stat().st_size,
                 "sha256_16": sha(path)}
            )
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plant": "1500 t/d natural-gas ammonia (concept/BED)",
        "level": "BED 方案级可用：用于方案比选与下一步设计输入，不用于施工、采购或安全决策",
        "artifacts": artifacts,
    }
    (BED / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    md = [
        "# 天然气制氨 BED 包清单",
        "",
        f"生成时间：{manifest['generated_at']}",
        "",
        "> 定位：**BED 方案级可用**。用于路线比选、规模论证与下一阶段设计输入；"
        "不用于施工、采购、许可或安全决策。",
        "",
        "| 文件 | 大小 (KB) | SHA256 前 16 位 |",
        "|---|---:|---|",
    ]
    for a in artifacts:
        if a["path"] == "MANIFEST.json":
            continue
        md.append(f"| {a['path']} | {a['bytes'] / 1024:.1f} | `{a['sha256_16']}` |")
    (BED / "MANIFEST.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nMANIFEST: {BED / 'MANIFEST.md'} ({len(artifacts)} artifacts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
