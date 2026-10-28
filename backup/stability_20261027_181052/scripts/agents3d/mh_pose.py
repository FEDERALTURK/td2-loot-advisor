"""MakeHuman (CC0) temel bedenini iskelet ağırlıklarıyla poza sokar ve Blender için hazırlar.

    python mh_pose.py MAKEHUMAN_DATA_DIR OUT.json

Çıktı: pozlanmış köşeler (metre, Blender eksenleri: X = ajanın solu, -Y = ön, Z = yukarı), yalnız 'body' yüzleri,
her köşenin bölgesi (head/torso/arm/hand/leg/foot) ve pozlanmış eklem noktaları. Poz: tüfek iki elle 'hazır' tutuluyor.
"""
import json
import sys

import numpy as np

D, OUT = sys.argv[1], sys.argv[2]

V, F, G, cur = [], [], [], None
for line in open(f"{D}/3dobjs/base.obj"):
    if line.startswith("v "): V.append([float(x) for x in line.split()[1:4]])
    elif line.startswith("g "): cur = line.split()[1]
    elif line.startswith("f "):
        F.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]]); G.append(cur)
V = np.array(V)
sk = json.load(open(f"{D}/rigs/default.mhskel"))
WJ = json.load(open(f"{D}/rigs/default_weights.mhw"))["weights"]
J = sk["joints"]
bones = sk["bones"]
head = {b: V[J[d["head"]]].mean(0) for b, d in bones.items()}
tail = {b: V[J[d["tail"]]].mean(0) for b, d in bones.items()}
parent = {b: d["parent"] for b, d in bones.items()}

order, seen = [], set()
def visit(b):
    if b in seen: return
    if parent[b]: visit(parent[b])
    seen.add(b); order.append(b)
for b in bones: visit(b)


def rot(axis, ang):
    a = np.asarray(axis, float); a = a / (np.linalg.norm(a) or 1)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def align(u, v):
    u = u / np.linalg.norm(u); v = v / np.linalg.norm(v)
    c = np.cross(u, v); s = np.linalg.norm(c)
    if s < 1e-9: return np.eye(3)
    return rot(c, np.arctan2(s, float(np.dot(u, v))))


def about(R, p):
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = p - R @ p; return M


def apply(M, p): return M[:3, :3] @ p + M[:3, 3]


Mw = {}           # her kemik için dünya dönüşümü (dinlenme → poz)
W = {}            # kemiğe uygulanacak ek dünya dönüşümü (pozlanmış eklem etrafında)
def fk():
    for b in order:
        P = Mw[parent[b]] if parent[b] else np.eye(4)
        Mw[b] = (W[b] @ P) if b in W else P
def ph(b): return apply(Mw[parent[b]] if parent[b] else np.eye(4), head[b])     # pozlanmış baş noktası
def pt(b): return apply(Mw[b], tail[b])


def set_world(b, R):
    """b kemiğini (ve alt zincirini) kendi pozlanmış başı etrafında dünya ekseninde döndür."""
    fk(); W[b] = about(R, ph(b)) @ W.get(b, np.eye(4)); fk()


def point(b, target_dir, twist=0.0):
    fk()
    cur = pt(b) - ph(b)
    R = align(cur, target_dir)
    if twist: R = rot(target_dir, twist) @ R
    set_world(b, R)


fk()
H0 = V[:, 1].min()
SH_L, SH_R = head["upperarm01.L"], head["upperarm01.R"]
side_l = 1 if SH_L[0] > 0 else -1              # MakeHuman: .L = +x olmalı
CH = (head["spine03"] + head["spine04"]) / 2
PEL = head["pelvis.L"] * 0 + (head["upperleg01.L"] + head["upperleg01.R"]) / 2


def ik(b1, b2, target, pole):
    """İki kemikli kol IK: b1 (üst kol), b2 (ön kol) — bilek target'a, dirsek pole yönüne."""
    fk()
    S = ph(b1)
    l1 = np.linalg.norm(tail[b1] - head[b1]) + (np.linalg.norm(tail[b1.replace("01", "02")] - head[b1.replace("01", "02")]) if b1.replace("01", "02") in bones else 0)
    l2 = np.linalg.norm(tail[b2] - head[b2]) + (np.linalg.norm(tail[b2.replace("01", "02")] - head[b2.replace("01", "02")]) if b2.replace("01", "02") in bones else 0)
    T = np.asarray(target, float); d = T - S; L = np.linalg.norm(d)
    L = min(L, (l1 + l2) * 0.999); dn = d / np.linalg.norm(d)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L); hgt = np.sqrt(max(0.0, l1 * l1 - a * a))
    pv = np.asarray(pole, float) - S; pv = pv - dn * np.dot(pv, dn); pv /= np.linalg.norm(pv)
    E = S + dn * a + pv * hgt
    # üst kol: baştan dirseğe; ön kol: dirsekten bileğe (01 ve 02 parçaları birlikte döner)
    up_end = b1.replace("01", "02") if b1.replace("01", "02") in bones else b1
    fk(); R = align(pt(up_end) - ph(b1), E - S); set_world(b1, R)
    lo_end = b2.replace("01", "02") if b2.replace("01", "02") in bones else b2
    fk(); R = align(pt(lo_end) - ph(b2), T - ph(b2)); set_world(b2, R)


