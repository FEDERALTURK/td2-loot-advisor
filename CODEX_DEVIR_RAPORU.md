# CODEX DEVİR RAPORU
Tarih: 8 Kasım 2026, Europe/Istanbul; kaynak çalışma alanı C:/Users/PC/Desktop/Thedivision2program/; belge oluşturulmadan önce HEAD 04148ca idi. [Doğrulandı]

Bu raporun doğrudan Git kanıtı sınırı c2d14f6^..04148ca aralığıdır; önceki uzun sohbet talepleri geçmiş bağlamdır, her birinin bu ajan tarafından uygulandığı doğrulanamaz. [Doğrulandı]
c2d14f6 büyük bir toplu commit olup önceden hazırlanmış işleri de içerir; diff'in varlığı her satırın bu oturumda sıfırdan yazıldığını kanıtlamaz. [Doğrulandı]
Aşağıdaki kod/komut blokları birebir kanıttır; blok açıklamalarının etiketleri blokların tamamını kapsar. [Doğrulandı]

## 1. ÇALIŞMA ORTAMI VE KISITLAR
Windows dosya sistemi ve PowerShell üzerinden yerel Git, dosya okuma/yazma, ağ üzerinden GitHub REST ve bağlı GitHub araçları kullanıldı. [Doğrulandı]
Flutter PATH'te bulunamadığında önce SDK yok sanıldı; daha sonra C:/Users/PC/tools/flutter/bin/flutter.bat üzerinden gerçek analiz ve test çalıştırıldı; önceki “yerelde Flutter yok” açıklaması eksikti. [Doğrulandı]
Android SDK yolu C:/Users/PC/tools/android-sdk, ADB yolu platform-tools/adb.exe idi; adb devices çıktısı boştu. [Doğrulandı]
Gerçek telefon kurulum, izin ekranı, APK imzası karşılaştırması ve Android 16 uçtan uca güncelleme denenmedi. [Test edilmedi]
Bu mobil yayın çalışmasında gerçek Windows oyun/Tk ekranı, GPU performansı, HDR ve overlay görsel testi yapılmadı; araç erişimi olması bu testlerin yapıldığı anlamına gelmez. [Test edilmedi]
Ruflo araçları bu devir turunda mevcut araç adlarında arandı ve bulunamadı; swarm çalıştırıldığı iddia edilmemelidir. [Doğrulandı]

## 2. BU OTURUMDA TAM OLARAK NE İSTENDİ
Aşağıdaki sıra görünür konuşmanın bu değişiklik aralığıyla ilgili kullanıcı talepleridir; çok eski taleplerin tamamının bu commit'lerde karşılandığı söylenemez. [Doğrulandı]
1. “faz 2 geçelim”, “devam et”, “faz 3 başlayalım”, “https://github.com/ruvnet/ruflo bu repoyu yükle ve çalıştır projede agentlar çalışsın”, “faz 4 geçelim”, “faz 5 var mı?=”, “tamma iki tarafı da yapalım mobil ve pc”. [Doğrulandı]
2. “Bunların hepsini yap yanlış anlaşıldım.” ve ardından “evet” ile push/tag/release/APK/installer isteği netleştirildi. [Doğrulandı]
3. “apk uygulamasında yeni gelen güncellemeleri kendi tarayıp otomatik güncelleyecek bir yapıda yapabilir miyiz?” [Doğrulandı]
4. “benim istediğim kullanıcı güncelleme bildirimi gitsin ve kullanıcı güncelle dediğinde kendisi otomatik güncellemeyi indirsin ve yüklesin”. [Doğrulandı]
5. “uygulama yeni güncelleme yüklesemde kendini beta 0.1.5 olarak görüyor bu sorunu düzelt ve istediğim güncelleme yönetimini uygula”. [Doğrulandı]
6. “evet” ile companion-v0.1.7 yayını onaylandı. [Doğrulandı]
7. “uygulama halen daha beta 0.1.5 beta olarak görüyor ve otomatik güncelleme çalışmıyor”. [Doğrulandı]
8. “sorunu düzeltirse güncelleme yayınla”. [Doğrulandı]
9. “Kontrol etmeye gerek yok sen son güncelleme yayınla” ile cihaz doğrulamasını beklemeden yayın açıkça istendi. [Doğrulandı]
10. Son talep, bu belgeyi tüm kanıt ve eksiklerle hazırlamak, yalnız raporu commit etmek ve push etmemektir. [Doğrulandı]

## 3. DEĞİŞEN/OLUŞTURULAN HER DOSYA
Aşağıdaki her kayıt tam yol, Git değişiklik türü, ilgili talep grubu, son commit geçmişi ve c2d14f6^..04148ca tam net diff'ini içerir; ara commit'ler için git show 06f992c, 961640c, d9a6179 ve 04148ca kullanılabilir. [Doğrulandı]
Kullanıcı runtime dosyası builds.json bu aralık değişiklik envanterine dahil değildir; çalışma ağacındaki değişikliği commit edilmedi. [Doğrulandı]

### C:/Users/PC/Desktop/Thedivision2program/.agents/README.md
Tür: Yeni; talep ilişkisi: Ruflo/ajan entegrasyonu talebi. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.agents/README.md b/.agents/README.md
new file mode 100644
index 0000000..aa4406b
--- /dev/null
+++ b/.agents/README.md
@@ -0,0 +1,38 @@
+# .agents Directory
+
+This directory contains agent configuration and skills for OpenAI Codex CLI.
+
+## Structure
+
+```
+.agents/
+  config.toml     # Main configuration file
+  skills/         # Skill definitions
+    skill-name/
+      SKILL.md    # Skill instructions
+      scripts/    # Optional scripts
+      docs/       # Optional documentation
+  README.md       # This file
+```
+
+## Configuration
+
+The `config.toml` file controls:
+- Model selection
+- Approval policies
+- Sandbox modes
+- MCP server connections
+- Skills configuration
+
+## Skills
+
+Skills are invoked using `$skill-name` syntax. Each skill has:
+- YAML frontmatter with metadata
+- Trigger and skip conditions
+- Commands and examples
+
+## Documentation
+
+- Main instructions: `AGENTS.md` (project root)
+- Local overrides: `.codex/AGENTS.override.md` (gitignored)
+- Ruflo: https://github.com/ruvnet/ruflo
```

### C:/Users/PC/Desktop/Thedivision2program/.agents/config.toml
Tür: Yeni; talep ilişkisi: Ruflo/ajan entegrasyonu talebi. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.agents/config.toml b/.agents/config.toml
new file mode 100644
index 0000000..1976f49
--- /dev/null
+++ b/.agents/config.toml
@@ -0,0 +1,308 @@
+# =============================================================================
+# Claude Flow V3 - Codex Configuration
+# =============================================================================
+# Generated by: @claude-flow/codex
+# Documentation: https://github.com/ruvnet/ruflo
+#
+# This file configures the Codex CLI for Claude Flow integration.
+# Place in .agents/config.toml (project) or .codex/config.toml (user).
+# =============================================================================
+
+# =============================================================================
+# Core Settings
+# =============================================================================
+
+# Model selection - the AI model to use for code generation
+# Options: gpt-5.3-codex, gpt-4o, claude-sonnet, claude-opus
+model = "gpt-5.3-codex"
+
+# Approval policy determines when human approval is required
+# - untrusted: Always require approval
+# - on-failure: Require approval only after failures
+# - on-request: Require approval for significant changes
+# - never: Auto-approve all actions (use with caution)
+approval_policy = "on-request"
+
+# Sandbox mode controls file system access
+# - read-only: Can only read files, no modifications
+# - workspace-write: Can write within workspace directory
+# - danger-full-access: Full file system access (dangerous)
+sandbox_mode = "workspace-write"
+
+# Web search enables internet access for research
+# - disabled: No web access
+# - cached: Use cached results when available
+# - live: Always fetch fresh results
+web_search = "cached"
+
+# =============================================================================
+# Project Documentation
+# =============================================================================
+
+# Maximum bytes to read from AGENTS.md files
+project_doc_max_bytes = 65536
+
+# Fallback filenames if AGENTS.md not found
+project_doc_fallback_filenames = [
+  "AGENTS.md",
+  "TEAM_GUIDE.md",
+  ".agents.md"
+]
+
+# =============================================================================
+# Ruflo Agentic Policy Engine (ADR-324)
+# =============================================================================
+
+[policy]
+# legacy preserves existing installs; observe records would-deny decisions; enforce blocks
+mode = "legacy"
+
+[swarm.automation]
+# Unattended fanout is opt-in. Interactive Codex may still delegate explicitly.
+enabled = false
+max_concurrent = 4
+max_writers = 2
+worktree_isolation = true
+dependency_failure = "cancel"
+agent_timeout_seconds = 1800
+max_output_bytes = 1048576
+
+# =============================================================================
+# Features
+# =============================================================================
+
+[features]
+# Enable child AGENTS.md guidance
+child_agents_md = true
+
+# Cache shell environment for faster repeated commands
+shell_snapshot = true
+
+# Smart approvals based on request context
+request_rule = true
+
+# Enable remote compaction for large histories
+remote_compaction = true
+
+# =============================================================================
+# MCP Servers
+# =============================================================================
+
+[mcp_servers.ruflo]
+command = "cmd"
+args = ["/c", "npx", "-y", "ruflo@latest", "mcp", "start"]
+enabled = true
+tool_timeout_sec = 120
+
+# =============================================================================
+# Skills Configuration
+# =============================================================================
+
+[[skills.config]]
+path = ".agents/skills/swarm-orchestration"
+enabled = true
+
+[[skills.config]]
+path = ".agents/skills/memory-management"
+enabled = true
+
+# =============================================================================
+# Profiles
+# =============================================================================
+
+# Development profile - more permissive for local work
+[profiles.dev]
+approval_policy = "on-request"
+sandbox_mode = "workspace-write"
+web_search = "live"
+
+# Safe profile - maximum restrictions
+[profiles.safe]
+approval_policy = "untrusted"
+sandbox_mode = "read-only"
+web_search = "disabled"
+
+# CI profile - for automated pipelines
+[profiles.ci]
+approval_policy = "never"
+sandbox_mode = "workspace-write"
+web_search = "cached"
+
+# =============================================================================
+# History
+# =============================================================================
+
+[history]
+# Save all session transcripts
+persistence = "save-all"
+
+# =============================================================================
+# Shell Environment
+# =============================================================================
+
+[shell_environment_policy]
+# Inherit environment variables
+inherit = "core"
+
+# Exclude sensitive variables
+exclude = ["*_KEY", "*_SECRET", "*_TOKEN", "*_PASSWORD"]
+
+# =============================================================================
+# Sandbox Workspace Write Settings
+# =============================================================================
+
+[sandbox_workspace_write]
+# Additional writable paths beyond workspace
+writable_roots = []
+
+# Allow network access
+network_access = true
+
+# Exclude temp directories
+exclude_slash_tmp = false
+
+# =============================================================================
+# Security Settings
+# =============================================================================
+
+[security]
+# Enable input validation for all user inputs
+input_validation = true
+
+# Prevent directory traversal attacks
+path_traversal_prevention = true
+
+# Scan for hardcoded secrets
+secret_scanning = true
+
+# Scan dependencies for known CVEs
+cve_scanning = true
+
+# Maximum file size for operations (bytes)
+max_file_size = 10485760
+
+# Allowed file extensions (empty = allow all)
+allowed_extensions = []
+
+# Blocked file patterns (regex)
+blocked_patterns = ["\\.env$", "credentials\\.json$", "\\.pem$", "\\.key$"]
+
+# =============================================================================
+# Performance Settings
+# =============================================================================
+
+[performance]
+# Maximum concurrent agents
+max_agents = 8
+
+# Task timeout in seconds
+task_timeout = 300
+
+# Memory limit per agent
+memory_limit = "512MB"
+
+# Enable response caching
+cache_enabled = true
+
+# Cache TTL in seconds
+cache_ttl = 3600
+
+# Enable parallel task execution
+parallel_execution = true
+
+# =============================================================================
+# Logging Settings
+# =============================================================================
+
+[logging]
+# Log level: debug, info, warn, error
+level = "info"
+
+# Log format: json, text, pretty
+format = "pretty"
+
+# Log destination: stdout, file, both
+destination = "stdout"
+
+# =============================================================================
+# Neural Intelligence Settings
+# =============================================================================
+
+[neural]
+# Enable SONA (Self-Optimizing Neural Architecture)
+sona_enabled = true
+
+# Enable HNSW vector search
+hnsw_enabled = true
+
+# HNSW index parameters
+hnsw_m = 16
+hnsw_ef_construction = 200
+hnsw_ef_search = 100
+
+# Enable pattern learning
+pattern_learning = true
+
+# Learning rate for neural adaptation
+learning_rate = 0.01
+
+# =============================================================================
+# Swarm Orchestration Settings
+# =============================================================================
+
+[swarm]
+# Default topology: hierarchical, mesh, ring, star
+default_topology = "hierarchical"
+
+# Default strategy: balanced, specialized, adaptive
+default_strategy = "specialized"
+
+# Consensus algorithm: raft, byzantine, gossip
+consensus = "raft"
+
+# Enable anti-drift measures
+anti_drift = true
+
+# Checkpoint interval (tasks)
+checkpoint_interval = 10
+
+# =============================================================================
+# Hooks Configuration
+# =============================================================================
+
+[hooks]
+# Enable lifecycle hooks
+enabled = true
+
+# Pre-task hook
+pre_task = true
+
+# Post-task hook (for learning)
+post_task = true
+
+# Enable neural training on post-edit
+train_on_edit = true
+
+# =============================================================================
+# Background Workers
+# =============================================================================
+
+[workers]
+# Enable background workers
+enabled = true
+
+# Worker configuration
+[workers.audit]
+enabled = true
+priority = "critical"
+interval = 300
+
+[workers.optimize]
+enabled = true
+priority = "high"
+interval = 600
+
+[workers.consolidate]
+enabled = true
+priority = "low"
+interval = 1800
```

### C:/Users/PC/Desktop/Thedivision2program/.agents/skills/memory-management/SKILL.md
Tür: Yeni; talep ilişkisi: Ruflo/ajan entegrasyonu talebi. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.agents/skills/memory-management/SKILL.md b/.agents/skills/memory-management/SKILL.md
new file mode 100644
index 0000000..0a2e0a0
--- /dev/null
+++ b/.agents/skills/memory-management/SKILL.md
@@ -0,0 +1,45 @@
+---
+name: memory-management
+description: >
+  AgentDB memory system with HNSW vector search.
+  Use when: need to store patterns, search for solutions, semantic lookup.
+  Skip when: no learning needed, ephemeral tasks.
+---
+
+# Memory Management Skill
+
+## Purpose
+AgentDB memory system with HNSW vector search.
+
+## When to Trigger
+- need to store patterns
+- search for solutions
+- semantic lookup
+
+## When to Skip
+- no learning needed
+- ephemeral tasks
+
+## Commands
+
+### Store Data
+Store a pattern in memory
+
+```bash
+npx @claude-flow/cli memory store --key "key" --value "value" --namespace patterns
+```
+
+### Search Data
+Semantic search in memory
+
+```bash
+npx @claude-flow/cli memory search --query "search terms" --limit 10
+```
+
+
+
+## Best Practices
+1. Check memory for existing patterns before starting
+2. Use hierarchical topology for coordination
+3. Store successful patterns after completion
+4. Document any new learnings
```

### C:/Users/PC/Desktop/Thedivision2program/.agents/skills/swarm-orchestration/SKILL.md
Tür: Yeni; talep ilişkisi: Ruflo/ajan entegrasyonu talebi. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.agents/skills/swarm-orchestration/SKILL.md b/.agents/skills/swarm-orchestration/SKILL.md
new file mode 100644
index 0000000..6023703
--- /dev/null
+++ b/.agents/skills/swarm-orchestration/SKILL.md
@@ -0,0 +1,53 @@
+---
+name: swarm-orchestration
+description: >
+  Multi-agent swarm coordination for complex tasks.
+  Use when: 3+ files need changes, new features, refactoring.
+  Skip when: single file edits, simple fixes, documentation.
+---
+
+# Swarm Orchestration Skill
+
+## Purpose
+Multi-agent swarm coordination for complex tasks.
+
+## When to Trigger
+- 3+ files need changes
+- new features
+- refactoring
+
+## When to Skip
+- single file edits
+- simple fixes
+- documentation
+
+## Commands
+
+### Initialize Swarm
+Start a new swarm with hierarchical topology
+
+```bash
+npx @claude-flow/cli swarm init --topology hierarchical --max-agents 8
+```
+
+### Route Task
+Route a task to the appropriate agents
+
+```bash
+npx @claude-flow/cli hooks route --task "[task description]"
+```
+
+### Monitor Status
+Check the current swarm status
+
+```bash
+npx @claude-flow/cli swarm status
+```
+
+
+
+## Best Practices
+1. Check memory for existing patterns before starting
+2. Use hierarchical topology for coordination
+3. Store successful patterns after completion
+4. Document any new learnings
```

### C:/Users/PC/Desktop/Thedivision2program/.github/release_notes.md
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
1c32976 FEDERALTURK feat(mobile): harden pairing and prepare device release
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.github/release_notes.md b/.github/release_notes.md
index 764c219..4267d94 100644
--- a/.github/release_notes.md
+++ b/.github/release_notes.md
@@ -1,5 +1,13 @@
 ## TD2 Loot Advisor — Windows
 
