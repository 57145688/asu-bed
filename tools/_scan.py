import yaml, os, glob

ROOT = r"e:\trae\trae workspace\nsc-ChemE-as-Code\asu-bed"

fs = yaml.safe_load(open(f"{ROOT}/process/flowsheet.yaml"))
s = fs["streams"][0]
state = s.get("state", {})
print(f"[flowsheet] state keys = {list(state.keys())}")

p = yaml.safe_load(open(f"{ROOT}/plant.yaml"))
print(f"[plant] stage = {p.get('stage')}")
print(f"[plant] classification = {p.get('classification')}")

lines = yaml.safe_load(open(f"{ROOT}/piping/line-list.yaml"))
print(f"[piping] line count = {len(lines.get('lines', []))}")

eq = yaml.safe_load(open(f"{ROOT}/equipment/equipment-list.yaml"))
print(f"[equipment] keys = {list(eq.keys())[:5]}")
eq_key = "equipment" if "equipment" in eq else ("items" if "items" in eq else list(eq.keys())[0] if eq else "?")
print(f"[equipment] count = {len(eq.get(eq_key, []))} (key={eq_key})")

hazop_dirs = sorted([d for d in os.listdir(f"{ROOT}/safety/hazop") if d.startswith("H-")])
print(f"[hazop] studies = {hazop_dirs}")

pids = sorted(glob.glob(f"{ROOT}/pid/P-*.xml"))
print(f"[pid] P&IDs = {[os.path.basename(p) for p in pids]}")

sim_path = f"{ROOT}/process/simulation.yaml"
if os.path.exists(sim_path):
    sim = yaml.safe_load(open(sim_path))
    print(f"[sim] engine = {sim.get('engine', sim.get('simulator', '?'))} converged = {sim.get('converged', sim.get('status', '?'))}")
else:
    print("[sim] NO simulation.yaml")

# LCA
lca_path = f"{ROOT}/lca/lca.yaml"
if os.path.exists(lca_path):
    l = yaml.safe_load(open(lca_path))
    print(f"[lca] exists - keys: {list(l.keys())[:5]}")
    res_path = f"{ROOT}/lca/results.csv"
    if os.path.exists(res_path):
        import pandas as pd
        df = pd.read_csv(res_path)
        print(f"[lca] results.csv rows = {len(df)} cols = {list(df.columns)[:8]}")
    res_md = f"{ROOT}/lca/results.md"
    if os.path.exists(res_md):
        with open(res_md, encoding="utf-8") as f:
            lines = f.readlines()
        print(f"[lca] results.md = {len(lines)} lines")

# estimate
tea_path = f"{ROOT}/estimate/tea.yaml"
if os.path.exists(tea_path):
    t = yaml.safe_load(open(tea_path))
    print(f"[tea] keys = {list(t.keys())[:8]}")

print("\n=== FILES ===")
total = 0
by_top = {}
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
    for fn in files:
        total += 1
        rel = os.path.relpath(os.path.join(root, fn), ROOT)
        top = rel.split(os.sep)[0]
        by_top[top] = by_top.get(top, 0) + 1
print(f"total files = {total}")
for k in sorted(by_top.keys()):
    print(f"  {k}/ = {by_top[k]}")