CURL_SIGN = {"R": 1, "L": float(sys.argv[7]) if len(sys.argv) > 7 else -1}


def curl(hand_side, amount=1.15, thumb=0.6):
    s = hand_side
    fk()
    lat = ph(f"finger2-1.{s}") - ph(f"finger5-1.{s}")
    for f in (2, 3, 4, 5):
        for seg in (1, 2, 3):
            b = f"finger{f}-{seg}.{s}"
            fk(); d = pt(b) - ph(b)
            ax = lat if s == "L" else lat
            set_world(b, rot(ax, amount * (0.6 if seg == 1 else 1.0) * (CURL_SIGN[s])))
    for seg in (2, 3):
        b = f"finger1-{seg}.{s}"
        set_world(b, rot(lat, thumb * CURL_SIGN[s]))


u = 1.0  # MakeHuman birimi ≈ 10 cm
R_, L_ = ("R", "L")
sx = side_l                                     # ajanın solu = +x ise 1
# hedefler omuza göre (MakeHuman birimi ≈ 10 cm): sağ el kabzada (dirsek ~90°), sol el el kundağında
grip = SH_R + np.array([sx * 0.5, -2.65, 2.05])
fore = SH_L + np.array([-sx * 1.3, -2.95, 3.05])
for s_, sg in (("L", -1), ("R", 1)):             # bacakları topla
    set_world(f"upperleg01.{s_}", rot([0, 0, 1], sg * sx * 0.075))
    fk(); set_world(f"foot.{s_}", rot([0, 0, 1], -sg * sx * 0.075))
ik("upperarm01.R", "lowerarm01.R", grip, SH_R + np.array([-sx * 2.0, -3.0, -1.5]))
ik("upperarm01.L", "lowerarm01.L", fore, SH_L + np.array([sx * 2.5, -3.0, -0.5]))
# bilekler: avuçları tüfeğe çevir
fk()
for s, tw in (("R", float(sys.argv[3]) if len(sys.argv) > 3 else 1.2), ("L", float(sys.argv[4]) if len(sys.argv) > 4 else -1.4)):
    fa = ph(f"wrist.{s}") - ph(f"lowerarm01.{s}")
    set_world(f"lowerarm02.{s}", rot(fa, tw))
curl("R", float(sys.argv[5]) if len(sys.argv) > 5 else 1.1)
curl("L", float(sys.argv[6]) if len(sys.argv) > 6 else 0.9)
# hafif duruş: ağırlık bir bacakta, baş hafif yana
set_world("neck01", rot([0, 1, 0], -0.12 * sx))
fk()

# --- deri (LBS)
acc = np.zeros_like(V); wsum = np.zeros(len(V))
for b, lst in WJ.items():
    if b not in Mw: continue
    idx = np.array([i for i, _ in lst]); w = np.array([x for _, x in lst])
    M = Mw[b]
    acc[idx] += w[:, None] * (V[idx] @ M[:3, :3].T + M[:3, 3]); wsum[idx] += w
P = np.where(wsum[:, None] > 0, acc / np.maximum(wsum, 1e-9)[:, None], V)

# --- bölge etiketi (en ağır kemiğe göre)
def region(b):
    if b.startswith(("upperarm", "lowerarm")): return "arm"
    if b.startswith(("wrist", "metacarpal", "finger")): return "hand"
    if b.startswith(("upperleg", "lowerleg", "pelvis", "root")): return "leg"
    if b.startswith(("foot", "toe")): return "foot"
    if b.startswith(("spine", "breast", "clavicle", "shoulder")): return "torso"
    return "head"
best = np.full(len(V), -1.0); lab = ["head"] * len(V)
for b, lst in WJ.items():
    r = region(b)
    for i, w in lst:
        if w > best[i]: best[i] = w; lab[i] = r

# --- Blender eksenleri, metre
S = 0.106
def tb(p): p = np.asarray(p); return [float(p[0]) * S * sx, float(-p[2]) * S, float(p[1] - H0) * S]
keep = [f for f, g in zip(F, G) if g == "body"]
used = sorted({i for f in keep for i in f}); remap = {o: n for n, o in enumerate(used)}
out = {"verts": [tb(P[i]) for i in used], "faces": [[remap[i] for i in f] for f in keep], "labels": [lab[i] for i in used],
       "joints": {b: {"head": tb(ph(b)), "tail": tb(pt(b))} for b in bones if not b.startswith(("levator", "oris", "orbicularis", "risorius", "temporalis", "special", "tongue"))},
       "grip": tb(grip), "fore": tb(fore), "side_l": int(sx),
       "hand_R": tb(np.mean([P[i] for i in range(len(V)) if lab[i] == "hand" and P[i][0] * sx < 0], axis=0)),
       "hand_L": tb(np.mean([P[i] for i in range(len(V)) if lab[i] == "hand" and P[i][0] * sx > 0], axis=0))}
json.dump(out, open(OUT, "w"))
print("verts", len(used), "faces", len(keep), "height m", round(max(v[2] for v in out["verts"]), 3), "side_l", sx)
