# Маяк Авито — Owner Egress Decisions Capture v1.0

**Статус:** APPROVED owner decision capture for Module 07 semantic planning  
**Дата:** 2026-07-12  
**Модуль:** `07-egress-routing`  
**Roadmap step:** `ER-01`  
**Technical task:** `ER-01-GOVERNANCE-CAPTURE-20260712-003`  
**Source-of-truth playbook:** `docs/04-modules/07-egress-routing/MODULE_PLAYBOOK.md`  
**Governance decision:** `ADR-0019`

## 1. Назначение

Этот документ фиксирует предоставленные владельцем решения и границы для Egress Routing до использования этих решений в semantic contracts, synthetic fixtures, tests, product-code, runtime или operations.

Документ не реализует route, agent, proxy, VPN, tunnel, browser worker, Windows service, cookies/session storage, live Avito access, persistence, migrations или deploy.

## 2. Primary route direction

Первичный целевой кандидат для Egress Routing — Linux/server reference-style outbound route.

Под этим понимается bounded server-side HTTP/transport path, концептуально совместимый с reference-style parser approach, без отдельного постоянного browser process для каждого Beacon и без переноса всего SaaS на Windows.

Этот route family не считается production-proven для проекта «Маяк Авито».

До implementation требуется отдельный `proof_only` step с точными:

- route identity;
- request envelope;
- headers/fingerprint boundary;
- cookie/session policy, если она действительно потребуется;
- safe rate and attempt limits;
- no-secrets logging;
- success, failure and STOP criteria;
- Parser/Egress outcome separation;
- explicit no-CAPTCHA-solving rule.

Это решение не разрешает live Avito traffic, mass requests, unbounded retry, raw payload retention или production parser implementation.

## 3. Browser-extension route evidence and boundary

Владелец подтверждает, что browser-extension route ранее фактически работал с Avito.

Это считается owner-provided evidence, что browser-extension approach в принципе может работать как route family.

Это не доказывает:

- production-scale SaaS readiness;
- масштабирование на 1000 Beacons;
- стабильность provider behavior;
- окончательную Windows topology;
- необходимость installer/native host;
- безопасность personal browser profile;
- автоматическое разрешение production implementation.

Future Avito browser-extension route может рассматриваться только как:

- fallback route family;
- proof route;
- development/testing route;
- future bounded browser-worker route after separate gates.

Future production-scope extension должна сохранять только необходимый Avito route scope:

- Avito page interaction/extraction;
- bounded assignment execution;
- safe result return;
- explicit route/transport outcome classification;
- no secrets in logs;
- exact minimum site permissions.

Из production scope должны быть исключены, если отдельный gate не докажет необходимость:

- self-editing extension behavior;
- developer-control/editing features;
- unrelated GDevelop/Web Hands helpers;
- unrelated automation targets;
- unnecessary native-host capabilities;
- unnecessary installer automation;
- broad permissions beyond exact Avito route needs.

Browser-extension route не владеет Account, Beacon, Parser, Scan, Notification, database или SaaS runtime.

## 4. Linux and Windows boundary

Полный SaaS на Windows сейчас не выбирается.

Linux остаётся предпочтительным target environment для SaaS core:

- API;
- PostgreSQL;
- scheduler;
- workers;
- module runtime;
- deployment;
- operations.

Windows может использоваться только там, где отдельное доказательство покажет необходимость Windows/browser behavior:

- Windows Egress Agent;
- Windows VM;
- Windows browser worker;
- browser-extension fallback.

Windows VM, Windows Agent и Windows Browser Worker являются заменяемыми execution dependencies.

Они:

- получают только bounded assignment;
- возвращают explicit outcome;
- не владеют business state;
- не имеют primary database access;
- не получают full Account, Beacon, tariff, Scan history или Notification history;
- не становятся источником истины проекта.

Если Linux/server reference-style proof не проходит, выбор конкретной Windows topology требует отдельного решения и evidence.

## 5. Development owner bridge

При временной неработоспособности primary route во время разработки допускается owner-assisted development bridge.

Development bridge:

- используется только для отдельного development/proof scope;
- требует явного согласия владельца на конкретное использование;
- не является production dependency;
- не является доказательством масштабируемости;
- не является окончательной архитектурой;
- должен быть заменяем будущим production route;
- не должен раскрывать или сохранять secrets и raw private data без отдельного gate.

## 6. Browser worker model

Отдельный постоянно работающий browser для каждого Beacon не является целевой архитектурой.

Предпочтительный fallback model after separate implementation gate:

- bounded browser worker pool;
- limited concurrency;
- controlled project-owned sessions;
- route lease and assignment lifecycle;
- explicit outcome;
- safe worker recycling/restart;
- no full business state inside browser worker.

Temporary proof с одним или несколькими browsers допустим только в отдельном bounded proof task.

Количество Beacons не должно автоматически определять равное количество постоянно открытых browser processes.

## 7. Russian residential route

Russian residential proxy / Russian residential route разрешён как возможный future route type, если доказательства покажут необходимость.

Сейчас не выбираются:

- конкретный provider;
- конкретный product or tariff;
- credential format;
- payment/provider contract;
- protocol;
- route priority;
- production configuration.

Использование такого route требует отдельных proof, security, secret-storage, rate, cost and operations gates.

## 8. Cookies and sessions

Cookies/session могут использоваться только после отдельного isolated project session gate.

Допустимая будущая модель должна использовать:

