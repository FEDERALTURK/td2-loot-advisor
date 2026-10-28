"""Özgün taktik ajan modelleri (Blender, Python ile kod üzerinden modellenir) ve döner render.

    python build_agent.py --outfit operator --views front,side,back --out OUT_DIR [--size 600x720] [--samples 48]
    python build_agent.py --outfit operator --turntable 48 --out OUT_DIR       # 48 kare 360° + yuva maskeleri

Her kare için iki görüntü: <i>.png (renk, şeffaf zemin + gölge) ve <i>_id.png (yuva maskesi: her yuva sabit bir renk).
Tasarımlar özgündür; hiçbir oyun dosyası, modeli ya da dokusu kullanılmaz.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

SLOT_IDS = {"Mask": (255, 0, 0), "Chest": (0, 255, 0), "Backpack": (0, 0, 255), "Gloves": (255, 255, 0),
            "Holster": (255, 0, 255), "Kneepads": (0, 255, 255), "Weapon": (255, 128, 0), "Sidearm": (128, 0, 255)}


# ------------------------------------------------------------------ sahne
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.cycles.max_bounces = 6
    sc.render.film_transparent = True
    try: sc.view_settings.view_transform = "Khronos PBR Neutral"
    except TypeError: sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = -0.3
    w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.03, 0.035, 0.05, 1); bg.inputs[1].default_value = 0.22
    root = bpy.data.objects.new("Agent", None); sc.collection.objects.link(root)
    return root


ROOT = None


def link(ob, slot=None, parent=True):
    if ob.name not in bpy.context.scene.collection.objects:
        try: bpy.context.scene.collection.objects.link(ob)
        except RuntimeError: pass
    if slot: ob["slot"] = slot
    if parent and ROOT: ob.parent = ROOT
    return ob


def smooth(ob):
    for p in ob.data.polygons: p.use_smooth = True


# ------------------------------------------------------------------ malzemeler
MATS = {}


def mat(name, color, rough=0.7, metal=0.0, bump=0.25, scale=180.0, camo=None, webbing=False, sheen=0.0, coat=0.0, folds=0.0):
    """Principled malzeme: ince gürültü kabartması (kumaş dokusu), isteğe bağlı kamuflaj ve MOLLE şeritleri."""
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    bsdf = N["Principled BSDF"]
    def rgb(c): c = c.lstrip("#"); return tuple((int(c[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)) + (1,)
    tc = N.new("ShaderNodeTexCoord")
    if camo:
        vor = N.new("ShaderNodeTexNoise"); vor.inputs["Scale"].default_value = 3.2; vor.inputs["Detail"].default_value = 2.0
        L.new(tc.outputs["Object"], vor.inputs["Vector"])
        ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
        els = ramp.color_ramp.elements; els[0].position = 0.0; els[0].color = rgb(color); els[1].position = 0.52; els[1].color = rgb(camo[0])
        if len(camo) > 1:
            e = els.new(0.62); e.color = rgb(camo[1])
        L.new(vor.outputs["Fac"], ramp.inputs["Fac"]); L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        var = N.new("ShaderNodeTexNoise"); var.inputs["Scale"].default_value = 6.0
        L.new(tc.outputs["Object"], var.inputs["Vector"])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
        fac = next(x for x in mix.inputs if x.name.startswith("Factor") and x.enabled)
        ca = next(x for x in mix.inputs if x.name == "A" and x.type == "RGBA")
        cb = next(x for x in mix.inputs if x.name == "B" and x.type == "RGBA")
        res = next(x for x in mix.outputs if x.type == "RGBA")
        fac.default_value = 0.0; ca.default_value = rgb(color)
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"                # renkte hafif ton oynaması
        L.new(var.outputs["Fac"], mul.inputs[0]); mul.inputs[1].default_value = 0.35; mul.inputs[2].default_value = 0.83
        bright = N.new("ShaderNodeMix"); bright.data_type = "RGBA"; bright.blend_type = "MULTIPLY"
        bf = next(x for x in bright.inputs if x.name.startswith("Factor") and x.enabled); bf.default_value = 1.0
        ba = next(x for x in bright.inputs if x.name == "A" and x.type == "RGBA"); ba.default_value = rgb(color)
        bb = next(x for x in bright.inputs if x.name == "B" and x.type == "RGBA")
        comb = N.new("ShaderNodeCombineColor")
        for i in range(3): L.new(mul.outputs[0], comb.inputs[i])
        L.new(comb.outputs[0], bb)
        L.new(next(x for x in bright.outputs if x.type == "RGBA"), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if "Sheen Weight" in bsdf.inputs: bsdf.inputs["Sheen Weight"].default_value = sheen
    if "Coat Weight" in bsdf.inputs: bsdf.inputs["Coat Weight"].default_value = coat
    if bump > 0:
        n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 6.0
        L.new(tc.outputs["Object"], n.inputs["Vector"])
        b = N.new("ShaderNodeBump"); b.inputs["Strength"].default_value = bump; b.inputs["Distance"].default_value = 0.002
        h = n.outputs["Fac"]
        if webbing:
            wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
            wv.inputs["Scale"].default_value = 16.0; wv.wave_profile = "SAW"
            L.new(tc.outputs["Object"], wv.inputs["Vector"])
            mx = N.new("ShaderNodeMath"); mx.operation = "ADD"
            L.new(n.outputs["Fac"], mx.inputs[0]); L.new(wv.outputs["Fac"], mx.inputs[1]); h = mx.outputs[0]
            b.inputs["Strength"].default_value = bump * 1.6
        if folds:                                       # kumaş kırışıklığı: dikey uzatılmış, bükülmüş dalgalar
            mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 0.22)
            L.new(tc.outputs["Object"], mp.inputs["Vector"])
            fw = N.new("ShaderNodeTexWave"); fw.inputs["Scale"].default_value = 9.0; fw.inputs["Distortion"].default_value = 7.0
            fw.inputs["Detail"].default_value = 3.0
            L.new(mp.outputs["Vector"], fw.inputs["Vector"])
            mf = N.new("ShaderNodeMath"); mf.operation = "MULTIPLY_ADD"
            L.new(fw.outputs["Fac"], mf.inputs[0]); mf.inputs[1].default_value = folds; L.new(h, mf.inputs[2]); h = mf.outputs[0]
            b.inputs["Distance"].default_value = 0.006
        L.new(h, b.inputs["Height"]); L.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    MATS[name] = m
    return m


def setmat(ob, m):
    ob.data.materials.clear(); ob.data.materials.append(m); return ob


# ------------------------------------------------------------------ şekiller
def mods(ob, bevel=0.0, seg=3, subdiv=0, solid=0.0):
    if solid:
        s = ob.modifiers.new("solid", "SOLIDIFY"); s.thickness = solid
    if bevel:
        b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel; b.segments = seg; b.limit_method = "ANGLE"
    if subdiv:
        d = ob.modifiers.new("sub", "SUBSURF"); d.levels = subdiv; d.render_levels = subdiv
    return ob


def cube(name, loc, size, m, bevel=0.008, rot=(0, 0, 0), slot=None, subdiv=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=[math.radians(a) for a in rot])
    ob = bpy.context.active_object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    mods(ob, bevel=bevel, subdiv=subdiv); smooth(ob); setmat(ob, m)
    return link(ob, slot)


def cyl(name, p0, p1, r, m, verts=24, slot=None, bevel=0.0, r2=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r if r2 is None else r2, depth=d.length,
                                    location=(p0 + p1) / 2)
    ob = bpy.context.active_object; ob.name = name
    ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    if bevel: mods(ob, bevel=bevel, seg=2)
    smooth(ob); setmat(ob, m)
    return link(ob, slot)


def sphere(name, loc, scale, m, slot=None, seg=32, rings=16, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc, rotation=[math.radians(a) for a in rot])
    ob = bpy.context.active_object; ob.name = name; ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    smooth(ob); setmat(ob, m)
    return link(ob, slot)


def shell(name, loc, scale, m, cut_z=0.0, slot=None, thick=0.006, rot=(0, 0, 0)):
    """Yarım küre kabuk (kask, dizlik kapağı)."""
    ob = sphere(name, loc, scale, m, slot=slot, rot=rot)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data)
    rm = [v for v in bm.verts if v.co.z < cut_z * scale[2]]
    bmesh.ops.delete(bm, geom=rm, context="VERTS"); bm.to_mesh(ob.data); bm.free()
    mods(ob, solid=thick); smooth(ob)
    return ob


def skin(name, verts, edges, radii, m, subdiv=2, slot=None):
    """İskelet çizgisinden organik gövde (Skin + Subdivision)."""
    me = bpy.data.meshes.new(name); me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new(name, me); link(ob, slot)
    sk = ob.modifiers.new("skin", "SKIN"); sk.use_smooth_shade = True
    for i, r in enumerate(radii):
        me.skin_vertices[0].data[i].radius = r if isinstance(r, (tuple, list)) else (r, r)
    me.skin_vertices[0].data[0].use_root = True
    d = ob.modifiers.new("sub", "SUBSURF"); d.levels = subdiv; d.render_levels = subdiv
    setmat(ob, m)
    return ob


# ------------------------------------------------------------------ duruş (metre; ajan -Y yönüne bakar)
J = {"pelvis": (0, 0, 0.98), "spine": (0, 0.005, 1.16), "chest": (0, 0.01, 1.33), "neck": (0, 0.0, 1.5),
     "shL": (-0.19, 0.01, 1.43), "shR": (0.19, 0.01, 1.43), "elL": (-0.25, -0.12, 1.2), "elR": (0.25, -0.05, 1.16),
     "wrL": (-0.1, -0.4, 1.04), "wrR": (0.12, -0.27, 1.1),
     "hipL": (-0.1, 0, 0.93), "hipR": (0.1, 0, 0.93), "knL": (-0.11, -0.04, 0.52), "knR": (0.12, -0.02, 0.52),
     "anL": (-0.12, 0.01, 0.1), "anR": (0.13, 0.02, 0.1)}


def V(k): return Vector(J[k])


def body(shirt_m, pants_m, bulk=1.0, sleeve=1.0):
    b = bulk
    up = ["pelvis", "spine", "chest", "neck", "shL", "elL", "wrL", "shR", "elR", "wrR"]
    e = [(0, 1), (1, 2), (2, 3), (2, 4), (4, 5), (5, 6), (2, 7), (7, 8), (8, 9)]
    r = [(0.2 * b, 0.135 * b), (0.19 * b, 0.135 * b), (0.23 * b, 0.155 * b), 0.075, 0.095 * b, 0.072 * b * sleeve, 0.058 * sleeve,
         0.095 * b, 0.072 * b * sleeve, 0.058 * sleeve]
    skin("Shirt", [J[k] for k in up], e, r, shirt_m)
    lo = ["pelvis", "hipL", "knL", "anL", "hipR", "knR", "anR"]
    e = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6)]
    r = [(0.21 * b, 0.14 * b), 0.12 * b, 0.088 * b, 0.068, 0.12 * b, 0.088 * b, 0.068]
    skin("Pants", [J[k] for k in lo], e, r, pants_m)


def hands(m, slot="Gloves"):
    for s in "LR":
        el, wr = V("el" + s), V("wr" + s)
        d = (wr - el).normalized()
        c = wr + d * 0.045
        ob = sphere("Glove" + s, c, (0.038, 0.05, 0.034), m, slot)
        ob.rotation_mode = "QUATERNION"; ob.rotation_quaternion = d.to_track_quat("Y", "Z")
        cyl("Cuff" + s, wr - d * 0.03, wr + d * 0.01, 0.043, m, slot=slot)
        sphere("Thumb" + s, c + Vector((0.025 if s == "R" else -0.025, -0.01, 0.02)), (0.014, 0.022, 0.014), m, slot)


def boots(m, sole_m):
    for s in "LR":
        a = V("an" + s)
        cube("Boot" + s, (a.x, a.y - 0.045, 0.06), (0.1, 0.25, 0.11), m, bevel=0.035, subdiv=1)
        cube("Sole" + s, (a.x, a.y - 0.045, 0.012), (0.105, 0.26, 0.025), sole_m, bevel=0.008)
        cyl("Ankle" + s, (a.x, a.y, 0.08), (a.x, a.y, 0.2), 0.055, m)


def kneepads(m, big=False):
    for s in "LR":
        k = V("kn" + s)
        sc = (0.06, 0.07, 0.05) if not big else (0.07, 0.085, 0.06)
        shell("Knee" + s, (k.x, k.y - 0.035, k.z), sc, m, cut_z=0.0, slot="Kneepads", thick=0.01, rot=(90, 0, 0))
        cyl("KneeStrap" + s, (k.x, k.y, k.z + 0.05), (k.x, k.y, k.z + 0.07), 0.07, MATS["strap"], slot="Kneepads")


def holster(m, grip_m):
    cube("LegPlatform", (0.175, 0.0, 0.73), (0.03, 0.1, 0.2), m, slot="Holster")
    cube("HolsterBody", (0.2, -0.01, 0.72), (0.05, 0.075, 0.17), m, bevel=0.012, slot="Holster")
    for z in (0.66, 0.8):
        cyl("LegStrap%d" % int(z * 100), (0.12, 0.0, z), (0.12, 0.0, z + 0.025), 0.085, MATS["strap"], slot="Holster")
    cube("PistolGrip", (0.205, 0.005, 0.835), (0.036, 0.05, 0.075), grip_m, bevel=0.008, rot=(-12, 0, 0), slot="Sidearm")


def rifle(kind="carbine"):
    gun = mat("gunmetal", "#22252a", rough=0.38, metal=0.65, bump=0.05)
    poly = mat("polymer", "#2c2d2a", rough=0.6, bump=0.08)
    wr, wl = V("wrR"), V("wrL")
    x = (wl - wr).normalized(); upv = Vector((0, 0, 1))
    z = (upv - x * upv.dot(x)).normalized(); y = z.cross(x)
    from mathutils import Matrix
    R = Matrix((x, y, z)).transposed().to_quaternion()
    E = bpy.data.objects.new("Rifle", None); link(E)
    E.location = wr + z * 0.035; E.rotation_mode = "QUATERNION"; E.rotation_quaternion = R
    L = 1.25 if kind == "dmr" else (0.8 if kind == "smg" else 1.0)
    parts = []
    parts.append(cube("Receiver", (0.05, 0, 0.045), (0.24, 0.036, 0.06), gun, bevel=0.006))
    parts.append(cube("Handguard", (0.25 * L, 0, 0.05), (0.2 * L, 0.046, 0.052), poly, bevel=0.01))
    parts.append(cyl("Barrel", (0.35 * L, 0, 0.05), (0.52 * L, 0, 0.05), 0.009, gun))
    parts.append(cyl("Muzzle", (0.52 * L, 0, 0.05), (0.56 * L, 0, 0.05), 0.014, gun))
    mh = 0.08 if kind == "dmr" else 0.12
    parts.append(cube("Mag", (0.1, 0, -0.02), (0.036, 0.026, mh), poly, bevel=0.005, rot=(0, 12, 0)))
    parts.append(cube("Grip", (0.0, 0, -0.015), (0.03, 0.03, 0.075), poly, bevel=0.006, rot=(0, -18, 0)))
    parts.append(cyl("Buffer", (-0.07, 0, 0.055), (-0.16, 0, 0.055), 0.015, gun))
    parts.append(cube("Stock", (-0.2, 0, 0.035), (0.15, 0.036, 0.065), poly, bevel=0.01))
    if kind == "dmr":
        parts.append(cyl("Scope", (-0.04, 0, 0.12), (0.18, 0, 0.12), 0.022, gun, r2=0.026))
    else:
        parts.append(cyl("Optic", (0.02, 0, 0.115), (0.11, 0, 0.115), 0.019, gun))
    parts.append(cube("Mount", (0.06, 0, 0.085), (0.08, 0.025, 0.025), gun))
    for p in parts:
        p["slot"] = "Weapon"; p.parent = E


def backpack(m, w=0.32, h=0.42, d=0.17, z=1.27):
    cube("Pack", (0, 0.13 + d / 2 + 0.03, z), (w, d, h), m, bevel=0.045, subdiv=1, slot="Backpack")
    for s in (-1, 1):
        cube("PackSide%d" % s, (s * (w / 2 + 0.025), 0.13 + d / 2 + 0.03, z - 0.06), (0.05, d * 0.7, h * 0.45), m, bevel=0.015, slot="Backpack")
    cube("PackLid", (0, 0.13 + d / 2 + 0.02, z + h / 2), (w * 0.9, d * 0.95, 0.05), m, bevel=0.02, slot="Backpack")
    cube("PackPouch", (0, 0.13 + d + 0.045, z - 0.05), (w * 0.6, 0.04, h * 0.45), m, bevel=0.012, slot="Backpack")


def carrier(m, pouch_m, heavy=False):
    t = 0.06 if heavy else 0.045
    cube("PlateF", (0, -0.13 - t / 2 + 0.02, 1.3), (0.31, t, 0.33), m, bevel=0.015, slot="Chest")
    cube("PlateB", (0, 0.13 + t / 2 - 0.02, 1.3), (0.31, t, 0.35), m, bevel=0.015, slot="Chest")
    for s in (-1, 1):
        cube("Cummer%d" % s, (s * 0.165, 0, 1.2), (0.035, 0.25, 0.15), m, bevel=0.01, slot="Chest")
        cube("Strap%d" % s, (s * 0.105, 0, 1.475), (0.06, 0.27, 0.03), m, bevel=0.008, slot="Chest")
    for x in (-0.09, 0, 0.09):
        cube("MagPouch%d" % int(x * 100), (x, -0.135 - t - 0.012, 1.215), (0.075, 0.04, 0.12), pouch_m, bevel=0.01, slot="Chest")
    cube("Admin", (0, -0.135 - t - 0.008, 1.37), (0.17, 0.03, 0.075), pouch_m, bevel=0.01, slot="Chest")
    if heavy:
        for s in (-1, 1):
            shell("Pauldron%d" % s, (s * 0.21, 0.0, 1.44), (0.085, 0.1, 0.07), m, cut_z=-0.1, slot="Chest", thick=0.012)
        cyl("Collar", (0, 0, 1.46), (0, 0, 1.53), 0.105, m, slot="Chest")
        cube("Groin", (0, -0.12, 0.95), (0.18, 0.03, 0.16), m, bevel=0.015, slot="Chest")


def belt(m):
    ob = cyl("Belt", (0, 0, 1.0), (0, 0, 1.06), 0.165, m); ob.scale = (1, 0.72, 1)


# ------------------------------------------------------------------ kıyafetler (özgün)
def outfit_operator():
    MATS["strap"] = mat("strap", "#1c1d1b", rough=0.75, bump=0.3, webbing=True)
    body(mat("shirt", "#585c50", rough=0.85, bump=0.35, sheen=0.12), mat("pants", "#6b624d", rough=0.88, bump=0.35, camo=["#4c4838", "#857a60"], sheen=0.2))
    bala = mat("balaclava", "#141516", rough=0.9, bump=0.5, scale=260, sheen=0.15)
    sphere("Head", (0, -0.005, 1.66), (0.09, 0.105, 0.115), bala, "Mask")
    cyl("Neck", (0, 0, 1.48), (0, 0, 1.6), 0.056, bala, slot="Mask")
    helm = mat("helmet", "#8a7b5f", rough=0.55, bump=0.12, coat=0.15)
    shell("Helmet", (0, 0.008, 1.685), (0.116, 0.132, 0.112), helm, cut_z=-0.1, thick=0.012)
    for s in (-1, 1): cube("Rail%d" % s, (s * 0.112, 0.0, 1.68), (0.014, 0.1, 0.03), helm, bevel=0.004)
    cube("Shroud", (0, -0.118, 1.76), (0.05, 0.02, 0.035), mat("blackpoly", "#151617", rough=0.5), bevel=0.005)
    lens = mat("lens", "#1d2b33", rough=0.05, metal=0.4, bump=0, coat=1.0)
    rub = mat("rubber", "#121314", rough=0.65, bump=0.1)
    cube("GoggleFrame", (0, -0.093, 1.672), (0.165, 0.035, 0.06), rub, bevel=0.015, slot="Mask")
    cube("GoggleLens", (0, -0.108, 1.672), (0.15, 0.012, 0.048), lens, bevel=0.01, slot="Mask")
    bpy.ops.mesh.primitive_torus_add(major_radius=0.098, minor_radius=0.008, location=(0, 0.0, 1.672))
    gs = bpy.context.active_object; gs.name = "GoggleStrap"; gs.scale = (1, 1.12, 1); setmat(gs, MATS["strap"]); link(gs, "Mask")
    coy = mat("coyote", "#7a6a4f", rough=0.8, bump=0.4, webbing=True, sheen=0.15)
    carrier(coy, mat("pouch", "#6f6048", rough=0.8, bump=0.35, webbing=True))
    belt(MATS["strap"])
    hands(mat("glove", "#2b2c2d", rough=0.7, bump=0.25))
    kneepads(mat("kneecap", "#1a1b1c", rough=0.45, bump=0.08))
    boots(mat("boot", "#4a3b2c", rough=0.6, bump=0.3), rub)
    holster(mat("holster", "#1d1e1f", rough=0.55, bump=0.12), MATS["blackpoly"])
    backpack(mat("pack", "#5a5a44", rough=0.82, bump=0.4, webbing=True, sheen=0.15))
    rifle("carbine")


OUTFITS = {"operator": outfit_operator}


# ------------------------------------------------------------------ ışık, kamera, render
def lights_camera(w, h):
    sc = bpy.context.scene
    def area(name, loc, power, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA"); ld.energy = power; ld.size = size; ld.color = color
        ob = bpy.data.objects.new(name, ld); sc.collection.objects.link(ob); ob.location = loc
        c = ob.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
        return ob
    tgt = bpy.data.objects.new("Target", None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 0.95)
    area("Key", (-2.8, -2.2, 3.2), 620, 1.4, (1.0, 0.95, 0.88))
    area("Rim", (2.4, 2.2, 2.6), 900, 1.0, (0.7, 0.82, 1.0))
    area("Rim2", (-2.4, 2.0, 1.8), 520, 0.9, (1.0, 0.62, 0.32))
    area("Fill", (2.6, -2.2, 1.0), 45, 3.0)
    cd = bpy.data.cameras.new("Cam"); cd.lens = 70; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 36
    cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, -4.4, 1.1)
    c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); fl = bpy.context.active_object; fl.name = "Floor"
    fl.is_shadow_catcher = True
    sc.render.resolution_x, sc.render.resolution_y = w, h


def render(path, samples):
    sc = bpy.context.scene
    sc.cycles.samples = samples
    sc.render.filepath = path; sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)


def render_ids(path):
    """Yuva maskesi: her yuvanın parçaları düz sabit renk, geri kalan siyah (tek örnek, kenar yumuşatma yok)."""
    sc = bpy.context.scene
    saved = {}
    flat = {}
    for slot, col in list(SLOT_IDS.items()) + [("none", (0, 0, 0))]:
        m = bpy.data.materials.new("id_" + slot); m.use_nodes = True
        N = m.node_tree.nodes; N.clear()
        em = N.new("ShaderNodeEmission"); em.inputs[0].default_value = tuple(c / 255 for c in col) + (1,)
        out = N.new("ShaderNodeOutputMaterial"); m.node_tree.links.new(em.outputs[0], out.inputs[0])
        flat[slot] = m
    for ob in sc.objects:
        if ob.type != "MESH": continue
        if ob.name == "Floor": ob.hide_render = True; continue
        saved[ob.name] = [s.material for s in ob.material_slots]
        slot = ob.get("slot") or "none"
        for s in ob.material_slots: s.material = flat[slot]
    st = (sc.cycles.samples, sc.cycles.use_denoising, sc.render.film_transparent, sc.view_settings.view_transform, sc.view_settings.look,
          sc.render.filter_size, sc.world.node_tree.nodes["Background"].inputs[1].default_value)
    sc.cycles.samples = 1; sc.cycles.use_denoising = False; sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sc.render.filter_size = 0.01
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.render.filepath = path; sc.render.image_settings.color_mode = "RGB"
    bpy.ops.render.render(write_still=True)
    for name, ms in saved.items():
        for s, m in zip(bpy.data.objects[name].material_slots, ms): s.material = m
    bpy.data.objects["Floor"].hide_render = False
    (sc.cycles.samples, sc.cycles.use_denoising, sc.render.film_transparent, sc.view_settings.view_transform, sc.view_settings.look,
     sc.render.filter_size, sc.world.node_tree.nodes["Background"].inputs[1].default_value) = st


def main():
    global ROOT
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--outfit", default="operator"); ap.add_argument("--out", required=True)
    ap.add_argument("--views", default=""); ap.add_argument("--turntable", type=int, default=0)
    ap.add_argument("--size", default="600x720"); ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--ids", action="store_true"); ap.add_argument("--frames", default="")
    ap.add_argument("--blend", default="")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    w, h = (int(x) for x in a.size.split("x"))
    ROOT = reset()
    OUTFITS[a.outfit]()
    lights_camera(w, h)
    if a.blend: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
    angles = {"front": 0, "q3": 35, "side": 90, "back": 180, "q3back": 215}
    jobs = [(v, angles[v]) for v in a.views.split(",") if v]
    if a.turntable:
        idx = range(a.turntable)
        if a.frames:
            s, e = (int(x) for x in a.frames.split("-")); idx = range(s, e)
        jobs += [("%02d" % i, 360.0 * i / a.turntable) for i in idx]
    for name, deg in jobs:
        ROOT.rotation_euler = (0, 0, math.radians(deg))
        render(os.path.join(a.out, name + ".png"), a.samples)
        if a.ids or a.turntable: render_ids(os.path.join(a.out, name + "_id.png"))
        print("rendered", name, flush=True)


if __name__ == "__main__":
    main()
