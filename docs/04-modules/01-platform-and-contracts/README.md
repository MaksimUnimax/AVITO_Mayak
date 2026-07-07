# Platform & Contracts

**Статус:** APPROVED documentation playbook v1.0; Run 12 server synchronization/acceptance pending.

Canonical playbook:

- `MODULE_PLAYBOOK.md`

Module boundary:

- future application/package skeleton;
- common contract/error/idempotency/configuration/process conventions;
- architecture/import rules;
- migration tooling conventions only after separate gates;
- shared fake/test-support semantics.

The module does not own foreign business state and this publication creates no code, dependency files, lock, tests, migrations, database, runtime or infrastructure.

Next implementation activity is not automatic. It requires an exact task, isolated toolchain proof and the playbook gates.
