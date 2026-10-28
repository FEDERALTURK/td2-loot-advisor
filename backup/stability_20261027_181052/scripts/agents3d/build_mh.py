"""Özgün taktik ajan: MakeHuman (CC0) pozlanmış beden + koddan üretilen kıyafet ve teçhizat (Blender).

    blender-python build_mh.py -- --pose posed.json --outfit operator --out DIR [--views q3,side,back] [--turntable 48]
"""
import argparse
import json
import math
import os
import sys

import bpy
import bmesh  # noqa: E402  (bpy'den sonra yüklenmeli)
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_agent as B   # noqa: E402
from build_agent import mat, cube, cyl, sphere, shell, setmat, link, smooth, MATS   # noqa: E402

P = {}          # poz verisi


def J(name, end="head"): return Vector(P["joints"][name][end])


def region_mesh(name, regions, m, offset, thick=0.004, subdiv=1, slot=None, zmin=None, zmax=None, grow=None, extra=None, smooth_iter=0):
    """Bedenin seçili bölgelerinden kıyafet: yüzey normali boyunca dışarı itilir, kalınlık ve yumuşatma verilir."""
    verts, faces, lab = P["verts"], P["faces"], P["labels"]
    ok = [r in regions for r in lab]
    if zmin is not None or zmax is not None:
        ok = [o and (zmin is None or v[2] >= zmin) and (zmax is None or v[2] <= zmax) for o, v in zip(ok, verts)]
    if extra: ok = [o or extra(r, v) for o, r, v in zip(ok, lab, verts)]
    fs = [f for f in faces if all(ok[i] for i in f)]
    used = sorted({i for f in fs for i in f}); rm = {o: n for n, o in enumerate(used)}
    me = bpy.data.meshes.new(name); me.from_pydata([verts[i] for i in used], [], [[rm[i] for i in f] for f in fs]); me.update()
    ob = bpy.data.objects.new(name, me); link(ob, slot); smooth(ob)
    me.validate(); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
    for v in bm.verts:
        o = offset(v.co) if callable(offset) else offset
        v.co += v.normal * o
    bm.to_mesh(me); bm.free()
    if smooth_iter:
        sm = ob.modifiers.new("smooth", "SMOOTH"); sm.factor = 1.0; sm.iterations = smooth_iter
    if thick:
        s = ob.modifiers.new("solid", "SOLIDIFY"); s.thickness = thick; s.offset = 1.0
    if subdiv:
        d = ob.modifiers.new("sub", "SUBSURF"); d.levels = subdiv; d.render_levels = subdiv
    setmat(ob, m)
    return ob


def stats(regions, zmin, zmax):
    vs = [Vector(v) for v, r in zip(P["verts"], P["labels"]) if r in regions and zmin <= v[2] <= zmax]
    xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
    return {"xmin": min(xs), "xmax": max(xs), "ymin": min(ys), "ymax": max(ys), "c": sum(vs, Vector()) / len(vs)}


def rifle(kind="carbine"):
    gun = mat("gunmetal", "#22252a", rough=0.38, metal=0.65, bump=0.05)
    poly = mat("polymer", "#2b2c29", rough=0.55, bump=0.08)
    g, f = Vector(P.get("hand_R", P["grip"])), Vector(P.get("hand_L", P["fore"]))
    f = g + (f - g) * 1.0
    x = (f - g).normalized(); upv = Vector((0, 0, 1))
    z = (upv - x * upv.dot(x)).normalized(); y = z.cross(x)
    from mathutils import Matrix
    E = bpy.data.objects.new("Rifle", None); link(E)
    E.location = g - x * 0.0 + z * 0.0; E.rotation_mode = "QUATERNION"; E.rotation_quaternion = Matrix((x, y, z)).transposed().to_quaternion()
    L = {"dmr": 1.22, "smg": 0.78, "lmg": 1.1}.get(kind, 1.0)
    parts = [cube("Receiver", (0.06, 0, 0.045), (0.26, 0.036, 0.062), gun, bevel=0.006),
             cube("Handguard", (0.29 * L, 0, 0.05), (0.24 * L, 0.048, 0.054), poly, bevel=0.012),
             cyl("Barrel", (0.41 * L, 0, 0.05), (0.58 * L, 0, 0.05), 0.009, gun),
             cyl("Muzzle", (0.58 * L, 0, 0.05), (0.63 * L, 0, 0.05), 0.015, gun),
             cube("Mag", (0.12, 0, -0.03), (0.038, 0.026, 0.07 if kind == "dmr" else (0.02 if kind in ("lmg", "smg") else 0.13)), poly, bevel=0.005, rot=(0, 14, 0)),
             cube("Grip", (0.0, 0, -0.012), (0.032, 0.03, 0.08), poly, bevel=0.006, rot=(0, -18, 0)),
             cyl("Buffer", (-0.08, 0, 0.055), (-0.18, 0, 0.055), 0.016, gun),
             cube("Stock", (-0.23, 0, 0.035), (0.16, 0.038, 0.07), poly, bevel=0.012),
             cube("Mount", (0.07, 0, 0.088), (0.09, 0.026, 0.026), gun)]
    if kind == "dmr": parts.append(cyl("Scope", (-0.04, 0, 0.125), (0.2, 0, 0.125), 0.022, gun, r2=0.027))
    else: parts.append(cyl("Optic", (0.03, 0, 0.118), (0.13, 0, 0.118), 0.02, gun))
    if kind == "lmg":
        parts.append(cube("BoxMag", (0.1, 0.0, -0.055), (0.12, 0.09, 0.11), poly, bevel=0.01))
        parts.append(cube("FeedCover", (0.06, 0, 0.09), (0.18, 0.05, 0.03), gun, bevel=0.006))
        parts.append(cyl("HeavyBarrel", (0.38, 0, 0.05), (0.66, 0, 0.05), 0.016, gun))
        for sg in (-1, 1):
            parts.append(cyl("Bipod%d" % sg, (0.5, sg * 0.012, 0.035), (0.53, sg * 0.05, -0.12), 0.006, gun, verts=8))
    if kind == "smg":
        parts.append(cube("SmgMag", (0.07, 0, -0.08), (0.032, 0.022, 0.17), poly, bevel=0.004, rot=(0, 6, 0)))
    parts.append(cube("Sling", (-0.05, 0.024, 0.03), (0.3, 0.004, 0.02), MATS["strap"]))
    for p in parts: p["slot"] = "Weapon"; p.parent = E


