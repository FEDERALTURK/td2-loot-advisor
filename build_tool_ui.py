"""Standalone MX-style desktop build planner UI."""
import tkinter as tk
import copy
import webbrowser
from tkinter import filedialog, messagebox, ttk
from td2app.ui import ui_theme
try:
    from td2app.ui.ctk_compat import (CtkFrame, CtkLabel, CtkButton, CtkEntry,
        CtkComboBox, CtkTextbox, CtkToplevel, CtkScrollbar)
except ImportError:
    CtkFrame, CtkLabel, CtkButton = tk.Frame, tk.Label, tk.Button
    CtkEntry, CtkComboBox = ttk.Entry, ttk.Combobox
    CtkTextbox, CtkToplevel, CtkScrollbar = tk.Text, tk.Toplevel, ttk.Scrollbar

import build_tool
import share


def _fixed_value_text(attribute):
    value = str(attribute.get("value", "")).strip()
    if not value:
        return "fixed roll"
    sign = "" if value.startswith(("+", "-")) else "+"
    return f"{sign}{value}{attribute.get('unit', '')}"


def _slot_grid_positions(width, count, min_card_width=165, max_columns=4):
    columns = max(1, min(max_columns, int(max(1, width) // min_card_width)))
    return columns, [(index // columns, index % columns) for index in range(count)]


class BuildToolPanel:
    SPECIALIZATIONS = ("", "Survivalist", "Demolitionist", "Sharpshooter", "Gunner", "Technician", "Firewall")
    ATTRIBUTES = ("crit_chance", "crit_damage", "headshot_damage", "weapon_damage", "weapon_type_damage", "armor",
                  "explosive_resistance", "hazard_protection", "health", "skill_haste", "skill_damage",
                  "skill_duration", "repair_skills", "stability", "accuracy", "ammo_capacity",
                  "base_damage", "rpm", "magazine_size", "reload_time", "reload_speed")
    SHD = ("Weapon Damage", "Headshot Damage", "Critical Chance", "Critical Damage", "Armor", "Skill Haste")
    COLORS = ("#ff6400", "#55b7e8", "#a78de0")

    def __init__(self, parent, root, catalog, path, version, palette, stash_provider=None,
                 target_loot_provider=None, summary_callback=None):
        self.root, self.catalog, self.path = root, catalog or {}, path
        self.version, self.palette = version, palette
        self.stash_provider = stash_provider
        self.target_loot_provider = target_loot_provider
        self.summary_callback = summary_callback
        self._stash_matches = None
        self._farm_routes = {}
        self._slot_cards = []
        self._grid_columns = 0
        self.enemy_hp = tk.StringVar(value="2000000")
        self.error = None
        try:
            store = build_tool.load_store(path)
            self.builds, self.templates = store["builds"], store["templates"]
            self._persisted_builds = copy.deepcopy(self.builds)
            self._persisted_templates = copy.deepcopy(self.templates)
        except (OSError, ValueError) as exc:
            self.builds, self.templates, self.error = [], [], exc
            self._persisted_builds = []
            self._persisted_templates = []
            messagebox.showerror("Build Tool", f"Build data could not be loaded; the file was left unchanged.\n{exc}", parent=root)
        self.frame = CtkFrame(parent)
        self.frame.pack(fill="both", expand=True)
        self.content = ui_theme.scrollable(self.frame, self.palette["bg"])
        self._create()

    def _create(self):
        f = self.content
        f.columnconfigure(0, weight=3); f.columnconfigure(1, weight=2)
        f.rowconfigure(2, weight=1); f.rowconfigure(4, weight=1)
        head = CtkFrame(f); head.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=5)
        CtkLabel(head, text="THE DIVISION 2 BUILDS TOOL", style="Title.TLabel").pack(side="left")
        actions = ttk.Menubutton(head, text="Build actions ▾")
        actions_menu = tk.Menu(actions, tearoff=False)
        actions_menu.add_command(label="Compare builds", command=self.compare_dialog)
        actions_menu.add_command(label="Templates", command=self.template_dialog)
        actions_menu.add_separator()
        actions_menu.add_command(label="Import builds / templates from JSON", command=self.import_json)
        actions_menu.add_command(label="Export builds / templates to JSON", command=self.export_json)
        actions["menu"] = actions_menu
        actions.pack(side="right", padx=3)
        for text, command in (("Credits", self.credits), ("Patch Notes", self.patch_notes),
                              ("Issues or bug?", self.issues), ("Save & Share", self.share), ("Save Screenshot", self.screenshot),
                              ("Clear", self.clear), ("New Build", self.new)):
            CtkButton(head, text=text, command=command).pack(side="right", padx=3)
        ctl = CtkFrame(f); ctl.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        ctl.columnconfigure(1, weight=1)
        CtkLabel(ctl, text="Build").grid(row=0, column=0, padx=4)
        self.choice = CtkComboBox(ctl, state="readonly", width=24); self.choice.grid(row=0, column=1, sticky="ew", padx=4)
        self.choice.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        CtkLabel(ctl, text="Specialization").grid(row=0, column=2, padx=(12, 4))
        self.spec = CtkComboBox(ctl, state="readonly", width=18, values=self.SPECIALIZATIONS)
        self.spec.grid(row=0, column=3, padx=4); self.spec.bind("<<ComboboxSelected>>", lambda _e: self.update_meta())
        CtkLabel(ctl, text="Name").grid(row=0, column=4, padx=(12, 4))
        self.name = tk.StringVar(); CtkEntry(ctl, textvariable=self.name, width=22).grid(row=0, column=5, padx=4)
        CtkButton(ctl, text="Save", command=self.save_current).grid(row=0, column=6, padx=4)
        self.grid = CtkFrame(f); self.grid.grid(row=2, column=0, sticky="nsew", padx=(8, 4), pady=4)
        self.grid.bind("<Configure>", lambda event: self._layout_slot_cards(event.width))
        self.detail = CtkFrame(f); self.detail.grid(row=2, column=1, sticky="nsew", padx=(4, 8), pady=4)
        self.weapons_box = ttk.LabelFrame(f, text="Weapon damage / RPM / magazine")
        self.weapons_box.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.chart = tk.Canvas(f, height=180, bg=self.palette["surface"], highlightthickness=1,
                               highlightbackground=self.palette["border"])
        self.chart.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=8, pady=4)
        self.chart.bind("<Configure>", lambda _e: self.refresh_chart())
        self.ttk_box = ttk.LabelFrame(f, text="Time to Kill · estimate")
        self.ttk_box.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.status = tk.StringVar(value=("Read-only · build data could not be loaded · original file preserved"
                                          if self.error else "Independent local data: build_tool.json"))
        CtkLabel(f, textvariable=self.status, foreground=self.palette["muted"]).grid(
            row=6, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        self._refresh_job = self.root.after_idle(self.refresh)

    def current(self):
        try:
            idx = self.choice.current()
        except (tk.TclError, RuntimeError):
            # Theme/language rebuilds may invalidate the old panel before its
            # queued refresh callback is drained.
            return None
        return self.builds[idx] if 0 <= idx < len(self.builds) else None

    def persist(self):
        if self.error:
            self.status.set("Read-only · build data could not be loaded or saved · original file preserved")
            return False
        try:
            build_tool.save_store(self.path, self.builds, self.templates)
            self._persisted_builds = copy.deepcopy(self.builds)
            self._persisted_templates = copy.deepcopy(self.templates)
            self._stash_matches = None
            self.status.set(f"Saved locally · {len(self.builds)} build(s) · {self.path.name}")
            return True
        except OSError as exc:
            self.builds = copy.deepcopy(self._persisted_builds)
            self.templates = copy.deepcopy(self._persisted_templates)
            self.error = exc
            self.status.set("Read-only · build data could not be saved · last saved data restored")
            messagebox.showerror("Build Tool", f"Could not save build.\n{exc}", parent=self.root)
            return False

    def can_edit(self):
        if self.error:
            self.status.set("Read-only · build data could not be loaded or saved · original file preserved")
            return False
        return True

    def new(self):
        if not self.can_edit(): return
        build = build_tool.new_build()
        build_tool.stamp_catalog(build, self.catalog)
        self.builds.append(build)
        self.persist(); self.refresh(len(self.builds) - 1)

    def save_current(self):
        if not self.can_edit(): return
        build = self.current()
        if not build: return
        build["name"] = self.name.get().strip()[:80] or "Untitled build"
        build["specialization"] = self.spec.get().strip()
        build_tool.stamp_catalog(build, self.catalog)
        self.persist(); self.refresh(self.choice.current())

    def update_meta(self):
        if not self.can_edit(): return
        build = self.current()
        if build:
            build["specialization"] = self.spec.get().strip()
            build_tool.stamp_catalog(build, self.catalog)
            self.persist(); self.refresh(self.choice.current())

    def clear(self):
        if not self.can_edit(): return
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

    def _layout_slot_cards(self, width):
        columns, positions = _slot_grid_positions(width, len(self._slot_cards))
        if columns == self._grid_columns and all(card.grid_info() for card in self._slot_cards):
            return
        self._grid_columns = columns
        for col in range(4):
            self.grid.columnconfigure(col, weight=1 if col < columns else 0, minsize=0)
        for row in range(12):
            self.grid.rowconfigure(row, weight=0)
        for card, (row, col) in zip(self._slot_cards, positions):
            card.grid(row=row, column=col, sticky="nsew", padx=3, pady=3, ipadx=5, ipady=8)
        for row in range((len(self._slot_cards) + columns - 1) // columns):
            self.grid.rowconfigure(row, weight=1)

    def edit_slot(self, slot):
        if not self.can_edit(): return
        build = self.current()
        if not build: return
        old = build["slots"].get(slot) or {}
        win = CtkToplevel(self.root); win.title(f"Build Tool · {slot}"); win.transient(self.root); win.grab_set()
        win.geometry(f"{min(820, max(520, win.winfo_screenwidth() - 80))}x"
                     f"{min(900, max(480, win.winfo_screenheight() - 100))}")
        query = tk.StringVar(value=old.get("name", "")); CtkEntry(win, textvariable=query).pack(fill="x", padx=10, pady=8)
        lb = tk.Listbox(win, exportselection=False); lb.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        options = self.options(slot)
        pending_filter = {"after": None}
        def fill(*_):
            pending_filter["after"] = None
            lb.delete(0, "end")
            for value in build_tool.search_catalog_options(options, query.get(), self.catalog, slot):
                lb.insert("end", value)
        def schedule_fill(*_):
            if pending_filter["after"]:
                win.after_cancel(pending_filter["after"])
            pending_filter["after"] = win.after(80, fill)
        query.trace_add("write", schedule_fill); fill()
        editor = ttk.LabelFrame(win, text="Core, brand / gearset, talent and item stats")
        editor.pack(fill="x", padx=10, pady=4)
        editor.columnconfigure(1, weight=1)
        editor.columnconfigure(3, weight=1)
        core = tk.StringVar(value=old.get("core", "")); CtkLabel(editor, text="Core").grid(row=0, column=0, padx=5, pady=3)
        CtkComboBox(editor, textvariable=core, values=("", "Weapon Damage", "Armor", "Skill Tier"), width=20).grid(row=0, column=1, padx=5, pady=3)
        brand = tk.StringVar(value=old.get("brand", "")); gear = tk.StringVar(value=old.get("gear_set", ""))
        CtkLabel(editor, text="Brand").grid(row=0, column=2, padx=5)
        CtkComboBox(editor, textvariable=brand, values=tuple(self.catalog.get("brands", ())), width=24).grid(row=0, column=3, padx=5)
        CtkLabel(editor, text="Gearset").grid(row=1, column=0, padx=5)
        CtkComboBox(editor, textvariable=gear, values=tuple(self.catalog.get("gear_sets", ())), width=22).grid(row=1, column=1, padx=5)
        talent = tk.StringVar(value=old.get("talent", "")); CtkLabel(editor, text="Talent").grid(row=1, column=2, padx=5)
        CtkEntry(editor, textvariable=talent, width=24).grid(row=1, column=3, padx=5)
        attrs = old.get("attrs", {})
        entries = {}
        for idx, key in enumerate(self.ATTRIBUTES):
            row, pair = divmod(idx, 2)
            col = pair * 2
            CtkLabel(editor, text=key.replace("_", " ").title()).grid(row=row + 2, column=col, padx=5, pady=2, sticky="w")
            var = tk.StringVar(value=str(attrs.get(key, ""))); entries[key] = var
            CtkEntry(editor, textvariable=var, width=12).grid(row=row + 2, column=col + 1, padx=5, pady=2, sticky="w")
        preview = tk.StringVar(value="Select a catalog item to load its fixed details.")
        CtkLabel(win, textvariable=preview, wraplength=680, justify="left", foreground=self.palette["muted"]).pack(
            fill="x", padx=12, pady=4)

        def select_item(_event=None, reset=True):
            if not lb.curselection():
                return
            selected = lb.get(lb.curselection()[0])
            auto = build_tool.auto_details(selected, slot, self.catalog)
            if reset and selected.casefold() != old.get("name", "").casefold():
                core.set(auto["core"])
                brand.set(auto["brand"])
                gear.set(auto["gear_set"])
                talent.set(auto["talent"])
                for key, var in entries.items():
                    var.set(str(auto["attrs"].get(key, "")))
            lines = []
            if auto["catalog_status"] == "unverified":
                lines.append("REVIEW REQUIRED · item is not in the current catalog; fixed values were not inferred.")
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
            preview.set("\n".join(lines) if lines else
                        ("Catalogued item · no fixed catalog details; variable rolls remain editable."
                         if auto["catalog_status"] == "catalogued" else
                         "REVIEW REQUIRED · item is not in the current catalog; fixed values were not inferred."))

        lb.bind("<<ListboxSelect>>", select_item)
        existing = next((i for i, value in enumerate(options) if value.casefold() == old.get("name", "").casefold()), None)
        if existing is not None:
            lb.selection_set(existing)
            lb.see(existing)
            select_item(reset=False)
        def apply():
            if not self.can_edit(): return
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
            build_tool.stamp_catalog(build, self.catalog)
            self.persist(); win.destroy(); self.refresh(self.choice.current())
        buttons = CtkFrame(win); buttons.pack(fill="x", padx=10, pady=8)
        def remove():
            if not self.can_edit(): return
            build["slots"][slot] = None
            self.persist(); win.destroy(); self.refresh(self.choice.current())
        CtkButton(buttons, text="Remove", command=remove).pack(side="left")
        CtkButton(buttons, text="Apply", command=apply).pack(side="right", padx=4)
        CtkButton(buttons, text="Cancel", command=win.destroy).pack(side="right")
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

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="td2-builds.json",
                                            filetypes=[("Build Tool JSON", "*.json")])
        if not path:
            return
        try:
            build_tool.export_json(path, self.builds, self.templates)
            self.status.set(f"Exported {len(self.builds)} build(s) and {len(self.templates)} template(s) locally.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Build Tool", f"Export failed.\n{exc}", parent=self.root)

    def import_json(self):
        if not self.can_edit(): return
        path = filedialog.askopenfilename(filetypes=[("Build Tool JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            imported = build_tool.import_json(path)
            if len(self.builds) + len(imported["builds"]) > 200 or len(self.templates) + len(imported["templates"]) > 100:
                raise ValueError("The local limit is 200 builds and 100 templates.")
            existing_names = {item["name"].casefold() for item in self.builds}
            for item in imported["builds"]:
                if item["name"].casefold() in existing_names:
                    item["name"] = (item["name"][:68] + " (Imported)")[:80]
                existing_names.add(item["name"].casefold())
            self.builds.extend(imported["builds"])
            self.templates.extend(imported["templates"])
            if not self.persist():
                self.refresh()
                return
            self.refresh(len(self.builds) - len(imported["builds"]) if imported["builds"] else None)
            self.status.set(f"Imported {len(imported['builds'])} build(s) and {len(imported['templates'])} template(s).")
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror("Build Tool", f"Import failed; local data was not replaced.\n{exc}", parent=self.root)

    def template_dialog(self):
        win = CtkToplevel(self.root); win.title("Build Tool · Templates"); win.transient(self.root)
        win.geometry("560x420")
        CtkLabel(win, text="Saved locally · templates never replace your builds").pack(anchor="w", padx=10, pady=(10, 4))
        listing = tk.Listbox(win, exportselection=False); listing.pack(fill="both", expand=True, padx=10, pady=5)

        def refresh_list():
            listing.delete(0, "end")
            for item in self.templates:
                listing.insert("end", item["name"])

        def save_template():
            if not self.can_edit(): return
            current = self.current()
            if not current:
                messagebox.showinfo("Build Tool", "Create or select a build first.", parent=win); return
            template = copy.deepcopy(current)
            template["id"] = build_tool.new_build()["id"]
            template["name"] = ("Template · " + current["name"])[:80]
            self.templates.append(template)
            if self.persist():
                refresh_list()
                self.status.set(f"Saved template · {template['name']}")

        def use_template():
            if not listing.curselection(): return
            if not self.can_edit(): return
            template = copy.deepcopy(self.templates[listing.curselection()[0]])
            template["id"] = build_tool.new_build()["id"]
            if template["name"].startswith("Template · "):
                template["name"] = template["name"][11:]
            template["name"] = (template["name"] + " (copy)")[:80]
            self.builds.append(template)
            if self.persist():
                self.refresh(len(self.builds) - 1)
                self.status.set("Template copied to builds; the saved template is unchanged.")

        def delete_template():
            if not listing.curselection() or not self.can_edit(): return
            if not messagebox.askyesno("Build Tool", "Remove this saved template? Its source build is unchanged.", parent=win):
                return
            del self.templates[listing.curselection()[0]]
            if self.persist(): refresh_list()

        refresh_list()
        buttons = CtkFrame(win); buttons.pack(fill="x", padx=10, pady=8)
        CtkButton(buttons, text="Save current as template", command=save_template).pack(side="left")
        CtkButton(buttons, text="Use as new build", command=use_template).pack(side="left", padx=5)
        CtkButton(buttons, text="Remove template", command=delete_template).pack(side="left")
        CtkButton(buttons, text="Close", command=win.destroy).pack(side="right")

    def compare_dialog(self):
        if len(self.builds) < 2:
            messagebox.showinfo("Build Tool", "Save at least two builds to compare them.", parent=self.root)
            return
        win = CtkToplevel(self.root); win.title("Build Tool · Compare builds"); win.transient(self.root)
        win.geometry("760x520")
        names = [item["name"] for item in self.builds]
        row = CtkFrame(win); row.pack(fill="x", padx=10, pady=8)
        CtkLabel(row, text="Build A").pack(side="left")
        first = CtkComboBox(row, state="readonly", values=names, width=28); first.pack(side="left", padx=5)
        CtkLabel(row, text="Build B").pack(side="left", padx=(12, 0))
        second = CtkComboBox(row, state="readonly", values=names, width=28); second.pack(side="left", padx=5)
        first.current(max(0, self.choice.current()))
        second.current(1 if self.choice.current() != 1 else 0)
        columns = ("metric", "first", "second", "delta")
        table = ttk.Treeview(win, columns=columns, show="headings", height=18)
        for key, label in zip(columns, ("Metric", "Build A", "Build B", "B − A")):
            table.heading(key, text=label)
        table.column("metric", width=260); table.pack(fill="both", expand=True, padx=10, pady=4)
        note = tk.StringVar()
        CtkLabel(win, textvariable=note, foreground=self.palette["muted"], wraplength=720).pack(anchor="w", padx=10, pady=5)

        def refresh_comparison():
            if first.current() < 0 or second.current() < 0: return
            for iid in table.get_children(): table.delete(iid)
            data = build_tool.compare_builds(self.builds[first.current()], self.builds[second.current()], self.catalog)
            for key, values in data["stats"].items():
                table.insert("", "end", values=(key.replace("_", " ").title(), f"{values['first']:g}",
                            f"{values['second']:g}", f"{values['delta']:+g}"))
            table.insert("", "end", values=("Total armor (estimate)", f"{data['armor']['first']:,.0f}",
                        f"{data['armor']['second']:,.0f}", f"{data['armor']['delta']:+,.0f}"))
            for weapon in data["weapons"]:
                a, b = weapon["first"], weapon["second"]
                table.insert("", "end", values=(f"{weapon['slot']} DPS (estimate)",
                            f"{a['dps']:,.0f}" if a else "—", f"{b['dps']:,.0f}" if b else "—",
                            f"{weapon['dps_delta']:+,.0f}"))
                table.insert("", "end", values=(f"{weapon['slot']} TTK (estimate)",
                            f"{a['ttk']:.1f}s" if a else "—", f"{b['ttk']:.1f}s" if b else "—",
                            f"{weapon['ttk_delta']:+.1f}s"))
            for change in data["slot_changes"]:
                table.insert("", "end", values=(f"{change['slot']} · item",
                            change["first"] or "—", change["second"] or "—", "changed"))
            for bonus in data["bonus_changes"]["only_first"]:
                table.insert("", "end", values=(f"{bonus[0]} · {bonus[1]} pc bonus",
                            bonus[2], "—", "A only"))
            for bonus in data["bonus_changes"]["only_second"]:
                table.insert("", "end", values=(f"{bonus[0]} · {bonus[1]} pc bonus",
                            "—", bonus[2], "B only"))
            note.set(data["assumptions"] + " A negative TTK difference means the estimate is faster.")

        CtkButton(row, text="Compare", command=refresh_comparison).pack(side="left", padx=8)
        refresh_comparison()

    def patch_notes(self):
        messagebox.showinfo("Build Tool · Notes",
            "Standalone build records · specialization and 11 loadout slots · brand/gearset bonus preview · "
            "weapon DPS/TTK estimates. Estimates use the local game library or values entered in the slot editor.",
            parent=self.root)

    def credits(self):
        messagebox.showinfo("Build Tool · Credits",
            "MX Division Builds Tool (mxswat) is the reference for the layout and game data. "
            "This is an independent implementation with modifications. The referenced material is licensed "
            "under CC BY-NC-SA 4.0; attribution and the same license terms apply to adapted material.\n\n"
            "Source: https://github.com/mxswat/mx-division-builds\n"
            "Full notice: docs/third_party/mx-division-builds-attribution.md", parent=self.root)

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
            self.choice.set(""); self.name.set(""); self._clear_views()
            if callable(self.summary_callback):
                self.summary_callback()
            return
        self.name.set(build["name"]); self.spec.set(build.get("specialization", ""))
        result = build_tool.calculate(build, self.catalog)
        for child in self.grid.winfo_children(): child.destroy()
        self._slot_cards = []
        labels = ("PRIMARY", "SECONDARY", "SIDEARM", "MASK", "BACKPACK", "CHEST", "GLOVES", "HOLSTER", "KNEEPADS", "SKILL 1", "SKILL 2")
        slots = ("Primary", "Secondary", "SideArm") + build_tool.SLOTS[:6] + ("Skill1", "Skill2")
        for idx, (slot, title) in enumerate(zip(slots, labels)):
            item = build["slots"].get(slot) or {}
            card = CtkFrame(self.grid, bg=self.palette["surface"], highlightthickness=1,
                            highlightbackground=self.palette["border"], takefocus=1)
            self._slot_cards.append(card)
            CtkLabel(card, text=title, bg=self.palette["surface"], fg=self.palette["accent"], font=("Consolas", 9, "bold")).pack(anchor="w")
            CtkLabel(card, text=item.get("name") or "CHOOSE ITEM", bg=self.palette["surface"], fg=self.palette["fg"],
                     wraplength=140, justify="center", height=3).pack(fill="both", expand=True)
            for widget in (card, *card.winfo_children()):
                widget.bind("<Button-1>", lambda _e, s=slot: self.edit_slot(s))
            card.bind("<Return>", lambda _e, s=slot: self.edit_slot(s))
            card.bind("<space>", lambda _e, s=slot: self.edit_slot(s))
            card.bind("<FocusIn>", lambda _e, c=card: c.configure(highlightbackground=self.palette["accent"]))
            card.bind("<FocusOut>", lambda _e, c=card: c.configure(highlightbackground=self.palette["border"]))
        self._grid_columns = 0
        self._layout_slot_cards(self.grid.winfo_width())
        self._draw_stats(result)
        self._draw_weapon_stats(build, result)
        self._draw_ttk(result)
        self.refresh_chart()
        if callable(self.summary_callback):
            self.summary_callback()

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
                source = result["gear_attribute_contributions"].get(field)
                contribution = f" · gear attributes +{source:g}" if source is not None else ""
                CtkLabel(group, text=f"{field.replace('_', ' ').title()}: {result['stats'][field]:g}{contribution}").pack(anchor="w", padx=6, pady=1)
        CtkLabel(self.detail, text=f"Total Armor · {result['armor']:,.0f} · estimate", foreground=self.palette["accent"], style="Title.TLabel").pack(anchor="w", padx=6, pady=4)
        CtkLabel(self.detail, text=(f"Armor inputs · base 660,014 + {result['cores']['defensive']} defensive cores × 170,000 "
                  f"+ gear armor attributes {result['gear_attribute_contributions'].get('armor', 0):g}"),
                  wraplength=460, foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        CtkLabel(self.detail, text=("PvE baseline estimate only. PvP balancing/normalization, talents, "
                  "specialization and SHD effects are not included."), wraplength=460,
                  foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        watch = ttk.LabelFrame(self.detail, text="SHD Watch Levels")
        watch.pack(fill="x", padx=4, pady=3)
        levels = self.current().get("shd_levels", {})
        CtkButton(watch, text="Set all to max", command=self.set_all_shd).grid(row=0, column=4, padx=5)
        for i, name in enumerate(self.SHD):
            row = i//2 + 1
            CtkLabel(watch, text=name).grid(row=row, column=(i%2)*2, padx=5, pady=2, sticky="w")
            value = tk.IntVar(value=levels.get(name, 0))
            spin = ttk.Spinbox(watch, from_=0, to=10, width=4, textvariable=value,
                               command=lambda n=name, v=value: self.set_shd(n, v.get()))
            spin.grid(row=row, column=(i%2)*2+1, padx=4)
        CtkLabel(watch, text="Watch levels are stored separately; their derived bonuses are not included in stat estimates.",
                  foreground=self.palette["muted"]).grid(row=4, column=0, columnspan=5, sticky="w", padx=5, pady=3)
        for title, values in (("Gearset Bonus", result["bonuses"]["gear_sets"]), ("Brand Bonus", result["bonuses"]["brands"])):
            panel = ttk.LabelFrame(self.detail, text=title); panel.pack(fill="x", padx=4, pady=3)
            for bonus in values:
                CtkLabel(panel, text=f"{bonus['name']} · {bonus['tier']} pc · {bonus['text']}", wraplength=460).pack(anchor="w", padx=6, pady=1)
            if not values: CtkLabel(panel, text="No active bonus", foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        fixed_frame = ttk.LabelFrame(self.detail, text="Selected item · catalog fixed details")
        fixed_frame.pack(fill="x", padx=4, pady=3)
        any_details = False
        for slot, item in self.current()["slots"].items():
            if not item:
                continue
            current = build_tool.auto_details(item.get("name"), slot, self.catalog)
            lines = []
            talent = item.get("talent") or current.get("talent")
            if talent:
                lines.append(f"Talent: {talent}")
            fixed_attributes = {(attr.get("slot", ""), attr.get("name", "")): attr
                     for attr in item.get("fixed_attributes", [])
                     if not str(attr.get("slot", "")).startswith("core_")}
            fixed_attributes.update({(attr.get("slot", ""), attr.get("name", "")): attr
                          for attr in current.get("fixed_attributes", [])})
            for attr in fixed_attributes.values():
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
                CtkLabel(fixed_frame, text=f"{slot} · {item['name']}\n" + "\n".join(lines),
                          wraplength=460, justify="left").pack(anchor="w", padx=6, pady=3)
        if not any_details:
            CtkLabel(fixed_frame, text="No catalogued fixed details for selected items.",
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        self._draw_insights()

    def _draw_insights(self):
        build = self.current()
        if not build:
            return
        catalog = build_tool.catalog_diagnostics(self.catalog)
        origin = catalog["provenance"]
        basis = ttk.LabelFrame(self.detail, text="Library source and version")
        basis.pack(fill="x", padx=4, pady=3)
        counts = catalog["counts"]
        CtkLabel(basis, text=(f"Coverage: {counts['gear_items']} gear items · {counts['weapons']} weapons · "
                  f"{counts['brands']} brands · {counts['gear_sets']} sets · {counts['attributes']} attributes\n"
                  f"Library {origin['version']} · {origin['community_name']} · "
                  f"commit date {origin['community_date']}\n"
                  f"Community repository: {origin['community_repository']} · license {origin['community_license']}\n"
                  f"Declared source: {origin['source']}\n"
                  f"Source verification: {catalog['verification_status']}\n"
                  f"Catalog fingerprint: {origin['fingerprint']} · this records identity, not correctness"),
                  wraplength=460, justify="left").pack(anchor="w", padx=6, pady=4)
        snapshot = build.get("catalog_snapshot") or {}
        if snapshot and snapshot.get("fingerprint") != origin["fingerprint"]:
            CtkLabel(basis, text=f"This build was saved with catalog {snapshot.get('version', 'unknown')} · basis differs",
                      foreground=self.palette["accent"], wraplength=460).pack(anchor="w", padx=6, pady=(0, 4))
        if catalog["warnings"]:
            CtkLabel(basis, text="Metadata gaps: " + "; ".join(catalog["warnings"]),
                      foreground=self.palette["muted"], wraplength=460).pack(anchor="w", padx=6, pady=(0, 4))

        issues = build_tool.validate_build(build, self.catalog)
        warnings = [issue for issue in issues if issue["level"] == "warning"]
        empty = sum(1 for issue in issues if issue["level"] == "info" and issue["message"] == "Slot is empty")
        validation = ttk.LabelFrame(self.detail, text="Build check · advisory")
        validation.pack(fill="x", padx=4, pady=3)
        headline = f"{len(warnings)} warning(s) · {empty} empty slot(s)"
        CtkLabel(validation, text=headline,
                  foreground=self.palette["accent"] if warnings else self.palette["fg"]).pack(anchor="w", padx=6, pady=3)
        for issue in warnings[:4]:
            CtkLabel(validation, text=f"{issue['slot']}: {issue['message']}", wraplength=460,
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=1)
        if len(warnings) > 4:
            CtkLabel(validation, text=f"and {len(warnings) - 4} more warning(s)",
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=1)
        if not warnings:
            CtkLabel(validation, text="No catalog or roll-limit warnings. This does not certify in-game performance.",
                      wraplength=460, foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=1)
        if catalog["warnings"]:
            CtkLabel(validation, text="Catalog review: " + "; ".join(catalog["warnings"]),
                      wraplength=460, foreground=self.palette["accent"]).pack(anchor="w", padx=6, pady=2)

        roll_frame = ttk.LabelFrame(self.detail, text="Variable roll quality · catalog based")
        roll_frame.pack(fill="x", padx=4, pady=3)
        rows = build_tool.roll_quality(build, self.catalog)
        for row in rows[:8]:
            basis_text = "range" if row["range_verified"] else "max-relative; minimum not supplied"
            CtkLabel(roll_frame, text=(f"{row['slot']} · {row['attribute'].replace('_', ' ').title()}: "
                      f"{row['value']:g}/{row['maximum']:g} ({row['percent']:.0f}%, {basis_text})"),
                      wraplength=460).pack(anchor="w", padx=6, pady=1)
        if not rows:
            CtkLabel(roll_frame, text="Enter a variable roll; fixed catalog stats are excluded.",
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        if len(rows) > 8:
            CtkLabel(roll_frame, text=f"Showing 8 of {len(rows)} roll(s).",
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=1)

        farm = ttk.LabelFrame(self.detail, text="Owned gear match · read only")
        farm.pack(fill="x", padx=4, pady=3)
        CtkButton(farm, text="Refresh stash matches", command=self.refresh_stash_matches).pack(anchor="w", padx=6, pady=3)
        if not callable(self.stash_provider):
            CtkLabel(farm, text="Stash connection is unavailable in this context.",
                      foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=2)
        else:
            if self._stash_matches is None:
                self.refresh_stash_matches(redraw=False)
            matches = self._stash_matches or []
            owned_count = sum(bool(row["owned"]) for row in matches)
            if not matches:
                CtkLabel(farm, text="Select gear items to compare them with the local stash.",
                          foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=1)
            else:
                CtkLabel(farm, text=f"{owned_count}/{len(matches)} selected gear target(s) have a matching owned item.",
                          foreground=self.palette["fg"]).pack(anchor="w", padx=6, pady=1)
                if callable(self.target_loot_provider):
                    try:
                        rows = self.target_loot_provider()
                        self._farm_routes = build_tool.farm_routes(matches, rows)
                    except (OSError, ValueError, TypeError) as exc:
                        self._farm_routes = {}
                        self.status.set(f"Target-loot data unavailable · {exc}")
            for row in matches[:6]:
                if row["owned"]:
                    label = ", ".join(f"{item['name']} ({item['match']})" for item in row["candidates"][:2])
                else:
                    routes = self._farm_routes.get(row["slot"], [])
                    if routes:
                        route = routes[0]
                        locations = ", ".join(route["targets"])
                        missions = ", ".join(route["missions"][:3])
                        label = (f"Missing · {row['target']} · {locations} · {route['event']} · "
                                 f"{missions or 'open-world drop'} · {route['day']} · not guaranteed")
                    else:
                        label = f"Missing · {row['target']} · no current verified target-loot route"
                CtkLabel(farm, text=f"{row['slot']}: {label}", wraplength=460,
                          foreground=self.palette["muted"] if row["owned"] else self.palette["accent"]).pack(anchor="w", padx=6, pady=1)
            if matches and not callable(self.target_loot_provider):
                CtkLabel(farm, text="Current target-loot feed is unavailable in this context.",
                          foreground=self.palette["muted"]).pack(anchor="w", padx=6, pady=1)

    def refresh_stash_matches(self, redraw=True):
        if not callable(self.stash_provider):
            self._stash_matches = []
            return
        try:
            self._stash_matches = build_tool.stash_matches(self.current(), self.stash_provider(), self.catalog)
        except (OSError, ValueError, TypeError) as exc:
            self._stash_matches = []
            self.status.set(f"Stash read failed · {exc}")
        if redraw and self.current():
            self.refresh(self.choice.current())

    def set_shd(self, name, value):
        if not self.can_edit(): return
        build = self.current()
        if build:
            try: build.setdefault("shd_levels", {})[name] = max(0, min(10, int(value)))
            except (ValueError, TypeError): return
            build_tool.stamp_catalog(build, self.catalog)
            if not self.persist(): self.refresh(self.choice.current())

    def set_all_shd(self):
        if not self.can_edit(): return
        build = self.current()
        if build:
            build["shd_levels"] = {name: 10 for name in self.SHD}
            build_tool.stamp_catalog(build, self.catalog)
            self.persist(); self.refresh(self.choice.current())

    def _draw_weapon_stats(self, build, result):
        for child in self.weapons_box.winfo_children(): child.destroy()
        by_slot = {row["slot"]: row for row in result["weapons"]}
        for slot in ("Primary", "Secondary", "SideArm"):
            item = build["slots"].get(slot) or {}; calc = by_slot.get(slot, {})
            text = (f"{slot}\n{item.get('name') or 'No weapon selected'}\n"
                    f"Damage {calc.get('damage', 0):g} · RPM {calc.get('rpm', 0):g} · Mag {calc.get('magazine', 0):g} · Reload {calc.get('reload', 0):g}s")
            CtkLabel(self.weapons_box, text=text, bg=self.palette["surface"], fg=self.palette["fg"], justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=5)

    def _draw_ttk(self, result):
        for child in self.ttk_box.winfo_children(): child.destroy()
        self.enemy_hp.set(str(int(result["enemy_hp"])))
        CtkLabel(self.ttk_box, text="Target HP").grid(row=0, column=0, padx=6, pady=4)
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
            CtkLabel(self.ttk_box, text="Select a weapon or enter base damage and RPM in its slot editor.",
                      foreground=self.palette["muted"]).grid(row=2, column=0, columnspan=7, sticky="w", padx=6)
        CtkLabel(self.ttk_box, text="PvE baseline estimate only: DPS/TTK uses weapon base damage, RPM, offensive cores, entered damage/critical attributes and parsed attachment stats. PvP balancing/normalization, talents, specialization and SHD effects are excluded.",
                  wraplength=900, foreground=self.palette["muted"]).grid(row=3, column=0, columnspan=7, sticky="w", padx=6, pady=2)

    def update_enemy_hp(self):
        if not self.can_edit(): return
        build = self.current()
        if not build: return
        try:
            build["enemy_hp"] = max(1, min(100_000_000, int(float(self.enemy_hp.get().replace(",", ".")))))
        except (ValueError, TypeError):
            self.enemy_hp.set(str(int(build["enemy_hp"])))
            return
        build_tool.stamp_catalog(build, self.catalog)
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
