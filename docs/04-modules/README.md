# Автономные module playbooks

**Статус:** RESERVED — директории модулей созданы, но ни один playbook в репозитории пока не является `APPROVED`.

Для каждого из 13 модулей будет создан один самодостаточный `MODULE_PLAYBOOK.md`. Он обязан включать:

- цель, границы и data ownership;
- точные входы и выходы;
- интерфейсы и запрещённые прямые записи;
- fake dependencies, mocks, fixtures и input/output test vectors;
- roadmap шагов;
- acceptance tests;
- запреты и риски;
- формат report/handoff;
- append-only историю;
- версию встроенного contract package.

Агент получает только свой playbook и текущий task packet. Он не должен читать общее ТЗ или ожидать готовности соседнего модуля. Но playbook нельзя выпускать до утверждения общих контрактов и data ownership.