- project-owned isolated session;
- project-owned cookie profile;
- bounded route scope;
- explicit storage boundary;
- safe rotation and revocation;
- redacted diagnostics;
- no secret values in Git, logs or ordinary reports.

Запрещено:

- читать personal Chrome profile;
- читать browser passwords;
- использовать unrelated or foreign cookies;
- использовать private owner session по умолчанию;
- передавать cookie/session values in CLI prompts or reports;
- хранить cookie/session values in Git;
- логировать cookies, tokens or session secrets.

В текущем scope cookies/session implementation отсутствует.

## 9. CAPTCHA and provider restrictions

CAPTCHA solving и CAPTCHA bypass запрещены.

CAPTCHA, challenge, restriction or provider rejection are not a clean empty result and do not mean that Beacon should be forgotten.

Egress Routing должен в будущей semantic/runtime модели:

- return explicit technical outcome;
- preserve safe reason/evidence reference;
- change route health/restriction state according to approved policy;
- if needed place affected route in degraded/restricted/quarantined state;
- not issue affected new assignments according to policy;
- not erase route history.

Scan Orchestration владеет pending recovery scan and business handling scan status.

Notification Delivery владеет доставкой сообщения пользователю.

Egress Routing не решает Scan success и не отправляет сообщение пользователю.

## 10. Policy-based automatic fallback

Автоматический fallback разрешён только как controlled policy-based behavior.

Будущая semantic policy может:

- проверить readiness, capability, purpose and scope;
- проверить health, restriction and quarantine state;
- выбрать следующий заранее approved route;
- записать selection and fallback reason;
- создать bounded fallback attempt;
- вернуть explicit fallback outcome;
- остановиться после approved bound.

Запрещено:

- random route switching;
- blind fallback;
- fallback without policy;
- fallback without audit/evidence;
- infinite fallback loop;
- use fallback as CAPTCHA bypass;
- hiding исходной route failure;
- самостоятельный выбор route Parser, Scan or Notification module.

Если все approved routes недоступны, Egress returns explicit unavailable, restricted, ambiguous or fallback-exhausted outcome.

## 11. Route selection authority

Runtime route selection принадлежит only Egress Routing.

Parser Adapter, Scan Orchestration, Beacon Management and Notification Delivery do not choose route.

Admin may in future request protected route policy changes through a separate capability, but does not perform runtime selection and does not write Egress state directly.

## 12. Minimal bounded assignment

Agent or browser worker receives only the minimum bounded assignment.

Допустимые semantic fields after exact task may include:

- assignment ID;
- correlation and causation IDs;
- purpose;
- safe request envelope;
- safe source/reference;
- timeout/deadline;
- route policy reference;
- expected response class;
- profile/evidence reference;
- redacted configuration reference.

Agent must not receive:

- full Account record;
- full Beacon record;
- tariff/payment state;
- full Scan history;
- Notification credentials or history;
- primary database credentials;
- global secrets;
- unbounded cookies;
- unrelated personal data.

## 13. Agent database boundary

Agent does not have direct access to primary project database.

Agent is a replaceable execution dependency and interacts only through bounded server contract / assignment protocol.

Compromise or failure of agent must not automatically reveal full SaaS state.

## 14. Live Avito proof boundary

Live Avito proof разрешён only as separate owner-approved `proof_only` task.

Each proof task must predefine:

- exact route family;
- exact purpose;
- exact test URL or URL class;
- maximum attempts;
- maximum duration;
- allowed safe logs;
- raw payload visibility and non-retention/redaction rule;
- forbidden secrets;
- success criteria;
- failure criteria;
- STOP conditions;
- final evidence report.

Первый proof не должен включать:

- mass scraping;
- production scheduler;
- database persistence;
- notification delivery;
- CAPTCHA solving;
- unbounded retry or fallback;
- raw payload publication;
- provider permission claims beyond actual evidence.

## 15. Current gates

После этого governance capture разрешено only use captured decisions as input for future exact semantic tasks.

Этот документ не разрешает:

- route runtime;
- proxy/VPN/tunnel implementation;
- concrete route provider selection;
- browser automation implementation;
- browser-extension modification;
- Windows Agent implementation;
- Windows service, native host or installer;
- cookies/session storage;
- live Avito proof;
- CAPTCHA solving;
- database schema;
- migrations;
- scheduler/worker runtime;
- Docker;
- CI/CD;
- deployment;
- ports, firewall, DNS, TLS or certificates;
- secrets or credentials;
- direct Parser, Scan, Notification or Beacon business-state mutation.

`OD-009`, `OD-010`, `OD-011` and `OD-013` remain open.

## 16. Consequence for the Module 07 roadmap

After independent acceptance of ER-01:

- ER-02 may define deterministic semantic contracts and synthetic fixtures only;
- ER-03 may define logical agent/route registration semantics only;
- ER-05 may define controlled policy-based fallback semantics only;
- ER-06 may define lease/assignment lifecycle semantics only;
- ER-07 and ER-08 may define transport/restriction/CAPTCHA outcomes without solving CAPTCHA;
- ER-09 remains implementation-gated for cookies/session/secrets;
- ER-10 remains proof and implementation gated for browser-extension/Windows fallback;
- ER-11 remains development-only and explicit-owner-consent gated;
- ER-13 may define proof rules but may not execute live proof without another exact task;
- ER-14 persistence/runtime remains blocked.

No later roadmap step is automatically authorized by this document.