# ------------------------------------------------------------------ kıyafet parçaları
def head_box():
    zs = J("head").z
    return stats({"head"}, zs - 0.02, 3.0)


def helmet(m, rail_m):
    hb = head_box(); c = hb["c"]
    hx, hy = (hb["xmax"] - hb["xmin"]) / 2, (hb["ymax"] - hb["ymin"]) / 2
    top = max(v[2] for v, r in zip(P["verts"], P["labels"]) if r == "head")
    hz = (top - J("head").z) * 0.62
    cc = Vector((c.x, (hb["ymax"] + hb["ymin"]) / 2 + 0.006, top - hz + 0.012))
    shell("Helmet", cc, (hx * 1.2, hy * 1.14, hz * 1.12), m, cut_z=-0.18, thick=0.012)
    for s in (-1, 1): cube("Rail%d" % s, (cc.x + s * hx * 1.18, cc.y + 0.005, cc.z - 0.01), (0.014, hy * 1.2, 0.028), rail_m, bevel=0.004)
    cube("Shroud", (cc.x, cc.y - hy * 1.12, cc.z + hz * 0.45), (0.05, 0.02, 0.035), rail_m, bevel=0.005)
    return cc, hx, hy, hz


def goggles(cc, hx, hy, frame_m, lens_m):
    eye_z = J("head").z + (cc.z - J("head").z) * 0.62
    fy = cc.y - hy * 1.03
    cube("GoggleFrame", (cc.x, fy + 0.012, eye_z), (hx * 1.85, 0.04, 0.062), frame_m, bevel=0.016, slot="Mask")
    cube("GoggleLens", (cc.x, fy - 0.005, eye_z), (hx * 1.7, 0.012, 0.05), lens_m, bevel=0.01, slot="Mask")
    bpy.ops.mesh.primitive_torus_add(major_radius=hx * 1.06, minor_radius=0.007, location=(cc.x, cc.y + 0.004, eye_z))
    t = bpy.context.active_object; t.name = "GoggleStrap"; t.scale = (1, hy / hx * 1.08, 1); setmat(t, MATS["strap"]); link(t, "Mask")


def carrier(m, pouch_m, heavy=False, style="std"):
    z0, z1 = J("spine02").z - 0.06, J("neck01").z - 0.06
    st = stats({"torso"}, z0, z1)
    cx, cy = (st["xmin"] + st["xmax"]) / 2, (st["ymin"] + st["ymax"]) / 2
    w = (st["xmax"] - st["xmin"]) * 0.7; zc = (z0 + z1) / 2; hgt = (z1 - z0)
    t = 0.05 if heavy else 0.038
    fy, by = st["ymin"] - 0.012 - t / 2, st["ymax"] + 0.01 + t / 2
    cube("PlateF", (cx, fy, zc), (w, t, hgt), m, bevel=0.016, slot="Chest")
    cube("PlateB", (cx, by, zc + 0.01), (w * 1.02, t, hgt * 1.05), m, bevel=0.016, slot="Chest")
    for s in (-1, 1):
        cube("Cummer%d" % s, (cx + s * ((st["xmax"] - st["xmin"]) / 2 + 0.008), cy, zc - hgt * 0.25), (0.03, by - fy, hgt * 0.45), m, bevel=0.01, slot="Chest")
        cube("ShStrap%d" % s, (cx + s * w * 0.32, cy, z1 + 0.035), (0.06, by - fy + 0.01, 0.03), m, bevel=0.008, slot="Chest")
    if style == "std":
        for i, x in enumerate((-0.085, 0.0, 0.085)):
            cube("MagPouch%d" % i, (cx + x * w / 0.29, fy - t / 2 - 0.02, zc - hgt * 0.22), (0.072, 0.042, hgt * 0.42), pouch_m, bevel=0.01, slot="Chest")
        cube("Admin", (cx, fy - t / 2 - 0.014, zc + hgt * 0.2), (w * 0.55, 0.03, hgt * 0.22), pouch_m, bevel=0.01, slot="Chest")
        cube("Radio", (cx - w * 0.62, cy - 0.02, zc - hgt * 0.1), (0.04, 0.07, hgt * 0.4), pouch_m, bevel=0.01, slot="Chest")
    elif style == "slick":
        cube("Admin", (cx, fy - t / 2 - 0.01, zc + hgt * 0.05), (w * 0.62, 0.022, hgt * 0.3), pouch_m, bevel=0.008, slot="Chest")
        for i, x in enumerate((-0.05, 0.05)):
            cube("Flat%d" % i, (cx + x, fy - t / 2 - 0.01, zc - hgt * 0.3), (0.07, 0.02, hgt * 0.22), pouch_m, bevel=0.006, slot="Chest")
    elif style == "heavy":
        for i, x in enumerate((-0.1, -0.035, 0.035, 0.1)):
            cube("MagPouch%d" % i, (cx + x * w / 0.29, fy - t / 2 - 0.024, zc - hgt * 0.2), (0.062, 0.048, hgt * 0.44), pouch_m, bevel=0.01, slot="Chest")
        cube("Admin", (cx, fy - t / 2 - 0.016, zc + hgt * 0.24), (w * 0.6, 0.034, hgt * 0.22), pouch_m, bevel=0.01, slot="Chest")
    if heavy:
        for sg in (-1, 1):
            sh = J("upperarm01." + ("L" if sg * P.get("side_l", 1) > 0 else "R"))
            shell("Pauldron%d" % sg, (sh.x + sg * 0.03, sh.y, sh.z + 0.015), (0.09, 0.105, 0.075), m, cut_z=-0.15, slot="Chest", thick=0.012)
        n = J("neck01")
        cyl("Collar", (cx, cy, z1 + 0.01), (cx, cy, z1 + 0.075), (st["xmax"] - st["xmin"]) * 0.32, m, slot="Chest", verts=24, r2=(st["xmax"] - st["xmin"]) * 0.27)
        wz = J("upperleg01.L").z
        cube("Groin", (cx, fy + 0.005, wz + 0.01), (0.18, 0.03, 0.17), m, bevel=0.015, slot="Chest")
        for sg in (-1, 1):
            cube("Tasset%d" % sg, (cx + sg * 0.11, fy + 0.03, wz + 0.02), (0.11, 0.03, 0.15), m, bevel=0.014, slot="Chest", rot=(0, 0, sg * 12))
    return {"fy": fy, "by": by + t / 2, "cx": cx, "zc": zc, "w": w, "h": hgt}


