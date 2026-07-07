# Маяк Авито — Environment Isolation Policy

**Версия:** 1.0  
**Статус:** APPROVED documentation policy  
**Дата:** 2026-07-07  
**Основание:** TASK-001 accepted evidence, `CURRENT_STATE.md`, `REMOTE_REPOSITORY_SUPERVISION_PROTOCOL_v1.0.md`.  
**Не является:** deployment runbook, port allocation, network design, service configuration или permission to use shared-host resources.

---

## 1. Цель

Политика устанавливает минимальные правила безопасной изоляции проекта на shared host и в будущих environments.

TASK-001 подтвердил, что observed host не пуст: на нём существуют foreign Docker/containerd/Nginx resources, а некоторые public and local ports уже заняты. Эти объекты не принадлежат Маяку.

## 2. Главный принцип

Наличие ресурса на host не означает право проекта его использовать.

Foreign containers, databases, queues, Nginx configuration, ports, networks, volumes, certificates, service accounts, credentials, logs and backups являются запрещёнными project dependencies, пока отдельное доказанное решение не установит ownership and access boundary.

## 3. Логические environment classes

Это классы документации, не provisioned infrastructure.

| Класс | Назначение | Статус |
|---|---|---|
| Local development | Изолированная разработка разработчика | implementation not started |
| Shared development host | Ограниченный evidence/source host | observed; foreign resources prohibited |
| Isolated test environment | Будущие repeatable tests and integration checks | not designed |
| Production | Будущая эксплуатация пользователей | not designed |

Ни один класс не определяет конкретный server, IP, port, container runtime, cloud provider, reverse proxy или deployment method.

## 4. Mandatory isolation boundaries

Перед созданием любого project runtime должны быть документально определены и приняты:

1. **Filesystem boundary** — dedicated project-owned working and data locations; foreign paths запрещены.
2. **Runtime boundary** — dedicated project process/container ownership; foreign service reuse запрещено.
3. **Data boundary** — project-owned database/queue/storage only; foreign database/queue access запрещён.
4. **Network boundary** — explicit bind address, exposure decision and port ownership; occupied port не переиспользуется предположением.
5. **Secret boundary** — project secrets isolated from shell history, source tree, ordinary logs and foreign configurations.
6. **Identity boundary** — project service identity and permission model documented before runtime creation.
7. **Backup boundary** — future backup and recovery scope covers only project-owned data.

## 5. Shared-host restrictions

На shared development host запрещено:

- подключаться к foreign databases, queues, containers or volumes;
- читать or alter foreign configuration, service units, environment files, credentials or process arguments;
- change Nginx, public ingress, firewall, ports, DNS, certificates or system services;
- treat occupied 80, 443, 5432 or any discovered listener as available project capacity;
- install packages, create users, create services, start containers or provision runtime before separate approved task;
- store project secrets in repository, shell history or ordinary task reports.

## 6. Allowed evidence work

До deployment documentation разрешается только evidence work that:

- is explicitly read-only;
- does not inspect secrets or foreign application data;
- reports only information necessary for the stated gate;
- does not infer ownership from visibility;
- keeps output free of credentials, private paths, tokens, personal data and foreign application internals.

## 7. Required gates for future environment use

No project environment may be created or used for runtime until accepted documents define:

- environment matrix;
- secret delivery and rotation boundary;
- network exposure and ingress ownership;
- observability and alerting boundary;
- backup and recovery boundary;
- release and rollback procedure;
- project-owned service/runtime identity;
- data ownership and migration policy.

## 8. Open decisions

The following remain open:

- concrete environments and providers;
- container versus non-container runtime;
- port assignments;
- ingress/reverse-proxy/TLS ownership;
- database/queue provisioning;
- secret-management mechanism;
- service accounts and least-privilege permissions;
- production backup and disaster-recovery targets.

This policy must not be used to fill any open decision by assumption.

## 9. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | Зафиксированы shared-host limits и mandatory project-isolation boundaries без deployment design. |
