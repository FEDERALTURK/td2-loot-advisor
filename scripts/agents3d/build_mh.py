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
             cube("Mag", (0.12, 0, -0.03), (0.038, 0.026, 0.07 if kind == "dmr" else 0.13), poly, bevel=0.005, rot=(0, 14, 0)),
             cube("Grip", (0.0, 0, -0.012), (0.032, 0.03, 0.08), poly, bevel=0.006, rot=(0, -18, 0)),
             cyl("Buffer", (-0.08, 0, 0.055), (-0.18, 0, 0.055), 0.016, gun),
             cube("Stock", (-0.23, 0, 0.035), (0.16, 0.038, 0.07), poly, bevel=0.012),
             cube("Mount", (0.07, 0, 0.088), (0.09, 0.026, 0.026), gun)]
    if kind == "dmr": parts.append(cyl("Scope", (-0.04, 0, 0.125), (0.2, 0, 0.125), 0.022, gun, r2=0.027))
    else: parts.append(cyl("Optic", (0.03, 0, 0.118), (0.13, 0, 0.118), 0.02, gun))
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


def carrier(m, pouch_m, heavy=False):
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
    for i, x in enumerate((-0.085, 0.0, 0.085)):
        cube("MagPouch%d" % i, (cx + x * w / 0.29, fy - t / 2 - 0.02, zc - hgt * 0.22), (0.072, 0.042, hgt * 0.42), pouch_m, bevel=0.01, slot="Chest")
    cube("Admin", (cx, fy - t / 2 - 0.014, zc + hgt * 0.2), (w * 0.55, 0.03, hgt * 0.22), pouch_m, bevel=0.01, slot="Chest")
    cube("Radio", (cx - w * 0.62, cy - 0.02, zc - hgt * 0.1), (0.04, 0.07, hgt * 0.4), pouch_m, bevel=0.01, slot="Chest")
    return {"fy": fy, "by": by + t / 2, "cx": cx, "zc": zc, "w": w, "h": hgt}


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
        length = (toe - Vector((a.x, heel_y, 0))).length + 0.045
        width = (max(v.x for v in fv) - min(v.x for v in fv)) + 0.03
        ang = math.atan2(d.x, -d.y)
        c = Vector((a.x, heel_y, 0)) + d * (length / 2 - 0.02)
        cube("Boot" + s, (c.x, c.y, 0.065), (width, length, 0.105), m, bevel=0.04, rot=(0, 0, math.degrees(ang)), subdiv=1)
        cube("Toe" + s, (c.x + d.x * length * 0.33, c.y + d.y * length * 0.33, 0.05), (width * 0.95, length * 0.32, 0.075), m, bevel=0.035, rot=(0, 0, math.degrees(ang)), subdiv=1)
        cube("Sole" + s, (c.x, c.y, 0.015), (width + 0.012, length + 0.015, 0.03), rub, bevel=0.01, rot=(0, 0, math.degrees(ang)))
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


OUTFITS = {"operator": outfit_operator}


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