def chest_rig(m, pouch_m):
    """Hafif göğüs teçhizatı: H askı + karın hizasında cep sırası."""
    z0, z1 = J("spine02").z - 0.08, J("neck01").z - 0.06
    st = stats({"torso"}, z0, z1); cx = (st["xmin"] + st["xmax"]) / 2; cy = (st["ymin"] + st["ymax"]) / 2
    zc = z0 + 0.06; w = (st["xmax"] - st["xmin"]) * 0.78
    cube("RigPanel", (cx, st["ymin"] - 0.016, zc), (w, 0.03, 0.15), m, bevel=0.01, slot="Chest")
    for i, x in enumerate((-0.11, -0.037, 0.037, 0.11)):
        cube("RigPouch%d" % i, (cx + x * w / 0.3, st["ymin"] - 0.045, zc - 0.005), (0.06, 0.036, 0.13), pouch_m, bevel=0.009, slot="Chest")
    for sg in (-1, 1):
        cyl("HStrapF%d" % sg, (cx + sg * 0.09, st["ymin"] - 0.012, zc + 0.07), (cx + sg * 0.1, cy - 0.02, z1 + 0.05), 0.016, m, slot="Chest", verts=6)
        cyl("HStrapB%d" % sg, (cx + sg * 0.1, cy + 0.02, z1 + 0.05), (cx + sg * 0.08, st["ymax"] + 0.015, zc + 0.05), 0.016, m, slot="Chest", verts=6)
    return {"fy": st["ymin"] - 0.03, "by": st["ymax"] + 0.012, "cx": cx, "zc": (z0 + z1) / 2, "w": w, "h": z1 - z0}


def backpack(m, cr, w=0.32, h=0.44, d=0.17):
    y = cr["by"] + d / 2 + 0.005; z = cr["zc"] - 0.02
    cube("Pack", (cr["cx"], y, z), (w, d, h), m, bevel=0.045, subdiv=1, slot="Backpack")
    for s in (-1, 1):
        cube("PackSide%d" % s, (cr["cx"] + s * (w / 2 + 0.025), y, z - 0.06), (0.05, d * 0.7, h * 0.45), m, bevel=0.015, slot="Backpack")
    cube("PackLid", (cr["cx"], y - 0.005, z + h / 2), (w * 0.9, d * 0.95, 0.05), m, bevel=0.02, slot="Backpack")
    cube("PackPouch", (cr["cx"], y + d / 2 + 0.018, z - 0.05), (w * 0.62, 0.04, h * 0.45), m, bevel=0.012, slot="Backpack")


def boots(m, ank):
    """Bot: ayak kutusu (topuktan buruna, ayak yönünde) + konç; yuvarlatılmış."""
    from mathutils import Matrix
    rub = MATS.get("rubber") or mat("rubber", "#121314", rough=0.65, bump=0.1)
    for s in "LR":
        a = J("foot." + s)
        fv = [Vector(v) for v, r in zip(P["verts"], P["labels"]) if r == "foot" and (v[0] > 0) == (a.x > 0)]
        toe = min(fv, key=lambda v: v.y)
        d = Vector((toe.x - a.x, toe.y - a.y, 0)).normalized()
        heel_y = max(v.y for v in fv)
        length = (toe - Vector((a.x, heel_y, 0))).length + 0.03
        width = (max(v.x for v in fv) - min(v.x for v in fv)) + 0.012
        ang = math.atan2(d.x, -d.y)
        c = Vector((a.x, heel_y, 0)) + d * (length / 2 - 0.02)
        cube("Boot" + s, (c.x, c.y, 0.06), (width, length, 0.095), m, bevel=0.035, rot=(0, 0, math.degrees(ang)), subdiv=1)
        cube("Toe" + s, (c.x + d.x * length * 0.33, c.y + d.y * length * 0.33, 0.05), (width * 0.95, length * 0.32, 0.075), m, bevel=0.035, rot=(0, 0, math.degrees(ang)), subdiv=1)
        cube("Sole" + s, (c.x, c.y, 0.014), (width + 0.008, length + 0.01, 0.026), rub, bevel=0.01, rot=(0, 0, math.degrees(ang)))
        cyl("Shaft" + s, (a.x, a.y + 0.01, 0.08), (a.x, a.y + 0.005, ank + 0.035), 0.06, m, verts=24, r2=0.064)
        cyl("Lace" + s, (a.x, a.y - 0.05, 0.09), (a.x, a.y - 0.035, ank + 0.02), 0.012, MATS["strap"], verts=8)


