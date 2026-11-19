"""Standalone MX-style desktop build planner UI."""
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk
from td2app.ui import ui_theme

import build_tool
import share


def _fixed_value_text(attribute):
    value = str(attribute.get("value", "")).strip()
    if not value:
        return "fixed roll"
    sign = "" if value.startswith(("+", "-")) else "+"
    return f"{sign}{value}{attribute.get('unit', '')}"


class BuildToolPanel:
    SPECIALIZATIONS = ("", "Survivalist", "Demolitionist", "Sharpshooter", "Gunner", "Technician", "Firewall")
    ATTRIBUTES = ("crit_chance", "crit_damage", "headshot_damage", "weapon_damage", "armor",
                  "explosive_resistance", "hazard_protection", "health", "skill_haste", "skill_damage",
                  "skill_duration", "repair_skills", "stability", "accuracy", "ammo_capacity",
                  "base_damage", "rpm", "magazine_size", "reload_time", "reload_speed")
    SHD = ("Weapon Damage", "Headshot Damage", "Critical Chance", "Critical Damage", "Armor", "Skill Haste")
    COLORS = ("#ff6400", "#55b7e8", "#a78de0")

    def __init__(self, parent, root, catalog, path, version, palette):
        self.root, self.catalog, self.path = root, catalog or {}, path
        self.version, self.palette = version, palette
        self.enemy_hp = tk.StringVar(value="2000000")
        self.error = None
        try:
            self.builds = build_tool.load(path)
        except (OSError, ValueError) as exc:
            self.builds, self.error = [], exc
            messagebox.showerror("Build Tool", f"Build data could not be loaded; the file was left unchanged.\n{exc}", parent=root)
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self.content = ui_theme.scrollable(self.frame, self.palette["bg"])
        self._create()

    def _create(self):
        f = self.content
        f.columnconfigure(0, weight=3); f.columnconfigure(1, weight=2)
        f.rowconfigure(2, weight=1); f.rowconfigure(4, weight=1)
        head = ttk.Frame(f); head.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=5)
        ttk.Label(head, text="THE DIVISION 2 BUILDS TOOL", style="Title.TLabel").pack(side="left")
        for text, command in (("Credits", self.credits), ("Patch Notes", self.patch_notes),
                              ("Issues or bug?", self.issues), ("Save & Share", self.share), ("Save Screenshot", self.screenshot),
                              ("Clear", self.clear), ("New Build", self.new)):
            ttk.Button(head, text=text, command=command).pack(side="right", padx=3)
        ctl = ttk.Frame(f); ctl.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        ctl.columnconfigure(1, weight=1)
        ttk.Label(ctl, text="Build").grid(row=0, column=0, padx=4)
        self.choice = ttk.Combobox(ctl, state="readonly", width=24); self.choice.grid(row=0, column=1, sticky="ew", padx=4)
        self.choice.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Label(ctl, text="Specialization").grid(row=0, column=2, padx=(12, 4))
        self.spec = ttk.Combobox(ctl, state="readonly", width=18, values=self.SPECIALIZATIONS)
        self.spec.grid(row=0, column=3, padx=4); self.spec.bind("<<ComboboxSelected>>", lambda _e: self.update_meta())
        ttk.Label(ctl, text="Name").grid(row=0, column=4, padx=(12, 4))
        self.name = tk.StringVar(); ttk.Entry(ctl, textvariable=self.name, width=22).grid(row=0, column=5, padx=4)
        ttk.Button(ctl, text="Save", command=self.save_current).grid(row=0, column=6, padx=4)
        self.grid = ttk.Frame(f); self.grid.grid(row=2, column=0, sticky="nsew", padx=(8, 4), pady=4)
        self.detail = ttk.Frame(f); self.detail.grid(row=2, column=1, sticky="nsew", padx=(4, 8), pady=4)
        self.weapons_box = ttk.LabelFrame(f, text="Weapon damage / RPM / magazine")
        self.weapons_box.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.chart = tk.Canvas(f, height=180, bg=self.palette["surface"], highlightthickness=1,
                               highlightbackground=self.palette["border"])
        self.chart.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=8, pady=4)
        self.chart.bind("<Configure>", lambda _e: self.refresh_chart())
        self.ttk_box = ttk.LabelFrame(f, text="Time to Kill · estimate")
        self.ttk_box.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.status = tk.StringVar(value="Independent local data: build_tool.json")
        ttk.Label(f, textvariable=self.status, foreground=self.palette["muted"]).grid(
            row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        self.refresh()

    def current(self):
        idx = self.choice.current()
        return self.builds[idx] if 0 <= idx < len(self.builds) else None

    def persist(self):
        if self.error:
            return False
        try:
            build_tool.save(self.path, self.builds)
            self.status.set(f"Saved locally · {len(self.builds)} build(s) · {self.path.name}")
            return True
        except OSError as exc:
            messagebox.showerror("Build Tool", f"Could not save build.\n{exc}", parent=self.root)
            return False

    def new(self):
        self.builds.append(build_tool.new_build())
        self.persist(); self.refresh(len(self.builds) - 1)

    def save_current(self):
        build = self.current()
        if not build: return
        build["name"] = self.name.get().strip()[:80] or "Untitled build"
        build["specialization"] = self.spec.get().strip()
        if self.persist(): self.refresh(self.choice.current())

    def update_meta(self):
        build = self.current()
        if build:
            build["specialization"] = self.spec.get().strip()
            self.persist(); self.refresh(self.choice.current())

    def clear(self):
        build = self.current()
        if build and messagebox.askyesno("Build Tool", "Clear all items and SHD values in this build?", parent=self.root):
            build["slots"] = {slot: None for slot in build_tool.SLOTS}
            build["shd_levels"] = {}
            self.persist(); self.refresh(self.choice.current())

    def options(self, slot):
        data = self.catalog
        if slot in build_tool.SLOTS[:6]:
            vals = list(data.get("items", {})) + list(data.get("gear_sets", [])) + list(data.get("brands", []))
        elif slot in ("Primary", "Secondary", "SideArm"):
            vals = list(data.get("weapon_index", {}))
        else:
            skills = data.get("skills", [])
            vals = list(skills if isinstance(skills, list) else skills.keys())
            vals += [item.get("name", "") for item in data.get("skill_variants", []) if isinstance(item, dict)]
        return sorted(set(str(v) for v in vals if str(v).strip()), key=str.casefold)[:1000]

    def edit_slot(self, slot):
        build = self.current()
        if not build: return
        old = build["slots"].get(slot) or {}
        win = tk.Toplevel(self.root); win.title(f"Build Tool · {slot}"); win.transient(self.root); win.grab_set()
        win.geometry("820x900")
        query = tk.StringVar(value=old.get("name", "")); ttk.Entry(win, textvariable=query).pack(fill="x", padx=10, pady=8)
        lb = tk.Listbox(win, exportselection=False); lb.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        options = self.options(slot)
        def fill(*_):
            lb.delete(0, "end")
            for value in options:
                if query.get().casefold() in value.casefold(): lb.insert("end", value)
        query.trace_add("write", fill); fill()
        editor = ttk.LabelFrame(win, text="Core, brand / gearset, talent and item stats")
        editor.pack(fill="x", padx=10, pady=4)
        editor.columnconfigure(1, weight=1)
        editor.columnconfigure(3, weight=1)
        core = tk.StringVar(value=old.get("core", "")); ttk.Label(editor, text="Core").grid(row=0, column=0, padx=5, pady=3)
        ttk.Combobox(editor, textvariable=core, values=("", "Weapon Damage", "Armor", "Skill Tier"), width=20).grid(row=0, column=1, padx=5, pady=3)
        brand = tk.StringVar(value=old.get("brand", "")); gear = tk.StringVar(value=old.get("gear_set", ""))
        ttk.Label(editor, text="Brand").grid(row=0, column=2, padx=5)
        ttk.Combobox(editor, textvariable=brand, values=tuple(self.catalog.get("brands", ())), width=24).grid(row=0, column=3, padx=5)
        ttk.Label(editor, text="Gearset").grid(row=1, column=0, padx=5)
        ttk.Combobox(editor, textvariable=gear, values=tuple(self.catalog.get("gear_sets", ())), width=22).grid(row=1, column=1, padx=5)
        talent = tk.StringVar(value=old.get("talent", "")); ttk.Label(editor, text="Talent").grid(row=1, column=2, padx=5)
        ttk.Entry(editor, textvariable=talent, width=24).grid(row=1, column=3, padx=5)
        attrs = old.get("attrs", {})
        entries = {}
        for idx, key in enumerate(self.ATTRIBUTES):
            row, pair = divmod(idx, 2)
            col = pair * 2
            ttk.Label(editor, text=key.replace("_", " ").title()).grid(row=row + 2, column=col, padx=5, pady=2, sticky="w")
            var = tk.StringVar(value=str(attrs.get(key, ""))); entries[key] = var
            ttk.Entry(editor, textvariable=var, width=12).grid(row=row + 2, column=col + 1, padx=5, pady=2, sticky="w")
        preview = tk.StringVar(value="Select a catalog item to load its fixed details.")
        ttk.Label(win, textvariable=preview, wraplength=680, justify="left", foreground=self.palette["muted"]).pack(
            fill="x", padx=12, pady=4)

        def select_item(_event=None):
            if not lb.curselection():
                return
            selected = lb.get(lb.curselection()[0])
            auto = build_tool.auto_details(selected, slot, self.catalog)
            core.set(auto["core"])
            brand.set(auto["brand"])
            gear.set(auto["gear_set"])
            talent.set(auto["talent"])
            for key, var in entries.items():
                var.set(str(auto["attrs"].get(key, "")))
            lines = []
            if auto["talent"]:
                lines.append(f"Talent: {auto['talent']}")
            for fixed in auto["fixed_attributes"]:
                lines.append(f"Fixed attribute · {fixed['name']}: {_fixed_value_text(fixed)}")
            for attachment in auto["attachments"]:
                line = f"{attachment['slot'].title()}: {attachment['name']}"
                if not attachment.get("stats") or attachment["stats"].strip().upper() == "N/A":
                    line += " · fixed attribute data unavailable in catalog"
                lines.append(line)
            lines.extend(f"Available {value} slot" for value in auto["mod_slots"])
            preview.set("\n".join(lines) if lines else "No fixed catalog details; variable rolls remain editable.")

        lb.bind("<<ListboxSelect>>", select_item)
        existing = next((i for i, value in enumerate(options) if value.casefold() == old.get("name", "").casefold()), None)
        if existing is not None:
            lb.selection_set(existing)
            lb.see(existing)
            select_item()
        def apply():
            name = lb.get(lb.curselection()[0]) if lb.curselection() else query.get().strip()
            if not name:
                messagebox.showerror("Build Tool", "Choose or type an item name.", parent=win); return
            auto = build_tool.auto_details(name, slot, self.catalog)
            parsed = dict(auto["attrs"])
            for key, var in entries.items():
                if var.get().strip():
                    try: parsed[key] = float(var.get().replace(",", "."))
                    except ValueError:
                        messagebox.showerror("Build Tool", f"Invalid number in {key}.", parent=win); return
            build["slots"][slot] = {**auto, "name": name[:120], "core": core.get().strip(),
                                    "brand": brand.get().strip(), "gear_set": gear.get().strip(),
                                    "talent": talent.get().strip(), "attrs": parsed}
            self.persist(); win.destroy(); self.refresh(self.choice.current())
        buttons = ttk.Frame(win); buttons.pack(fill="x", padx=10, pady=8)
        ttk.Button(buttons, text="Remove", command=lambda: (build["slots"].__setitem__(slot, None), self.persist(), win.destroy(), self.refresh(self.choice.current()))).pack(side="left")
        ttk.Button(buttons, text="Apply", command=apply).pack(side="right", padx=4)
        ttk.Button(buttons, text="Cancel", command=win.destroy).pack(side="right")
        lb.bind("<Double-1>", lambda _e: apply())

    def share(self):
        build = self.current()
        if build:
            slots = dict(build["slots"])
            slots["Sidearm"] = slots.pop("SideArm", None)
            payload = {"name": build["name"], "build_tool": {
                "specialization": build["specialization"], "watch": sum(build["shd_levels"].values()),
                "shd_levels": build["shd_levels"], "enemy_hp": build["enemy_hp"], "slots": slots}}
            self.root.clipboard_clear(); self.root.clipboard_append(share.encode(payload))
            self.status.set("Share string copied to clipboard; it was not uploaded.")

    def patch_notes(self):
        messagebox.showinfo("Build Tool · Notes",
            "Standalone build records · specialization and 11 loadout slots · brand/gearset bonus preview · "
            "weapon DPS/TTK estimates. Estimates use the local game library or values entered in the slot editor.",
            parent=self.root)

    def credits(self):
        messagebox.showinfo("Build Tool · Credits",
            "MX Division Builds Tool is the reference for the layout and calculations. "
            "This is an independent implementation. See docs/third_party/mx-division-builds-attribution.md "
            "for the source and license notice.", parent=self.root)

    def issues(self):
        webbrowser.open("https://github.com/FEDERALTURK/td2-loot-advisor/issues")

    def screenshot(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", initialfile="td2-build-tool.png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                from PIL import ImageGrab
                self.root.update_idletasks()
                box = (self.root.winfo_rootx(), self.root.winfo_rooty(), self.root.winfo_rootx()+self.root.winfo_width(), self.root.winfo_rooty()+self.root.winfo_height())
                ImageGrab.grab(bbox=box).save(path)
            except Exception as exc:
                messagebox.showerror("Build Tool", str(exc), parent=self.root)

    def refresh(self, index=None):
        if index is None: index = self.choice.current()
        names = [item["name"] for item in self.builds]
        self.choice["values"] = names
        if names:
            index = min(max(index, 0), len(names)-1); self.choice.current(index); build = self.builds[index]
        else:
            self.choice.set(""); self.name.set(""); self._clear_views(); return
        self.name.set(build["name"]); self.spec.set(build.get("specialization", ""))
        result = build_tool.calculate(build, self.catalog)
        for child in self.grid.winfo_children(): child.destroy()
        labels = ("PRIMARY", "SECONDARY", "SIDEARM", "MASK", "BACKPACK", "CHEST", "GLOVES", "HOLSTER", "KNEEPADS", "SKILL 1", "SKILL 2")
        slots = ("Primary", "Secondary", "SideArm") + build_tool.SLOTS[:6] + ("Skill1", "Skill2")
        for col in range(4): self.grid.columnconfigure(col, weight=1)
        for idx, (slot, title) in enumerate(zip(slots, labels)):
            row, col = divmod(idx, 4); item = build["slots"].get(slot) or {}
            card = tk.Frame(self.grid, bg=self.palette["surface"], highlightthickness=1, highlightbackground=self.palette["border"])
            card.grid(row=row, column=col, sticky="nsew", padx=3, pady=3, ipadx=5, ipady=8)
            tk.Label(card, text=title, bg=self.palette["surface"], fg=self.palette["accent"], font=("Consolas", 9, "bold")).pack(anchor="w")
            tk.Label(card, text=item.get("name") or "CHOOSE ITEM", bg=self.palette["surface"], fg=self.palette["fg"],
                     wraplength=140, justify="center", height=3).pack(fill="both", expand=True)
            for widget in (card, *card.winfo_children()): widget.bind("<Button-1>", lambda _e, s=slot: self.edit_slot(s))
        self._draw_stats(result)
        self._draw_weapon_stats(build, result)
        self._draw_ttk(result)
        self.refresh_chart()

    def _clear_views(self):
        for widget in (self.grid, self.detail, self.weapons_box, self.ttk_box):
            for child in widget.winfo_children(): child.destroy()
        self.chart.delete("all")

    def _draw_stats(self, result):
        for child in self.detail.winfo_children(): child.destroy()
        for title, key, fields in (("Offensive", "offensive", ("weapon_damage", "headshot_damage", "crit_chance", "crit_damage", "reload_speed", "stability", "accuracy", "ammo_capacity")),
                                   ("Defensive", "defensive", ("armor", "explosive_resistance", "hazard_protection", "health")),
                                   ("Utility", "utility", ("skill_haste", "skill_damage", "skill_duration", "repair_skills", "skill_tier"))):
            group = ttk.LabelFrame(self.detail, text=f"{title} Cores · {result['cores'][key]}"); group.pack(fill="x", padx=4, pady=3)
            for field in fields:
                ttk.Label(group, text=f"{field.replace('_', ' ').title()}: {result['stats'][field]:g}").pack(anchor="w", padx=6, pady=1)
        ttk.Label(self.detail, text=f"Total Armor · {result['armor']:,.0f} · estimate", foreground=self.palette["accent"], style="Title.TLabel").pack(anchor="w", padx=6, pady=4)
        watch = ttk.LabelFrame(self.detail, text="SHD Watch Levels")
        watch.pack(fill="x", padx=4, pady=3)
        levels = self.current().get("shd_levels", {})
        ttk.Button(watch, text="Set all to max", command=self.set_all_shd).grid(row=0, column=4, padx=5)
        for i, name in enumerate(self.SHD):
            row = i//2 + 1
            ttk.Label(watch, text=name).grid(row=row, column=(i%2)*2, padx=5, pady=2, sticky="w")
            value = tk.IntVar(value=levels.get(name, 0))
            spin = ttk.Spinbox(watch, from_=0, to=10, width=4, textvariable=value,
                               command=lambda n=name, v=value: self.set_shd(n, v.get()))
            spin.grid(row=row, column=(i%2)*2+1, padx=4)
        ttk.Label(watch, text="Watch levels are stored separately; their derived bonuses are not included in stat estimates.",
                  foreground=self.palette["muted"]).grid(row=4, column=0, columnspan=5, sticky="w", padx=5, pady=3)
        for title, values in (("Gearset Bonus", result["bonuses"]["gear_sets"]), ("Brand Bonus", result["bonuses"]["brands"])):
            panel = ttk.LabelFrame(self.detail, text=title); panel.pack(fill="x", padx=4, pady=3)
            for bonus in values:
                ttk.Label(panel, text=f"{bonus['name']} · {bonus['tier']} pc · {bonus['text']}", wraplength=460).pack(anchor="w", padx=6, pady=1)
            if not values: ttk.Label(panel, text="No active bonus", foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        fixed = ttk.LabelFrame(self.detail, text="Selected item · catalog fixed details")
        fixed.pack(fill="x", padx=4, pady=3)
        any_details = False
        for slot, item in self.current()["slots"].items():
            if not item:
                continue
            current = build_tool.auto_details(item.get("name"), slot, self.catalog)
            lines = []
            talent = item.get("talent") or current.get("talent")
            if talent:
                lines.append(f"Talent: {talent}")
            fixed = {(attr.get("slot", ""), attr.get("name", "")): attr
                     for attr in item.get("fixed_attributes", [])
                     if not str(attr.get("slot", "")).startswith("core_")}
            fixed.update({(attr.get("slot", ""), attr.get("name", "")): attr
                          for attr in current.get("fixed_attributes", [])})
            for attr in fixed.values():
                lines.append(f"Fixed attribute · {attr['name']}: {_fixed_value_text(attr)}")
            attachments = {attachment.get("slot", ""): attachment
                           for attachment in item.get("attachments", [])}
            attachments.update({attachment.get("slot", ""): attachment
                                for attachment in current.get("attachments", [])})
            for attachment in attachments.values():
                line = f"{attachment['slot'].title()}: {attachment['name']}"
                if not attachment.get("stats") or attachment["stats"].strip().upper() == "N/A":
                    line += " · fixed attribute data unavailable in catalog"
                lines.append(line)
            available_slots = dict.fromkeys(current.get("mod_slots", []) + item.get("mod_slots", []))
            lines.extend(f"Available {value} slot" for value in available_slots)
            if lines:
                any_details = True
                ttk.Label(fixed, text=f"{slot} · {item['name']}\n" + "\n".join(lines),
                          wraplength=460, justify="left").pack(anchor="w", padx=6, pady=3)
        if not any_details:
            ttk.Label(fixed, text="No catalogued fixed details for selected items.",
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)

    def set_shd(self, name, value):
        build = self.current()
        if build:
            try: build.setdefault("shd_levels", {})[name] = max(0, min(10, int(value)))
            except (ValueError, TypeError): return
            self.persist()

    def set_all_shd(self):
        build = self.current()
        if build:
            build["shd_levels"] = {name: 10 for name in self.SHD}
            self.persist(); self.refresh(self.choice.current())

    def _draw_weapon_stats(self, build, result):
        for child in self.weapons_box.winfo_children(): child.destroy()
        by_slot = {row["slot"]: row for row in result["weapons"]}
        for slot in ("Primary", "Secondary", "SideArm"):
            item = build["slots"].get(slot) or {}; calc = by_slot.get(slot, {})
            text = (f"{slot}\n{item.get('name') or 'No weapon selected'}\n"
                    f"Damage {calc.get('damage', 0):g} · RPM {calc.get('rpm', 0):g} · Mag {calc.get('magazine', 0):g} · Reload {calc.get('reload', 0):g}s")
            tk.Label(self.weapons_box, text=text, bg=self.palette["surface"], fg=self.palette["fg"], justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=5)

    def _draw_ttk(self, result):
        for child in self.ttk_box.winfo_children(): child.destroy()
        self.enemy_hp.set(str(int(result["enemy_hp"])))
        ttk.Label(self.ttk_box, text="Target HP").grid(row=0, column=0, padx=6, pady=4)
        hp = ttk.Spinbox(self.ttk_box, from_=1, to=100_000_000, increment=100_000, textvariable=self.enemy_hp, width=12,
                         command=self.update_enemy_hp)
        hp.grid(row=0, column=1, padx=4, pady=4); hp.bind("<FocusOut>", lambda _e: self.update_enemy_hp())
        columns = ("slot", "weapon", "damage", "rpm", "mag", "dps", "ttk")
        table = ttk.Treeview(self.ttk_box, columns=columns, show="headings", height=3)
        for key, title in zip(columns, ("Slot", "Weapon", "Damage", "RPM", "Mag", "DPS estimate", "TTK estimate")):
            table.heading(key, text=title)
        table.column("weapon", width=220); table.column("slot", width=90)
        table.grid(row=1, column=0, columnspan=7, sticky="ew", padx=4, pady=3)
        for weapon in result["weapons"]:
            table.insert("", "end", values=(weapon["slot"], weapon["name"], f"{weapon['damage']:,.0f}",
                        f"{weapon['rpm']:,.0f}", f"{weapon['magazine'] or 0:,.0f}", f"{weapon['dps']:,.0f}", f"{weapon['ttk']:.1f}s"))
        if not result["weapons"]:
            ttk.Label(self.ttk_box, text="Select a weapon or enter base damage and RPM in its slot editor.",
                      foreground=self.palette["muted"]).grid(row=2, column=0, columnspan=7, sticky="w", padx=6)

    def update_enemy_hp(self):
        build = self.current()
        if not build: return
        try:
            build["enemy_hp"] = max(1, min(100_000_000, int(float(self.enemy_hp.get().replace(",", ".")))))
        except (ValueError, TypeError):
            self.enemy_hp.set(str(int(build["enemy_hp"])))
            return
        self.persist(); self.refresh(self.choice.current())

    def refresh_chart(self):
        if not hasattr(self, "chart"): return
        self.chart.delete("all"); width=max(self.chart.winfo_width(), 500); height=max(self.chart.winfo_height(), 160)
        left, top, right, bottom = 46, 32, width-12, height-24
        self.chart.create_text(10, 8, text="Damage over Time · estimate", anchor="nw", fill=self.palette["fg"])
        self.chart.create_line(left, bottom, right, bottom, fill=self.palette["muted"]); self.chart.create_line(left, top, left, bottom, fill=self.palette["muted"])
        build = self.current()
        if not build: return
        weapons = build_tool.calculate(build, self.catalog)["weapons"]
        if not weapons:
            self.chart.create_text((left+right)/2, (top+bottom)/2, text="Select a weapon with library base stats or enter damage and RPM.", fill=self.palette["muted"]); return
        max_dps = max(w["dps"] for w in weapons) or 1
        for idx, weapon in enumerate(weapons):
            points=[]
            for n in range(21):
                sec=n/2; points += [left+(right-left)*n/20, bottom-(bottom-top)*min(1, weapon["dps"]*sec/(max_dps*10))]
            color=self.COLORS[idx%len(self.COLORS)]; self.chart.create_line(*points, fill=color, width=2)
            self.chart.create_text(left+4, top+idx*16, text=f"{weapon['slot']} · {weapon['dps']:,.0f}", anchor="nw", fill=color)