+**9.1.5.34 — Faz 5 karar merkezi ve güncelleme denetimi**
+
+- Komuta Merkezi'ne kişisel hedeflerle son taranan eşyayı güvenli biçimde karşılaştıran karar merkezi eklendi.
+- Exotic, Named, Prototype ve kilitli eşyalar tam eşleşse bile REVIEW korumasında kalır; otomatik söküm kararı üretilmez.
+- Mobil Companion güncelleme denetimi kalıcı zaman damgasıyla altı saatte bir sınırlandırıldı.
+- Faz 4 hedef/farm planı ve Faz 5 karar merkezi testleri eklendi.
+
+
 **9.1.5.33 — Companion güvenlik ve cihaz yayını hazırlığı**
 
 - Mobil Companion bulut oturumu ve cihaz kimliği artık düz uygulama tercihleri yerine Android Keystore / iOS Keychain temelli güvenli depoda tutulur. Önceki beta kurulumlarının kayıtları güvenli biçimde taşınır; taşıma tamamlanmadan eski kayıt silinmez.
```

### C:/Users/PC/Desktop/Thedivision2program/.github/workflows/build-mobile.yml
Tür: Yeni; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
06f992c FEDERALTURK fix: download and install companion updates safely
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.github/workflows/build-mobile.yml b/.github/workflows/build-mobile.yml
new file mode 100644
index 0000000..7939a00
--- /dev/null
+++ b/.github/workflows/build-mobile.yml
@@ -0,0 +1,48 @@
+name: Build Companion APK
+
+on:
+  workflow_dispatch:
+  push:
+    tags: ["companion-v*"]
+
+permissions:
+  contents: write
+
+jobs:
+  build:
+    runs-on: ubuntu-latest
+    defaults:
+      run:
+        working-directory: mobile
+    steps:
+      - uses: actions/checkout@v5
+      - uses: subosito/flutter-action@v2
+        with:
+          flutter-version: "3.47.8"
+          channel: stable
+          cache: true
+      - run: flutter pub get
+      - run: flutter analyze
+      - run: flutter test
+      - run: flutter build apk --release
+      - name: Rename APK
+        shell: bash
+        run: |
+          cp build/app/outputs/flutter-apk/app-release.apk "TD2LootAdvisor_Companion_${GITHUB_REF_NAME#companion-v}.apk"
+          sha256sum "TD2LootAdvisor_Companion_${GITHUB_REF_NAME#companion-v}.apk" > SHA256SUMS.sha256
+      - uses: actions/upload-artifact@v5
+        with:
+          name: TD2LootAdvisor-companion-apk
+          path: |
+            mobile/TD2LootAdvisor_Companion_*.apk
+            mobile/SHA256SUMS.sha256
+      - name: Publish companion release
+        if: startsWith(github.ref, 'refs/tags/companion-v')
+        uses: softprops/action-gh-release@v2
+        with:
+          tag_name: ${{ github.ref_name }}
+          name: TD2 Loot Advisor Companion ${{ github.ref_name }}
+          prerelease: true
+          files: |
+            mobile/TD2LootAdvisor_Companion_*.apk
+            mobile/SHA256SUMS.sha256
```

### C:/Users/PC/Desktop/Thedivision2program/.gitignore
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
e0da9c2 FEDERALTURK Release 6.0.2: stabilize OCR decisions, translation and background workloads
c0d900a Claude Canlı çeviri: açıklama çevirileri (TR tohum), canlı haber akışı, testler
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/.gitignore b/.gitignore
index 70eae96..6d571b7 100644
--- a/.gitignore
+++ b/.gitignore
@@ -26,6 +26,7 @@ private/
 tests/.stash_test.json
 vendor_cache.json
 stash.json
+targets.json
 drop_queue.json
 verdict_feedback.json
 verdict_feedback.json.tmp
@@ -57,3 +58,23 @@ translate_cache.json
 descriptions_cache.json
 models/
 cache/
+
+# Yerel oturum, ekran durumu ve kullanıcı yedekleri
+# Bunlar bilgisayara/kullanıcıya özgüdür; kaynak veya sürüm verisi değildir.
+sessions.json
+screen_states.json
+tasks_sent.json
+*.bak
+
+# Geçici test çıktıları
+tests/.fake_sub.png
+tests/.fake_sub_game.py
+tests/.translate_result.json
+
+# Ruflo / Codex kullanıcı ve çalışma zamanı verileri
+.codex/
+.claude-flow/data/
+.claude-flow/logs/
+.claude-flow/policy/
+.claude-flow/swarm/
+.swarm/
```

### C:/Users/PC/Desktop/Thedivision2program/app.py
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
1c32976 FEDERALTURK feat(mobile): harden pairing and prepare device release
b1f3866 FEDERALTURK fix: make HDR sync warnings evidence-based
db6b1dc Claude Üst yatay menü, dijital kod yağmuru, 3B radar + rastgele tespit noktaları (v9.1.5.31)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/app.py b/app.py
index d297d3f..4235074 100644
--- a/app.py
+++ b/app.py
@@ -20,7 +20,7 @@ from collections import Counter
 from datetime import datetime, timedelta, timezone
 from difflib import SequenceMatcher, get_close_matches
 from pathlib import Path
-from tkinter import ttk, filedialog, messagebox
+from tkinter import ttk, filedialog, messagebox, simpledialog
 from td2app.ui import splash, ui_theme, ui_hud, ui_art, view3d, fx, bgvideo
 
 if "--dml-probe" in sys.argv:          # ekran kartı (DirectML) denemesi: ayrı süreçte, programın geri kalanı yüklenmeden
@@ -107,6 +107,8 @@ import gamedata
 import engine
 import display
 import ocr_backend
+import ocr_lab
+import review_queue
 import features
 import stash
 import intelligence
@@ -141,11 +143,14 @@ import itempolicy
 import performance
 import workqueue
 import game_assistant
+import game_runtime
 import diagnostics_center
+import target_planner
+import decision_center
 from i18n import t
 
 APP_NAME = "TD2 Loot Advisor"
-APP_VERSION = "9.1.5.33"
+APP_VERSION = "9.1.5.34"
 # "Bu oturumda ne kazandın?" özeti için kaba tahmin: bir eşyayı elle inceleyip
 # build'e göre karar vermenin (istatistikleri okuma + karşılaştırma) ortalama
 # süresi, saniye. Gerçek bir ölçüm değil — yalnızca arayüzde "tahmini" etiketiyle
@@ -165,6 +170,7 @@ BUNDLE = Path(getattr(sys, "_MEIPASS", BASE))
 ART_DIR = (BASE / "art") if (BASE / "art").exists() else (BUNDLE / "art")
 CFG_PATH, LOG_PATH, DEBUG_PATH, PROG_PATH = (BASE / n for n in ("builds.json", "loot_log.csv", "last_crop.png", "progress.json"))
 STASH_PATH = BASE / "stash.json"
+TARGETS_PATH = BASE / "targets.json"
 VENDOR_CACHE = BASE / "vendor_cache.json"
 DROPQ_PATH = BASE / "drop_queue.json"
 ACCOUNT_PATH = BASE / "account.dat"
@@ -190,6 +196,7 @@ def _test_browser(url):
 REPORTS_DIR = BASE / "reports"
 ISSUES_URL = "https://github.com/FEDERALTURK/td2-loot-advisor/issues/new"
 APPLOG_DIR = BASE / "logs"
+OCR_REVIEW_PATH = APPLOG_DIR / "ocr_review_queue.jsonl"
 APPLOG_PATH = APPLOG_DIR / "app.log"
 LOG_HEADER = ["time", "item", "verdict", "best_build", "score", "slot", "rarity"]
 ALL_SLOTS = ["Mask", "Backpack", "Chest", "Gloves", "Holster", "Kneepads", "Weapon", "Sidearm"]
@@ -1649,6 +1656,7 @@ class App:
             except Exception: continue
 
         self._perf_policy = performance.get_policy(stg)
+        self._runtime_plan = game_runtime.plan(stg)
         self.root._td2_suspend_animations = False
         self.root._td2_animation_multiplier = 1.0
         self.root.title(f"{APP_NAME} v{APP_VERSION}")
@@ -1775,7 +1783,9 @@ class App:
         if getattr(self, "_closing", False): return
         try:
             hidden = self.root.state() != "normal"
-            foreground = bool(getattr(self, "game_on", False) and game_active())
+            focused = game_active()
+            self._runtime_plan = game_runtime.plan(self.cfg["settings"], game_focused=focused, app_hidden=hidden)
+            foreground = bool(getattr(self, "game_on", False) and focused)
             self._perf_policy = performance.get_policy(self.cfg["settings"], foreground, hidden)
             self.root._td2_suspend_animations = self._perf_policy.suspend_animations
             self.root._td2_animation_multiplier = self._perf_policy.ui_animation_multiplier
@@ -2241,13 +2251,15 @@ class App:
         revision = getattr(self, "_lt_revision", 0)
         try:
             while not stop.is_set():
+                runtime = game_runtime.plan(self.cfg["settings"])
                 try:
                     if revision != getattr(self, "_lt_revision", 0):
                         prev = last = None; stable = 0
                         revision = getattr(self, "_lt_revision", 0)
                     area = self.lt_area()
                     st = self.cfg["settings"]
-                    if area and not (st.get("only_game_active", True) and not game_active()):
+                    runtime = game_runtime.plan(st, game_focused=game_active())
+                    if area and runtime.passive_translation:
                         h = g.thumb(area)
                         stable = stable + 1 if prev is not None and dist(h, prev) < AUTO_STABLE else 0
                         prev = h
@@ -2260,7 +2272,7 @@ class App:
                             self._queue_translation(area, revision=revision)
                 except Exception as e:
                     log.debug("live translate loop: %s", e)
-                stop.wait(self._policy().translation_poll_s)
+                stop.wait(max(self._policy().translation_poll_s, runtime.wait_s))
         finally:
             g.release()
 
@@ -2402,7 +2414,11 @@ class App:
         size = int(st.get("tr_font", 15)); mode = force_mode or st.get("tr_mode", "subtitle")
         log.info("Translation overlay: mode=%s pairs=%d area=%sx%s", mode, len(pairs), area.get("width"), area.get("height"))
         if mode == "inplace":
-            return self._lt_show_inplace(pairs, area)
+            try:
+                return self._lt_show_inplace(pairs, area)
+            except Exception:
+                log.exception("In-place translation rendering failed")
+                return self._lt_panel_fallback(pairs)
         sty = self.lt_style()
         w = self._lt_win = tk.Toplevel(self.root); w.overrideredirect(True)
         w.attributes("-topmost", True, "-alpha", float(st.get("tr_alpha", 0.9)))
@@ -2450,15 +2466,25 @@ class App:
             # OCR kutuları oyun alanı dışında kaldıysa boş siyah pencere bırakma.
             ip.hide()
             self._lt_inplace = None
-            return self._lt_show(pairs, area, 0, force_mode="screen")
+            return self._lt_panel_fallback(pairs)
         self._lt_win = ip.show(items, area)
         if self._lt_win is None:
             # A renderer can discard all lines after font measurement.  Do
             # not leave an empty transparent Toplevel above the game.
+            ip.hide()
             self._lt_inplace = None
-            return self._lt_show(pairs, area, 0, force_mode="screen")
+            return self._lt_panel_fallback(pairs)
         self._lt_job = self.root.after(int(float(st.get("tr_hide", 10)) * 1000), self._lt_hide)
 
+    def _lt_panel_fallback(self, pairs):
+        """Keep translated text accessible without opening another overlay."""
+        self._lt_hide()
+        text = "\n\n".join(tr for _, tr, _ in pairs if tr and tr.strip())
+        panel = getattr(self, "lt_out", None)
+        if panel is not None:
+            panel.config(text=text, fg=PAL["fg"])
+        self._lt_status(t("lt.panel_fallback"), "warning")
+
     def _lt_overlay_window(self, w):
         # Opak native kutular click-through olur, fakat layered olmaz: bu
         # Windows/DX12 yolunda koyu kutu kalıp Canvas metni kaybolabiliyor.
@@ -3721,8 +3747,11 @@ class App:
 
     def api_state(self):
         st = dict(self.comp_state)
+        runtime = getattr(self, "_runtime_plan", game_runtime.plan(self.cfg["settings"]))
         return {"app": APP_NAME, "version": APP_VERSION, "running": self.running, "translate": self.tr_state()["translate"],
                 "game": {"running": self.game_on, "state": self.game_state, "learned": self.screen.learned()},
+                "runtime": {"state": runtime.state, "passive_capture": runtime.passive_capture,
+                            "passive_translation": runtime.passive_translation},
                 "last": {k: st.get(k) for k in ("verdict", "verdict_label", "best", "item", "note", "time")} if st.get("verdict") else None,
                 "build": st.get("build"), "session": self._session_brief(), "tier": self.ent.tier}
 
@@ -5113,6 +5142,15 @@ class App:
         except Exception:
             log.debug("library learn failed", exc_info=True)
         verdict = itempolicy.protect_verdict(item, color_hints(card, lines, item, verdict))
+        # OCR confidence is a review signal only. The queue is local and never
+        # turns an uncertain result into a destructive action.
+        try:
+            confidence = float(item.get("confidence") or 0) if isinstance(item, dict) else 0
+            if (not valid_item(item)) or item.get("partial") or confidence < LOW_CONF_WARN:
+                review_queue.add(OCR_REVIEW_PATH, text, item, verdict,
+                                 "partial or low-confidence OCR")
+        except Exception:
+            log.debug("OCR review queue failed", exc_info=True)
         sig = signature(item)
         if timings is not None: timings.record("ocr_total", ocr_seconds * 1000)
         if auto:
@@ -5633,9 +5671,11 @@ class App:
         idle = 0                                          # art arda kart bulunamayan dünya okumaları
         while not stop.is_set():
             policy = self._policy()
+            runtime = game_runtime.plan(self.cfg["settings"])
             try:
                 region = self.scan_area()
-                if region and self.cfg["settings"].get("only_game_active", True) and not game_active():
+                runtime = game_runtime.plan(self.cfg["settings"], game_focused=game_active())
+                if region and not runtime.passive_capture:
                     prev = None; stable = 0                     # oyun önde değil: okuma yapma
                 elif region:
                     smart = self.cfg["settings"].get("smart_scan", True)
@@ -5667,7 +5707,7 @@ class App:
                 msg = f"{type(e).__name__}: {e}"
                 if msg != self.last_err:
                     self.last_err = msg; self.results.put(("err", msg))
-            stop.wait(policy.scan_poll_s)
+            stop.wait(max(policy.scan_poll_s, runtime.wait_s))
 
     def poll(self):
         # Arka plan işlerinden çok sayıda sonuç aynı anda gelirse Tk ana
@@ -8084,6 +8124,7 @@ class App:
             x = timings.get(name, {})
             return f"{x.get('median_ms', 0):.0f} ms medyan / {x.get('p95_ms', 0):.0f} ms p95" if x else "veri yok"
         st = self.cfg.get("settings", {})
+        runtime = getattr(self, "_runtime_plan", game_runtime.plan(st))
         trans = self._translation_jobs.stats() if getattr(self, "_translation_jobs", None) else {}
         assistant = self._assistant_jobs.stats() if getattr(self, "_assistant_jobs", None) else {}
         try: game_found = bool(display.game_window())
@@ -8103,6 +8144,9 @@ class App:
             "ocr": [f"Motor: {getattr(OCR, 'name', 'yok')}", f"Son OCR: {stat('ocr_total')}", f"Son tarama: {stat('scan_total')}", f"OCR geçişi: {getattr(self, 'auto_passes', lambda: '?')()}", f"Durum: {'çalışıyor' if getattr(self, 'running', False) else 'durduruldu'}"],
             "ceviri": [f"Çeviri kuyruğu: active={trans.get('active', 0)} pending={trans.get('pending', 0)}", f"Çeviri ölçümü: {stat('translate_model')}", f"Canlı çeviri: {'açık' if st.get('tr_on') else 'kapalı'}"],
             "asistan": [f"Asistan kuyruğu: active={assistant.get('active', 0)} pending={assistant.get('pending', 0)}", f"AI sağlayıcı: {st.get('ai_provider', 'builtin')}"],
+            "oyun_yardimcisi": [f"Çalışma planı: {runtime.state}",
+                                 f"Pasif OCR taraması: {'açık' if runtime.passive_capture else 'beklemede'}",
+                                 f"Pasif canlı çeviri: {'açık' if runtime.passive_translation else 'beklemede'}"],
             "arayuz": [f"Tema: {st.get('ui_theme', 'isac')}", f"Animasyonlar: {'askıda' if getattr(self.root, '_td2_suspend_animations', False) else 'aktif'}", f"Fare izi overlay: {'aktif' if getattr(self, 'trail_fx', None) else 'kapalı/güvenli'}", f"Son hata: {self.last_err or 'yok'}"],
             "hatalar": [f"Kayıt sayısı: {len(getattr(self, '_diag_errors', []))}"] + [f"{x['time']}  {x['message']}" for x in getattr(self, '_diag_errors', [])[-10:]],
         }
@@ -8685,6 +8729,7 @@ class App:
         o3 = ttk.Frame(ob); o3.pack(fill="x", padx=8, pady=4)
         ttk.Button(o3, text=ui_theme.with_icon(t("ocr.calibrate"), "🎯"), command=self.auto_calibrate_ocr).pack(side="left")
         ttk.Button(o3, text=ui_theme.with_icon(t("ocr.preview"), "👁"), command=self.ocr_preview).pack(side="left", padx=8)
+        ttk.Button(o3, text="⚖ Motorları karşılaştır", command=self.ocr_lab_report).pack(side="left", padx=8)
         self.ocr_msg = ttk.Label(o3, text="", foreground=PAL["muted"]); self.ocr_msg.pack(side="left", padx=8)
         ttk.Label(ob, text=t("ocr.note_rapid") if OCR.name == "rapidocr" else t("ocr.note"), foreground=PAL["muted"],
                   wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0, 4))
@@ -8798,6 +8843,30 @@ class App:
         self.ocr_msg.config(text=t("ocr.calib_done", thr=th, scale=sc, q=round(q, 1)))
         log.info("OCR auto-calibration: threshold=%s scale=%s quality=%.2f", th, sc, q)
 
+    def ocr_lab_report(self):
+        """Aynı son kartta kurulu OCR yollarını ölç; ağ veya oyun gerekmez."""
+        img = self._calib_image()
+        if img is None:
+            return messagebox.showinfo(APP_NAME, t("ocr.need_card"))
+        engines = {"rapidocr": lambda im: OCR.segments(im) if OCR and OCR.name == "rapidocr" else (_ for _ in ()).throw(RuntimeError("RapidOCR unavailable"))}
+        windows = self._winocr()
+        if windows.available:
+            engines["windows"] = windows.segments
+        try:
+            tess = ocr_backend.Engine("tesseract", tess_lang=self.cfg["settings"].get("ocr_lang", "eng"),
+                                      tess_config=ocr_config(self.cfg["settings"]), preprocess=gamedata.text_image)
+            engines["tesseract"] = tess.segments
+        except Exception as exc:
+            log.info("Tesseract lab unavailable: %s", exc)
+        report = ocr_lab.benchmark(img, engines)
+        out = APPLOG_DIR / "ocr_lab_latest.json"
+        APPLOG_DIR.mkdir(parents=True, exist_ok=True)
+        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
+        lines = [f"{name}: " + (f"{data['elapsed_ms']} ms, güven {data['mean_confidence']:.2f}" if data.get("available") else "kullanılamıyor")
+                 for name, data in report["engines"].items()]
+        self.toast("OCR laboratuvarı: " + (report["winner"] or "uygun motor yok"))
+        messagebox.showinfo(APP_NAME, "\n".join(lines) + f"\n\nRapor: {out}")
+
     def ocr_preview(self):
         """Orijinal kart ↔ işlenmiş (siyah-beyaz) görüntü + OCR metni + tanınanlar; eşik kaydırıcısıyla canlı."""
         img = self._calib_image()
@@ -9629,10 +9698,76 @@ class App:
         tools = ttk.Frame(parent); tools.pack(fill="x", padx=10, pady=6)
         ttk.Button(tools, text=t("command.search"), command=self._universal_search_window).pack(side="left")
         ttk.Button(tools, text=t("command.audit"), command=self._library_report_window).pack(side="left", padx=6)
+        ttk.Button(tools, text="🧭 Karar merkezi", command=self._decision_center_window).pack(side="left", padx=6)
+        target_box = ttk.LabelFrame(parent, text="🎯 Kişisel hedef ve farm planı")
+        target_box.pack(fill="x", padx=10, pady=(0, 6))
+        target_tools = ttk.Frame(target_box); target_tools.pack(fill="x", padx=6, pady=4)
+        ttk.Button(target_tools, text="＋ Hedef ekle", command=self._target_add).pack(side="left")
+        ttk.Button(target_tools, text="↻ Farm planını yenile", command=self.refresh_stash).pack(side="left", padx=6)
+        ttk.Label(target_tools, text="Yerel hedefler; eski/verisi belirsiz kaynaklar REVIEW olur.", foreground=PAL["muted"]).pack(side="left", padx=8)
+        self.target_tv = ttk.Treeview(target_box, columns=("name", "slot", "priority", "state"), show="headings", height=4)
+        for col, title, width in (("name", "Eşya", 230), ("slot", "Yuva", 120), ("priority", "Öncelik", 90), ("state", "Durum", 120)):
+            self.target_tv.heading(col, text=title); self.target_tv.column(col, width=width, anchor="w")
+        self.target_tv.pack(fill="x", padx=6, pady=(0, 5))
         self.command_txt = tk.Text(parent, bg=PAL["surface"], fg=PAL["fg"], relief="flat", wrap="word", font=(ui_theme.FONT, 11))
         self.command_txt.pack(fill="both", expand=True, padx=10, pady=10)
         ttk.Button(parent, text=t("command.refresh"), command=self.refresh_stash).pack(anchor="e", padx=10, pady=(0, 8))
 
+    def _target_add(self):
+        name = simpledialog.askstring(APP_NAME, "Eşya adı:", parent=self.root)
+        if not name or not name.strip():
+            return
+        slot = simpledialog.askstring(APP_NAME, "Yuva (ör. Weapon, Chest):", parent=self.root)
+        if not slot or not slot.strip():
+            return
+        attrs = simpledialog.askstring(APP_NAME, "Attribute adları (virgülle ayır; isteğe bağlı):", parent=self.root) or ""
+        current = target_planner.load_targets(TARGETS_PATH)
+        current.append(target_planner.normalize_target({"name": name.strip(), "slot": slot.strip(),
+                                                        "attributes": [x.strip() for x in attrs.split(",") if x.strip()]}))
+        target_planner.save_targets(TARGETS_PATH, current)
+        self._refresh_command(getattr(self, "stash", stash.Stash(STASH_PATH)).owned())
+
+    def _target_sources(self):
+        sources = []
+        week = self.vendor_week or {}
+        fetched = week.get("fetched", 0)
+        for item in week.get("items", []) or []:
+            row = dict(item) if isinstance(item, dict) else {}
+            row.update({"source": "vendor", "updated_at": fetched, "cadence": "weekly"})
+            sources.append(row)
+        for event, rows in (week.get("target_loot") or {}).items():
+            for row in rows or []:
+                for day in row.get("target_loot_by_day", []) or []:
+                    for name in day.get("target_loot", []) or []:
+                        sources.append({"source": "target_loot", "name": name, "slot": "", "event": event,
+                                        "updated_at": fetched, "cadence": "dated"})
+        for category, rows in (self.tasks.get("items", {}) or {}).items():
+            for task in rows or []:
+                if not isinstance(task, dict):
+                    continue
+                sources.append({"source": "task", "name": task.get("item") or task.get("name") or task.get("en") or task.get("title"),
+                                "slot": task.get("slot") or "", "attributes": task.get("attributes"),
+                                "updated_at": task.get("updated_at") or fetched, "cadence": task.get("period") or category})
+        return sources
+
+    def _refresh_targets(self, items=None):
+        if not getattr(self, "target_tv", None):
+            return
+        targets = target_planner.load_targets(TARGETS_PATH)
+        sources = self._target_sources()
+        matches = target_planner.match_targets(targets, sources)
+        self.target_tv.delete(*self.target_tv.get_children())
+        for target in targets:
+            rows = [x for x in matches if x["target"]["name_key"] == target["name_key"]]
+            state = "NO_MATCH" if not rows else rows[0]["status"]
+            self.target_tv.insert("", "end", values=(target["name"], target["slot"], target["priority"], state))
+        if getattr(self, "command_txt", None) and targets:
+            self.command_txt.insert("end", "\nKİŞİSEL HEDEF PLANI\n")
+            for row in matches:
+                name = row["target"]["name"]
+                detail = row["source"] or "kaynak bulunamadı"
+                self.command_txt.insert("end", f"• {name}: {row['status']} · {detail}\n")
+
     def _universal_search_window(self):
         w = tk.Toplevel(self.root); w.title(t("command.search")); w.geometry("760x500")
         q = tk.StringVar(); ttk.Entry(w, textvariable=q).pack(fill="x", padx=10, pady=10)
@@ -9660,6 +9795,17 @@ class App:
                 if key not in known: rows.append(t("command.unknown_attr", name=item.get('name'), key=key))
         messagebox.showinfo(t("command.audit"), '\n'.join(rows) or t("command.audit_ok"), parent=self.root)
 
+    def _decision_center_window(self):
+        if not self.last_scan:
+            return messagebox.showinfo(APP_NAME, "Önce bir eşya tarayın; son taranan eşya burada karşılaştırılır.", parent=self.root)
+        item, _results, _signature = self.last_scan
+        rows = decision_center.compare_item_to_targets(item, target_planner.load_targets(TARGETS_PATH))
+        summary = decision_center.farm_summary(rows)
+        text = [f"Eşya: {item.get('name', '?')}", f"Özet: {summary}", ""]
+        for row in rows:
+            text.append(f"• {row['target']['name']}: {row['recommendation']} · {row['status']} · {', '.join(row['reasons']) or 'eşleşme yok'}")
+        messagebox.showinfo("Karar merkezi", "\n".join(text), parent=self.root)
+
     def _refresh_command(self, items):
         if not getattr(self, "command_txt", None): return
         b = active_build(self.cfg)
@@ -9688,6 +9834,7 @@ class App:
                 if not row['routes']:
                     self.command_txt.insert("end", "    " + t("command.no_route") + "\n")
             self.command_txt.insert("end", "\n" + t("command.summary", protected=snap['protected'], duplicates=snap['duplicates'], library=len(snap['library'])) + "\n")
+        self._refresh_targets(items)
         self.command_txt.config(state="disabled")
 
     def _stash_rec_toggle(self):
```