def cuffs(shirt_m, pants_m, ank):
    for s in "LR":
        w = J("wrist." + s); e = J("lowerarm02." + s)
        d = (w - e).normalized()
        cyl("Cuff" + s, w - d * 0.055, w - d * 0.005, 0.047, shirt_m, verts=20)


def cargo(m):
    for s in "LR":
        a, b = J("upperleg01." + s), J("upperleg01." + s, "tail")
        mid = a.lerp(b, 0.62)
        side_v = [v for v, r in zip(P["verts"], P["labels"]) if r == "leg" and abs(v[2] - mid.z) < 0.03 and (v[0] > 0) == (a.x > 0)]
        if s == "R":                                  # sağda kılıf var: cep biraz önde
            ox = min(v[1] for v in side_v)
            cube("Cargo" + s, (mid.x, ox - 0.012, mid.z - 0.04), (0.11, 0.035, 0.14), m, bevel=0.015)
            cube("Flap" + s, (mid.x, ox - 0.03, mid.z + 0.035), (0.115, 0.02, 0.035), m, bevel=0.008)
        else:
            ox = max(abs(v[0]) for v in side_v) * (1 if a.x > 0 else -1); sg = 1 if a.x > 0 else -1
            cube("Cargo" + s, (ox + sg * 0.014, mid.y, mid.z - 0.04), (0.035, 0.12, 0.15), m, bevel=0.015)
            cube("Flap" + s, (ox + sg * 0.032, mid.y, mid.z + 0.035), (0.02, 0.125, 0.038), m, bevel=0.008)


def soles():
    rub = MATS.get("rubber") or mat("rubber", "#121314", rough=0.65, bump=0.1)
    for s in "LR":
        fv = [Vector(v) for v, r in zip(P["verts"], P["labels"]) if r == "foot" and (v[0] > 0) == (J("foot." + s).x > 0)]
        ys = [v.y for v in fv]; xs = [v.x for v in fv]
        cx = sum(xs) / len(xs)
        cube("Sole" + s, (cx, (min(ys) + max(ys)) / 2, 0.014), (max(xs) - min(xs) + 0.035, max(ys) - min(ys) + 0.045, 0.028), rub, bevel=0.01)


def belt(m):
    z = J("upperleg01.L").z + 0.11
    st = stats({"leg", "torso"}, z - 0.03, z + 0.03)
    c = Vector(((st["xmin"] + st["xmax"]) / 2, (st["ymin"] + st["ymax"]) / 2, z))
    ob = cyl("Belt", (c.x, c.y, z - 0.025), (c.x, c.y, z + 0.025), (st["xmax"] - st["xmin"]) / 2 + 0.018, m, verts=32)
    ob.scale = (1, (st["ymax"] - st["ymin"] + 0.036) / (st["xmax"] - st["xmin"] + 0.036), 1)
    cube("Buckle", (c.x, st["ymin"] - 0.016, z), (0.06, 0.012, 0.045), MATS["blackpoly"], bevel=0.004)
    return c, st


def kneepads(m):
    for s in "LR":
        k = J("lowerleg01." + s)
        st = stats({"leg"}, k.z - 0.03, k.z + 0.03)
        side = [v for v, r in zip(P["verts"], P["labels"]) if r == "leg" and abs(v[2] - k.z) < 0.03 and (v[0] > 0) == (k.x > 0)]
        fy = min(v[1] for v in side)
        shell("Knee" + s, (k.x, fy + 0.012, k.z - 0.01), (0.058, 0.07, 0.042), m, cut_z=0.0, slot="Kneepads", thick=0.012, rot=(90, 0, 0))
        r = max(abs(v[0] - k.x) for v in side) + 0.016
        cyl("KneeStrap" + s, (k.x, k.y, k.z + 0.04), (k.x, k.y, k.z + 0.062), r, MATS["strap"], slot="Kneepads", verts=24)
        cyl("KneeStrapB" + s, (k.x, k.y, k.z - 0.07), (k.x, k.y, k.z - 0.05), r * 0.9, MATS["strap"], slot="Kneepads", verts=24)


