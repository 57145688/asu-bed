"""ASU BED 流水线 — 续跑（前 4 步已成功，从 LCA 开始）

asu-bed 特殊点：
- 有 DWSIM simulation.yaml（已 converged）
- 有完整 lca/ 结果（results.csv/md, inventory.csv, dataset.yaml, scenarios/）
- 4 张 P&ID (P-01..P-04)，4 个 HAZOP (H-01..H-04)
- Brightway 跳过（缺 bw2calc），直接用 cheme built-in LCA
- 无 terminal_summary / 无 FreeCAD
"""
from __future__ import annotations

import glob, hashlib, json, os, shutil, subprocess, sys, yaml
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BED = ROOT / "bed"
PY = sys.executable
CHEME = shutil.which("cheme") or str(ROOT.parent / ".venv" / "Scripts" / "cheme.exe")


def run(name, cmd, check=True, env=None):
    print(f"\n=== {name} ===", flush=True)
    print("$", " ".join(str(c) for c in cmd), flush=True)
    proc = subprocess.run(
        [str(c) for c in cmd], cwd=str(ROOT), text=True, encoding="utf-8",
        errors="replace", env={**os.environ, **(env or {})},
    )
    print(f"[{name}] exit={proc.returncode}", flush=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"{name} failed with {proc.returncode}")
    return proc.returncode


def sha(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()[:16]


def main() -> int:
    # --- 5. LCA (cheme built-in, open factors) ---
    run("LCA (cheme)", [CHEME, "assess", "lca", "--write"], check=False)

    # --- 6. PSI 应力初算 ---
    run("PSI batch stress", [PY, ROOT / "tools" / "psi_batch.py"])

    # --- 7. HAZOP 导出 ---
    run("HAZOP export", [PY, ROOT / "tools" / "hazop_export.py"])

    # --- 8. HAZOP reports 遍历 H-01..H-04 ---
    hazon_ids = sorted(
        d.name for d in (ROOT / "safety" / "hazop").iterdir() if d.is_dir()
    ) if (ROOT / "safety" / "hazop").exists() else []
    print(f"\nHAZOP studies = {hazon_ids}", flush=True)
    for hid in hazon_ids:
        run(f"HAZOP report {hid}", [CHEME, "safety", "hazop", "report", hid], check=False)
        src_md = ROOT / "build" / "hazop" / f"{hid}.md"
        src_html = ROOT / "build" / "hazop" / f"{hid}.html"
        if src_md.exists():
            shutil.copy2(src_md, BED / "hazop" / f"{hid}-full-report.md")
        if src_html.exists():
            shutil.copy2(src_html, BED / "hazop" / f"{hid}-full-report.html")

    # --- 9. 渲染所有 P&ID ---
    (BED / "pid").mkdir(parents=True, exist_ok=True)
    for pid_xml in sorted(glob.glob(str(ROOT / "pid" / "*.xml"))):
        pid_id = Path(pid_xml).stem
        run(f"render {pid_id}", [CHEME, "render", pid_xml, "-o", str(BED / "pid" / f"{pid_id}.svg")],
            check=False)

    # --- 10. 复制上游原始文件 ---
    copies = [
        (ROOT / "plant.yaml", BED / "plant.yaml"),
        (ROOT / "DESIGN.md", BED / "DESIGN.md"),
        (ROOT / "README.md", BED / "README.md"),
        (ROOT / "process" / "design-basis.yaml", BED / "dwsim" / "design-basis.yaml"),
        (ROOT / "process" / "simulation.yaml", BED / "dwsim" / "simulation-spec.yaml"),
        (ROOT / "process" / "simulation-run.json", BED / "dwsim" / "simulation-run.json"),
        (ROOT / "lca" / "results.md", BED / "lca" / "cheme-lca-results.md"),
        (ROOT / "lca" / "results.csv", BED / "lca" / "cheme-lca-results.csv"),
        (ROOT / "lca" / "inventory.csv", BED / "lca" / "cheme-lca-inventory.csv"),
        (ROOT / "estimate" / "tea.md", BED / "estimate" / "tea.md"),
        (ROOT / "estimate" / "mto.md", BED / "estimate" / "mto.md"),
    ]
    for src, dst in copies:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  copy {src.name} -> {dst.relative_to(BED)}")

    # --- 11. MANIFEST ---
    artifacts = []
    for path in sorted(BED.rglob("*")):
        if path.is_file():
            artifacts.append(
                {"path": path.relative_to(BED).as_posix(), "bytes": path.stat().st_size,
                 "sha256_16": sha(path)}
            )

    plant = yaml.safe_load((ROOT / "plant.yaml").read_text(encoding="utf-8")) if (ROOT / "plant.yaml").exists() else {}
    flowsheet = yaml.safe_load((ROOT / "process" / "flowsheet.yaml").read_text(encoding="utf-8"))

    feed_count = len(flowsheet.get("feeds", []))
    product_count = len(flowsheet.get("products", []))
    block_count = len(flowsheet.get("blocks", []))
    step_count = len(flowsheet.get("steps", []))
    stream_count = len(flowsheet.get("streams", []))

    summary = (
        f"ASU 深冷空分（asu-1, GoO2=99.6% / 400 t/d 液氧 / 6000 Nm³/h 氮 / 18000 kW 电）"
    )
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plant": summary,
        "stage": plant.get("stage", "basic"),
        "kind": "BED 基础工程设计包（basic engineering design）",
        "level": "BED 基础级：用于方案比选与下一阶段 FEED 设计输入；不用于施工、采购、许可或安全决策",
        "upstream": "ChemE-as-Code/process-library process:asu-1",
        "plant_summary": {
            "feeds": feed_count, "products": product_count,
            "blocks": block_count, "steps": step_count, "streams": stream_count,
            "hazop_studies": hazon_ids,
        },
        "artifacts": artifacts,
    }
    (BED / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    md = [
        "# ASU 空分厂 BED 包清单",
        "",
        f"生成时间：{manifest['generated_at']}",
        "",
        f"**工厂**：ASU 深冷空分 — {feed_count} feeds / {product_count} products / "
        f"{block_count} blocks / {step_count} steps / {stream_count} streams",
        "",
        f"**HAZOP studies**：{', '.join(hazon_ids) if hazon_ids else 'N/A'}",
        "",
        f"**上游**：ChemE-as-Code/process-library `processes/asu-1`",
        "",
        "> 定位：**BED 基础级**。用于路线比选、规模论证与 FEED 设计输入；"
        "不用于施工、采购、许可或安全决策。HAZOP 为 draft，PSI 为保守筛查，LCA 为 gate-to-gate。",
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
