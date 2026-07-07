# Operations documentation

**Статус:** APPROVED documentation baseline; runtime/deploy absent.

Current documents cover environment isolation/matrix, observability, backup/recovery, deployment/release boundaries and Windows Egress Agent boundaries.

Они не создают project service, container, port, ingress, TLS, backup, scheduler, queue, credential или production infrastructure. Foreign/shared-host resources не принадлежат проекту и не могут быть переиспользованы без отдельного approved ownership decision and implementation task.

Смотри `docs/00-governance/DOCUMENTATION_BACKLOG.md`, DB-05 and DB-06.