def holster(m, grip_m, side="R"):
    a, b = J("upperleg01." + side), J("upperleg01." + side, "tail")
    mid = a.lerp(b, 0.55)
    side_v = [v for v, r in zip(P["verts"], P["labels"]) if r == "leg" and abs(v[2] - mid.z) < 0.03 and (v[0] > 0) == (a.x > 0)]
    ox = max(abs(v[0]) for v in side_v) * (1 if a.x > 0 else -1)
    sg = 1 if a.x > 0 else -1
    cube("LegPlatform", (ox + sg * 0.012, mid.y, mid.z), (0.024, 0.11, 0.21), m, slot="Holster")
    cube("HolsterBody", (ox + sg * 0.04, mid.y - 0.01, mid.z), (0.05, 0.08, 0.18), m, bevel=0.014, slot="Holster")
    r = abs(ox - a.x) + 0.01
    for dz in (-0.06, 0.07):
        cyl("LegStrap%s%d" % (side, dz * 100), (a.x, mid.y, mid.z + dz), (a.x, mid.y, mid.z + dz + 0.022), r, MATS["strap"], slot="Holster", verts=24)
    cube("PistolGrip", (ox + sg * 0.04, mid.y + 0.005, mid.z + 0.12), (0.036, 0.052, 0.078), grip_m, bevel=0.008, rot=(-12, 0, 0), slot="Sidearm")


# ------------------------------------------------------------------ kıyafetler
def outfit_operator():
    MATS["strap"] = mat("strap", "#1b1c1a", rough=0.75, bump=0.3, webbing=True)
    MATS["blackpoly"] = mat("blackpoly", "#151617", rough=0.5, bump=0.05)
    shirt = mat("shirt", "#3f443b", rough=0.86, bump=0.4, scale=220, sheen=0.12, folds=0.8)
    pants = mat("pants", "#5a5341", rough=0.88, bump=0.4, scale=220, camo=["#3a3729", "#6f6550"], sheen=0.1, folds=0.9)
    waist = J("upperleg01.L").z + 0.11
    ank = J("foot.L").z + 0.11
    region_mesh("Shirt", {"torso", "arm"}, shirt, 0.02, thick=0.004, smooth_iter=3)
    region_mesh("Pants", {"leg"}, pants, 0.026, thick=0.004, zmin=ank - 0.03, smooth_iter=4, extra=lambda r, v: r == "torso" and v[2] < waist)
    cuffs(shirt, pants, ank)
    cargo(pants)
    bala = mat("balaclava", "#151617", rough=0.92, bump=0.6, scale=300, sheen=0.1)
    region_mesh("Balaclava", {"head"}, bala, 0.004, thick=0.003, slot="Mask")
    region_mesh("Gloves", {"hand"}, mat("glove", "#2a2b2c", rough=0.7, bump=0.3), 0.004, thick=0.003, slot="Gloves")
    boots(mat("boot", "#3a2f24", rough=0.55, bump=0.35), ank)
    cc, hx, hy, hz = helmet(mat("helmet", "#6f634b", rough=0.55, bump=0.12, coat=0.15), MATS["blackpoly"])
    goggles(cc, hx, hy, mat("rubber", "#121314", rough=0.65, bump=0.1), mat("lens", "#1c2a33", rough=0.05, metal=0.4, bump=0, coat=1.0))
    cr = carrier(mat("coyote", "#6a5a41", rough=0.8, bump=0.45, webbing=True, sheen=0.12), mat("pouch", "#5f523d", rough=0.8, bump=0.4, webbing=True))
    belt(MATS["strap"])
    kneepads(mat("kneecap", "#19191a", rough=0.45, bump=0.08))
    holster(mat("holster", "#1c1d1e", rough=0.55, bump=0.12), MATS["blackpoly"])
    backpack(mat("pack", "#4a4a38", rough=0.82, bump=0.45, webbing=True, sheen=0.12), cr)
    rifle("carbine")




# ------------------------------------------------------------------ baş parçaları
def head_geo():
    hb = head_box(); c = hb["c"]
    hx, hy = (hb["xmax"] - hb["xmin"]) / 2, (hb["ymax"] - hb["ymin"]) / 2
    top = max(v[2] for v, r in zip(P["verts"], P["labels"]) if r == "head")
    hz = (top - J("head").z) * 0.62
    cc = Vector((c.x, (hb["ymax"] + hb["ymin"]) / 2 + 0.006, top - hz + 0.012))
    eye_z = J("head").z + (cc.z - J("head").z) * 0.62
    return cc, hx, hy, hz, top, eye_z


def open_shell(name, loc, scale, m, cut_z, face_open, face_zmax, thick=0.008, slot=None):
    """Önü açık kabuk (kapüşon): alt kesim + yüz açıklığı."""
    ob = sphere(name, loc, scale, m, slot=slot, seg=40, rings=20)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    rm = [v for v in bm.verts if v.co.z < cut_z * scale[2] or (v.co.y < -face_open * scale[1] and v.co.z < face_zmax * scale[2])]
    bmesh.ops.delete(bm, geom=rm, context="VERTS"); bm.to_mesh(ob.data); bm.free()
    B.mods(ob, solid=thick, subdiv=1); smooth(ob)
    return ob


def visor(name, cc, hx, hy, hz, m):
    ob = sphere(name, (cc.x, cc.y - 0.01, cc.z - hz * 0.25), (hx * 1.32, hy * 1.26, hz * 1.05), m, slot="Mask", seg=40, rings=20)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    rm = [v for v in bm.verts if v.co.y > -0.25 * hy * 1.26 or v.co.z < -0.85 * hz * 1.05 or v.co.z > 0.42 * hz * 1.05]
    bmesh.ops.delete(bm, geom=rm, context="VERTS"); bm.to_mesh(ob.data); bm.free()
    B.mods(ob, solid=0.006); smooth(ob)


def lower_face(name, m, eye_z, off=0.012):
    return region_mesh(name, {"head"}, m, off, thick=0.004, slot="Mask", zmax=eye_z - 0.012, smooth_iter=2)


