# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| When creating a pull request, opening a PR, or preparing changes for review. | branch-pr | C:\Users\cchacon\.gemini\antigravity\skills\branch-pr\SKILL.md |
| When user says "caveman mode", "talk like caveman", "use caveman", "less tokens", "be brief", or invokes /caveman. | caveman | C:\Users\cchacon\.gemini\antigravity\skills\caveman\SKILL.md |
| when a PR would exceed 400 changed lines, when planning chained PRs, stacked PRs, or reviewable slices. | chained-pr | C:\Users\cchacon\.gemini\antigravity\skills\chained-pr\SKILL.md |
| when writing guides, READMEs, RFCs, onboarding docs, architecture docs, or review-facing documentation. | cognitive-doc-design | C:\Users\cchacon\.gemini\antigravity\skills\cognitive-doc-design\SKILL.md |
| when drafting or posting feedback, review comments, maintainer replies, Slack messages, or GitHub comments. | comment-writer | C:\Users\cchacon\.gemini\antigravity\skills\comment-writer\SKILL.md |
| When writing Go tests, using teatest, or adding test coverage. | go-testing | C:\Users\cchacon\.gemini\antigravity\skills\go-testing\SKILL.md |
| When creating a GitHub issue, reporting a bug, or requesting a feature. | issue-creation | C:\Users\cchacon\.gemini\antigravity\skills\issue-creation\SKILL.md |
| When user says "judgment day", "judgment-day", "review adversarial", "dual review", "doble review", "juzgar", "que lo juzguen". | judgment-day | C:\Users\cchacon\.gemini\antigravity\skills\judgment-day\SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI. | skill-creator | C:\Users\cchacon\.gemini\antigravity\skills\skill-creator\SKILL.md |
| when implementing a change, preparing commits, splitting PRs, or planning chained or stacked PRs. | work-unit-commits | C:\Users\cchacon\.gemini\antigravity\skills\work-unit-commits\SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### branch-pr

- Every PR MUST link an approved issue — no exceptions
- Every PR MUST have exactly one `type:*` label
- Automated checks must pass before merge is possible
- Blank PRs without issue linkage will be blocked by GitHub Actions

### caveman

- Extremely concise output to save tokens while keeping technical accuracy
- No pleasantries or fluff

### chained-pr

- MUST split when a PR exceeds 400 changed lines unless maintainer-approved
- Scope: One deliverable work unit per PR; do not mix unrelated items
- Every chained PR MUST state where it starts, ends, what came before, and what comes next
- PR #1 targets feature/tracker branch; later child PRs target the immediate previous PR branch

### cognitive-doc-design

- Lead with the answer (decision/action first, context later)
- Use progressive disclosure (happy path first, then edge cases)
- Chunk information and use signposting (headings, callouts)
- Prefer tables, checklists, and templates for easier recognition

### comment-writer

- Formula: <Direct observation/request> \n <Why it matters> \n <Concrete next action>
- Be direct but warm, focused on concrete next steps

### go-testing

- Use Table-Driven Tests pattern for multiple test cases
- Create Helper functions for common setup
- Utilize teatest for TUI integration tests (e.g. testing Bubbletea)
- Apply Golden File testing for output comparisons

### issue-creation

- Blank issues are disabled — MUST use a template (bug report or feature request)
- Every issue gets `status:needs-review` automatically on creation
- A maintainer MUST add `status:approved` before any PR can be opened
- Questions go to Discussions, not issues

### judgment-day

- Parallel adversarial review protocol: launch TWO sub-agents independently
- Obtain skill registry and build Compact Rules before launching
- Categorize warnings: "real" (needs fix) or "theoretical" (INFO, do not block)
- Synthesize findings (Confirmed, Suspect, Contradiction)
- Re-judge with both agents after fixes, escalate if not clean after 2 iterations

### skill-creator

- Create skills when a pattern is repeated, workflow needs instructions, or there are project-specific conventions
- Do not create for trivial tasks or already documented information
- Must include SKILL.md with frontmatter (name, description, etc.)

### work-unit-commits

- Commit by work unit (deliverable behavior, fix, migration, or doc)
- Do not commit by file type (e.g., all models, all services)
- Keep tests and docs with the code they verify or explain
- Provide context in commit messages so reviewers understand why it exists

### Shell Execution (Windows/PowerShell)

- **Atomic Git Commands**: Execute `git add`, `git commit`, and `git push` as separate, discrete steps. 
- **Avoid Bash Operators**: Do NOT use `&&` or `||` for chaining commands; use `;` if necessary, but separate calls are preferred for reliability.
- **Pathing**: Use backslashes `\` for paths in terminal commands.
- **Verification**: Always check `git status` or command output before assuming success.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | C:\Antigravity\md2kindle\AGENTS.md | Index — references files below |
| md2kindle.py | md2kindle.py | Referenced by AGENTS.md |
| cli.py | md2kindle/app/cli.py | Referenced by AGENTS.md |
| pipeline.py | md2kindle/app/pipeline.py | Referenced by AGENTS.md |
| settings.py | md2kindle/core/config/settings.py | Referenced by AGENTS.md |
| binaries.py | md2kindle/core/config/binaries.py | Referenced by AGENTS.md |
| pipeline.py (model) | md2kindle/core/models/pipeline.py | Referenced by AGENTS.md |
| setup.py | md2kindle/core/logging/setup.py | Referenced by AGENTS.md |
| service.py | md2kindle/services/converter/service.py | Referenced by AGENTS.md |
| api.py | md2kindle/services/mangadex/api.py | Referenced by AGENTS.md |
| downloader.py | md2kindle/services/mangadex/downloader.py | Referenced by AGENTS.md |
| service.py (delivery) | md2kindle/services/delivery/service.py | Referenced by AGENTS.md |
| telegram.py | md2kindle/services/delivery/telegram.py | Referenced by AGENTS.md |
| r2.py | md2kindle/services/delivery/r2.py | Referenced by AGENTS.md |
| usb.py | md2kindle/services/delivery/usb.py | Referenced by AGENTS.md |
| ffsend.py | md2kindle/services/delivery/ffsend.py | Referenced by AGENTS.md |
| d1.py | md2kindle/services/delivery/d1.py | Referenced by AGENTS.md |
| ranges.py | md2kindle/utils/ranges.py | Referenced by AGENTS.md |
| .env | .env | Referenced by AGENTS.md |
| manga-pipeline.yml | .github/workflows/manga-pipeline.yml | Referenced by AGENTS.md |
| telegram-bot.js | .github/workers/telegram-bot.js | Referenced by AGENTS.md |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
