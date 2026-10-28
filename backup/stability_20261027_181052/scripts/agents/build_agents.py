"""Özgün, gerçekçi ajan modelleri (Blender, bpy) — Eksik Parçalar sekmesindeki döner 3D görünüm için.

Her kıyafet: Blender'da betikle modellenir, 360° etrafında N kare render edilir (şeffaf zemin, gölge),
ayrıca her kare için yuva kimlik maskesi (maske/yelek/çanta/eldiven/kılıf/dizlik/silah/tabanca) çıkarılır.
Çıktı: meta/agents/<kıyafet>/f00.webp … + m00.png … + info.json

    python3.11 scripts/agents/build_agents.py --outfit operator --views          # 3 önizleme açısı
    python3.11 scripts/agents/build_agents.py --outfit operator --frames 48      # tüm kareler
Tasarımlar tamamen özgündür; hiçbir oyunun karakter/kıyafet tasarımı kullanılmaz.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
SLOTS = ("Mask", "Chest", "Backpack", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm")
SLOT_ID = {s: i + 1 for i, s in enumerate(SLOTS)}
SLOT_RGB = {s: ((i + 1) * 30, 0, 0) for i, s in enumerate(SLOTS)}           # maske: kırmızı kanal = yuva*30

# ------------------------------------------------------------------ sahne
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.use_denoising = True
    s.render.film_transparent = True
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    return s


RIG = None


def link(obj, slot=None):
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = RIG
    if slot:
        obj["slot"] = slot
        obj.pass_index = SLOT_ID[slot]
    return obj


# ------------------------------------------------------------------ malzemeler
_MATS = {}


def mat(name, color, rough=0.8, metal=0.0, bump=0.25, scale=220.0, var=0.12, sheen=0.0, coat=0.0, emit=None):
    """Kumaş/naylon/metal: renk değişkenliği (gürültü) + mikro kabartı."""
    if name in _MATS: return _MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]
    c = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [x ** 2.2 for x in c]
    tex = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = scale / 18; noise.inputs["Detail"].default_value = 6
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*[x * (1 - var) for x in lin], 1)
    ramp.color_ramp.elements[1].color = (*[min(1, x * (1 + var)) for x in lin], 1)
    L.new(tex.outputs["Object"], noise.inputs["Vector"]); L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    fine = N.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = scale; fine.inputs["Detail"].default_value = 3
    bmp = N.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = bump; bmp.inputs["Distance"].default_value = 0.002
    L.new(tex.outputs["Object"], fine.inputs["Vector"]); L.new(fine.outputs["Fac"], bmp.inputs["Height"])
    L.new(bmp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sheen: b.inputs["Sheen Weight"].default_value = sheen
    if coat: b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 3
    _MATS[name] = m
    return m


def glass(name, tint="#1a2228"):
    if name in _MATS: return _MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = [int(tint[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    b.inputs["Base Color"].default_value = (*[x ** 2.2 for x in c], 1)
    b.inputs["Roughness"].default_value = 0.05; b.inputs["Metallic"].default_value = 0.4
    b.inputs["Coat Weight"].default_value = 1.0
    _MATS[name] = m
    return m


def setmat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
    return o


# ------------------------------------------------------------------ şekil yardımcıları
def smooth(o, sub=2, shade=True):
    if sub:
        md = o.modifiers.new("sub", "SUBSURF"); md.levels = sub; md.render_levels = sub
    if shade:
        for p in o.data.polygons: p.use_smooth = True
    return o


def bevel(o, w=0.008, seg=3):
    md = o.modifiers.new("bev", "BEVEL"); md.width = w; md.segments = seg; md.limit_method = "ANGLE"
    for p in o.data.polygons: p.use_smooth = True
    return o


def box(name, loc, size, m, rot=(0, 0, 0), bev=0.008, slot=None, sub=0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.scale = size; o.location = loc; o.rotation_euler = rot
    link(o, slot); setmat(o, m)
    if bev: bevel(o, bev)
    if sub: smooth(o, sub)
    return o


def sphere(name, loc, scale, m, slot=None, seg=24, ring=16, cut=None, rot=(0, 0, 0)):
    """cut: z eşiği (yerel, -1..1) — altı silinir (kask/kubbe)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=1.0)
    if cut is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < cut], context="VERTS")
        edge = [e for e in bm.edges if e.is_boundary]
        if edge: bmesh.ops.holes_fill(bm, edges=edge, sides=0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = loc; o.scale = scale; o.rotation_euler = rot
    link(o, slot); setmat(o, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def cyl(name, p0, p1, r, m, slot=None, seg=16, r1=None, bev=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r1 is None else r1, depth=(p1 - p0).length)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = (p0 + p1) / 2
    o.rotation_euler = (p1 - p0).to_track_quat("Z", "Y").to_euler()
    link(o, slot); setmat(o, m)
    if bev: bevel(o, bev, 2)
    else:
        for p in o.data.polygons: p.use_smooth = True
    return o


def skin(name, joints, edges, m, slot=None, sub=2, root=0):
    """Deri (skin) değiştiricisiyle organik gövde/uzuv: joints = [((x,y,z), (rx, ry)), …]."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([j[0] for j in joints], edges, [])
    o = bpy.data.objects.new(name, me)
    link(o, slot)
    md = o.modifiers.new("skin", "SKIN")
    md.use_smooth_shade = True
    for i, (_, r) in enumerate(joints):
        o.data.skin_vertices[0].data[i].radius = r
    o.data.skin_vertices[0].data[root].use_root = True
    smooth(o, sub, shade=False)
    setmat(o, m)
    return o


def displace(o, strength=0.006, scale=0.08):
    """Kumaş kırışıklığı: düşük frekanslı gürültüyle hafif yüzey dalgası."""
    t = bpy.data.textures.new(o.name + "_wr", "CLOUDS"); t.noise_scale = scale
    md = o.modifiers.new("wrinkle", "DISPLACE"); md.texture = t; md.strength = strength; md.mid_level = 0.5
    return o


def along(name, p0, p1, parts, slot=None):
    """Tüfek gibi bir nesneyi yerel +X ekseninde kurup p0→p1 doğrultusuna yerleştirir. parts: [(fn, kwargs)]"""
    p0, p1 = Vector(p0), Vector(p1)
    piv = bpy.data.objects.new(name, None); link(piv)
    d = (p1 - p0).normalized()
    piv.location = p0
    piv.rotation_euler = d.to_track_quat("X", "Z").to_euler()
    for o in parts:
        o.parent = piv
    return piv


# ------------------------------------------------------------------ gövde ve ortak teçhizat
def body(P, k=1.0, pose="ready"):
    """Gövde iskeleti (Z yukarı, ajan -Y'ye bakar). Döndürür: önemli noktalar sözlüğü."""
    J = {
        "pelvis": (0, 0.0, 0.96), "spine": (0, 0.0, 1.12), "chest": (0, 0.012, 1.32), "neck": (0, 0.01, 1.5),
        "shR": (0.19 * k, 0.02, 1.43), "shL": (-0.19 * k, 0.02, 1.43),
        "elR": (0.26 * k, 0.0, 1.18), "elL": (-0.25 * k, -0.12, 1.2),
        "wrR": (0.11, -0.21, 1.17), "wrL": (-0.12, -0.33, 1.12),
        "hipR": (0.1 * k, 0.0, 0.93), "hipL": (-0.1 * k, 0.0, 0.93),
        "knR": (0.115 * k, -0.035, 0.5), "knL": (-0.115 * k, -0.02, 0.5),
        "anR": (0.13 * k, 0.01, 0.1), "anL": (-0.13 * k, 0.02, 0.1),
    }
    R = lambda a, b: (a * k, b * k)
    top = skin("jacket", [(J["spine"], R(0.15, 0.11)), (J["chest"], R(0.175, 0.125)), (J["neck"], (0.062, 0.062)),
                          (J["shR"], R(0.068, 0.068)), (J["elR"], R(0.052, 0.052)), (J["wrR"], R(0.04, 0.04)),
                          (J["shL"], R(0.068, 0.068)), (J["elL"], R(0.052, 0.052)), (J["wrL"], R(0.04, 0.04))],
               [(0, 1), (1, 2), (1, 3), (3, 4), (4, 5), (1, 6), (6, 7), (7, 8)], P["top"])
    displace(top, 0.005)
    legs = skin("pants", [(J["spine"], R(0.14, 0.1)), (J["pelvis"], R(0.155, 0.112)),
                          (J["hipR"], R(0.082, 0.085)), (J["knR"], R(0.06, 0.062)), (J["anR"], R(0.046, 0.046)),
                          (J["hipL"], R(0.082, 0.085)), (J["knL"], R(0.06, 0.062)), (J["anL"], R(0.046, 0.046))],
                [(0, 1), (1, 2), (2, 3), (3, 4), (1, 5), (5, 6), (6, 7)], P["pants"])
    displace(legs, 0.006)
    # kemer
    box("belt", (0, 0.0, 1.03), (0.31 * k, 0.225 * k, 0.045), P["strap"], bev=0.01, sub=1)
    box("buckle", (0, -0.113 * k, 1.03), (0.05, 0.012, 0.035), P["metal"], bev=0.003)
    # baş + boyun (yüz örtülü: kumaş)
    cyl("neck_c", (0, 0.01, 1.47), (0, 0.0, 1.6), 0.052, P["face"])
    sphere("head", (0, -0.005, 1.655), (0.092, 0.108, 0.118), P["face"])
    # botlar
    for side, an in (("R", J["anR"]), ("L", J["anL"])):
        x, y, z = an
        box("boot" + side, (x, y - 0.045, 0.055), (0.105, 0.27, 0.11), P["boot"], bev=0.025, sub=1)
        box("sole" + side, (x, y - 0.045, 0.012), (0.112, 0.28, 0.024), P["rubber"], bev=0.006)
        cyl("cuff" + side, (x, y, 0.1), (x, y, 0.2), 0.056, P["boot"])
    # eldivenler (yuva)
    for side, wr, el in (("R", J["wrR"], J["elR"]), ("L", J["wrL"], J["elL"])):
        d = (Vector(wr) - Vector(el)).normalized()
        c = Vector(wr) + d * 0.05
        sphere("glove" + side, c, (0.042, 0.05, 0.06), P["glove"], slot="Gloves", rot=d.to_track_quat("Z", "Y").to_euler())
        cyl("gcuff" + side, Vector(wr) - d * 0.02, Vector(wr) + d * 0.02, 0.045, P["glove"], slot="Gloves")
    return J


def kneepads(J, P, big=False):
    for side in ("R", "L"):
        x, y, z = J["kn" + side]
        s = 1.25 if big else 1.0
        sphere("knee" + side, (x, y - 0.058, z + 0.01), (0.062 * s, 0.03 * s, 0.075 * s), P["pad"], slot="Kneepads")
        cyl("kstrap" + side, (x, y, z + 0.06), (x, y, z + 0.075), 0.066, P["strap"], slot="Kneepads")
        cyl("kstrap2" + side, (x, y, z - 0.055), (x, y, z - 0.04), 0.06, P["strap"], slot="Kneepads")
        if big:
            box("shin" + side, (x, y - 0.06, z - 0.2), (0.07, 0.03, 0.22), P["pad"], bev=0.012, slot="Kneepads", sub=1)


def holster(J, P):
    x, y, z = J["hipR"]
    tx = x + 0.08
    cyl("thighband1", (x, 0.0, 0.8), (x, 0.0, 0.82), 0.09, P["strap"], slot="Holster")
    cyl("thighband2", (x + 0.005, -0.01, 0.64), (x + 0.005, -0.01, 0.66), 0.082, P["strap"], slot="Holster")
    box("holster", (tx, -0.01, 0.72), (0.05, 0.11, 0.17), P["gear"], bev=0.012, slot="Holster", sub=1)
    box("pistol_grip", (tx, 0.01, 0.84), (0.035, 0.045, 0.09), P["gun"], rot=(0.25, 0, 0), bev=0.006, slot="Sidearm")
    box("pistol_slide", (tx, -0.03, 0.81), (0.03, 0.09, 0.03), P["gun"], bev=0.004, slot="Sidearm")


def plate_carrier(P, k=1.0, heavy=False):
    T = "Chest"
    d = 0.06 if heavy else 0.045
    fr = box("plate_front", (0, -0.14 * k, 1.29), (0.29 * k, d, 0.32), P["gear"], rot=(-0.06, 0, 0), bev=0.02, slot=T, sub=1)
    box("plate_back", (0, 0.145 * k, 1.3), (0.3 * k, d, 0.34), P["gear"], rot=(0.04, 0, 0), bev=0.02, slot=T, sub=1)
    for sx in (-1, 1):
        box("cummer" + str(sx), (0.165 * k * sx, 0.0, 1.2), (0.03, 0.27 * k, 0.15), P["gear"], bev=0.01, slot=T)
        box("shstrap" + str(sx), (0.105 * k * sx, 0.0, 1.47), (0.07, 0.3 * k, 0.03), P["gear"], rot=(0, 0.25 * sx, 0), bev=0.01, slot=T)
    for i in range(4):                                         # MOLLE şeritleri
        box("molle%d" % i, (0, -0.14 * k - d / 2 - 0.004, 1.17 + i * 0.05), (0.27 * k, 0.006, 0.018), P["strap"], rot=(-0.06, 0, 0), bev=0.002, slot=T)
    for i, x in enumerate((-0.09, 0.0, 0.09)):                 # şarjör cepleri
        box("magpouch%d" % i, (x * k, -0.14 * k - d / 2 - 0.03, 1.2), (0.075, 0.05, 0.12), P["gear2"], rot=(-0.06, 0, 0), bev=0.01, slot=T, sub=1)
        box("magflap%d" % i, (x * k, -0.14 * k - d / 2 - 0.032, 1.265), (0.078, 0.052, 0.03), P["gear"], rot=(-0.06, 0, 0), bev=0.008, slot=T)
    box("admin", (0, -0.14 * k - d / 2 - 0.02, 1.38), (0.16, 0.03, 0.09), P["gear2"], rot=(-0.06, 0, 0), bev=0.01, slot=T)
    box("radio", (-0.17 * k, -0.02, 1.25), (0.05, 0.07, 0.13), P["gear2"], bev=0.01, slot=T, sub=1)
    cyl("antenna", (-0.17 * k, -0.02, 1.31), (-0.17 * k, 0.01, 1.52), 0.004, P["rubber"], slot=T)
    if heavy:
        box("collar", (0, 0.0, 1.5), (0.24, 0.24, 0.06), P["gear"], bev=0.025, slot=T, sub=1)
        box("groin", (0, -0.13, 0.95), (0.16, 0.04, 0.16), P["gear"], bev=0.02, slot=T, sub=1)
        for sx in (-1, 1):
            sphere("pauldron" + str(sx), (0.21 * k * sx, 0.01, 1.45), (0.09, 0.1, 0.06), P["gear"], slot=T, cut=-0.2,
                   rot=(0, 0.45 * sx, 0))
    return fr


def backpack(P, k=1.0, w=0.3, h=0.4, d=0.17, z=1.28, roll=False):
    T = "Backpack"
    y = 0.145 * k + 0.03 + d / 2
    box("pack", (0, y, z), (w * k, d, h), P["gear"], bev=0.03, slot=T, sub=1)
    box("pack_top", (0, y - 0.01, z + h / 2 + 0.02), (w * k * 0.92, d * 0.9, 0.06), P["gear2"], bev=0.02, slot=T, sub=1)
    box("pack_front", (0, y + d / 2 + 0.02, z - 0.04), (w * k * 0.7, 0.05, h * 0.55), P["gear2"], bev=0.02, slot=T, sub=1)
    for sx in (-1, 1):
        box("pack_side" + str(sx), ((w * k / 2 + 0.025) * sx, y, z - 0.06), (0.05, d * 0.7, h * 0.45), P["gear2"], bev=0.015, slot=T, sub=1)
        for zz in (z - 0.08, z + 0.08):
            box("compress%d%d" % (sx, int(zz * 100)), ((w * k / 2 + 0.004) * sx, y, zz), (0.012, d * 1.02, 0.018), P["strap"], bev=0.003, slot=T)
    if roll:
        cyl("bedroll", (-w * k * 0.55, y, z + h / 2 + 0.09), (w * k * 0.55, y, z + h / 2 + 0.09), 0.06, P["roll"], slot=T, bev=0.0)
    return y + d / 2


def rifle(P, butt, muzzle, kind="ar"):
    T = "Weapon"
    L = (Vector(muzzle) - Vector(butt)).length
    g, g2 = P["gun"], P["gun2"]
    parts = []
    rec = 0.24 if kind != "smg" else 0.18
    parts.append(box("stock", (0.09, 0, 0.0), (0.18, 0.04, 0.07), g2, bev=0.008, slot=T))
    parts.append(box("receiver", (0.18 + rec / 2, 0, 0.012), (rec, 0.045, 0.07), g, bev=0.006, slot=T))
    parts.append(box("grip", (0.22, 0, -0.06), (0.035, 0.035, 0.08), g2, rot=(0, 0.3, 0), bev=0.006, slot=T))
    mag_l = 0.16 if kind == "ar" else (0.1 if kind == "dmr" else 0.2)
    parts.append(box("mag", (0.32, 0, -0.07), (0.05, 0.028, mag_l), g2, rot=(0, -0.2, 0), bev=0.005, slot=T))
    hg0 = 0.18 + rec
    hg1 = L - (0.12 if kind == "dmr" else 0.08)
    o = cyl("handguard", (hg0, 0, 0.015), (hg1, 0, 0.015), 0.024, g, slot=T, seg=8); parts.append(o)
    parts.append(cyl("barrel", (hg1, 0, 0.015), (L, 0, 0.015), 0.009, g2, slot=T, seg=12))
    parts.append(box("rail", (0.18 + (L - 0.18) / 2 - 0.04, 0, 0.05), (L - 0.3, 0.022, 0.01), g2, bev=0.002, slot=T))
    if kind == "dmr":
        parts.append(cyl("scope", (0.24, 0, 0.09), (0.46, 0, 0.09), 0.022, g, slot=T, seg=16))
        parts.append(cyl("scope_obj", (0.46, 0, 0.09), (0.52, 0, 0.09), 0.022, g, slot=T, seg=16, r1=0.03))
    else:
        parts.append(box("optic", (0.36, 0, 0.08), (0.08, 0.04, 0.045), g, bev=0.008, slot=T))
        parts.append(box("lens", (0.315, 0, 0.082), (0.004, 0.03, 0.03), glass("lens"), bev=0.0, slot=T))
    if kind == "lmg":
        parts.append(box("boxmag", (0.32, 0.0, -0.09), (0.1, 0.07, 0.1), g2, bev=0.01, slot=T))
    return along("rifle", butt, muzzle, parts)


def shadow_plane():
    me = bpy.data.meshes.new("ground")
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("ground", me); bpy.context.scene.collection.objects.link(o)
    o.is_shadow_catcher = True
    return o


# ------------------------------------------------------------------ kıyafetler (özgün)
def palette(**over):
    P = {
        "top": mat("top", "#3b4049", rough=0.9, bump=0.35), "pants": mat("pants", "#4a4740", rough=0.9, bump=0.35),
        "face": mat("face", "#22252a", rough=0.95, bump=0.4), "boot": mat("boot", "#2a2622", rough=0.6, bump=0.3),
        "rubber": mat("rubber", "#141414", rough=0.7, bump=0.1), "strap": mat("strap", "#25282c", rough=0.8, bump=0.4, scale=400),
        "metal": mat("metal", "#8a8f96", rough=0.35, metal=1.0, bump=0.05), "glove": mat("glove", "#26282b", rough=0.75, bump=0.3),
        "pad": mat("pad", "#2c2f33", rough=0.5, bump=0.08, coat=0.2), "gear": mat("gear", "#3e4237", rough=0.75, bump=0.45, scale=380),
        "gear2": mat("gear2", "#454a3e", rough=0.75, bump=0.45, scale=380), "gun": mat("gun", "#1c1e21", rough=0.4, metal=0.6, bump=0.05),
        "gun2": mat("gun2", "#2a2c2f", rough=0.55, metal=0.2, bump=0.05), "roll": mat("roll", "#5b5546", rough=0.9, bump=0.4),
        "helmet": mat("helmet", "#3a3d38", rough=0.55, bump=0.2, coat=0.1),
    }
    for k, v in over.items(): P[k] = mat(k + "_" + v[0], *v)
    return P


def o_operator():
    P = palette()
    J = body(P)
    # kask (yüksek kesim) + raylar + kulaklık + gözlük + boyunluk (Mask)
    sphere("helmet", (0, 0.0, 1.69), (0.122, 0.132, 0.105), P["helmet"], cut=-0.05)
    for sx in (-1, 1):
        box("hrail" + str(sx), (0.115 * sx, -0.01, 1.68), (0.012, 0.11, 0.022), P["gun2"], bev=0.003)
        cyl("earcup" + str(sx), (0.095 * sx, -0.005, 1.63), (0.125 * sx, -0.005, 1.63), 0.042, P["rubber"], bev=0.01)
    box("nvg_mount", (0, -0.13, 1.72), (0.05, 0.02, 0.035), P["gun2"], bev=0.004)
    box("glasses", (0, -0.103, 1.668), (0.16, 0.02, 0.038), glass("glasses"), bev=0.01, slot="Mask")
    sphere("gaiter", (0, -0.03, 1.595), (0.098, 0.1, 0.072), mat("gaiter", "#4a4d45", rough=0.95, bump=0.5), slot="Mask")
    plate_carrier(P)
    backpack(P)
    kneepads(J, P)
    holster(J, P)
    rifle(P, (0.13, -0.11, 1.33), (-0.33, -0.56, 0.99), "ar")
    return {"label": "operator"}


OUTFITS = {"operator": o_operator}


# ------------------------------------------------------------------ kamera, ışık, render
def stage(res=(420, 560)):
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    cam = bpy.data.cameras.new("cam"); cam.lens = 70
    co = bpy.data.objects.new("cam", cam); s.collection.objects.link(co); s.camera = co
    co.location = (0, -5.2, 1.25)
    co.rotation_euler = (Vector((0, 0, 0.92)) - co.location).to_track_quat("-Z", "Y").to_euler()
    def area(name, loc, power, size, color=(1, 1, 1)):
        l = bpy.data.lights.new(name, "AREA"); l.energy = power; l.size = size; l.color = color
        o = bpy.data.objects.new(name, l); s.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, 1.1)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    area("key", (-2.2, -2.6, 3.0), 650, 1.6, (1.0, 0.96, 0.9))
    area("fill", (2.6, -2.0, 1.4), 160, 2.5, (0.85, 0.9, 1.0))
    area("rim", (1.6, 2.6, 2.6), 520, 1.0, (1.0, 0.75, 0.55))
    area("rim2", (-2.0, 2.4, 2.0), 260, 1.0, (0.7, 0.8, 1.0))
    w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.014, 0.018, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    shadow_plane()


def render_frame(path, samples=48):
    s = bpy.context.scene
    s.cycles.samples = samples
    s.render.image_settings.file_format = "PNG"; s.render.image_settings.color_mode = "RGBA"
    s.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_mask(path):
    """Yuva kimlik maskesi: Workbench, düz renk, kenar yumuşatma kapalı."""
    s = bpy.context.scene
    prev = s.render.engine
    s.render.engine = "BLENDER_WORKBENCH"
    s.display.shading.light = "FLAT"; s.display.shading.color_type = "OBJECT"
    s.display.render_aa = "OFF"
    s.display.shading.show_shadows = False; s.display.shading.show_cavity = False
    s.render.film_transparent = True
    s.view_settings.view_transform = "Standard"; s.view_settings.look = "None"
    for o in s.objects:
        if o.type != "MESH": continue
        sl = o.get("slot") or (o.parent.get("slot") if o.parent else None)
        if not sl and o.parent and o.parent.name.startswith("rifle"): sl = "Weapon"
        o.color = (SLOT_ID[sl] * 30 / 255, 0, 0, 1) if sl else (0.004, 0, 0, 1)
        o.hide_render = o.name == "ground"
    s.render.image_settings.file_format = "PNG"; s.render.image_settings.color_mode = "RGB"
    s.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    for o in s.objects:
        o.hide_render = False
    s.render.engine = prev
    s.view_settings.view_transform = "AgX"; s.view_settings.look = "AgX - Medium High Contrast"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outfit", default="operator")
    ap.add_argument("--views", action="store_true", help="3 önizleme açısı (ön, yan, arka)")
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--out", default=str(ROOT / "meta" / "agents"))
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    global RIG
    reset()
    RIG = bpy.data.objects.new("rig", None); bpy.context.scene.collection.objects.link(RIG)
    OUTFITS[a.outfit]()
    stage()
    out = Path(a.out) / a.outfit; out.mkdir(parents=True, exist_ok=True)
    if a.views:
        for name, ang in (("front", 25), ("side", 95), ("back", 200)):
            RIG.rotation_euler = (0, 0, math.radians(ang))
            render_frame(out / f"view_{name}.png", a.samples)
        return
    n = a.frames
    for i in range(n):
        RIG.rotation_euler = (0, 0, 2 * math.pi * i / n)
        render_frame(out / f"f{i:02d}.png", a.samples)
        render_mask(out / f"m{i:02d}.png")
        print(f"frame {i + 1}/{n}", flush=True)
    (out / "info.json").write_text(json.dumps({"frames": n, "slots": {s: SLOT_ID[s] * 30 for s in SLOTS}}, indent=1))


if __name__ == "__main__":
    main()