def glasses(cc, hx, hy, eye_z, lens_m, frame_m):
    fy = cc.y - hy * 1.02
    cube("Glasses", (cc.x, fy - 0.006, eye_z), (hx * 1.6, 0.01, 0.034), lens_m, bevel=0.008, slot="Mask")
    for sg in (-1, 1):
        cube("Temple%d" % sg, (cc.x + sg * hx * 0.98, cc.y - hy * 0.4, eye_z + 0.004), (0.006, hy * 1.2, 0.008), frame_m, slot="Mask")


def sling_bag(m, cr):
    sl = P.get("side_l", 1)
    cube("SlingBag", (cr["cx"] - 0.05 * sl, cr["by"] + 0.07, cr["zc"] - 0.06), (0.26, 0.11, 0.3), m, bevel=0.035, subdiv=1, slot="Backpack", rot=(0, 18 * sl, 0))
    a, b = J("upperarm01.L"), J("upperleg01.R")
    cyl("BagStrap", (a.x - 0.02, cr["fy"] - 0.01, a.z + 0.03), (b.x + 0.02, cr["fy"] - 0.012, b.z + 0.12), 0.022, m, slot="Backpack", verts=6)
    cyl("BagStrapB", (a.x - 0.02, cr["by"] + 0.01, a.z + 0.03), (b.x, cr["by"] + 0.02, b.z + 0.14), 0.022, m, slot="Backpack", verts=6)


def antenna(cr, m):
    cyl("Antenna", (cr["cx"] + 0.09, cr["by"] + 0.12, cr["zc"] + 0.22), (cr["cx"] + 0.12, cr["by"] + 0.15, cr["zc"] + 0.62), 0.005, m, slot="Backpack", verts=6, r2=0.003)


def base_mats():
    MATS["strap"] = mat("strap", "#1b1c1a", rough=0.75, bump=0.3, webbing=True)
    MATS["blackpoly"] = mat("blackpoly", "#151617", rough=0.5, bump=0.05)
    MATS["rubber"] = mat("rubber", "#121314", rough=0.65, bump=0.1)
    MATS["lens"] = mat("lens", "#1c2a33", rough=0.05, metal=0.4, bump=0, coat=1.0)


def dress(shirt, pants, glove, boot, shirt_off=0.02, pants_off=0.026, shirt_smooth=3):
    waist = J("upperleg01.L").z + 0.11
    ank = J("foot.L").z + 0.11
    region_mesh("Shirt", {"torso", "arm"}, shirt, shirt_off, thick=0.004, smooth_iter=shirt_smooth)
    region_mesh("Pants", {"leg"}, pants, pants_off, thick=0.004, zmin=ank - 0.03, smooth_iter=4, extra=lambda r, v: r == "torso" and v[2] < waist)
    cuffs(shirt, pants, ank)
    cargo(pants)
    region_mesh("Gloves", {"hand"}, glove, 0.004, thick=0.003, slot="Gloves")
    boots(boot, ank)
    return waist, ank


def outfit_scout():
    base_mats()
    wood = mat("wood", "#3e4a32", rough=0.86, bump=0.4, scale=220, camo=["#2c3424", "#5b6646", "#6d5f45"], sheen=0.1, folds=0.9)
    dress(mat("shirt_s", "#4a5340", rough=0.86, bump=0.4, scale=220, sheen=0.12, folds=0.8), wood,
          mat("glove_s", "#5b5446", rough=0.72, bump=0.3), mat("boot_s", "#4a3a29", rough=0.58, bump=0.35))
    cc, hx, hy, hz, top, eye_z = head_geo()
    skinm = mat("skin_s", "#8a6a55", rough=0.55, bump=0.1, scale=400)
    region_mesh("Face", {"head"}, skinm, 0.0, thick=0, subdiv=1)
    scarf = mat("scarf", "#6d6650", rough=0.92, bump=0.55, scale=260, folds=1.2, sheen=0.15)
    lower_face("Scarf", scarf, eye_z, off=0.014)
    cyl("ScarfWrap", (cc.x, cc.y, J("neck01").z - 0.02), (cc.x, cc.y, J("head").z + 0.01), hx * 0.95, scarf, slot="Mask", verts=24, r2=hx * 0.8)
    glasses(cc, hx, hy, eye_z, MATS["lens"], MATS["blackpoly"])
    hat = mat("boonie", "#4a543c", rough=0.9, bump=0.45, camo=["#323b29", "#66704d"], folds=0.6)
    shell("HatCrown", (cc.x, cc.y + 0.004, top - hz * 0.55), (hx * 1.12, hy * 1.08, hz * 0.85), hat, cut_z=-0.05, thick=0.008)
    cyl("HatBrim", (cc.x, cc.y + 0.004, top - hz * 0.62), (cc.x, cc.y + 0.004, top - hz * 0.6), hx * 1.85, hat, verts=36)
    rig = chest_rig(mat("rig_s", "#565a40", rough=0.82, bump=0.45, webbing=True), mat("pouch_s", "#4e5238", rough=0.82, bump=0.4, webbing=True))
    belt(MATS["strap"])
    kneepads(mat("kneecap_s", "#2e3127", rough=0.5, bump=0.1))
    holster(mat("holster_s", "#3b3d30", rough=0.6, bump=0.15), MATS["blackpoly"])
    pk = mat("pack_s", "#4f5440", rough=0.84, bump=0.45, webbing=True)
    backpack(pk, rig, w=0.26, h=0.5, d=0.13)
    antenna(rig, MATS["blackpoly"])
    rifle("dmr")


