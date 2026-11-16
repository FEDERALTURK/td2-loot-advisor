# AI Araç Envanteri — 16.11.2026

## 1. Özet

Salt-okunur taramada 219 kalem raporlandı: 11 skill, 176 agent, 1 mcp-server, 17 vscode-extension, 5 cli-tool, 2 local-model ve 7 other.

GitHub kaynağı kanıtlanan satırlar: 7. Kanıt yalnız yerel skills-lock.json, .git\config veya SKILL.md/README içindeki açık bağlantılara dayandırıldı. Kanıt bulunmayan tüm satırlarda adres tam olarak [Doğrulanmadı — kaynak bulunamadı] bırakıldı.

Claude Desktop'a doğrudan taşınabilir grup: beceriler ve ruflo MCP tanımıdır. Ajanlar Claude Desktop'a doğrudan taşınamaz; Claude Code için elle .claude\agents\<ad>.md biçimine uyarlanabilir. VS Code eklentileri, CLI araçları ve yerel model çalıştırıcıları taşınamaz.

Gizlilik: API anahtarı, token, parola, bağlantı dizesi ve özel anahtar değerleri rapora yazılmadı. Yapılandırma kanıtları yalnız ad/path düzeyinde tutuldu.

## 2. Envanter tablosu

| Ad | Tür | Yerel yol | Sürüm | GitHub | Kanıt | Claude karşılığı |
|---|---|---|---|---|---|---|
| brag | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\brag | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | .agents\skills\brag\SKILL.md | Zipleyip Skills → Upload a Skill |
| brag-slim | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\brag-slim | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | .agents\skills\brag-slim\SKILL.md | Zipleyip Skills → Upload a Skill |
| memory-management | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\memory-management | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | .agents\skills\memory-management\SKILL.md | Zipleyip Skills → Upload a Skill |
| modern-web-guidance | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\modern-web-guidance | [Dosyada yok] | https://github.com/GoogleChrome/modern-web-guidance | skills-lock.json source=GoogleChrome/modern-web-guidance, sourceType=github, computedHash | Zipleyip Skills → Upload a Skill |
| prompt-master | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\prompt-master | [Dosyada yok] | https://github.com/nidhinjs/prompt-master.git | SKILL.md/README içindeki açık bağlantı | Zipleyip Skills → Upload a Skill |
| supabase | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\supabase | [Dosyada yok] | https://github.com/supabase/agent-skills | skills-lock.json source=supabase/agent-skills, sourceType=github, computedHash | Zipleyip Skills → Upload a Skill |
| supabase-postgres-best-practices | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\supabase-postgres-best-practices | [Dosyada yok] | https://github.com/supabase/agent-skills | skills-lock.json source=supabase/agent-skills, sourceType=github, computedHash | Zipleyip Skills → Upload a Skill |
| swarm-orchestration | skill | C:\Users\PC\Desktop\Thedivision2program\.agents\skills\swarm-orchestration | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | .agents\skills\swarm-orchestration\SKILL.md | Zipleyip Skills → Upload a Skill |
| reverse-engineer-anything (user .agents) | skill | C:\Users\PC\.agents\skills\reverse-engineer-anything | [Dosyada yok] | https://github.com/morluto/rea; https://github.com/mrexodia/ida-pro-mcp | SKILL.md açık bağlantıları; SHA-256 8818B645... | Tek kopya yüklenmeli |
| reverse-engineer-anything (Claude) | skill | C:\Users\PC\.claude\skills\reverse-engineer-anything | [Dosyada yok] | https://github.com/morluto/rea; https://github.com/mrexodia/ida-pro-mcp | SKILL.md açık bağlantıları; user .agents kopyasıyla aynı SHA-256 | İkinci kez yüklenmemeli |
| template | skill | C:\Users\PC\skills\template | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | SKILL.md varlığı | İçeriği incelenmeden yüklenmemeli |
| ruflo | mcp-server | Proje .agents\config.toml | ruflo@latest tanımı | [Doğrulanmadı — kaynak bulunamadı] | [mcp_servers.ruflo], command=cmd, args=/c npx -y ruflo@latest mcp start | claude_desktop_config.json içindeki mcpServers |
| ab-test-analysis | agent | C:\Users\PC\.codex\agents\ab-test-analysis.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ab-test-analysis.md olarak elle uyarlanmalı |
| accessibility-tester | agent | C:\Users\PC\.codex\agents\accessibility-tester.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\accessibility-tester.md olarak elle uyarlanmalı |
| ad-security-reviewer | agent | C:\Users\PC\.codex\agents\ad-security-reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ad-security-reviewer.md olarak elle uyarlanmalı |
| agent-installer | agent | C:\Users\PC\.codex\agents\agent-installer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\agent-installer.md olarak elle uyarlanmalı |
| agent-organizer | agent | C:\Users\PC\.codex\agents\agent-organizer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\agent-organizer.md olarak elle uyarlanmalı |
| ai-engineer | agent | C:\Users\PC\.codex\agents\ai-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ai-engineer.md olarak elle uyarlanmalı |
| ai-governance-auditor | agent | C:\Users\PC\.codex\agents\ai-governance-auditor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ai-governance-auditor.md olarak elle uyarlanmalı |
| ai-observability-engineer | agent | C:\Users\PC\.codex\agents\ai-observability-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ai-observability-engineer.md olarak elle uyarlanmalı |
| ai-writing-auditor | agent | C:\Users\PC\.codex\agents\ai-writing-auditor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ai-writing-auditor.md olarak elle uyarlanmalı |
| angular-architect | agent | C:\Users\PC\.codex\agents\angular-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\angular-architect.md olarak elle uyarlanmalı |
| anti-ui-slop-reviewer | agent | C:\Users\PC\.codex\agents\anti-ui-slop-reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\anti-ui-slop-reviewer.md olarak elle uyarlanmalı |
| api-designer | agent | C:\Users\PC\.codex\agents\api-designer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\api-designer.md olarak elle uyarlanmalı |
| api-documenter | agent | C:\Users\PC\.codex\agents\api-documenter.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\api-documenter.md olarak elle uyarlanmalı |
| architect-reviewer | agent | C:\Users\PC\.codex\agents\architect-reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\architect-reviewer.md olarak elle uyarlanmalı |
| assumption-mapping | agent | C:\Users\PC\.codex\agents\assumption-mapping.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\assumption-mapping.md olarak elle uyarlanmalı |
| azure-databricks-platform-architect | agent | C:\Users\PC\.codex\agents\azure-databricks-platform-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\azure-databricks-platform-architect.md olarak elle uyarlanmalı |
| azure-infra-engineer | agent | C:\Users\PC\.codex\agents\azure-infra-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\azure-infra-engineer.md olarak elle uyarlanmalı |
| backend-developer | agent | C:\Users\PC\.codex\agents\backend-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\backend-developer.md olarak elle uyarlanmalı |
| backlog-grooming | agent | C:\Users\PC\.codex\agents\backlog-grooming.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\backlog-grooming.md olarak elle uyarlanmalı |
| backstage-specialist | agent | C:\Users\PC\.codex\agents\backstage-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\backstage-specialist.md olarak elle uyarlanmalı |
| blockchain-developer | agent | C:\Users\PC\.codex\agents\blockchain-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\blockchain-developer.md olarak elle uyarlanmalı |
| browser-debugger | agent | C:\Users\PC\.codex\agents\browser-debugger.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\browser-debugger.md olarak elle uyarlanmalı |
| build-engineer | agent | C:\Users\PC\.codex\agents\build-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\build-engineer.md olarak elle uyarlanmalı |
| business-analyst | agent | C:\Users\PC\.codex\agents\business-analyst.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\business-analyst.md olarak elle uyarlanmalı |
| chaos-engineer | agent | C:\Users\PC\.codex\agents\chaos-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\chaos-engineer.md olarak elle uyarlanmalı |
| cli-developer | agent | C:\Users\PC\.codex\agents\cli-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\cli-developer.md olarak elle uyarlanmalı |
| cloud-architect | agent | C:\Users\PC\.codex\agents\cloud-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\cloud-architect.md olarak elle uyarlanmalı |
| code-mapper | agent | C:\Users\PC\.codex\agents\code-mapper.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\code-mapper.md olarak elle uyarlanmalı |
| code-reviewer | agent | C:\Users\PC\.codex\agents\code-reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\code-reviewer.md olarak elle uyarlanmalı |
| codebase-orchestrator | agent | C:\Users\PC\.codex\agents\codebase-orchestrator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\codebase-orchestrator.md olarak elle uyarlanmalı |
| cohort-analysis | agent | C:\Users\PC\.codex\agents\cohort-analysis.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\cohort-analysis.md olarak elle uyarlanmalı |
| competitive-analyst | agent | C:\Users\PC\.codex\agents\competitive-analyst.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\competitive-analyst.md olarak elle uyarlanmalı |
| compliance-auditor | agent | C:\Users\PC\.codex\agents\compliance-auditor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\compliance-auditor.md olarak elle uyarlanmalı |
| content-marketer | agent | C:\Users\PC\.codex\agents\content-marketer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\content-marketer.md olarak elle uyarlanmalı |
| content-quality-editor | agent | C:\Users\PC\.codex\agents\content-quality-editor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\content-quality-editor.md olarak elle uyarlanmalı |
| context-manager | agent | C:\Users\PC\.codex\agents\context-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\context-manager.md olarak elle uyarlanmalı |
| cpp-pro | agent | C:\Users\PC\.codex\agents\cpp-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\cpp-pro.md olarak elle uyarlanmalı |
| csharp-developer | agent | C:\Users\PC\.codex\agents\csharp-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\csharp-developer.md olarak elle uyarlanmalı |
| customer-success-manager | agent | C:\Users\PC\.codex\agents\customer-success-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\customer-success-manager.md olarak elle uyarlanmalı |
| data-analyst | agent | C:\Users\PC\.codex\agents\data-analyst.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\data-analyst.md olarak elle uyarlanmalı |
| data-engineer | agent | C:\Users\PC\.codex\agents\data-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\data-engineer.md olarak elle uyarlanmalı |
| data-researcher | agent | C:\Users\PC\.codex\agents\data-researcher.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\data-researcher.md olarak elle uyarlanmalı |
| data-scientist | agent | C:\Users\PC\.codex\agents\data-scientist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\data-scientist.md olarak elle uyarlanmalı |
| database-administrator | agent | C:\Users\PC\.codex\agents\database-administrator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\database-administrator.md olarak elle uyarlanmalı |
| database-optimizer | agent | C:\Users\PC\.codex\agents\database-optimizer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\database-optimizer.md olarak elle uyarlanmalı |
| debugger | agent | C:\Users\PC\.codex\agents\debugger.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\debugger.md olarak elle uyarlanmalı |
| dependency-manager | agent | C:\Users\PC\.codex\agents\dependency-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\dependency-manager.md olarak elle uyarlanmalı |
| deployment-engineer | agent | C:\Users\PC\.codex\agents\deployment-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\deployment-engineer.md olarak elle uyarlanmalı |
| design-bridge | agent | C:\Users\PC\.codex\agents\design-bridge.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\design-bridge.md olarak elle uyarlanmalı |
| devops-engineer | agent | C:\Users\PC\.codex\agents\devops-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\devops-engineer.md olarak elle uyarlanmalı |
| devops-incident-responder | agent | C:\Users\PC\.codex\agents\devops-incident-responder.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\devops-incident-responder.md olarak elle uyarlanmalı |
| django-developer | agent | C:\Users\PC\.codex\agents\django-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\django-developer.md olarak elle uyarlanmalı |
| docker-expert | agent | C:\Users\PC\.codex\agents\docker-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\docker-expert.md olarak elle uyarlanmalı |
| docs-researcher | agent | C:\Users\PC\.codex\agents\docs-researcher.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\docs-researcher.md olarak elle uyarlanmalı |
| documentation-engineer | agent | C:\Users\PC\.codex\agents\documentation-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\documentation-engineer.md olarak elle uyarlanmalı |
| dotnet-core-expert | agent | C:\Users\PC\.codex\agents\dotnet-core-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\dotnet-core-expert.md olarak elle uyarlanmalı |
| dotnet-framework-4.8-expert | agent | C:\Users\PC\.codex\agents\dotnet-framework-4.8-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\dotnet-framework-4.8-expert.md olarak elle uyarlanmalı |
| dx-optimizer | agent | C:\Users\PC\.codex\agents\dx-optimizer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\dx-optimizer.md olarak elle uyarlanmalı |
| electron-pro | agent | C:\Users\PC\.codex\agents\electron-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\electron-pro.md olarak elle uyarlanmalı |
| elixir-expert | agent | C:\Users\PC\.codex\agents\elixir-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\elixir-expert.md olarak elle uyarlanmalı |
| embedded-systems | agent | C:\Users\PC\.codex\agents\embedded-systems.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\embedded-systems.md olarak elle uyarlanmalı |
| erlang-expert | agent | C:\Users\PC\.codex\agents\erlang-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\erlang-expert.md olarak elle uyarlanmalı |
| error-coordinator | agent | C:\Users\PC\.codex\agents\error-coordinator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\error-coordinator.md olarak elle uyarlanmalı |
| error-detective | agent | C:\Users\PC\.codex\agents\error-detective.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\error-detective.md olarak elle uyarlanmalı |
| eval-engineer | agent | C:\Users\PC\.codex\agents\eval-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\eval-engineer.md olarak elle uyarlanmalı |
| expo-react-native-expert | agent | C:\Users\PC\.codex\agents\expo-react-native-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\expo-react-native-expert.md olarak elle uyarlanmalı |
| fastapi-developer | agent | C:\Users\PC\.codex\agents\fastapi-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\fastapi-developer.md olarak elle uyarlanmalı |
| fintech-engineer | agent | C:\Users\PC\.codex\agents\fintech-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\fintech-engineer.md olarak elle uyarlanmalı |
| first-principles-thinking | agent | C:\Users\PC\.codex\agents\first-principles-thinking.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\first-principles-thinking.md olarak elle uyarlanmalı |
| flutter-expert | agent | C:\Users\PC\.codex\agents\flutter-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\flutter-expert.md olarak elle uyarlanmalı |
| frontend-developer | agent | C:\Users\PC\.codex\agents\frontend-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\frontend-developer.md olarak elle uyarlanmalı |
| fullstack-developer | agent | C:\Users\PC\.codex\agents\fullstack-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\fullstack-developer.md olarak elle uyarlanmalı |
| game-developer | agent | C:\Users\PC\.codex\agents\game-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\game-developer.md olarak elle uyarlanmalı |
| gdpr-ccpa-compliance | agent | C:\Users\PC\.codex\agents\gdpr-ccpa-compliance.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\gdpr-ccpa-compliance.md olarak elle uyarlanmalı |
| git-workflow-manager | agent | C:\Users\PC\.codex\agents\git-workflow-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\git-workflow-manager.md olarak elle uyarlanmalı |
| golang-pro | agent | C:\Users\PC\.codex\agents\golang-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\golang-pro.md olarak elle uyarlanmalı |
| golden-path-designer | agent | C:\Users\PC\.codex\agents\golden-path-designer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\golden-path-designer.md olarak elle uyarlanmalı |
| graphql-architect | agent | C:\Users\PC\.codex\agents\graphql-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\graphql-architect.md olarak elle uyarlanmalı |
| growth-loops | agent | C:\Users\PC\.codex\agents\growth-loops.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\growth-loops.md olarak elle uyarlanmalı |
| hallucination-investigator | agent | C:\Users\PC\.codex\agents\hallucination-investigator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\hallucination-investigator.md olarak elle uyarlanmalı |
| healthcare-admin | agent | C:\Users\PC\.codex\agents\healthcare-admin.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\healthcare-admin.md olarak elle uyarlanmalı |
| hipaa-compliance | agent | C:\Users\PC\.codex\agents\hipaa-compliance.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\hipaa-compliance.md olarak elle uyarlanmalı |
| idp-architect | agent | C:\Users\PC\.codex\agents\idp-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\idp-architect.md olarak elle uyarlanmalı |
| incident-responder | agent | C:\Users\PC\.codex\agents\incident-responder.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\incident-responder.md olarak elle uyarlanmalı |
| iot-engineer | agent | C:\Users\PC\.codex\agents\iot-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\iot-engineer.md olarak elle uyarlanmalı |
| it-ops-orchestrator | agent | C:\Users\PC\.codex\agents\it-ops-orchestrator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\it-ops-orchestrator.md olarak elle uyarlanmalı |
| java-architect | agent | C:\Users\PC\.codex\agents\java-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\java-architect.md olarak elle uyarlanmalı |
| javascript-pro | agent | C:\Users\PC\.codex\agents\javascript-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\javascript-pro.md olarak elle uyarlanmalı |
| knowledge-synthesizer | agent | C:\Users\PC\.codex\agents\knowledge-synthesizer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\knowledge-synthesizer.md olarak elle uyarlanmalı |
| kotlin-specialist | agent | C:\Users\PC\.codex\agents\kotlin-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\kotlin-specialist.md olarak elle uyarlanmalı |
| kubernetes-specialist | agent | C:\Users\PC\.codex\agents\kubernetes-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\kubernetes-specialist.md olarak elle uyarlanmalı |
| laravel-specialist | agent | C:\Users\PC\.codex\agents\laravel-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\laravel-specialist.md olarak elle uyarlanmalı |
| legacy-modernizer | agent | C:\Users\PC\.codex\agents\legacy-modernizer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\legacy-modernizer.md olarak elle uyarlanmalı |
| legal-advisor | agent | C:\Users\PC\.codex\agents\legal-advisor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\legal-advisor.md olarak elle uyarlanmalı |
| license-engineer | agent | C:\Users\PC\.codex\agents\license-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\license-engineer.md olarak elle uyarlanmalı |
| llm-architect | agent | C:\Users\PC\.codex\agents\llm-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\llm-architect.md olarak elle uyarlanmalı |
| m365-admin | agent | C:\Users\PC\.codex\agents\m365-admin.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\m365-admin.md olarak elle uyarlanmalı |
| machine-learning-engineer | agent | C:\Users\PC\.codex\agents\machine-learning-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\machine-learning-engineer.md olarak elle uyarlanmalı |
| market-researcher | agent | C:\Users\PC\.codex\agents\market-researcher.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\market-researcher.md olarak elle uyarlanmalı |
| mcp-developer | agent | C:\Users\PC\.codex\agents\mcp-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\mcp-developer.md olarak elle uyarlanmalı |
| microservices-architect | agent | C:\Users\PC\.codex\agents\microservices-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\microservices-architect.md olarak elle uyarlanmalı |
| ml-engineer | agent | C:\Users\PC\.codex\agents\ml-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ml-engineer.md olarak elle uyarlanmalı |
| mlops-engineer | agent | C:\Users\PC\.codex\agents\mlops-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\mlops-engineer.md olarak elle uyarlanmalı |
| mobile-app-developer | agent | C:\Users\PC\.codex\agents\mobile-app-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\mobile-app-developer.md olarak elle uyarlanmalı |
| mobile-developer | agent | C:\Users\PC\.codex\agents\mobile-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\mobile-developer.md olarak elle uyarlanmalı |
| model-risk-manager | agent | C:\Users\PC\.codex\agents\model-risk-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\model-risk-manager.md olarak elle uyarlanmalı |
| multi-agent-coordinator | agent | C:\Users\PC\.codex\agents\multi-agent-coordinator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\multi-agent-coordinator.md olarak elle uyarlanmalı |
| network-engineer | agent | C:\Users\PC\.codex\agents\network-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\network-engineer.md olarak elle uyarlanmalı |
| nextjs-developer | agent | C:\Users\PC\.codex\agents\nextjs-developer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\nextjs-developer.md olarak elle uyarlanmalı |
| nlp-engineer | agent | C:\Users\PC\.codex\agents\nlp-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\nlp-engineer.md olarak elle uyarlanmalı |
| node-specialist | agent | C:\Users\PC\.codex\agents\node-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\node-specialist.md olarak elle uyarlanmalı |
| payment-integration | agent | C:\Users\PC\.codex\agents\payment-integration.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\payment-integration.md olarak elle uyarlanmalı |
| penetration-tester | agent | C:\Users\PC\.codex\agents\penetration-tester.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\penetration-tester.md olarak elle uyarlanmalı |
| performance-engineer | agent | C:\Users\PC\.codex\agents\performance-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\performance-engineer.md olarak elle uyarlanmalı |
| performance-monitor | agent | C:\Users\PC\.codex\agents\performance-monitor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\performance-monitor.md olarak elle uyarlanmalı |
| php-pro | agent | C:\Users\PC\.codex\agents\php-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\php-pro.md olarak elle uyarlanmalı |
| platform-engineer | agent | C:\Users\PC\.codex\agents\platform-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\platform-engineer.md olarak elle uyarlanmalı |
| platform-product-manager | agent | C:\Users\PC\.codex\agents\platform-product-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\platform-product-manager.md olarak elle uyarlanmalı |
| policy-guardrail-designer | agent | C:\Users\PC\.codex\agents\policy-guardrail-designer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\policy-guardrail-designer.md olarak elle uyarlanmalı |
| ponder-reviewer | agent | C:\Users\PC\.codex\agents\ponder-reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ponder-reviewer.md olarak elle uyarlanmalı |
| postgres-pro | agent | C:\Users\PC\.codex\agents\postgres-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\postgres-pro.md olarak elle uyarlanmalı |
| powershell-5.1-expert | agent | C:\Users\PC\.codex\agents\powershell-5.1-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\powershell-5.1-expert.md olarak elle uyarlanmalı |
| powershell-7-expert | agent | C:\Users\PC\.codex\agents\powershell-7-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\powershell-7-expert.md olarak elle uyarlanmalı |
| powershell-module-architect | agent | C:\Users\PC\.codex\agents\powershell-module-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\powershell-module-architect.md olarak elle uyarlanmalı |
| powershell-security-hardening | agent | C:\Users\PC\.codex\agents\powershell-security-hardening.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\powershell-security-hardening.md olarak elle uyarlanmalı |
| powershell-ui-architect | agent | C:\Users\PC\.codex\agents\powershell-ui-architect.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\powershell-ui-architect.md olarak elle uyarlanmalı |
| product-manager | agent | C:\Users\PC\.codex\agents\product-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\product-manager.md olarak elle uyarlanmalı |
| project-idea-validator | agent | C:\Users\PC\.codex\agents\project-idea-validator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\project-idea-validator.md olarak elle uyarlanmalı |
| project-manager | agent | C:\Users\PC\.codex\agents\project-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\project-manager.md olarak elle uyarlanmalı |
| prompt-engineer | agent | C:\Users\PC\.codex\agents\prompt-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\prompt-engineer.md olarak elle uyarlanmalı |
| prompt-regression-tester | agent | C:\Users\PC\.codex\agents\prompt-regression-tester.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\prompt-regression-tester.md olarak elle uyarlanmalı |
| python-pro | agent | C:\Users\PC\.codex\agents\python-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\python-pro.md olarak elle uyarlanmalı |
| qa-expert | agent | C:\Users\PC\.codex\agents\qa-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\qa-expert.md olarak elle uyarlanmalı |
| quant-analyst | agent | C:\Users\PC\.codex\agents\quant-analyst.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\quant-analyst.md olarak elle uyarlanmalı |
| rails-expert | agent | C:\Users\PC\.codex\agents\rails-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\rails-expert.md olarak elle uyarlanmalı |
| react-specialist | agent | C:\Users\PC\.codex\agents\react-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\react-specialist.md olarak elle uyarlanmalı |
| readme-generator | agent | C:\Users\PC\.codex\agents\readme-generator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\readme-generator.md olarak elle uyarlanmalı |
| refactoring-specialist | agent | C:\Users\PC\.codex\agents\refactoring-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\refactoring-specialist.md olarak elle uyarlanmalı |
| reinforcement-learning-engineer | agent | C:\Users\PC\.codex\agents\reinforcement-learning-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\reinforcement-learning-engineer.md olarak elle uyarlanmalı |
| research-analyst | agent | C:\Users\PC\.codex\agents\research-analyst.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\research-analyst.md olarak elle uyarlanmalı |
| responsible-ai-reviewer | agent | C:\Users\PC\.codex\agents\responsible-ai-reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\responsible-ai-reviewer.md olarak elle uyarlanmalı |
| resume-refiner | agent | C:\Users\PC\.codex\agents\resume-refiner.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\resume-refiner.md olarak elle uyarlanmalı |
| reviewer | agent | C:\Users\PC\.codex\agents\reviewer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\reviewer.md olarak elle uyarlanmalı |
| risk-manager | agent | C:\Users\PC\.codex\agents\risk-manager.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\risk-manager.md olarak elle uyarlanmalı |
| rust-engineer | agent | C:\Users\PC\.codex\agents\rust-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\rust-engineer.md olarak elle uyarlanmalı |
| sales-engineer | agent | C:\Users\PC\.codex\agents\sales-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\sales-engineer.md olarak elle uyarlanmalı |
| scientific-literature-researcher | agent | C:\Users\PC\.codex\agents\scientific-literature-researcher.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\scientific-literature-researcher.md olarak elle uyarlanmalı |
| scrum-master | agent | C:\Users\PC\.codex\agents\scrum-master.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\scrum-master.md olarak elle uyarlanmalı |
| search-specialist | agent | C:\Users\PC\.codex\agents\search-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\search-specialist.md olarak elle uyarlanmalı |
| security-auditor | agent | C:\Users\PC\.codex\agents\security-auditor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\security-auditor.md olarak elle uyarlanmalı |
| security-engineer | agent | C:\Users\PC\.codex\agents\security-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\security-engineer.md olarak elle uyarlanmalı |
| seo-specialist | agent | C:\Users\PC\.codex\agents\seo-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\seo-specialist.md olarak elle uyarlanmalı |
| slack-expert | agent | C:\Users\PC\.codex\agents\slack-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\slack-expert.md olarak elle uyarlanmalı |
| spring-boot-engineer | agent | C:\Users\PC\.codex\agents\spring-boot-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\spring-boot-engineer.md olarak elle uyarlanmalı |
| sql-pro | agent | C:\Users\PC\.codex\agents\sql-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\sql-pro.md olarak elle uyarlanmalı |
| sre-engineer | agent | C:\Users\PC\.codex\agents\sre-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\sre-engineer.md olarak elle uyarlanmalı |
| swift-expert | agent | C:\Users\PC\.codex\agents\swift-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\swift-expert.md olarak elle uyarlanmalı |
| symfony-specialist | agent | C:\Users\PC\.codex\agents\symfony-specialist.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\symfony-specialist.md olarak elle uyarlanmalı |
| task-distributor | agent | C:\Users\PC\.codex\agents\task-distributor.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\task-distributor.md olarak elle uyarlanmalı |
| technical-writer | agent | C:\Users\PC\.codex\agents\technical-writer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\technical-writer.md olarak elle uyarlanmalı |
| terraform-engineer | agent | C:\Users\PC\.codex\agents\terraform-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\terraform-engineer.md olarak elle uyarlanmalı |
| terragrunt-expert | agent | C:\Users\PC\.codex\agents\terragrunt-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\terragrunt-expert.md olarak elle uyarlanmalı |
| test-automator | agent | C:\Users\PC\.codex\agents\test-automator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\test-automator.md olarak elle uyarlanmalı |
| tooling-engineer | agent | C:\Users\PC\.codex\agents\tooling-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\tooling-engineer.md olarak elle uyarlanmalı |
| trend-analyst | agent | C:\Users\PC\.codex\agents\trend-analyst.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\trend-analyst.md olarak elle uyarlanmalı |
| typescript-pro | agent | C:\Users\PC\.codex\agents\typescript-pro.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\typescript-pro.md olarak elle uyarlanmalı |
| ui-designer | agent | C:\Users\PC\.codex\agents\ui-designer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ui-designer.md olarak elle uyarlanmalı |
| ui-fixer | agent | C:\Users\PC\.codex\agents\ui-fixer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ui-fixer.md olarak elle uyarlanmalı |
| ui-ux-tester | agent | C:\Users\PC\.codex\agents\ui-ux-tester.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ui-ux-tester.md olarak elle uyarlanmalı |
| ux-researcher | agent | C:\Users\PC\.codex\agents\ux-researcher.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\ux-researcher.md olarak elle uyarlanmalı |
| visual-asset-generator | agent | C:\Users\PC\.codex\agents\visual-asset-generator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\visual-asset-generator.md olarak elle uyarlanmalı |
| vue-expert | agent | C:\Users\PC\.codex\agents\vue-expert.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\vue-expert.md olarak elle uyarlanmalı |
| websocket-engineer | agent | C:\Users\PC\.codex\agents\websocket-engineer.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\websocket-engineer.md olarak elle uyarlanmalı |
| windows-infra-admin | agent | C:\Users\PC\.codex\agents\windows-infra-admin.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\windows-infra-admin.md olarak elle uyarlanmalı |
| wordpress-master | agent | C:\Users\PC\.codex\agents\wordpress-master.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\wordpress-master.md olarak elle uyarlanmalı |
| workflow-orchestrator | agent | C:\Users\PC\.codex\agents\workflow-orchestrator.toml | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | Dosya varlığı ve adı PowerShell ile doğrulandı | Claude Code: .claude\agents\workflow-orchestrator.md olarak elle uyarlanmalı |
| amitchorasiya.cloude-code-toolbox-vscode | vscode-extension | VS Code extension registry | 1.0.43 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| anthropic.claude-code | vscode-extension | VS Code extension registry | 2.1.325 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| continue.continue | vscode-extension | VS Code extension registry | 2.0.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| ms-python.debugpy | vscode-extension | VS Code extension registry | 2026.6.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| ms-python.python | vscode-extension | VS Code extension registry | 2026.10.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| ms-python.vscode-pylance | vscode-extension | VS Code extension registry | 2026.4.1 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| ms-python.vscode-python-envs | vscode-extension | VS Code extension registry | 1.42.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| ms-vscode.notepadplusplus-keybindings | vscode-extension | VS Code extension registry | 1.0.7 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| openai.chatgpt | vscode-extension | VS Code extension registry | 26.1111.21308 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| openai.codex-audio | vscode-extension | VS Code extension registry | 26.1111.21308 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| redhat.java | vscode-extension | VS Code extension registry | 1.58.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| vscjava.vscode-gradle | vscode-extension | VS Code extension registry | 3.19.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| vscjava.vscode-java-debug | vscode-extension | VS Code extension registry | 0.60.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| vscjava.vscode-java-dependency | vscode-extension | VS Code extension registry | 0.27.7 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| vscjava.vscode-java-pack | vscode-extension | VS Code extension registry | 0.31.2 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| vscjava.vscode-java-test | vscode-extension | VS Code extension registry | 0.47.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| vscjava.vscode-maven | vscode-extension | VS Code extension registry | 0.46.0 | [Doğrulanmadı — kaynak bulunamadı] | code --list-extensions --show-versions | Claude Desktop karşılığı yok — taşınamaz |
| claude | cli-tool | C:\Users\PC\.local\bin\claude.exe | 2.1.325 | [Doğrulanmadı — kaynak bulunamadı] | claude --version | Doğrudan taşınamaz |
| codex | cli-tool | C:\Users\PC\AppData\Local\OpenAI\Codex\bin\codex.exe | 0.169.0-alpha.11.1 | [Doğrulanmadı — kaynak bulunamadı] | codex --version | Doğrudan taşınamaz |
| uv | cli-tool | C:\Users\PC\.local\bin\uv.exe | 0.13.8 | [Doğrulanmadı — kaynak bulunamadı] | uv --version | Doğrudan taşınamaz |
| npx | cli-tool | C:\Program Files\nodejs\npx.ps1 | 12.2.2 | [Doğrulanmadı — kaynak bulunamadı] | npx --version | MCP command yürütücüsü olarak dolaylı kullanılabilir |
| node | cli-tool | C:\Program Files\nodejs\node.exe | v24.22.1 | [Doğrulanmadı — kaynak bulunamadı] | node --version | Doğrudan taşınamaz |
| Ollama | local-model | C:\Users\PC\AppData\Local\Programs\Ollama\ollama.exe; C:\Users\PC\.ollama | Çalışan instance yok | [Doğrulanmadı — kaynak bulunamadı] | ollama sürüm denemesi bağlantı olmadığını bildirdi | Taşınamaz |
| LM Studio | local-model | C:\Users\PC\.lmstudio | [Doğrulanmadı] | [Doğrulanmadı — kaynak bulunamadı] | .lmstudio\mcp.json ve model kökü bulundu | Taşınamaz |
| Claude Desktop yapılandırması | other | C:\Users\PC\AppData\Roaming\Claude\claude_desktop_config.json | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | Dosya mevcut; mcpServers boş | Hedef dosya; mevcut MCP yok |
| Codex kullanıcı beceri kataloğu | other | C:\Users\PC\.codex\skills | [Dosya bazlı] | [Doğrulanmadı — kaynak bulunamadı] | 43 SKILL.md klasörü | Seçilerek manuel yüklenebilir |
| Codex kullanıcı ajan kataloğu | other | C:\Users\PC\.codex\agents | [Dosya bazlı] | [Doğrulanmadı — kaynak bulunamadı] | 176 TOML dosyası | Claude Code'a elle uyarlanabilir |
| Claude Code beceri kökü | other | C:\Users\PC\.claude\skills | [Dosya bazlı] | [Doğrulanmadı — kaynak bulunamadı] | reverse-engineer-anything bulundu | Claude Code içinde mevcut |
| Proje Ruflo yapılandırması | other | C:\Users\PC\Desktop\Thedivision2program\.agents\config.toml | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | ruflo MCP bölümü | JSON'a elle çevrilir |
| Proje Git remote'u | other | C:\Users\PC\Desktop\Thedivision2program\.git\config | Git metadata | https://github.com/FEDERALTURK/td2-loot-advisor.git | remote.origin.url | Taşınabilir araç değil |
| VS Code proje önerileri | other | TD2 Loot Advisor.code-workspace | [Dosyada yok] | [Doğrulanmadı — kaynak bulunamadı] | Python/Pylance/Flutter/Dart önerileri | Taşınamaz |

