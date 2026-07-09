# Маяк Авито — Scan Orchestration & Listing State Owner Decisions Capture v1.0

## Metadata
- status: approved owner decision capture for governance use;
- date: 2026-07-09;
- module: 06-scan-orchestration-and-listing-state;
- roadmap gate: SOLS-01;
- not runtime/code/schema/parser/egress/notification/UI/deploy authorization.

## Owner decisions
1. Current Scan scope is new listings only, not old-listing price-change tracking.
2. Price may remain display/parser candidate data.
3. Price-change tracking and price-pair notification/event are deferred/disabled until separately approved.
4. Newest-first monitoring is required.
5. Parser Adapter owns observed order, sort context and publication/sort signals; Scan does not parse Avito.
6. Missing/ambiguous/unproven sort context means blocked/ambiguous/sort-not-proven, not false no-new.
7. Rolling anchors are compact memory.
8. Scan does not create full user-visible archive of old listings/cards/descriptions/phones/sellers/search history.
9. Anchor state updates after every successful comparison-eligible scan.
10. Anchor window size is not hard-coded and is future Admin-configurable.
11. Lost anchors and window overflow are different states.
12. Lost anchors: latest 3 may be state-restored/latest-fresh, not confirmed-new; then anchors update from current top-window.
13. Window overflow remains future design.
14. External failure, Avito unavailable, CAPTCHA, route failure, parser failure, malformed or ambiguous outcome is not no-new.
15. External failure does not erase baseline/anchors, does not advance anchors and does not create new-listing facts.
16. Keep one pending recovery scan, not accumulated missed scans.
17. One recovery result may be reported after entitlement expiry if failure began while access was active; then normal entitlement rules apply.
18. No-new status must not spam every interval by default.
19. One Beacon must not have parallel active comparison commits.
20. Lifecycle and entitlement must be re-checked before user-visible commit.
21. Paused/archived/deleted/frozen/denied/ambiguous/expired normal state blocks normal result except one recovery grace case.
22. Scan emits safe facts/status only; Notification Delivery and UI/channel modules own delivery/rendering.
23. Scheduler, worker, DB, parser/provider, Egress, Notification, UI, deploy, secrets and raw provider payload retention remain gated.
24. Older playbook v1.0 price-pair direction is superseded for current owner scope, not deleted from history.
25. OD-011 and OD-013 remain open.
26. No open decision is closed by assumption.