def outfit_heavy():
    base_mats()
    dark = mat("dark_h", "#2b2d2f", rough=0.85, bump=0.4, scale=220, sheen=0.1, folds=0.8)
    dress(mat("shirt_h", "#34372f", rough=0.86, bump=0.4, scale=220, sheen=0.1, folds=0.7), dark,
          mat("glove_h", "#1d1e1f", rough=0.6, bump=0.3), mat("boot_h", "#1e1f20", rough=0.55, bump=0.3), shirt_off=0.024, pants_off=0.03)
    cc, hx, hy, hz, top, eye_z = head_geo()
    region_mesh("Balaclava", {"head"}, mat("bala_h", "#151617", rough=0.92, bump=0.6, scale=300), 0.004, thick=0.003, slot="Mask")
    helm = mat("helmet_h", "#2f3330", rough=0.45, bump=0.08, coat=0.25)
    open_shell("Helmet", cc + Vector((0, 0.008, -0.004)), (hx * 1.2, hy * 1.16, hz * 1.14), helm, cut_z=-0.6, face_open=0.3, face_zmax=0.3, thick=0.016)
    visor("Visor", cc + Vector((0, -0.012, 0.0)), hx * 0.98, hy * 0.98, hz, mat("visor", "#10171d", rough=0.03, metal=0.35, bump=0, coat=1.0))
    for sg in (-1, 1): cube("HRail%d" % sg, (cc.x + sg * hx * 1.18, cc.y + 0.01, cc.z - hz * 0.2), (0.016, hy * 1.1, 0.03), MATS["blackpoly"], bevel=0.004)
    armor = mat("armor_h", "#3d4136", rough=0.62, bump=0.25, webbing=True, coat=0.1)
    cr = carrier(armor, mat("pouch_h", "#34382e", rough=0.8, bump=0.4, webbing=True), heavy=True, style="heavy")
    belt(MATS["strap"])
    kneepads(mat("kneecap_h", "#141516", rough=0.4, bump=0.08))
    for sd in "LR":
        k = J("lowerleg01." + sd); a = J("foot." + sd)
        side = [v for v, r in zip(P["verts"], P["labels"]) if r == "leg" and abs(v[2] - (k.z - 0.15)) < 0.03 and (v[0] > 0) == (k.x > 0)]
        fy = min(v[1] for v in side)
        cube("Shin" + sd, (k.x, fy - 0.012, (k.z + a.z) / 2 + 0.06), (0.09, 0.03, (k.z - a.z) * 0.62), MATS["blackpoly"], bevel=0.012, slot="Kneepads")
        u = J("upperleg01." + sd); m_ = u.lerp(k, 0.5)
        side = [v for v, r in zip(P["verts"], P["labels"]) if r == "leg" and abs(v[2] - m_.z) < 0.03 and (v[0] > 0) == (k.x > 0)]
        cube("Thigh" + sd, (m_.x, min(v[1] for v in side) - 0.014, m_.z), (0.12, 0.03, 0.18), armor, bevel=0.014)
    holster(mat("holster_h", "#1c1d1e", rough=0.55, bump=0.12), MATS["blackpoly"])
    pk = mat("pack_h", "#33362d", rough=0.82, bump=0.45, webbing=True)
    backpack(pk, cr, w=0.38, h=0.5, d=0.2)
    cube("AmmoCan", (cr["cx"] - 0.15, cr["by"] + 0.22, cr["zc"] - 0.3), (0.12, 0.2, 0.14), mat("ammo", "#3e4535", rough=0.5, metal=0.4, bump=0.05), bevel=0.01, slot="Backpack")
    rifle("lmg")


def outfit_urban():
    base_mats()
    jacket = mat("jacket_u", "#34465a", rough=0.68, bump=0.35, scale=180, sheen=0.08, folds=1.1)
    jeans = mat("pants_u", "#26282c", rough=0.85, bump=0.45, scale=260, folds=0.9)
    dress(jacket, jeans, mat("glove_u", "#18191a", rough=0.55, bump=0.25), mat("boot_u", "#202224", rough=0.5, bump=0.3), shirt_off=0.032, shirt_smooth=6)
    waist = J("upperleg01.L").z + 0.11
    st = stats({"torso", "leg"}, waist - 0.05, waist + 0.02)
    cx, cy = (st["xmin"] + st["xmax"]) / 2, (st["ymin"] + st["ymax"]) / 2
    hem = cyl("JacketHem", (cx, cy, waist - 0.07), (cx, cy, waist + 0.02), (st["xmax"] - st["xmin"]) / 2 + 0.032, jacket, verts=32)
    hem.scale = (1, (st["ymax"] - st["ymin"] + 0.06) / (st["xmax"] - st["xmin"] + 0.06), 1)
    cc, hx, hy, hz, top, eye_z = head_geo()
    region_mesh("FaceMask", {"head"}, mat("mask_u", "#141516", rough=0.85, bump=0.3, scale=300), 0.006, thick=0.003, slot="Mask")
    glasses(cc, hx, hy, eye_z, MATS["lens"], MATS["blackpoly"])
    open_shell("Hood", cc + Vector((0, 0.03, -0.03)), (hx * 1.42, hy * 1.42, hz * 1.5), jacket, cut_z=-0.7, face_open=0.45, face_zmax=0.35, thick=0.01)
    cr = carrier(mat("lowvis", "#23262b", rough=0.75, bump=0.4, webbing=True), mat("pouch_u", "#2a2d33", rough=0.75, bump=0.35, webbing=True), style="slick")
    belt(MATS["strap"])
    kneepads(mat("kneecap_u", "#151617", rough=0.45, bump=0.08))
    holster(mat("holster_u", "#18191a", rough=0.5, bump=0.12), MATS["blackpoly"])
    sling_bag(mat("bag_u", "#2b2f36", rough=0.7, bump=0.35, webbing=True), cr)
    rifle("smg")