## 3. Claude Desktop'a taşıma planı

### Beceriler

Ziplenerek ayrı ayrı yüklenebilecek proje klasörleri:

- .agents\skills\brag
- .agents\skills\brag-slim
- .agents\skills\memory-management
- .agents\skills\modern-web-guidance
- .agents\skills\prompt-master
- .agents\skills\supabase
- .agents\skills\supabase-postgres-best-practices
- .agents\skills\swarm-orchestration

reverse-engineer-anything için aynı SHA-256 değerine sahip iki kopyadan yalnız biri seçilmelidir. template, içeriği incelenmeden yüklenmemelidir. Claude: Settings → Capabilities → Skills → Upload a Skill.

### MCP sunucuları

Claude Desktop yapılandırması mevcut fakat mcpServers boş. Salt-okunur envanter bunu değiştirmedi. Ruflo için kullanıcı tarafından incelenip uygulanabilecek tam JSON bloğu:

~~~json
{
  "mcpServers": {
    "ruflo": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "ruflo@latest", "mcp", "start"]
    }
  }
}
~~~

npx -y ağdan paket çözümleme/kurulum davranışı doğurabilir. Bu görevde çalıştırılmadı; Ruflo kaynağı ve sürümü ayrıca doğrulanmalıdır.

### Ajanlar

