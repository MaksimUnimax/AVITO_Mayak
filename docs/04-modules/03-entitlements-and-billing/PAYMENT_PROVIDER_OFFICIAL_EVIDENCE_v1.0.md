# Маяк Авито — Payment Provider Official Evidence v1.0

**Статус:** APPROVED evidence capture for EB-08 planning/reference only  
**Дата:** 2026-07-08  
**Модуль:** `03-entitlements-and-billing`  
**Связанный governance decision:** `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`, `ADR-0013`

## 1. Purpose

This document captures official provider references for EB-08 `Payment provider adapter` planning/reference only.

It is not a runtime provider integration, SDK/API call implementation, webhook implementation, invoice/receipt/tax implementation, payment account setup, database schema, migration, repository, Admin UI, Web Cabinet UI, provider token/secret handling or entitlement-grant authority.

## 2. Current owner payment policy

Current owner policy remains:

- provider candidates: YooKassa, Telegram Stars, Tinkoff/T-Bank;
- first stage: manual renewal only;
- recurring payments are not implemented now;
- refunds are manual only;
- currencies: RUB and Telegram Stars;
- no trial/grace/proration;
- Free tariff is the alternative to trial/grace.

## 3. Global payment boundary

A payment provider response is external evidence only.

Raw provider payload is not entitlement authority.

Payment evidence must not create, change or extend access by itself.

A future entitlement transition requires a server-authorized business transition, idempotency, actor/service context where applicable, audit reference and an approved commit point.

## 4. YooKassa official reference

Official source title:

```text
Справочник API ЮKassa
```

Official URL:

```text
https://yookassa.ru/developers/api
```

Captured evidence:

YooKassa API reference describes methods for online payments and payouts.

The reference lists payment methods, invoices, refunds, receipts, payouts and webhooks.

The reference links to integration instructions, request/response format, authentication and idempotency-key requirements, OpenAPI specification, SDKs and incoming notifications/webhooks.

Project interpretation:

YooKassa is captured only as an official provider candidate reference.

This does not authorize SDK/API calls, webhooks, receipts, invoices, refunds, payment account setup, credentials or runtime integration.

## 5. Telegram Stars official references

Official source title:

```text
Bot Payments API for Digital Goods and Services
```

Official URL:

```text
https://core.telegram.org/bots/payments-stars
```

Official source title:

```text
Telegram Stars
```

Official URL:

```text
https://core.telegram.org/api/stars
```

Captured evidence:

Telegram Stars are virtual items for purchasing digital goods and services from bots and mini apps inside Telegram.

Official bot payments docs for digital goods/services state that digital goods/services payments use Telegram Stars.

For digital goods/services, invoices use currency XTR.

The documented Bot API flow includes sending invoice, receiving pre_checkout_query, answering it, receiving successful_payment, and storing telegram_payment_charge_id for possible future refund.

For digital goods/services, provider_token can be empty.

Telegram docs mention refundStarPayment for Stars refunds.

Project interpretation:

Telegram Stars are captured only as an official provider candidate reference.

Current owner decision still says manual renewal only and manual refunds only.

This does not authorize recurring Stars subscriptions, Stars refunds implementation, Bot API calls, provider tokens, Telegram runtime integration, payment screens or automatic entitlement grants.

## 6. Tinkoff / T-Bank official references

Official source title:

```text
T-Bank Dev Portal — Internet acquiring — Getting started
```

Official URL:

```text
https://developer.tbank.ru/eacq/intro
```

Official source title:

```text
T-Bank Dev Portal — T-API
```

Official URL:

```text
https://developer.tbank.ru/docs/api
```

Captured evidence:

T-Bank internet acquiring documentation states that internet acquiring allows accepting payments online: website, app, messengers, social networks, email and SMS.

It lists payment methods such as cards, SBP, T-Pay, SberPay, Mir Pay, Alfa Pay and Dolями.

The checklist includes selecting integration, applying for internet acquiring, creating an internet store in acquiring cabinet, setting up payment and online cash register integration.

T-API official docs list API areas including Payments and Trade Acquiring.

Project interpretation:

Tinkoff/T-Bank is captured only as an official provider candidate reference.

This does not authorize API calls, acquiring setup, online-cash-register implementation, receipts, invoices, credentials, payment account setup or runtime integration.

## 7. Explicit non-authorization

This evidence capture does not authorize:

runtime payment provider adapter;

provider SDK/API calls;

YooKassa runtime integration;

Telegram Stars runtime integration;

Tinkoff/T-Bank runtime integration;

webhooks;

payment account setup;

invoice, receipt or tax implementation;

refunds automation;

recurring billing;

payment reconciliation runtime;

card data handling;

provider credentials, tokens or secrets;

raw provider payload storage as entitlement state;

entitlement grant directly from provider response;

database schema;

repositories;

persistence;

migrations;

Admin UI;

Web Cabinet UI;

Telegram/MAX payment screens;

Beacon mutation;

scheduler integration;

notification sending;

Docker, CI/CD, deploy or runtime configuration.

## 8. Remaining open decisions and blockers

The following decisions remain open and must not be closed by assumption:

OD-010 — country-wide availability by market;

OD-011 — minimum monitoring frequency safety;

OD-013 — billing, audit and personal-data retention.

The following remain gated:

provider-specific runtime adapter implementation;

webhook processing;

payment reconciliation/refunds;

invoice/receipt/tax behavior;

physical persistence and migrations;

Admin UI/Web Cabinet runtime;

secrets/tokens/credentials handling.

## 9. Use in later roadmap steps

Later exact EB-08 tasks may use this document and ADR-0013 as official evidence input for provider-boundary documentation/reference preparation or deterministic semantic adapter contracts/tests only.

Any runtime provider adapter still requires a separate provider-specific exact task and must preserve the rule that provider response is evidence only, not entitlement authority.