### C:/Users/PC/Desktop/Thedivision2program/decision_center.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/decision_center.py b/decision_center.py
new file mode 100644
index 0000000..8e5dcb1
--- /dev/null
+++ b/decision_center.py
@@ -0,0 +1,48 @@
+"""Faz 5: kişisel hedef + taranan eşya için güvenli karar özeti."""
+from __future__ import annotations
+
+from datetime import datetime, timezone
+from typing import Any, Iterable
+
+import target_planner
+
+
+_PROTECTED = {"exotic", "named", "prototype"}
+
+
+def _protected(item: dict[str, Any]) -> bool:
+    rarity = {str(x).lower() for x in (item.get("rarity") or [])}
+    text = " ".join(str(x).lower() for x in (item.get("name"), item.get("gear_set"), item.get("brand")) if x)
+    return bool(rarity & _PROTECTED or any(word in text for word in _PROTECTED) or item.get("locked"))
+
+
+def compare_item_to_targets(item: dict[str, Any], targets: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
+    """Return review-safe target matches for a scanned item; never returns dismantle."""
+    source = target_planner.normalize_source({
+        "source": "scan",
+        "name": item.get("name"),
+        "slot": item.get("slot"),
+        "attributes": list((item.get("attrs") or {}).keys()),
+        "talents": item.get("talents"),
+        "prototype_augments": item.get("prototype_augments"),
+        "confidence": item.get("confidence", 1.0),
+        "updated_at": item.get("seen_at") or item.get("seen") or datetime.now(timezone.utc).timestamp(),
+        "cadence": "dated",
+    })
+    rows = target_planner.match_targets(list(targets), [source])
+    protected = _protected(item)
+    for row in rows:
+        row["recommendation"] = "REVIEW" if protected or row["status"] != "MATCH" else "KEEP"
+        row["protected"] = protected
+    return rows
+
+
+def farm_summary(matches: Iterable[dict[str, Any]]) -> dict[str, Any]:
+    rows = list(matches)
+    return {
+        "total": len(rows),
+        "matches": sum(row.get("status") == "MATCH" for row in rows),
+        "review": sum(row.get("status") == "REVIEW" for row in rows),
+        "missing": sum(row.get("status") == "NO_MATCH" for row in rows),
+        "protected": sum(bool(row.get("protected")) for row in rows),
+    }
```

### C:/Users/PC/Desktop/Thedivision2program/docs/phase2-overlay-health.md
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/docs/phase2-overlay-health.md b/docs/phase2-overlay-health.md
new file mode 100644
index 0000000..130fbfe
--- /dev/null
+++ b/docs/phase2-overlay-health.md
@@ -0,0 +1,38 @@
+# Faz 2 — Yerel overlay sağlık testi
+
+Kaynak sürüm için `scripts/overlay_health_check.bat` çalıştırılır. Python 3.13,
+kurulu RapidOCR ve `models/en-tr` içindeki yerel model gereklidir. Model indirilmez.
+JSON raporu benzersiz isimle Windows geçici klasörüne yazılır; GitHub'a gönderilmez.
+
+Test sentetik İngilizce kartı masaüstünde gösterir, ekran yakalamasını gerçek OCR
+ve yerel çeviri yolundan geçirir. Yakalama, OCR, çeviri, koordinatlar ve gerçek
+ekran piksellerindeki metin ayrı raporlanır. Pencerenin yalnız var olması başarı değildir.
+Görünürlük ölçümü sırasında yalnız test overlay'inin yakalamadan dışlanması ertelenir;
+ardından dışlama etkinleştirilerek arka plandaki sentetik görüntüyle karşılaştırılır.
+
+Yerinde overlay oluşturma/yerleşim hatasında çeviri panelde ve geçmişte kalır.
+Başka bir overlay açılmaz. Başlatılırken hata veren native pencereler de temizlenir.
+Bu geri dönüş, sürücünün sessizce çizmediği tüm durumları otomatik algıladığı anlamına gelmez.
+
+## Doğrulama sınırları
+
+- Foreground pencere korunması ve Windows click-through stil bitleri ölçülür.
+- Tk ölçek değerleri 1.0, 1.5, 2.0 ile tekrar çizim yapılır.
+- Gerçek fare tıklamasının alttaki oyuna geçmesi ve monitörler arasında DPI
+  değişimi etkileşimli test gerektirir. Stil bitleri fiziksel tıklama kanıtı değildir.
+- Sentetik masaüstü testi oyun/DX12, HDR veya tam ekran uyumluluğu kanıtlamaz.
+- Test sırasında başka pencerelerin sentetik alanı kapatması ölçümü bozabilir.
+
+## Regresyon testleri
+
+Her dosya ayrı süreçte çalıştırılır:
+
+```powershell
+py -3.13 -B tests/test_translation_controls.py
+py -3.13 -B tests/test_inplace_anchors.py
+py -3.13 -B tests/test_overlay.py
+py -3.13 -B tests/test_translation_reliability.py
+py -3.13 -B tests/test_stability_widgets.py
+```
+
+Bu faz yerelde hazırlanır; yayın ve installer üretimi için ayrıca kullanıcı onayı gerekir.
```

### C:/Users/PC/Desktop/Thedivision2program/docs/phase3-ocr-lab.md
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/docs/phase3-ocr-lab.md b/docs/phase3-ocr-lab.md
new file mode 100644
index 0000000..61bdd01
--- /dev/null
+++ b/docs/phase3-ocr-lab.md
@@ -0,0 +1,19 @@
+# Faz 3 — OCR laboratuvarı ve inceleme kuyruğu
+
+Settings → OCR içindeki **Motorları karşılaştır** düğmesi son kaydedilen kartı
+RapidOCR, Windows OCR ve kurulu Tesseract yollarına aynı girdide verir. Her yol
+için süre, satır sayısı, ortalama güven, metin benzerliği ve `review` işareti
+raporlanır. Rapor yalnız yerel `logs/ocr_lab_latest.json` dosyasına yazılır.
+
+OCR laboratuvarı motoru otomatik değiştirmez. En uzun/ortalama güveni yüksek
+sonuç yalnız kıyaslama kazananıdır; oyun kartlarıyla ayrıca doğrulanmadan kalıcı
+motor seçimi yapılmaz.
+
+Düşük güvenli, kısmi veya geçersiz eşya okumaları yerel
+`logs/ocr_review_queue.jsonl` kuyruğuna eklenir. Kayıt zorla `REVIEW` olur ve
+aynı kart tekrar görülürse çoğaltılmaz. `Exotic`, `Named`, `Prototype` veya
+kilitli eşyalar için bu kuyruk dışında otomatik silme/kırma yolu yoktur.
+
+Kapsam sınırı: laboratuvar ekran görüntüsü ve yerel motorları ölçer; oyun
+belleği, DLL injection, ağ tabanlı OCR ve gerçek oyun içi anti-cheat/DX12
+uyumluluğu kapsam dışıdır.
```

### C:/Users/PC/Desktop/Thedivision2program/docs/phase4-target-planner.md
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/docs/phase4-target-planner.md b/docs/phase4-target-planner.md
new file mode 100644
index 0000000..d95a7d1
--- /dev/null
+++ b/docs/phase4-target-planner.md
@@ -0,0 +1,13 @@
+# Faz 4 — Kişisel hedef ve farm planı
+
+Komuta Merkezi içindeki hedef alanı, kullanıcı hedeflerini yalnızca yerel `targets.json` dosyasına kaydeder. Hedefler eşya adı, yuva, attribute, talent, Prototype Augment ve öncelik alanlarını destekler.
+
+Farm eşleştirme motoru satıcı ve hedef-loot önbelleklerini kaynak olarak kullanır. Kaynağın tarihi cadence'e göre geçmişse veya güveni düşükse sonuç `REVIEW` olur; veri yoksa `NO_MATCH` gösterilir. Sonuçlar planlama bilgisidir, otomatik silme/kırma veya oyun değişikliği yapmaz.
+
+Doğrulama:
+
+```powershell
+python -m unittest -v tests/test_target_planner.py
+python -B tests/test_stability_widgets.py
+python -m py_compile target_planner.py app.py
+```
```

### C:/Users/PC/Desktop/Thedivision2program/docs/phase5-decision-center.md
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/docs/phase5-decision-center.md b/docs/phase5-decision-center.md
new file mode 100644
index 0000000..8da92a9
--- /dev/null
+++ b/docs/phase5-decision-center.md
@@ -0,0 +1,7 @@
+# Faz 5 — Akıllı karar merkezi
+
+PC tarafına kişisel hedef ile son taranan eşyayı karşılaştıran güvenli bir karar katmanı eklendi. Bu katman yalnızca `KEEP`, `REVIEW` ve hedef eşleşmesi üretir; hiçbir durumda `DISMANTLE` önermez.
+
+Exotic, Named, Prototype veya kilitli kayıtlar tam eşleşse bile `REVIEW` olarak kalır. Düşük OCR güveni, eski kaynak veya eksik alanlar da incelemeye yönlendirilir.
+
+Mobil tarafındaki Faz 5 güncelleme denetimi, haber/görev yenileme ve bildirim izinleri mevcut `CompanionModel` akışında korunur. Mobil mağaza yayını için gerçek cihaz, imza, Play Console ve iOS/macOS adımları hâlâ ayrı çıkış koşullarıdır.
```

### C:/Users/PC/Desktop/Thedivision2program/docs/ruflo-integration.md
Tür: Yeni; talep ilişkisi: Ruflo/ajan entegrasyonu talebi. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/docs/ruflo-integration.md b/docs/ruflo-integration.md
new file mode 100644
index 0000000..df66e85
--- /dev/null
+++ b/docs/ruflo-integration.md
@@ -0,0 +1,32 @@
+# Ruflo ajan entegrasyonu
+
+Bu proje için Ruflo’nun Codex yüzeyi `.agents/config.toml` ve iki yerel skill
+altında kuruldu. Ana `AGENTS.md` dosyası korunmuştur; Ruflo yönergeleri onun
+yerine geçmez.
+
+Ruflo, Python uygulamasının içine gömülü bir oyun motoru değildir. Proje
+geliştirme görevlerini yönlendiren bir CLI/MCP orkestrasyon katmanıdır. OCR,
+canlı çeviri ve loot kararları yine TD2 Loot Advisor’ın yerel Python kodunda
+çalışır. Ajanlara oyun belleği, DLL injection, anti-cheat aşma veya oyun dosyası
+yazma yetkisi verilmez.
+
+## Kontrol
+
+```powershell
+npx --yes ruflo@latest doctor --json -c node
+npx --yes ruflo@latest mcp start
+```
+
+`mcp start` stdio MCP sunucusudur; uzun süreli servis olarak elle başlatılması
+gerekmez. Codex, `.agents/config.toml` içindeki `ruflo` sunucusunu gerektiğinde
+`cmd /c npx -y ruflo@latest mcp start` ile başlatır.
+
+## Güvenli sınırlar
+
+- Onay politikası `on-request`, sandbox `workspace-write` olarak ayarlanmıştır.
+- Swarm otomasyonu kapalıdır; izole worktree ve açık görev olmadan ajan fan-out
+  yapılmaz.
+- Ağ ve model sağlayıcıları Ruflo’nun MCP/ajan görevleri için opsiyoneldir;
+  ekran görüntüsü ve OCR metni varsayılan olarak uzak servise gönderilmez.
+- `.codex/`, `.claude-flow/data/` ve `.claude-flow/logs/` runtime dosyalarıdır;
+  Git’e eklenmez.
```

### C:/Users/PC/Desktop/Thedivision2program/game_runtime.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/game_runtime.py b/game_runtime.py
new file mode 100644
index 0000000..fc70761
--- /dev/null
+++ b/game_runtime.py
@@ -0,0 +1,36 @@
+"""Safe runtime plan for the desktop helper.
+
+The plan only receives UI/game-window focus already discovered by the app.  It
+does not inspect processes, game memory, files, GPU state, or network traffic.
+"""
+from dataclasses import dataclass
+from collections.abc import Mapping
+
+
+@dataclass(frozen=True)
+class RuntimePlan:
+    """Read-only policy consumed by passive OCR and translation loops."""
+
+    state: str
+    passive_capture: bool
+    passive_translation: bool
+    wait_s: float
+
+
+def plan(settings, *, game_focused=False, app_hidden=False):
+    """Return a bounded passive-work policy without modifying saved settings."""
+    settings = settings if isinstance(settings, Mapping) else {}
+    focused = bool(game_focused)
+    only_game_active = bool(settings.get("only_game_active", True))
+
+    if focused:
+        return RuntimePlan(
+            "game_focus_tray" if app_hidden else "game_focus",
+            passive_capture=True,
+            passive_translation=True,
+            wait_s=0.0,
+        )
+    if only_game_active:
+        # A bounded wait avoids busy polling while another application is focused.
+        return RuntimePlan("background", passive_capture=False, passive_translation=False, wait_s=1.5)
+    return RuntimePlan("desktop", passive_capture=True, passive_translation=True, wait_s=0.0)
```

### C:/Users/PC/Desktop/Thedivision2program/lang/de.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/de.json b/lang/de.json
index 74e0668..d0968f4 100644
--- a/lang/de.json
+++ b/lang/de.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay nicht verfügbar. Die Übersetzung steht im Panel und Verlauf.",
   "__meta__": {
     "name": "Deutsch",
     "english_name": "German"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/en.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/en.json b/lang/en.json
index d20518d..b819fdf 100644
--- a/lang/en.json
+++ b/lang/en.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay unavailable. Translation is available in the panel and history.",
 "command.unknown_attr": "{name}: unknown attribute {key}",
 "command.audit_ok": "No unknown attribute keys found in builds or stash records.",
 "command.backup_ok": "Stash and builds backed up",
```

### C:/Users/PC/Desktop/Thedivision2program/lang/es.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/es.json b/lang/es.json
index bf548c2..0739ecd 100644
--- a/lang/es.json
+++ b/lang/es.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay no disponible. La traducción está en el panel y el historial.",
   "__meta__": {
     "name": "Español",
     "english_name": "Spanish"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/fr.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/fr.json b/lang/fr.json
index a4d5779..045effa 100644
--- a/lang/fr.json
+++ b/lang/fr.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay indisponible. La traduction est disponible dans le panneau et l’historique.",
   "__meta__": {
     "name": "Français",
     "english_name": "French"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/it.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/it.json b/lang/it.json
index 78494cc..300cf07 100644
--- a/lang/it.json
+++ b/lang/it.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay non disponibile. Traduzione disponibile nel pannello e nella cronologia.",
   "__meta__": {
     "name": "Italiano",
     "english_name": "Italian"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/nl.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/nl.json b/lang/nl.json
index 29823f9..979c2a4 100644
--- a/lang/nl.json
+++ b/lang/nl.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay niet beschikbaar. De vertaling staat in het paneel en de geschiedenis.",
   "__meta__": {
     "name": "Nederlands",
     "english_name": "Dutch"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/pl.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/pl.json b/lang/pl.json
index 643b0f4..d23985b 100644
--- a/lang/pl.json
+++ b/lang/pl.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Nakładka niedostępna. Tłumaczenie jest w panelu i historii.",
   "__meta__": {
     "name": "Polski",
     "english_name": "Polish"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/pt.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/pt.json b/lang/pt.json
index 0d398f4..0f22756 100644
--- a/lang/pt.json
+++ b/lang/pt.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay indisponível. A tradução está no painel e no histórico.",
   "__meta__": {
     "name": "Português",
     "english_name": "Portuguese"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/ru.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/ru.json b/lang/ru.json
index b41f674..fcc8e18 100644
--- a/lang/ru.json
+++ b/lang/ru.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Оверлей недоступен. Перевод доступен на панели и в истории.",
   "__meta__": {
     "name": "Русский",
     "english_name": "Russian"
```

### C:/Users/PC/Desktop/Thedivision2program/lang/tr.json
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
69e030c Claude feat: canlı çeviri 10 dile genelleştirildi + düşük OCR güveni uyarısı (9.1.5.29)
0a75f16 Claude feat: Kaivolt teması + Hakkında sekmesi — sade/modern varsayılan görünüm (v9.1.5.28)
69621ef Claude feat: "Bu karar yanlıştı" geri bildirimi — yanlış SAKLA/KIR kararını işaretleme (v9.1.5.27)
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/lang/tr.json b/lang/tr.json
index 23440b1..7aa6e46 100644
--- a/lang/tr.json
+++ b/lang/tr.json
@@ -1,4 +1,5 @@
 {
+  "lt.panel_fallback": "Overlay gösterilemedi. Çeviri panelde ve geçmişte mevcut.",
 "command.unknown_attr": "{name}: bilinmeyen attribute {key}",
 "command.audit_ok": "Build ve sandık kayıtlarında bilinmeyen attribute anahtarı bulunmadı.",
 "command.backup_ok": "Sandık ve build yedeği kaydedildi",
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/PHASE5_RELEASE_READINESS_TR.md
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
06f992c FEDERALTURK fix: download and install companion updates safely
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
1c32976 FEDERALTURK feat(mobile): harden pairing and prepare device release
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/PHASE5_RELEASE_READINESS_TR.md b/mobile/PHASE5_RELEASE_READINESS_TR.md
index 46fb4ee..0291fef 100644
--- a/mobile/PHASE5_RELEASE_READINESS_TR.md
+++ b/mobile/PHASE5_RELEASE_READINESS_TR.md
@@ -5,6 +5,9 @@ durumu ve kullanıcı hesabı/cihaz erişimi gerektiren açık adımları ayır
 
 ## Bu çalışma alanında doğrulananlar
 
+- Güncelleme denetimi kalıcı zaman damgasıyla altı saatte bir sınırlandırılır; kullanıcı ayarı açık olsa bile her uygulama açılışında GitHub API çağrısı yapılmaz.
+- Companion sürüm kimliği `pubspec.yaml`, `companionVersion` ve release tag arasında aynı tutulur; APK indirme akışı SHA-256 doğrulamasından sonra Android kurulum intent'ini açar.
+
 - Flutter `3.47.8` ve Dart `3.13.7` ile `flutter analyze` temiz geçti.
 - `flutter test` geçti; başlangıç testi asenkron splash ekranını doğrulayacak
   şekilde güncellendi.
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/android/app/build.gradle.kts
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
06f992c FEDERALTURK fix: download and install companion updates safely
a021259 FEDERALTURK feat(mobile): refresh content and notify opted-in users
b8adc9f Claude feat(mobile): FCM/APNs push-token kaydı eklendi (Flutter tarafı)
9aebb2e FEDERALTURK Release 9.0.9 with Android companion launch fix
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/android/app/build.gradle.kts b/mobile/android/app/build.gradle.kts
index 318852a..324f7c6 100644
--- a/mobile/android/app/build.gradle.kts
+++ b/mobile/android/app/build.gradle.kts
@@ -76,6 +76,7 @@ android {
 }
 
 dependencies {
+    implementation("androidx.core:core:1.13.1")
     coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")
 }
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/android/app/src/main/AndroidManifest.xml
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
06f992c FEDERALTURK fix: download and install companion updates safely
b8adc9f Claude feat(mobile): FCM/APNs push-token kaydı eklendi (Flutter tarafı)
6237d1f FEDERALTURK Release 9.0.8: Android companion beta
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/android/app/src/main/AndroidManifest.xml b/mobile/android/app/src/main/AndroidManifest.xml
index 2fb178e..6a326b4 100644
--- a/mobile/android/app/src/main/AndroidManifest.xml
+++ b/mobile/android/app/src/main/AndroidManifest.xml
@@ -2,12 +2,23 @@
     <uses-permission android:name="android.permission.INTERNET" />
     <!-- Push bildirimi (Faz 4): Android 13+'ta çalışma zamanı izni için gerekli. -->
     <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
+    <!-- Yalnız GitHub beta APK akışı için; Play sürümünde Play In-App Updates kullanılmalıdır. -->
+    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
 
     <application
         android:label="TD2 Loot Advisor"
         android:name="${applicationName}"
         android:icon="@mipmap/ic_launcher"
         android:usesCleartextTraffic="true">
+        <provider
+            android:name="androidx.core.content.FileProvider"
+            android:authorities="${applicationId}.fileprovider"
+            android:exported="false"
+            android:grantUriPermissions="true">
+            <meta-data
+                android:name="android.support.FILE_PROVIDER_PATHS"
+                android:resource="@xml/file_paths" />
+        </provider>
         <activity
             android:name=".MainActivity"
             android:exported="true"
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/android/app/src/main/kotlin/com/federalturk/td2companion/MainActivity.kt
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
04148ca FEDERALTURK fix: companion version display and update permission flow
06f992c FEDERALTURK fix: download and install companion updates safely
9aebb2e FEDERALTURK Release 9.0.9 with Android companion launch fix
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/android/app/src/main/kotlin/com/federalturk/td2companion/MainActivity.kt b/mobile/android/app/src/main/kotlin/com/federalturk/td2companion/MainActivity.kt
index 59d9497..244faec 100644
--- a/mobile/android/app/src/main/kotlin/com/federalturk/td2companion/MainActivity.kt
+++ b/mobile/android/app/src/main/kotlin/com/federalturk/td2companion/MainActivity.kt
@@ -1,5 +1,45 @@
 package com.federalturk.td2companion
 
+import android.content.Intent
+import android.net.Uri
+import android.os.Build
+import android.provider.Settings
+import androidx.core.content.FileProvider
+import io.flutter.embedding.engine.FlutterEngine
 import io.flutter.embedding.android.FlutterActivity
+import io.flutter.plugin.common.MethodChannel
+import java.io.File
 
-class MainActivity : FlutterActivity()
+class MainActivity : FlutterActivity() {
+    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
+        super.configureFlutterEngine(flutterEngine)
+        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "td2_companion/update")
+            .setMethodCallHandler { call, result ->
+                if (call.method != "installApk") {
+                    result.notImplemented()
+                    return@setMethodCallHandler
+                }
+                try {
+                    val path = call.argument<String>("path") ?: throw IllegalArgumentException("APK yolu boş")
+                    val apk = File(path)
+                    if (!apk.isFile) throw IllegalArgumentException("APK bulunamadı")
+                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
+                        !packageManager.canRequestPackageInstalls()) {
+                        startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
+                            Uri.parse("package:$packageName")))
+                        result.error("INSTALL_PERMISSION",
+                            "Bu uygulamadan yüklemeye izin verin; ardından geri dönüp güncelleme düğmesine tekrar basın.", null)
+                        return@setMethodCallHandler
+                    }
+                    val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", apk)
+                    startActivity(Intent(Intent.ACTION_VIEW).apply {
+                        setDataAndType(uri, "application/vnd.android.package-archive")
+                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION)
+                    })
+                    result.success(true)
+                } catch (error: Exception) {
+                    result.error("INSTALL_FAILED", error.message, null)
+                }
+            }
+    }
+}
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/android/app/src/main/res/xml/file_paths.xml
Tür: Yeni; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
06f992c FEDERALTURK fix: download and install companion updates safely
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/android/app/src/main/res/xml/file_paths.xml b/mobile/android/app/src/main/res/xml/file_paths.xml
new file mode 100644
index 0000000..717eaed
--- /dev/null
+++ b/mobile/android/app/src/main/res/xml/file_paths.xml
@@ -0,0 +1,4 @@
+<?xml version="1.0" encoding="utf-8"?>
+<paths xmlns:android="http://schemas.android.com/apk/res/android">
+    <files-path name="app_files" path="." />
+</paths>
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/lib/main.dart
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
04148ca FEDERALTURK fix: companion version display and update permission flow
d9a6179 FEDERALTURK fix: satisfy companion update lint
961640c FEDERALTURK fix: satisfy companion analyzer formatting
06f992c FEDERALTURK fix: download and install companion updates safely
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/lib/main.dart b/mobile/lib/main.dart
index 4745f84..7a16bea 100644
--- a/mobile/lib/main.dart
+++ b/mobile/lib/main.dart
@@ -1,11 +1,13 @@
-import 'dart:convert';
 import 'dart:async';
+import 'dart:convert';
 import 'dart:io';
 
+import 'package:crypto/crypto.dart';
 import 'package:flutter/material.dart';
 import 'package:flutter/services.dart';
 import 'package:http/http.dart' as http;
 import 'package:mobile_scanner/mobile_scanner.dart';
+import 'package:path_provider/path_provider.dart';
 import 'package:shared_preferences/shared_preferences.dart';
 import 'package:url_launcher/url_launcher.dart';
 
@@ -151,6 +153,9 @@ class CompanionModel extends ChangeNotifier {
   String? availableVersion;
   String? availableVersionUrl;
   String? availableApkUrl;
+  String? availableSha256Url;
+  bool downloadingUpdate = false;
+  double updateProgress = 0;
   DateTime? lastUpdateCheck;
   SharedPreferences? _prefs;
   Timer? _desktopPoll;
@@ -202,6 +207,10 @@ class CompanionModel extends ChangeNotifier {
           .toSet();
       newsAlertsEnabled = _prefs?.getBool('news_alerts_enabled') ?? false;
       updateAlertsEnabled = _prefs?.getBool('update_alerts_enabled') ?? false;
+      final lastUpdateMillis = _prefs?.getInt('last_update_check_ms');
+      if (lastUpdateMillis != null) {
+        lastUpdateCheck = DateTime.fromMillisecondsSinceEpoch(lastUpdateMillis);
+      }
       final rawBuilds = _prefs?.getStringList('saved_builds') ?? <String>[];
       savedBuilds = rawBuilds
           .map((row) {
@@ -220,7 +229,7 @@ class CompanionModel extends ChangeNotifier {
     loading = false;
     notifyListeners();
     await refresh(quiet: true);
-    unawaited(checkForUpdate());
+    unawaited(checkForUpdate(force: true));
   }
 
   void _restoreContentCache() {
@@ -345,7 +354,8 @@ class CompanionModel extends ChangeNotifier {
     );
   }
 
-  Future<void> checkForUpdate() async {
+  Future<void> checkForUpdate({bool force = false}) async {
+    if (!force && !isUpdateCheckDue(lastUpdateCheck)) return;
     final client = http.Client();
     try {
       final release = await fetchLatestCompanionRelease(client);
@@ -353,7 +363,9 @@ class CompanionModel extends ChangeNotifier {
       availableVersion = release.version;
       availableVersionUrl = release.url;
       availableApkUrl = release.apkUrl;
+      availableSha256Url = release.sha256Url;
       lastUpdateCheck = DateTime.now();
+      await _prefs?.setInt('last_update_check_ms', lastUpdateCheck!.millisecondsSinceEpoch);
       if (updateAlertsEnabled && updateAvailable) {
         final notified = _prefs?.getString('notified_companion_version');
         if (notified != release.version) {
@@ -376,6 +388,66 @@ class CompanionModel extends ChangeNotifier {
     }
   }
 
+  Future<String?> downloadAndInstallUpdate() async {
+    final apkUrl = availableApkUrl;
+    if (apkUrl == null || downloadingUpdate) return 'APK bağlantısı bulunamadı.';
+    downloadingUpdate = true;
+    updateProgress = 0;
+    notifyListeners();
+    try {
+      final response = await http
+          .get(Uri.parse(apkUrl))
+          .timeout(const Duration(minutes: 3));
+      if (response.statusCode != 200 || response.bodyBytes.isEmpty) {
+        return 'APK indirilemedi (HTTP ${response.statusCode}).';
+      }
+      final expected = await _fetchChecksum();
+      if (expected == null || !RegExp(r'^[a-f0-9]{64}$').hasMatch(expected)) {
+        return 'APK doğrulama bilgisi alınamadı. Lütfen tekrar deneyin.';
+      }
+      final actual = sha256.convert(response.bodyBytes).toString();
+      if (expected != actual) {
+        return 'APK doğrulaması başarısız; dosya kurulmadı.';
+      }
+      final directory = await getApplicationSupportDirectory();
+      final file = File(
+        '${directory.path}/TD2LootAdvisor_Companion_$availableVersion.apk',
+      );
+      await file.writeAsBytes(response.bodyBytes, flush: true);
+      await const MethodChannel('td2_companion/update').invokeMethod<bool>(
+        'installApk',
+        {'path': file.path},
+      );
+      return null;
+    } catch (error) {
+      return 'Güncelleme indirilemedi: $error';
+    } finally {
+      downloadingUpdate = false;
+      updateProgress = 0;
+      notifyListeners();
+    }
+  }
+
+  Future<String?> _fetchChecksum() async {
+    final checksumUrl = availableSha256Url;
+    if (checksumUrl == null) return null;
+    try {
+      final text = await http
+          .read(Uri.parse(checksumUrl))
+          .timeout(const Duration(seconds: 20));
+      final apkName = 'TD2LootAdvisor_Companion_$availableVersion.apk';
+      for (final line in text.split(RegExp(r'\r?\n'))) {
+        final parts = line.trim().split(RegExp(r'\s+'));
+        if (parts.length >= 2 && parts.last.endsWith(apkName)) {
+          return parts.first.toLowerCase();
+        }
+      }
+    } catch (_) {
+      return null;
+    }
+    return null;
+  }
+
   Future<String?> setNewsAlertsEnabled(bool enabled) => _setAlerts(
     enabled: enabled,
     preferenceKey: 'news_alerts_enabled',
@@ -621,7 +693,7 @@ class _MainShellState extends State<MainShell> {
                     ),
                   ),
                   Text(
-                    'COMPANION  ·  BETA 0.1.5',
+                    'COMPANION  ·  BETA $companionVersion',
                     style: TextStyle(
                       fontSize: 9,
                       color: _soft,
@@ -864,19 +936,12 @@ class _ContentAlertsCard extends StatelessWidget {
   }
 
   Future<void> _startUpdate(BuildContext context) async {
-    final raw = model.availableApkUrl ?? model.availableVersionUrl;
-    final uri = raw == null ? null : Uri.tryParse(raw);
-    if (uri == null || uri.scheme != 'https') return;
-    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
+    final error = await model.downloadAndInstallUpdate();
     if (!context.mounted) return;
     ScaffoldMessenger.of(context).showSnackBar(
       SnackBar(
         content: Text(
-          opened
-              ? model.availableApkUrl != null
-                    ? 'APK indiriliyor. İndirme bitince Android kurulum onayını ver.'
-                    : 'GitHub sürüm sayfası açıldı. APK dosyasını indirip Android kurulum onayını ver.'
-              : 'İndirme bağlantısı açılamadı. Ağ bağlantını veya varsayılan tarayıcıyı kontrol et.',
+          error ?? 'APK indirildi ve Android kurulum onayı açıldı.',
         ),
       ),
     );
@@ -933,10 +998,12 @@ class _ContentAlertsCard extends StatelessWidget {
               Padding(
                 padding: const EdgeInsets.fromLTRB(16, 12, 16, 14),
                 child: FilledButton.icon(
-                  onPressed: () => _startUpdate(context),
+                  onPressed: model.downloadingUpdate ? null : () => _startUpdate(context),
                   icon: const Icon(Icons.system_update_alt_rounded),
                   label: Text(
-                    'v${model.availableVersion} GÜNCELLEMESİNİ İNDİR',
+                    model.downloadingUpdate
+                        ? 'GÜNCELLEME İNDİRİLİYOR'
+                        : 'v${model.availableVersion} GÜNCELLEMESİNİ İNDİR',
                   ),
                 ),
               ),
@@ -2241,7 +2308,7 @@ Future<void> _newBuild(
 void _about(BuildContext context) => showAboutDialog(
   context: context,
   applicationName: 'TD2 Loot Advisor Companion',
-  applicationVersion: '0.1.5-beta (build 7)',
+  applicationVersion: '$companionVersion-beta',
   applicationIcon: const Icon(Icons.hexagon_outlined, color: _orange, size: 34),
   children: [
     const Text(
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/lib/services/companion_release.dart
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
04148ca FEDERALTURK fix: companion version display and update permission flow
06f992c FEDERALTURK fix: download and install companion updates safely
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
7db5e31 FEDERALTURK release(mobile): prepare companion v0.1.5 beta
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/lib/services/companion_release.dart b/mobile/lib/services/companion_release.dart
index 8b794e5..90af820 100644
--- a/mobile/lib/services/companion_release.dart
+++ b/mobile/lib/services/companion_release.dart
@@ -4,13 +4,15 @@ import 'package:http/http.dart' as http;
 
 /// GitHub beta etiketi dört bileşene izin verir (ör. 0.1.4.1). Android'in
 /// package sürümü ise pubspec içinde üç bileşen + artan build numarasıdır.
-const companionVersion = '0.1.5';
+const companionVersion = '0.1.8';
+const updateCheckInterval = Duration(hours: 6);
 
 class CompanionRelease {
   const CompanionRelease({
     required this.version,
     required this.url,
     this.apkUrl,
+    this.sha256Url,
   });
 
   final String version;
@@ -19,6 +21,7 @@ class CompanionRelease {
   /// GitHub release içindeki imzalı Android APK'ya doğrudan HTTPS bağlantısı.
   /// Varlık yoksa uygulama güvenle release sayfasına geri dönebilir.
   final String? apkUrl;
+  final String? sha256Url;
 }
 
 /// GitHub'daki yalnız Companion ön-yayınlarını okur. Masaüstü `v9.x` yayınları
@@ -63,6 +66,7 @@ CompanionRelease? parseLatestCompanionRelease(dynamic decoded) {
       version: version,
       url: url,
       apkUrl: _findApkUrl(item['assets']),
+      sha256Url: _findSha256Url(item['assets']),
     );
     if (latest == null || isNewerVersion(candidate.version, latest.version)) {
       latest = candidate;
@@ -87,6 +91,17 @@ String? _findApkUrl(dynamic assets) {
   return null;
 }
 
+String? _findSha256Url(dynamic assets) {
+  if (assets is! List) return null;
+  for (final asset in assets) {
+    if (asset is! Map) continue;
+    final name = '${asset['name'] ?? ''}'.toLowerCase();
+    final url = '${asset['browser_download_url'] ?? ''}';
+    if (name == 'sha256sums.sha256' && _isSafeHttpsUrl(url)) return url;
+  }
+  return null;
+}
+
 bool _isSafeHttpsUrl(String value) {
   final uri = Uri.tryParse(value);
   return uri != null && uri.scheme == 'https' && uri.host.isNotEmpty;
@@ -102,6 +117,12 @@ bool isNewerVersion(String candidate, String installed) {
   return false;
 }
 
+bool isUpdateCheckDue(DateTime? lastCheck, {DateTime? now}) {
+  if (lastCheck == null) return true;
+  final current = now ?? DateTime.now();
+  return current.difference(lastCheck) >= updateCheckInterval;
+}
+
 bool _validVersion(String value) => _parts(value) != null;
 
 List<int>? _parts(String value) {
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/pubspec.lock
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
04148ca FEDERALTURK fix: companion version display and update permission flow
a021259 FEDERALTURK feat(mobile): refresh content and notify opted-in users
1c32976 FEDERALTURK feat(mobile): harden pairing and prepare device release
6237d1f FEDERALTURK Release 9.0.8: Android companion beta
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/pubspec.lock b/mobile/pubspec.lock
index 68a3b91..a75ffcd 100644
--- a/mobile/pubspec.lock
+++ b/mobile/pubspec.lock
@@ -66,7 +66,7 @@ packages:
     source: hosted
     version: "1.19.1"
   crypto:
-    dependency: transitive
+    dependency: "direct main"
     description:
       name: crypto
       sha256: e3626ae6270383c9e3a549f34c9e4cd26c09ae6a9adaab2bf4737a00340efdc4
@@ -417,7 +417,7 @@ packages:
     source: hosted
     version: "1.9.1"
   path_provider:
-    dependency: transitive
+    dependency: "direct main"
     description:
       name: path_provider
       sha256: a7f4874f987173da295a61c181b8ee71dab59b332a486b391babf26a1b884825
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/pubspec.yaml
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
04148ca FEDERALTURK fix: companion version display and update permission flow
06f992c FEDERALTURK fix: download and install companion updates safely
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
7db5e31 FEDERALTURK release(mobile): prepare companion v0.1.5 beta
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/pubspec.yaml b/mobile/pubspec.yaml
index cdf625f..2268a6d 100644
--- a/mobile/pubspec.yaml
+++ b/mobile/pubspec.yaml
@@ -16,7 +16,7 @@ publish_to: 'none' # Remove this line if you wish to publish to pub.dev
 # https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Articles/CoreFoundationKeys.html
 # In Windows, build-name is used as the major, minor, and patch parts
 # of the product and file versions while build-number is used as the build suffix.
-version: 0.1.5+7
+version: 0.1.8+10
 
 environment:
   sdk: ^3.13.7
@@ -35,6 +35,8 @@ dependencies:
   # Use with the CupertinoIcons class for iOS style icons.
   cupertino_icons: ^1.0.8
   http: ^1.6.0
+  crypto: ^3.0.6
+  path_provider: ^2.1.5
   shared_preferences: ^2.5.6
   url_launcher: ^6.3.3
   mobile_scanner: ^7.4.2
```

### C:/Users/PC/Desktop/Thedivision2program/mobile/test/companion_release_test.dart
Tür: Düzenleme; talep ilişkisi: Mobil sürüm ve güncelleme talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
961640c FEDERALTURK fix: satisfy companion analyzer formatting
06f992c FEDERALTURK fix: download and install companion updates safely
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
18cef04 FEDERALTURK feat(mobile): add one-tap companion APK update flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/mobile/test/companion_release_test.dart b/mobile/test/companion_release_test.dart
index 689c98c..66765ec 100644
--- a/mobile/test/companion_release_test.dart
+++ b/mobile/test/companion_release_test.dart
@@ -12,6 +12,13 @@ void main() {
     expect(isNewerVersion('beta', '0.1.4'), isFalse);
   });
 
+  test('update check is throttled but runs when no check exists', () {
+    final now = DateTime(2026, 11, 7, 12);
+    expect(isUpdateCheckDue(null, now: now), isTrue);
+    expect(isUpdateCheckDue(now.subtract(const Duration(hours: 5, minutes: 59)), now: now), isFalse);
+    expect(isUpdateCheckDue(now.subtract(const Duration(hours: 6)), now: now), isTrue);
+  });
+
   test('companion release selects the newest direct APK asset', () {
     final release = parseLatestCompanionRelease([
       {
@@ -28,7 +35,13 @@ void main() {
           },
           {
             'name': 'TD2LootAdvisor_Companion_0.1.4.1-beta.apk',
-            'browser_download_url': 'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.4.1-beta/TD2LootAdvisor_Companion_0.1.4.1-beta.apk',
+            'browser_download_url':
+                'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.4.1-beta/TD2LootAdvisor_Companion_0.1.4.1-beta.apk',
+          },
+          {
+            'name': 'SHA256SUMS.sha256',
+            'browser_download_url':
+                'https://github.com/FEDERALTURK/td2-loot-advisor/releases/download/companion-v0.1.4.1-beta/SHA256SUMS.sha256',
           },
         ],
       },
@@ -36,5 +49,6 @@ void main() {
 
     expect(release?.version, '0.1.4.1');
     expect(release?.apkUrl, endsWith('.apk'));
+    expect(release?.sha256Url, contains('SHA256SUMS.sha256'));
   });
 }
```

### C:/Users/PC/Desktop/Thedivision2program/ocr_lab.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/ocr_lab.py b/ocr_lab.py
new file mode 100644
index 0000000..4aea54c
--- /dev/null
+++ b/ocr_lab.py
@@ -0,0 +1,50 @@
+"""Deterministic OCR engine comparison helpers.
+
+The lab accepts already-created callables so tests do not need a display,
+network, model download, or a running game. Each callable returns the
+project's ``(text, box, confidence)`` line tuples.
+"""
+from difflib import SequenceMatcher
+from time import perf_counter
+
+
+def _text(lines):
+    return " ".join(str(row[0]).strip() for row in lines if row and str(row[0]).strip())
+
+
+def benchmark(image, engines):
+    """Run every named engine once and return comparable timing/quality data.
+
+    ``engines`` is a mapping of name -> callable(image). A failed optional
+    engine is reported as unavailable instead of hiding the other results.
+    """
+    results = {}
+    for name, reader in engines.items():
+        started = perf_counter()
+        try:
+            lines = list(reader(image) or [])
+            text = _text(lines)
+            confidence = [float(row[2]) for row in lines if len(row) >= 3]
+            results[name] = {
+                "available": True,
+                "elapsed_ms": round((perf_counter() - started) * 1000, 2),
+                "text": text,
+                "line_count": len(lines),
+                "mean_confidence": round(sum(confidence) / len(confidence), 4) if confidence else 0.0,
+            }
+        except Exception as exc:  # optional engine failure is data, not a lab crash
+            results[name] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
+    available = [v for v in results.values() if v.get("available")]
+    reference = ""
+    if available:
+        reference = max((v["text"] for v in available), key=len, default="")
+    for value in results.values():
+        if value.get("available"):
+            value["similarity_to_reference"] = round(SequenceMatcher(None, value["text"].lower(), reference.lower()).ratio(), 4)
+            value["review"] = value["mean_confidence"] < 0.68 or not value["text"].strip()
+    winner = max(
+        ((name, value) for name, value in results.items() if value.get("available")),
+        key=lambda pair: (pair[1].get("mean_confidence", 0), len(pair[1].get("text", "")), -pair[1].get("elapsed_ms", 1e9)),
+        default=(None, None),
+    )[0]
+    return {"engines": results, "winner": winner, "reference_text": reference}
```

### C:/Users/PC/Desktop/Thedivision2program/overlay.py
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
8213c97 FEDERALTURK Fix Windows in-place translation glyph rendering
be13091 FEDERALTURK Fix clipped Windows in-place translation text
eb577bd FEDERALTURK Fix Windows translation overlay and CI websocket timeout
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/overlay.py b/overlay.py
index af0c9fa..3b2955e 100644
--- a/overlay.py
+++ b/overlay.py
@@ -207,6 +207,7 @@ class InPlace:
             # glyph inside narrow source rectangles (dark box, no text).
             ww, hh = max(24, int(it["w"])), max(14, int(it["h"]))
             w = tk.Toplevel(self.root)
+            self._wins.append(w)
             w.overrideredirect(True)
             w.attributes("-topmost", True)
             # app._lt_overlay_window uses this to keep the box click-through
@@ -229,7 +230,6 @@ class InPlace:
             w.update_idletasks()
             if self.on_window:
                 self.on_window(w)
-            self._wins.append(w)
         self.win = self._wins[0] if self._wins else None
         return self.win
```

### C:/Users/PC/Desktop/Thedivision2program/review_queue.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/review_queue.py b/review_queue.py
new file mode 100644
index 0000000..cad9eff
--- /dev/null
+++ b/review_queue.py
@@ -0,0 +1,44 @@
+"""Local OCR review queue. It never authorizes destructive item actions."""
+import json
+import time
+import uuid
+from pathlib import Path
+
+
+def add(path, text, item, verdict, reason="low-confidence OCR"):
+    """Append a masked, review-only record and return its stable id."""
+    record = {
+        "id": uuid.uuid4().hex,
+        "created": int(time.time()),
+        "text": str(text or "")[:4000],
+        "item": dict(item or {}),
+        "verdict": "REVIEW",
+        "reason": reason,
+        "resolved": False,
+    }
+    record["item"].pop("_text", None)
+    target = Path(path)
+    target.parent.mkdir(parents=True, exist_ok=True)
+    # Autoscan can see the same blurred card repeatedly; keep one pending
+    # review entry for that text/name instead of growing the runtime log.
+    for previous in load(target)[-100:]:
+        if previous.get("text") == record["text"] and previous.get("item", {}).get("name") == record["item"].get("name"):
+            return previous["id"]
+    with target.open("a", encoding="utf-8") as stream:
+        stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
+    return record["id"]
+
+
+def load(path):
+    target = Path(path)
+    if not target.exists():
+        return []
+    rows = []
+    for line in target.read_text(encoding="utf-8").splitlines():
+        try:
+            row = json.loads(line)
+            if isinstance(row, dict) and not row.get("resolved"):
+                rows.append(row)
+        except (ValueError, TypeError):
+            continue
+    return rows
```

### C:/Users/PC/Desktop/Thedivision2program/scripts/overlay_health_check.bat
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/scripts/overlay_health_check.bat b/scripts/overlay_health_check.bat
new file mode 100644
index 0000000..da2785c
--- /dev/null
+++ b/scripts/overlay_health_check.bat
@@ -0,0 +1,13 @@
+@echo off
+setlocal
+cd /d "%~dp0.."
+set "TD2_REPORT=%TEMP%\td2-overlay-health-%RANDOM%-%RANDOM%.json"
+echo Yerel sentetik pencere testi basliyor. Oyun acik olmak zorunda degil.
+echo Test sirasinda pencereyi kapatmayin veya ustunu ortmeyin.
+py -3.13 -B app.py --translation-probe models/en-tr "%TD2_REPORT%"
+set "TD2_RESULT=%ERRORLEVEL%"
+echo Test cikis kodu: %TD2_RESULT%
+echo Rapor: %TD2_REPORT%
+if exist "%TD2_REPORT%" type "%TD2_REPORT%"
+pause
+exit /b %TD2_RESULT%
```

### C:/Users/PC/Desktop/Thedivision2program/scripts/ruflo_status.bat
Tür: Yeni; talep ilişkisi: Ruflo/ajan entegrasyonu talebi. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/scripts/ruflo_status.bat b/scripts/ruflo_status.bat
new file mode 100644
index 0000000..007bed3
--- /dev/null
+++ b/scripts/ruflo_status.bat
@@ -0,0 +1,8 @@
+@echo off
+cd /d "%~dp0.."
+echo Ruflo Node kontrolu:
+npx --yes ruflo@latest doctor --json -c node
+echo.
+echo MCP sunucusu stdio modunda baslatilabilir:
+echo npx --yes ruflo@latest mcp start
+pause
```

### C:/Users/PC/Desktop/Thedivision2program/target_planner.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/target_planner.py b/target_planner.py
new file mode 100644
index 0000000..0e2250a
--- /dev/null
+++ b/target_planner.py
@@ -0,0 +1,177 @@
+"""Faz 4: kişisel hedefler ile görev/satıcı/hedef-loot kaynaklarını eşleştirir.
+
+Bu modül yalnızca yerel veri planlaması yapar. Oyun belleğine veya oyun dosyalarına erişmez;
+eşleşme sonucu hiçbir zaman silme/kırma kararı üretmez.
+"""
+from __future__ import annotations
+
+import json
+import os
+import re
+import tempfile
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any, Iterable
+
+
+_SPACE = re.compile(r"\s+")
+_NONWORD = re.compile(r"[^a-z0-9çğıöşü]+", re.I)
+_CADENCE_MAX_AGE = {"daily": 36 * 3600, "weekly": 9 * 86400, "dated": 36 * 3600}
+
+
+def _norm(value: Any) -> str:
+    text = str(value or "").lower().replace("’", "'")
+    text = _NONWORD.sub(" ", text)
+    return _SPACE.sub(" ", text).strip()
+
+
+def _list(values: Any) -> list[str]:
+    if values is None:
+        return []
+    if isinstance(values, str):
+        values = [values]
+    return sorted({_norm(x) for x in values if _norm(x)})
+
+
+def normalize_target(record: dict[str, Any]) -> dict[str, Any]:
+    """Validate and normalize one user target record."""
+    if not isinstance(record, dict):
+        raise ValueError("target must be an object")
+    name = str(record.get("name") or "").strip()
+    if not name:
+        raise ValueError("target name is required")
+    slot = str(record.get("slot") or "").strip()
+    if not slot:
+        raise ValueError("target slot is required")
+    priority = str(record.get("priority") or "normal").lower()
+    if priority not in {"low", "normal", "high", "critical"}:
+        priority = "normal"
+    return {
+        "name": name,
+        "name_key": _norm(name),
+        "slot": slot,
+        "slot_key": _norm(slot),
+        "attributes": _list(record.get("attributes")),
+        "talents": _list(record.get("talents")),
+        "prototype_augments": _list(record.get("prototype_augments")),
+        "priority": priority,
+        "enabled": bool(record.get("enabled", True)),
+        "notes": str(record.get("notes") or "").strip()[:500],
+    }
+
+
+def normalize_source(record: dict[str, Any]) -> dict[str, Any]:
+    """Normalize a task/vendor/target-loot source row without trusting its freshness."""
+    if not isinstance(record, dict):
+        return {"source": "unknown", "name": "", "name_key": "", "attributes": [], "talents": []}
+    name = str(record.get("name") or record.get("name_en") or record.get("item") or record.get("title") or "").strip()
+    cadence = str(record.get("cadence") or record.get("period") or "unknown").lower()
+    if cadence not in _CADENCE_MAX_AGE:
+        cadence = "unknown"
+    updated = record.get("updated_at", record.get("fetched", 0))
+    try:
+        updated = float(updated or 0)
+    except (TypeError, ValueError):
+        updated = 0.0
+    return {
+        "source": str(record.get("source") or "unknown"),
+        "name": name,
+        "name_key": _norm(name),
+        "slot": str(record.get("slot") or record.get("slot_en") or record.get("slot_key") or ""),
+        "slot_key": _norm(record.get("slot") or record.get("slot_en") or record.get("slot_key") or ""),
+        "attributes": _list(record.get("attributes") or record.get("attrs")),
+        "talents": _list(record.get("talents")),
+        "prototype_augments": _list(record.get("prototype_augments")),
+        "updated_at": updated,
+        "cadence": cadence,
+        "confidence": float(record.get("confidence", 1.0) or 0.0),
+        "raw": record,
+    }
+
+
+def _is_stale(source: dict[str, Any], now: datetime) -> bool:
+    updated = source.get("updated_at", 0)
+    if not updated:
+        return True
+    max_age = _CADENCE_MAX_AGE.get(source.get("cadence"), 24 * 3600)
+    return now.timestamp() - float(updated) > max_age
+
+
+def _match_score(target: dict[str, Any], source: dict[str, Any]) -> tuple[int, list[str]]:
+    reasons: list[str] = []
+    if target["name_key"] != source["name_key"]:
+        return 0, reasons
+    score = 50
+    reasons.append("name")
+    if target["slot_key"] and target["slot_key"] == source["slot_key"]:
+        score += 20
+        reasons.append("slot")
+    elif target["slot_key"] and source["slot_key"]:
+        return 0, reasons
+    for field, weight in (("attributes", 15), ("talents", 10), ("prototype_augments", 10)):
+        wanted = set(target[field])
+        if wanted and wanted.issubset(set(source[field])):
+            score += weight
+            reasons.append(field)
+        elif wanted:
+            return 0, reasons
+    return min(score, 100), reasons
+
+
+def match_targets(targets: Iterable[dict[str, Any]], sources: Iterable[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
+    now = now or datetime.now(timezone.utc)
+    rows = [normalize_source(x) for x in sources]
+    output: list[dict[str, Any]] = []
+    for raw_target in targets:
+        target = normalize_target(raw_target)
+        if not target["enabled"]:
+            continue
+        matches = []
+        for source in rows:
+            score, reasons = _match_score(target, source)
+            if score:
+                stale = _is_stale(source, now)
+                review = stale or source["confidence"] < 0.75
+                matches.append({"target": target, "source": source["source"], "source_record": source["raw"],
+                                "score": score, "reasons": reasons, "stale": stale,
+                                "status": "REVIEW" if review else "MATCH"})
+        if matches:
+            matches.sort(key=lambda x: (x["status"] != "MATCH", -x["score"]))
+            output.extend(matches)
+        else:
+            output.append({"target": target, "source": None, "source_record": None, "score": 0,
+                           "reasons": [], "stale": False, "status": "NO_MATCH"})
+    return output
+
+
+def load_targets(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
+    try:
+        with open(path, encoding="utf-8") as handle:
+            data = json.load(handle)
+    except (OSError, ValueError):
+        return []
+    values = data.get("targets", data) if isinstance(data, dict) else data
+    if not isinstance(values, list):
+        return []
+    out = []
+    for row in values:
+        try:
+            out.append(normalize_target(row))
+        except ValueError:
+            continue
+    return out
+
+
+def save_targets(path: str | os.PathLike[str], targets: Iterable[dict[str, Any]]) -> None:
+    destination = Path(path)
+    destination.parent.mkdir(parents=True, exist_ok=True)
+    payload = {"version": 1, "targets": [normalize_target(x) for x in targets]}
+    fd, temp_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=str(destination.parent))
+    try:
+        with os.fdopen(fd, "w", encoding="utf-8") as handle:
+            json.dump(payload, handle, ensure_ascii=False, indent=2)
+            handle.write("\n")
+        os.replace(temp_name, destination)
+    finally:
+        if os.path.exists(temp_name):
+            os.unlink(temp_name)
```

### C:/Users/PC/Desktop/Thedivision2program/tests/test_decision_center.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/tests/test_decision_center.py b/tests/test_decision_center.py
new file mode 100644
index 0000000..06c359e
--- /dev/null
+++ b/tests/test_decision_center.py
@@ -0,0 +1,31 @@
+import sys
+import unittest
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
+
+import decision_center
+import target_planner
+
+
+class DecisionCenterTests(unittest.TestCase):
+    def test_protected_named_item_is_review_even_on_exact_target(self):
+        target = target_planner.normalize_target({"name": "Test Named", "slot": "Chest"})
+        rows = decision_center.compare_item_to_targets(
+            {"name": "Test Named", "slot": "Chest", "rarity": ["NAMED"], "confidence": 0.99},
+            [target],
+        )
+        self.assertEqual(rows[0]["recommendation"], "REVIEW")
+        self.assertTrue(rows[0]["protected"])
+
+    def test_normal_item_exact_target_is_keep(self):
+        target = target_planner.normalize_target({"name": "Test Chest", "slot": "Chest"})
+        rows = decision_center.compare_item_to_targets(
+            {"name": "Test Chest", "slot": "Chest", "rarity": ["HIGH-END"], "confidence": 0.99},
+            [target],
+        )
+        self.assertEqual(rows[0]["recommendation"], "KEEP")
+
+
+if __name__ == "__main__":
+    unittest.main()
```

### C:/Users/PC/Desktop/Thedivision2program/tests/test_game_runtime.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/tests/test_game_runtime.py b/tests/test_game_runtime.py
new file mode 100644
index 0000000..53645c8
--- /dev/null
+++ b/tests/test_game_runtime.py
@@ -0,0 +1,63 @@
+"""Faz 1 oyun yardımcısı çalışma planı: yalnız pencere odağına göre karar verir."""
+from pathlib import Path
+import queue
+import sys
+import unittest
+from types import SimpleNamespace
+from unittest.mock import Mock, patch
+
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
+import game_runtime
+import app
+
+
+class RuntimePlanTests(unittest.TestCase):
+    def test_game_focus_keeps_passive_helpers_available(self):
+        plan = game_runtime.plan({"only_game_active": True}, game_focused=True)
+        self.assertEqual(plan.state, "game_focus")
+        self.assertTrue(plan.passive_capture)
+        self.assertTrue(plan.passive_translation)
+        self.assertEqual(plan.wait_s, 0)
+
+    def test_background_focus_pauses_passive_helpers_when_requested(self):
+        plan = game_runtime.plan({"only_game_active": True}, game_focused=False)
+        self.assertEqual(plan.state, "background")
+        self.assertFalse(plan.passive_capture)
+        self.assertFalse(plan.passive_translation)
+        self.assertGreaterEqual(plan.wait_s, 1)
+
+    def test_desktop_mode_preserves_existing_opt_out_behavior(self):
+        plan = game_runtime.plan({"only_game_active": False}, game_focused=False)
+        self.assertEqual(plan.state, "desktop")
+        self.assertTrue(plan.passive_capture)
+        self.assertTrue(plan.passive_translation)
+
+    def test_hidden_game_focus_is_reported_without_changing_capture_policy(self):
+        plan = game_runtime.plan({"only_game_active": True}, game_focused=True, app_hidden=True)
+        self.assertEqual(plan.state, "game_focus_tray")
+        self.assertTrue(plan.passive_capture)
+        self.assertTrue(plan.passive_translation)
+
+    def test_background_autoscan_waits_without_capturing_the_desktop(self):
+        class Stop:
+            def __init__(self): self.stopped, self.waits = False, []
+            def is_set(self): return self.stopped
+            def wait(self, seconds): self.waits.append(seconds); self.stopped = True; return True
+
+        stop = Stop()
+        obj = SimpleNamespace(
+            cfg={"settings": {"only_game_active": True}},
+            _policy=lambda: SimpleNamespace(scan_poll_s=0.1),
+            scan_area=Mock(return_value={"left": 0, "top": 0, "width": 10, "height": 10}),
+            results=queue.Queue(),
+            last_err="",
+        )
+        with patch.object(app, "game_active", return_value=False), \
+                patch.object(app.capture, "default", side_effect=AssertionError("desktop capture must not run")):
+            app.App._auto_loop(obj, stop)
+        self.assertEqual(stop.waits, [1.5])
+
+
+if __name__ == "__main__":
+    unittest.main()
```

### C:/Users/PC/Desktop/Thedivision2program/tests/test_inplace_anchors.py
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
f86c2e9 FEDERALTURK Fix Panel overlay text rendering on Windows
8213c97 FEDERALTURK Fix Windows in-place translation glyph rendering
be13091 FEDERALTURK Fix clipped Windows in-place translation text
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/tests/test_inplace_anchors.py b/tests/test_inplace_anchors.py
index 7372f33..465390e 100644
--- a/tests/test_inplace_anchors.py
+++ b/tests/test_inplace_anchors.py
@@ -18,6 +18,26 @@ def measure(pt):
 
 
 class InplaceTests(unittest.TestCase):
+    def test_callback_failure_does_not_leave_untracked_window(self):
+        import tkinter as tk
+        root = tk.Tk(); root.withdraw()
+        def fail(win):
+            raise RuntimeError("native hook unavailable")
+        renderer = overlay.InPlace(root, {"bg": "black", "fg": "white", "accent": "orange"},
+                                   on_window=fail, native_boxes=True)
+        try:
+            with self.assertRaises(RuntimeError):
+                renderer.show([{"x": 8, "y": 8, "w": 160, "h": 42, "pt": 10,
+                                "lines": ["Test"], "kind": "text"}],
+                              {"width": 220, "height": 90, "left": 0, "top": 0})
+            self.assertEqual(len(renderer._wins), 1)
+            win = renderer._wins[0]
+            renderer.hide()
+            self.assertFalse(win.winfo_exists())
+        finally:
+            renderer.hide()
+            root.destroy()
+
     def test_project_labels_remain_separate_source_rectangles(self):
         lines = [("Season Pass Project", (20, 20, 240, 40), .99),
                  ("DCD Headquarters", (20, 44, 210, 64), .99),
```

### C:/Users/PC/Desktop/Thedivision2program/tests/test_ocr_lab.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/tests/test_ocr_lab.py b/tests/test_ocr_lab.py
new file mode 100644
index 0000000..1273815
--- /dev/null
+++ b/tests/test_ocr_lab.py
@@ -0,0 +1,35 @@
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
+import ocr_lab
+import review_queue
+
+
+class OcrLabTests(unittest.TestCase):
+    def test_compares_engines_and_marks_low_confidence_for_review(self):
+        image = object()
+        report = ocr_lab.benchmark(image, {
+            "rapidocr": lambda _: [("Rewards", (0, 0, 1, 1), .93)],
+            "windows": lambda _: [("Rew ards", (0, 0, 1, 1), .42)],
+            "tesseract": lambda _: (_ for _ in ()).throw(RuntimeError("not installed")),
+        })
+        self.assertEqual(report["winner"], "rapidocr")
+        self.assertFalse(report["engines"]["rapidocr"]["review"])
+        self.assertTrue(report["engines"]["windows"]["review"])
+        self.assertFalse(report["engines"]["tesseract"]["available"])
+
+    def test_review_queue_is_append_only_and_forces_review(self):
+        with tempfile.TemporaryDirectory() as directory:
+            path = Path(directory) / "review.jsonl"
+            ident = review_queue.add(path, "blurred card", {"name": "?", "_text": "secret"}, "DISMANTLE")
+            rows = review_queue.load(path)
+            self.assertEqual(rows[0]["id"], ident)
+            self.assertEqual(rows[0]["verdict"], "REVIEW")
+            self.assertNotIn("_text", rows[0]["item"])
+
+
+if __name__ == "__main__":
+    unittest.main()
```

### C:/Users/PC/Desktop/Thedivision2program/tests/test_target_planner.py
Tür: Yeni; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/tests/test_target_planner.py b/tests/test_target_planner.py
new file mode 100644
index 0000000..5c81da9
--- /dev/null
+++ b/tests/test_target_planner.py
@@ -0,0 +1,55 @@
+import json
+import sys
+import unittest
+from pathlib import Path
+from datetime import datetime, timezone, timedelta
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
+import target_planner as tp
+
+
+class TargetPlannerTests(unittest.TestCase):
+    def test_normalize_target_preserves_prototype_augment(self):
+        target = tp.normalize_target({
+        "name": "St. Elmo's Engine",
+        "slot": "Weapon",
+        "attributes": ["Weapon Damage"],
+        "talents": ["Eagle's Strike"],
+        "prototype_augments": ["Shock Ammo"],
+    })
+        self.assertEqual(target["name_key"], "st elmo s engine")
+        self.assertEqual(target["attributes"], ["weapon damage"])
+        self.assertEqual(target["prototype_augments"], ["shock ammo"])
+
+
+    def test_match_exact_source_and_classify_stale_as_review(self):
+        now = datetime(2026, 11, 7, tzinfo=timezone.utc)
+        target = tp.normalize_target({"name": "St. Elmo's Engine", "slot": "Weapon", "attributes": ["Weapon Damage"]})
+        fresh = {"source": "target_loot", "name": "St. Elmo's Engine", "slot": "Weapon",
+                 "attributes": ["Weapon Damage"], "updated_at": now.timestamp(), "cadence": "daily"}
+        stale = dict(fresh, updated_at=(now - timedelta(days=3)).timestamp())
+        result = tp.match_targets([target], [fresh, stale], now=now)
+        self.assertEqual(result[0]["status"], "MATCH")
+        self.assertEqual(result[0]["source"], "target_loot")
+        self.assertEqual(result[1]["status"], "REVIEW")
+        self.assertTrue(result[1]["stale"])
+
+
+    def test_unmatched_target_is_no_match_and_roundtrip(self):
+        import tempfile
+        with tempfile.TemporaryDirectory() as directory:
+            path = Path(directory) / "targets.json"
+            target = tp.normalize_target({"name": "Test Item", "slot": "Chest", "priority": "high"})
+            tp.save_targets(path, [target])
+            loaded = tp.load_targets(path)
+            self.assertEqual(loaded[0]["name"], "Test Item")
+            self.assertEqual(tp.match_targets(loaded, [], now=datetime.now(timezone.utc))[0]["status"], "NO_MATCH")
+
+
+    def test_invalid_target_rejected(self):
+        with self.assertRaises(ValueError):
+            tp.normalize_target({"name": "", "slot": "Chest"})
+
+
+if __name__ == "__main__":
+    unittest.main()
```

### C:/Users/PC/Desktop/Thedivision2program/tests/test_translation_controls.py
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
acf9058 FEDERALTURK Fix translation start state collision and automatic job starvation
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/tests/test_translation_controls.py b/tests/test_translation_controls.py
index f8450e1..68d9b4b 100644
--- a/tests/test_translation_controls.py
+++ b/tests/test_translation_controls.py
@@ -10,6 +10,41 @@ import app
 
 
 class TranslationControlsTests(unittest.TestCase):
+    def test_render_exception_preserves_history_and_uses_panel(self):
+        obj = app.App.__new__(app.App)
+        obj.cfg = {"settings": {"tr_mode": "inplace"}}
+        for name in ("_lt_log", "_lt_status", "_lt_hist_fill", "_lt_after", "_lt_hide", "_lt_panel_fallback"):
+            setattr(obj, name, Mock())
+        obj._lt_show_inplace = Mock(side_effect=RuntimeError("draw failed"))
+        pairs = [("Rewards", "Ödüller", (0, 0, 100, 40))]
+        with self.assertLogs("td2", level="ERROR"):
+            obj._lt_show(pairs, {"width": 100, "height": 100}, 0)
+        self.assertEqual(obj.lt_hist, [("Rewards", "Ödüller")])
+        obj._lt_panel_fallback.assert_called_once_with(pairs)
+
+    def test_panel_fallback_closes_overlay_and_preserves_translation(self):
+        obj = app.App.__new__(app.App)
+        obj._lt_hide = Mock()
+        obj._lt_status = Mock()
+        obj.lt_out = Mock()
+        obj._lt_panel_fallback([("Rewards", "Ödüller", (0, 0, 100, 40))])
+        obj._lt_hide.assert_called_once()
+        self.assertEqual(obj.lt_out.config.call_args.kwargs["text"], "Ödüller")
+
+    def test_empty_layout_uses_panel_without_another_overlay(self):
+        obj = app.App.__new__(app.App)
+        obj.root = Mock()
+        obj.cfg = {"settings": {}}
+        obj.lt_style = Mock(return_value={})
+        obj._lt_panel_fallback = Mock()
+        pairs = [("Rewards", "Ödüller", (0, 0, 100, 40))]
+        with patch.object(app.overlay, "InPlace") as renderer, \
+             patch.object(app.overlay, "layout", return_value=[]):
+            obj._lt_show_inplace(pairs, {"width": 100, "height": 100})
+            renderer.return_value.hide.assert_called_once()
+            renderer.return_value.show.assert_not_called()
+        obj._lt_panel_fallback.assert_called_once_with(pairs)
+
     def test_building_statistics_does_not_create_a_speech_session(self):
         obj = app.App.__new__(app.App)
         obj.tabs = {"stats": Mock()}
```

### C:/Users/PC/Desktop/Thedivision2program/translation_probe.py
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
a5cae82 Claude 9.1.5.19: fix webbrowser/except-closure crashes, clean dead code, document mx data license scope
acf9058 FEDERALTURK Fix translation start state collision and automatic job starvation
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/translation_probe.py b/translation_probe.py
index 70961a6..ec4d04d 100644
--- a/translation_probe.py
+++ b/translation_probe.py
@@ -7,12 +7,42 @@ import json
 import queue
 import time
 from pathlib import Path
-from PIL import Image, ImageDraw, ImageFont
+from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageGrab, ImageChops, ImageStat
+
+
+def inspect_render(root, renderer):
+    """Measure actual glyph pixels as well as Tk items; capture exclusion must be off."""
+    root.update()
+    time.sleep(.15)
+    root.update()
+    windows = renderer._wins or ([renderer.win] if renderer.win else [])
+    reports = []
+    for win in windows:
+        canvases = [w for w in win.winfo_children() if w.winfo_class() == "Canvas"]
+        count = bright = 0
+        for canvas in canvases:
+            for item in canvas.find_all():
+                if canvas.type(item) != "text" or not canvas.itemcget(item, "text").strip():
+                    continue
+                count += 1
+                x0, y0, x1, y1 = canvas.bbox(item)
+                x0, y0 = max(0, x0), max(0, y0)
+                x1, y1 = min(canvas.winfo_width(), x1), min(canvas.winfo_height(), y1)
+                if x1 <= x0 or y1 <= y0:
+                    continue
+                x, y = canvas.winfo_rootx(), canvas.winfo_rooty()
+                shot = ImageGrab.grab(bbox=(x+x0, y+y0, x+x1, y+y1)).convert("RGB")
+                bright += sum(r > 185 and g > 185 and b > 185 for r, g, b in shot.getdata())
+        reports.append({"text_items": count, "bright_glyph_pixels": bright,
+                        "visible": bool(count and bright > 40)})
+    return {"ok": bool(reports) and all(r["visible"] for r in reports), "windows": reports}
 
 
 def run(app, model_dir, output):
     root = None
-    result = {"ok": False, "steps": []}
+    result = {"ok": False, "steps": [], "checks": {},
+              "limits": ["Synthetic desktop only; no game/DX12 verification",
+                         "Physical mouse pass-through and monitor DPI change require interactive validation"]}
     try:
         app.i18n.init(app.BUNDLE)
         app.i18n.set_language("tr")
@@ -48,7 +78,20 @@ def run(app, model_dir, output):
         card = Image.new("RGB", (900, 180), "#172028")
         font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
         ImageDraw.Draw(card).text((25, 50), "Agent, move to the safe house.", fill="white", font=font)
-        area = {"left": 40, "top": 40, "width": 900, "height": 180}
+        source = app.tk.Toplevel(root)
+        source.geometry("900x180+40+40")
+        source.overrideredirect(True)
+        source.attributes("-topmost", True)
+        photo = ImageTk.PhotoImage(card, master=root)
+        app.tk.Label(source, image=photo, bd=0).pack()
+        root.update(); time.sleep(.15); root.update()
+        area = {"left": source.winfo_rootx(), "top": source.winfo_rooty(), "width": 900, "height": 180}
+        card = app.capture.Grabber().grab(area)
+        result["checks"]["capture"] = {"ok": card.size == (900, 180)}
+        lines = app.OCR.lines(card)
+        result["checks"]["ocr"] = {"ok": any("agent" in line[0].lower() for line in lines),
+                                     "line_count": len(lines)}
+        assert result["checks"]["ocr"]["ok"], "Synthetic window OCR failed"
         t0 = time.monotonic()
         obj._lt_run(card, area, force=True)
         assert obj._translation_jobs.wait_idle(120), "Translation timed out"
@@ -61,13 +104,51 @@ def run(app, model_dir, output):
         en, tr = obj.lt_hist[-1]
         assert "agent" in en.lower() and tr != en and "ajan" in tr.lower(), (en, tr)
         result.update(english=en, turkish=tr, elapsed_ms=round((time.monotonic()-t0)*1000))
-        result["steps"].append("real RapidOCR + installed OPUS-MT + visible overlay")
+        result["checks"]["translation"] = {"ok": True}
+        result["steps"].append("captured synthetic window + RapidOCR + installed OPUS-MT")
         obj._lt_hide()
+        # Inspect pixels before capture exclusion; otherwise a working excluded
+        # overlay would correctly be absent from the screenshot.
+        obj._lt_overlay_window = app.click_through
+        foreground = app.ctypes.windll.user32.GetForegroundWindow() if app.os.name == "nt" else None
         obj._lt_show([(en, tr, (25, 50, 650, 90))], area, 0, force_mode="inplace")
         root.update_idletasks()
         assert obj._lt_win and obj._lt_win.winfo_exists(), "In-place overlay missing"
+        result["checks"]["render"] = inspect_render(root, obj._lt_inplace)
+        assert result["checks"]["render"]["ok"], "Overlay exists but glyph pixels are missing"
+        windows = obj._lt_inplace._wins or [obj._lt_win]
+        result["checks"]["coordinates"] = {"ok": all(
+            area["left"] <= w.winfo_rootx() < area["left"] + area["width"] and
+            area["top"] <= w.winfo_rooty() < area["top"] + area["height"] for w in windows)}
+        assert result["checks"]["coordinates"]["ok"], "Overlay outside synthetic source"
+        if foreground is not None:
+            result["checks"]["focus"] = {"ok": foreground == app.ctypes.windll.user32.GetForegroundWindow()}
+            flags = []
+            for win in windows:
+                hwnd = app.ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
+                flags.append(app.ctypes.windll.user32.GetWindowLongW(hwnd, -20))
+            result["checks"]["click_through_flags"] = {"ok": all(f & 0x08000020 == 0x08000020 for f in flags)}
+            excluded = all(app.exclude_from_capture(win, "probe") for win in windows)
+            root.update(); time.sleep(.15)
+            recaptured = app.capture.Grabber().grab(area)
+            difference = max(ImageStat.Stat(ImageChops.difference(card, recaptured)).mean)
+            result["checks"]["capture_exclusion"] = {"ok": excluded and difference < 2,
+                                                       "mean_difference": round(difference, 3)}
+            app.CAPTURE_MASK.pop("probe", None)
+        obj._lt_hide()
+        scaling = root.tk.call("tk", "scaling")
+        scaling_checks = []
+        try:
+            for value in (1.0, 1.5, 2.0):
+                root.tk.call("tk", "scaling", value)
+                obj._lt_show([(en, tr, (25, 50, 650, 110))], area, 0, force_mode="inplace")
+                scaling_checks.append({"tk_scaling": value, **inspect_render(root, obj._lt_inplace)})
+                obj._lt_hide()
+        finally:
+            root.tk.call("tk", "scaling", scaling)
+        result["checks"]["font_scaling"] = {"ok": all(c["ok"] for c in scaling_checks), "samples": scaling_checks}
         result["steps"].append("in-place overlay")
-        result["ok"] = True
+        result["ok"] = all(check["ok"] for check in result["checks"].values())
     except Exception:
         import traceback
         result["error"] = traceback.format_exc()
```

### C:/Users/PC/Desktop/Thedivision2program/updater.py
Tür: Düzenleme; talep ilişkisi: Faz 1–5 PC geliştirme ve yayın talepleri. [Doğrulandı]
Son dosya geçmişi aşağıdadır; yazar adı gerçek oturum sahipliğini tek başına kanıtlamaz. [Doğrulandı]
```text
c2d14f6 FEDERALTURK feat: add phase five decision and companion release flow
9c8eabc FEDERALTURK Fix version history listing and rollback controls
7a0818e FEDERALTURK Add version history and explicit rollback
9f6910a FEDERALTURK Allow beta installer updates
```
Tam net değişiklik aşağıdadır. [Doğrulandı]
```diff
diff --git a/updater.py b/updater.py
index c2f84fa..33f99ad 100644
--- a/updater.py
+++ b/updater.py
@@ -35,7 +35,15 @@ SOURCE_ALLOW = [r"[^/]+\.py", r"lang/[^/]+\.json", r"meta/(game_data|meta_builds
                 r"scripts/[^/]+", r"icon/[^/]+", r"server/[^/]+", r"tests/[^/]+(/[^/]+)?",
                 r"requirements[^/]*\.txt", r"README[^/]*\.md", r"LICENSE"]
 # Hiçbir koşulda yazılmaz (beyaz listeye uysa bile)
-NEVER = {"builds.json", "stash.json", "progress.json", "tasks.json", "loot_log.csv", "drop_queue.json", "learned_library.json"}
+# Kullanıcıya/cihaza ait durum verileri kaynak güncellemesinde hiçbir koşulda
+# değiştirilemez. SOURCE_ALLOW bugün bu kök JSON dosyalarının çoğunu zaten
+# kapsamıyor; yine de bu liste savunma katmanıdır ve ileride izin listesi
+# genişletilirse kişisel oturum/öğrenilmiş ekran verisini korur.
+NEVER = {
+    "builds.json", "stash.json", "progress.json", "tasks.json", "loot_log.csv",
+    "drop_queue.json", "learned_library.json", "sessions.json", "screen_states.json",
+    "tasks_sent.json", "verdict_feedback.json", "verdict_feedback.json.tmp",
+}
 
 
 def parse_version(v):
```

## 4. MİMARİ VE TASARIM KARARLARI
Mobil kontrol GitHub Releases listesinde companion-v etiketlerini seçer; masaüstü v9 etiketleri ayrı kalır; bu ayrım yanlış platform paketinin sunulmasını önlemek için kullanıldı. [Doğrulandı]
Tarayıcı açma yerine Dart HTTP indirme, crypto SHA256, uygulama destek klasörü ve Kotlin MethodChannel/FileProvider kurulum intent'i seçildi; kullanıcı tek düğmeyle indirme ve kurulumu başlatmak istedi. [Doğrulandı]
Android kurulum sonucunu takip eden bir sonuç kanalı eklenmedi; intent açılması başarılı kurulum anlamına gelmez. [Doğrulandı]
İlk SHA256 uygulaması checksum yokken devam ediyordu; son sürümde doğrulama bilgisi yok/geçersizse işlem durduruldu. [Doğrulandı]
Altı saat sınırlaması korunurken load içinden force:true kullanıldı; tekrar açılışta kontrolün atlanması kullanıcı şikâyetiyle çeliştiği için değiştirildi. [Doğrulandı]
Sürüm UI ve Hakkında için companionVersion'a bağlandı ancak pubspec hâlâ ayrı kaynak olduğundan iki değer arasında otomatik garanti yoktur. [Doğrulandı]
PC runtime politikası oyun odağı yokken pasif işleri bekletir; bu bir Windows servisi veya oyun motoru değişimi değildir. [Doğrulandı]
Overlay başarısızlığında başka boş pencere açmak yerine çeviri paneline düşme ve erken pencere kaydı seçildi; amaç hata halinde açık kalan kutuları azaltmaktır. [Doğrulandı]
Hedef planlayıcı saf veri eşleştirme modülü, karar merkezi ise KEEP/REVIEW katmanı olarak ayrıldı; oyun verisine yazmaz ve dismantle üretmez. [Doğrulandı]
Alternatif mimarilerin kapsamlı benchmark ile karşılaştırıldığına dair bu oturumda kanıt yoktur. [Test edilmedi]

## 5. BAĞIMLILIKLAR
mobile/pubspec.yaml dosyasına crypto ^3.0.6 ve path_provider ^2.1.5 doğrudan bağımlılık olarak eklendi; lock dosyasında mevcut çözümler sırasıyla 3.0.8 ve 2.1.6 olup transitive yerine direct main oldu. [Doğrulandı]
crypto APK hash hesabı, path_provider uygulama destek dizini için kullanılır. [Doğrulandı]
Android build.gradle.kts içine androidx.core:core:1.13.1 FileProvider için eklendi. [Doğrulandı]
Bu aralıkta requirements.txt veya package.json değişikliği yoktur; firebase ve flutter_local_notifications bu aralıktan önce mevcuttu. [Doğrulandı]
Bu paketlerin lisans metinleri ve güncel güvenlik duyuruları bağımsız incelenmedi; lisans güvenliği veya zafiyetsizlik iddiası yoktur. [Test edilmedi]
CI Flutter 3.47.8 kullanır; güncel paket uyarıları analiz çıktısında vardı, sırf yeni sürüm mevcut diye bağımlılıklar yükseltilmedi. [Doğrulandı]

## 6. TEST VE DOĞRULAMA — GERÇEK SONUÇLAR
Yerel mobile çalışma dizininde aşağıdaki komutlar önceki yayın turunda gerçekten çalıştı ve analiz temiz, dört test başarılı sonucunu verdi. [Doğrulandı]
```powershell
& C:/Users/PC/tools/flutter/bin/flutter.bat analyze
& C:/Users/PC/tools/flutter/bin/flutter.bat test
& C:/Users/PC/tools/flutter/bin/flutter.bat test test/companion_release_test.dart
```
Odaklı test üç senaryoyu, tüm test komutu bunlara ek olarak ilk Flutter frame/splash testini geçirdi; gerçek indirme, native izin, imza veya kurulum bu dört testin kapsamında değildir. [Doğrulandı]
Test sonuç mesajları “No issues found!” ve “All tests passed!” idi. [Doğrulandı]
İlk iki 0.1.7 CI denemesi flutter analyze aşamasında başarısız oldu; 42346877061 run / 128326441930 job logunda gerçek hata aşağıdaki gibi okundu. [Doğrulandı]
```text
info • Use the '??' operator rather than '?:' when testing for 'null'. Try rewriting the code to use '??' • lib/main.dart:941:11 • prefer_if_null_operators
1 issue found. (ran in 6.3s)
Process completed with exit code 1.
```
961640c import/format değişikliği kök nedeni çözmedi; d9a6179 içindeki error ?? mesaj değişikliği bu lint'i giderdi. [Doğrulandı]
Yetkisiz REST log isteği 403 döndü; bağlı GitHub fetch_workflow_job_logs aracıyla log sonradan okundu; uydurma job ID ile bir hatalı araç denemesi 404 döndü ve ardından run jobs üzerinden gerçek ID alındı. [Doğrulandı]
0.1.7 başarılı run: https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/42347086703; 0.1.8 başarılı run: https://github.com/FEDERALTURK/td2-loot-advisor/actions/runs/42384323013; analyze, test, build apk, artifact ve publish başarıları araç çıktılarında görüldü. [Doğrulandı]
0.1.7 etiketi yayın oluşmadan iki kez silinip düzeltme commit'ine yeniden oluşturuldu; sürüm geçmişi inceleyen geliştirici eski başarısız run'ları bu nedenle farklı SHA'larda görecektir. [Doğrulandı]
PC test dosyalarının eklenmesi tam diff ile kanıtlıdır; bu rapor turunda PC testleri tekrar çalıştırılmadı ve yalnız dosya varlığına dayanarak PASS yazılmadı. [Test edilmedi]
ADB komutu aşağıdaki gibi çalıştırıldı ve bağlı cihaz listesi boş geldi. [Doğrulandı]
```powershell
& C:/Users/PC/tools/android-sdk/platform-tools/adb.exe devices
```
GPU, canlı OCR, oyun overlay, telefon yükseltme, iOS, mağaza kurulumu, bildirimden kurulum ve offline/ağ kesintisi senaryoları uçtan uca doğrulanmadı. [Test edilmedi]

## 7. BİLİNEN SORUNLAR, YARIM KALAN İŞLER, ŞÜPHELİ NOKTALAR
P0: GitHub beta release debug signingConfig kullanıyor; build-mobile workflow kalıcı anahtar yüklemiyor; bu tasarım eski APK üstüne güncellemeyi engelleyebilecek imza sürekliliği riski taşır. [Doğrulandı]
Kurulu telefonun eski ve yeni sertifikalarının gerçekten farklı olduğu ölçülmedi; kullanıcıdaki kurulum sorununun kesin nedeni olarak sunulamaz. [Test edilmedi]
P1: APK getApplicationSupportDirectory içine yazılırken FileProvider yalnız files-path kullanıyor; gerçek Android path_provider dizini ile provider kökünün uyumu cihazda kontrol edilmelidir. [Test edilmedi]
P1: İzin verilince otomatik kaldığı yerden kurulum devam etmiyor; kullanıcı geri dönüp yeniden düğmeye basıyor ve indirme yeniden yapılıyor. [Doğrulandı]
P1: İndirme tüm APK'yı response.bodyBytes olarak RAM'de tutuyor; akışlı disk indirmesi, iptal, kaldığı yerden sürdürme ve gerçek ilerleme ölçümü yok; updateProgress yalnız sıfıra atanıyor. [Doğrulandı]
P1: checkForUpdate hataları sessiz yakalanıyor, HTTP başarısızlığı kullanıcıya açıklanmıyor; açılıştaki kontrol içerik refresh tamamlandıktan sonra başlıyor. [Doğrulandı]
P1: Arka planda uygulama kapalıyken zamanlanmış güncelleme hizmeti bu değişiklikte eklenmedi; LocalAlerts bildirim tıklamasını kurulum eylemine bağlayan callback içermiyor. [Doğrulandı]
P1: Asset URL kontrolü herhangi bir HTTPS hostunu kabul ediyor; draft ve eksik APK'lı release filtreleme, güvenilir host ve boyut sınırı daha sıkı olmalı. [Doğrulandı]
P1: Checksum aynı release üzerinden alınır, ayrı imzalı manifest değildir; Android paket imzası sürekliliğinin yerini tutmaz. [Doğrulandı]
P2: companion_release_test fixture'ında SHA256SUMS.sha256 iki kez mevcut; yeni force açılış yolu, hatalı checksum ve native permission akışı test edilmiyor. [Doğrulandı]
P2: main.dart HTTP User-Agent ve cloud_api.dart User-Agent içinde 0.1.5 hâlâ bulunur; görünen UI sürümü düzelmiş olsa da telemetri/istek başlığı sürümü eskidir. [Doğrulandı]
P1: review_queue.add docstring masked dese de ham OCR metni 4000 karaktere kadar saklanır; _text silinmesi tam maskeleme değildir; boyut/retention ve resolve UI bu modülde yoktur. [Doğrulandı]
P1: OCR lab en uzun metni referans seçer; similarity_to_reference doğruluk/ground truth değildir, farklı motorların confidence ölçekleri karşılaştırılabilir kabul edilmektedir. [Doğrulandı]
P1: app.ocr_lab_report motorları UI callback içinde senkron çalıştırıyor; donma süresi ölçülmedi. [Doğrulandı]
P1: target_planner confidence float dönüşümü bozuk metinde hata verebilir; gelecekteki timestamp tazelik kontrolünü geçebilir; eksik confidence 1.0 varsayılır. [Doğrulandı]
P1: Hedef adları tam normalize eşleşir; genel AR hedef loot kategorisinden belirli exotic'e kapsamlı farm çıkarımı yapılmaz. [Doğrulandı]
P1: decision_center rarity alanını liste kabul eder; string rarity harflerine ayrılır; yine de üretilen karar yalnız KEEP/REVIEW olsa da protected bayrağı eksik olabilir. [Doğrulandı]
P1: Info check önceki yayınlarda başarısızdı; ROADMAP 6 Kasım kaydı sebebi sabit haber ID'si y8s3-red-moon-unleashed olan test fixture'ının beslemeden silinmesi olarak bildiriyor; bu rapor turunda yeniden test edilmedi. [Kısmen doğrulandı]
P2: Hedef düzenleme/silme, inceleme kuyruğunu çözme ve mobil hedef planı tam senkronu bu eklenen modüllerle tamamlanmış sayılmamalıdır. [Test edilmedi]
Önceki yanıtım 0.1.7'nin bütün sürüm metinlerini ve güvenli güncellemeyi düzelttiğini fazla kesin söyledi; sabit UI metni kalmıştı, checksum fail-open idi ve cihaz testi yoktu; 0.1.8 ilk iki kod sorununu düzeltti, cihaz kanıtı hâlâ yoktur. [Doğrulandı]

## 8. GÜVENLİK, GİZLİLİK VE OYUN KURALLARI AÇISINDAN KONTROL
Bu commit aralığı diff'inde ReadProcessMemory, WriteProcessMemory, PRIVATE KEY, ghp_, github_pat_ ve AKIA desenleri için yapılan tarama eşleşme döndürmedi; bu sınırlı tarama bütün depo için güvenlik sertifikası değildir. [Doğrulandı]
Okunan runtime/planlayıcı/karar modülleri yerel veri işler; mobil değişiklikler GitHub indirme ve Android kurulum intent'idir, oyun belleği veya injection işlevi eklenmedi. [Doğrulandı]
APK, checksum ve GitHub sürüm metadatası internetten alınır; bu değişiklikler OCR görüntüsünü GitHub'a göndermez. [Doğrulandı]
Kişisel builds.json ve takip dışı çalışma klasörleri commit edilmedi; rapora kişisel dosya içerikleri alınmadı. [Doğrulandı]
Bütün proje, bağımlılıklar ve geçmiş commit'ler için eksiksiz sır taraması yapılmadı; mevcut uygulamanın tüm ağ akışlarının gizlilik denetimi tamamlanmış değildir. [Test edilmedi]
Koruma katmanı sadece bu karar merkezi için incelendi; bütün loot yollarının güvenliği yeniden test edilmedi. [Test edilmedi]

## 9. ÇELİŞKİ VE ÇAKIŞMA KONTROLÜ
İstenen altı belgenin tamamı dosya olarak okundu; belge beyanları bağımsız test kanıtı sayılmadı ve aşağıdaki çelişkiler kod/geçmiş ile karşılaştırıldı. [Doğrulandı]
1. HANDOFF v9.1.5.19, Claude devir raporu mobil 0.1.2, ROADMAP son masaüstü 9.1.5.32 bilgileri daha eski snapshot'lardır; mevcut kod 9.1.5.34 ve 0.1.8'dir. [Doğrulandı]
2. BUGS #6/#18, HANDOFF ve TESTING mobil test yok diyor; bu ifadeler ilgili Claude ortamı için tarihsel olabilir, ancak güncel Windows Flutter analyze/test ve CI APK build başarılarının yerine kullanılamaz. [Doğrulandı]
3. DEVELOPMENT_LOG 39c032c mobil splash/sıralama/onay/refresh değişikliklerini belgeliyor; aynı mobile/lib/main.dart dosyasına sonraki Codex commit'leri güncelleme akışını ekledi; aynı dosyada ardışık çalışma vardır, eşzamanlı edit veya kayıp satır kanıtı yoktur. [Doğrulandı]
4. app.py geçmişinde Claude db6b1dc, 986f79c, 69e030c ile daha sonra c2d14f6 birlikte bulunur; tema/çeviri ve runtime/fallback aynı büyük dosyada buluşur, UI regresyonunun olmadığı yalnız Git geçmişinden çıkarılamaz. [Doğrulandı]
5. Claude devir raporu Kaivolt ve 18 tema anlatırken DEVELOPMENT_LOG/BUGS sonraki tek tema değişimini açıklar; verilen AGENTS Kaivolt koru talimatı bu tarihsel değişimle çelişir, yeni tasarım kararı alınmadan tema geri getirilmemelidir. [Doğrulandı]
6. mobile/PHASE5_RELEASE_READINESS_TR.md her açılışta API çağrısı yapılmaz diyor; 04148ca load(force:true) bunun tersidir, belge güncelliğini yitirmiştir. [Doğrulandı]
7. docs/phase5-decision-center.md eksik alanların REVIEW olacağını söylüyor; confidence eksikse kodun 1.0 kullanması bu genellemeyi desteklemez. [Doğrulandı]
8. Mevcut server push-registration ile yeni LocalAlerts iki farklı bildirim yoludur; birinin testinin geçmesi diğerinin Firebase/APNs cihaz teslimatını kanıtlamaz; Gradle google-services satırı hâlâ yorumludur. [Doğrulandı]
9. SafeTrail, sentencepiece ve eski webbrowser/except-lambda düzeltmeleri eski belgelerde açıklanır; bu aralık bunları tekrar çözmedi, bu işlerin başarıları bu ajana mal edilmemelidir. [Doğrulandı]
10. Info check sorunu yeni mobil lint ile aynı hata değildir; mobile lint düzeltildi diye belgelediği eski test fixture sorunu kapanmaz. [Doğrulandı]
Dosya bazlı son dört commit, bölüm 3'te eksiksiz verilmiştir; FEDERALTURK yazar adı Claude/Codex kimliğini kesin ayırt etmediğinden yalnız commit yazarıyla sahiplik hükmü verilmedi. [Doğrulandı]

## 10. GÜNCEL PROJE DURUMU
Rapor öncesi git log -10 çıktısı aşağıdadır. [Doğrulandı]
```text
04148ca fix: companion version display and update permission flow
d9a6179 fix: satisfy companion update lint
961640c fix: satisfy companion analyzer formatting
06f992c fix: download and install companion updates safely
c2d14f6 feat: add phase five decision and companion release flow
4df500f Topluluk görevleri: 1 görev
7db5e31 release(mobile): prepare companion v0.1.5 beta
18cef04 feat(mobile): add one-tap companion APK update flow
4688c16 docs: add TD2 AI agent workflow contract
a48dbd1 release(mobile): prepare companion v0.1.4.1 beta
```
Rapor öncesi git status --short aşağıdadır; tüm bu kalemler kullanıcıya bırakıldı. [Doğrulandı]
```text
 M builds.json
?? 18_pull_and_recheck.bat
?? 19_cleanup.bat
?? "Claude outputs/"
?? flutter_recheck_log.txt
?? project_review/
?? tasks/
?? web_deploy/
```
GitHub release companion-v0.1.8 bu rapor turunda REST ile yeniden okundu; prerelease=true, APK 71691855 bayt, SHA256SUMS.sha256 101 bayttır. [Doğrulandı]
Yayın URL: https://github.com/FEDERALTURK/td2-loot-advisor/releases/tag/companion-v0.1.8 . [Doğrulandı]
Yerel pubspec 0.1.8+10, companionVersion 0.1.8 ve APP_VERSION 9.1.5.34'tür; son yerel tag sırası companion-v0.1.8, companion-v0.1.7, companion-v0.1.6, v9.1.5.34 olarak görüldü. [Doğrulandı]
Kanıtlanmış kapsam analiz/test/build/yayın adımlarıdır; bütün uygulamanın tamamen çalıştığı veya bütün eski kullanıcı sorunlarının bittiği kanıtlanmadı. [Test edilmedi]
Mobil kurulum izni, güncelleme motoru ve masaüstü karar modülleri kodda vardır; imza yönetimi, gerçek cihaz test matrisi, tam bildirim aksiyonu ve iOS yayını tamamlanmamıştır. [Test edilmedi]

## 11. CLAUDE İÇİN İLK ADIM ÖNERİSİ
Önce git status --short ve git log -10 ile bu snapshot'ın hâlâ geçerli olup olmadığını kontrol etmek önerilir. [Varsayım]
En riskli nokta mevcut APK üstüne güncellemedir; ilk teknik inceleme build-mobile.yml, mobile/android/app/build.gradle.kts, MainActivity.kt, file_paths.xml ve mobile/lib/main.dart üzerinde yapılmalıdır. [Varsayım]
Eski ve yeni APK sertifikalarını apksigner verify --print-certs ile karşılaştırmak ve kurulu paketin dumpsys package com.federalturk.td2companion çıktısını almak sorunu ayırabilir; bu komutlar bu oturumda çalıştırılmadı. [Test edilmedi]
Eski imza anahtarı yoksa sessizce yeni anahtar üretip “güncelleme düzeldi” denmemeli; veri yedekli göç ve kullanıcıya açık kurulum planı gerekir. [Varsayım]
Yerelde doğrulanmış SDK yoluyla aşağıdaki komutları çalıştırmak, ardından gerçek cihazda izin reddi/kabulü, bozuk checksum, ağ kesintisi, yeniden açılış ve kurulum sonucu senaryolarını eklemek önerilir. [Varsayım]
```powershell
Set-Location C:/Users/PC/Desktop/Thedivision2program/mobile
& C:/Users/PC/tools/flutter/bin/flutter.bat analyze
& C:/Users/PC/tools/flutter/bin/flutter.bat test
```
PC tarafında tests/test_game_runtime.py, tests/test_inplace_anchors.py, tests/test_translation_controls.py, tests/test_ocr_lab.py, tests/test_target_planner.py ve tests/test_decision_center.py tekil python -B komutlarıyla değerlendirilmelidir; gerçek oyun testi ayrıca gerekir. [Varsayım]
Info check için canlı haber ID bağımlılığını sabit fixture'a ayırmak ve hedef/verdict güvenlik uç durumlarını test etmek sonraki önceliklerdir. [Varsayım]
Bu devir görevi yalnız rapor commit'ine izin verir; push, tag veya yeni APK üretimi talep edilmedi. [Doğrulandı]

## 12. KISA YÖNETİCİ ÖZETİ
Mobil uygulamanın görünen eski sürüm yazısı son güncellemede düzeltildi. [Doğrulandı]
Güncelleme kontrolü uygulama açılışında yeniden çalışacak şekilde değişti. [Doğrulandı]
Dosya doğrulaması başarısızsa kurulum duruyor. [Doğrulandı]
Telefonun yükleme izni yoksa ilgili ayar ekranı açılıyor. [Doğrulandı]
Yeni Android sürümü 0.1.8 beta olarak GitHub'da mevcut. [Doğrulandı]
Yerel analiz ve dört test geçti; GitHub APK üretimi tamamlandı. [Doğrulandı]
Telefonda eski sürümün üstüne kurulum henüz denenmedi. [Test edilmedi]
İmza sürekliliği yeni geliştiricinin öncelikle ele alması gereken risktir. [Varsayım]
Masaüstü hedef, karar ve OCR inceleme araçlarının kodları bu devirde envanterlendi. [Doğrulandı]
Bu araçların gerçek oyundaki tüm davranışları yeniden doğrulanmadı. [Test edilmedi]
Eski devir belgelerindeki sürüm ve test bilgileri güncel durumla yer yer çelişiyor. [Doğrulandı]
Kullanıcı verileri ve kişisel çalışma klasörleri bu rapor commit'ine dahil edilmiyor. [Doğrulandı]
Önceki aşırı kesin başarı ifadeleri raporda düzeltildi ve eksikler açık bırakıldı. [Doğrulandı]