Her C:\Users\PC\.codex\agents\<ad>.toml dosyası Claude Code için persona/instructions içeriği incelenerek C:\Users\PC\.claude\agents\<ad>.md biçimine elle uyarlanmalıdır. Claude Desktop'ın kendisinde genel ajan dosyası yükleme karşılığı yoktur.

## 4. Taşınamayanlar ve nedenleri

- 17 VS Code eklentisi: editör eklentisi oldukları için Claude Desktop'a yüklenemez.
- claude, codex, uv, node ve npx: CLI araçlarıdır; doğrudan taşınamaz.
- Ollama ve LM Studio: yerel model runtime'larıdır; Claude Desktop'a runtime olarak taşınamaz.
- 176 Codex TOML ajanı: Claude Desktop'a doğrudan taşınamaz; Claude Code'a elle uyarlanabilir.
- Git remote, workspace ve yapılandırma dosyaları araç olarak taşınamaz.

## 5. Kaynağı belirlenemeyenler

Kaynak bulunamayan her satır bilinçli olarak [Doğrulanmadı — kaynak bulunamadı] işaretlendi. Elle doğrulama noktaları:

- Beceri: SKILL.md, README.md, skills-lock.json ve manifest.
- Ajan: TOML metadata'sı, kurulum günlüğü veya paket manifesti.
- MCP: .agents\config.toml, .codex\config.toml, .copilot\mcp-config.json, .lmstudio\mcp.json.
- VS Code: Marketplace veya eklenti manifesti.
- CLI/model runtime: --version, kurulum manifesti ve uygulama About bilgisi.

Açık izin hatası raporlanmadı. Büyük kullanıcı veri depoları satır satır raporlanmadı; yalnız araç kökleri ve tanımlama dosyaları incelendi.

## 6. Çakışma uyarıları

- reverse-engineer-anything iki yerde bulundu ve aynı SHA-256 hash'e sahip; Claude'a iki kez yüklenmemeli.
- Proje .agents\skills ile kullanıcı .codex\skills aynı ada sahip beceriler içerebilir; etkin sürüm belirsizleşmemesi için tek kaynak seçilmeli.
- skills-lock.json yalnız modern-web-guidance, supabase ve supabase-postgres-best-practices için hash içeriyor.
- Claude Desktop, Copilot ve LM Studio mcpServers anahtarları boş; yalnız proje .agents\config.toml Ruflo tanımı içeriyor.

## Doğrulama

- 8 proje becerisinin tamamı tabloda mevcut.
- 176 Codex ajanının tamamı ayrı satırda mevcut.
- Gizli değerler rapora yazılmadı; kontrol rapor dosyasının anahtar adı kalıpları ve bilinen değer kalıplarıyla yapılacak.
- Yalnız bu rapor dosyası oluşturuldu; kurulum ve yapılandırma değişikliği yapılmadı.

