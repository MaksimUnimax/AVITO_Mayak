# Маяк Авито — правила ведения документации

**Версия:** 1.1
**Статус:** APPROVED

ChatGPT owns document content; CLI receives exact path, mode, literal text/append block, checks and commit/push permission. CLI must not improve, infer or silently change text.

Public GitHub `main` is repository source of truth. Before change and after report, ChatGPT independently reviews current remote state. `APPROVED` is explicit; candidate is not acceptance.

Append-only files are never edited, removed or reordered. Correction is a new final record.

Documents distinguish confirmed fact, accepted decision, assumption, open decision, risk/limit and external-reference deviation. Significant boundary/contract/data/security/role/route changes require a decision-log entry before dependent documents update.

CLI reports paths, checks, hashes, commit and push state. ChatGPT independently verifies actual remote content. Shared-host resources are not project resources.