def outfit_arctic():
    base_mats()
    white = mat("white_a", "#8e959d", rough=0.82, bump=0.4, scale=200, camo=["#6b7480", "#a9b0b8"], sheen=0.05, folds=1.0)
    parka = mat("parka_a", "#9aa1a9", rough=0.78, bump=0.35, scale=160, sheen=0.05, folds=1.3)
    dress(parka, white, mat("glove_a", "#3a3f46", rough=0.7, bump=0.3), mat("boot_a", "#2d3035", rough=0.55, bump=0.3), shirt_off=0.045, pants_off=0.03, shirt_smooth=8)
    waist = J("upperleg01.L").z + 0.11
    st = stats({"torso", "leg"}, waist - 0.05, waist + 0.02)
    cx, cy = (st["xmin"] + st["xmax"]) / 2, (st["ymin"] + st["ymax"]) / 2
    r0 = (st["xmax"] - st["xmin"]) / 2 + 0.05
    sk = cyl("ParkaSkirt", (cx, cy, waist - 0.2), (cx, cy, waist + 0.04), r0 * 1.08, parka, verts=36, r2=r0)
    sk.scale = (1, (st["ymax"] - st["ymin"] + 0.1) / (st["xmax"] - st["xmin"] + 0.1), 1)
    cc, hx, hy, hz, top, eye_z = head_geo()
    region_mesh("Balaclava", {"head"}, mat("bala_a", "#5d636b", rough=0.92, bump=0.6, scale=300), 0.004, thick=0.003, slot="Mask")
    goggles(cc, hx, hy, MATS["rubber"], mat("lens_a", "#2b3d4d", rough=0.04, metal=0.5, bump=0, coat=1.0))
    open_shell("Hood", cc + Vector((0, 0.035, -0.035)), (hx * 1.5, hy * 1.5, hz * 1.58), parka, cut_z=-0.72, face_open=0.42, face_zmax=0.4, thick=0.012)
    fur = mat("fur", "#bdb5a6", rough=1.0, bump=1.2, scale=90, sheen=0.6)
    bpy.ops.mesh.primitive_torus_add(major_radius=hx * 1.2, minor_radius=0.03, location=(cc.x, cc.y - hy * 0.95, eye_z - 0.005),
                                     rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object; t.name = "FurTrim"; t.scale = (1, 1.35, 1); setmat(t, fur); link(t); smooth(t)
    rig = chest_rig(mat("rig_a", "#9ea6af", rough=0.8, bump=0.4, webbing=True), mat("pouch_a", "#8f98a2", rough=0.8, bump=0.4, webbing=True))
    kneepads(mat("kneecap_a", "#8a929b", rough=0.5, bump=0.1))
    holster(mat("holster_a", "#9aa2ab", rough=0.6, bump=0.12), MATS["blackpoly"])
    pk = mat("pack_a", "#a5adb6", rough=0.82, bump=0.45, webbing=True)
    backpack(pk, rig, w=0.36, h=0.48, d=0.2)
    cyl("Bedroll", (rig["cx"] - 0.2, rig["by"] + 0.12, rig["zc"] + 0.32), (rig["cx"] + 0.2, rig["by"] + 0.12, rig["zc"] + 0.32), 0.07, mat("roll", "#6b7380", rough=0.85, bump=0.4, folds=0.8), slot="Backpack", verts=24)
    rifle("carbine")


OUTFITS = {"operator": outfit_operator, "scout": outfit_scout, "heavy": outfit_heavy, "urban": outfit_urban, "arctic": outfit_arctic}



def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--pose", required=True); ap.add_argument("--outfit", default="operator"); ap.add_argument("--out", required=True)
    ap.add_argument("--views", default=""); ap.add_argument("--turntable", type=int, default=0); ap.add_argument("--frames", default="")
    ap.add_argument("--size", default="600x720"); ap.add_argument("--samples", type=int, default=48); ap.add_argument("--ids", action="store_true")
    ap.add_argument("--blend", default="")
    a = ap.parse_args(argv)
    P.update(json.load(open(a.pose)))
    os.makedirs(a.out, exist_ok=True)
    w, h = (int(x) for x in a.size.split("x"))
    B.ROOT = B.reset()
    OUTFITS[a.outfit]()
    B.lights_camera(w, h)
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    angles = {"front": 0, "q3": 35, "side": 90, "back": 180, "q3back": 215, "left": 300}
    jobs = [(v, angles[v]) for v in a.views.split(",") if v]
    if a.turntable:
        idx = range(a.turntable)
        if a.frames: s, e = (int(x) for x in a.frames.split("-")); idx = range(s, e)
        jobs += [("%02d" % i, 360.0 * i / a.turntable) for i in idx]
    for name, deg in jobs:
        B.ROOT.rotation_euler = (0, 0, math.radians(deg))
        B.render(os.path.join(a.out, name + ".png"), a.samples)
        if a.ids or a.turntable: B.render_ids(os.path.join(a.out, name + "_id.png"))
        print("rendered", name, flush=True)


if __name__ == "__main__":
    main()
