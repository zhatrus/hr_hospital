# System Patterns

## Архітектура
Стандартна модульна архітектура Odoo:
- models (Python)
- views/wizard (XML)
- security/data
- static/description

## Ключові компоненти
- hr.hospital.patient
- hr.hospital.doctor
- hr.hospital.visit
- Wizard-и для масових/допоміжних операцій

## Патерни розробки
- XML form/tree views
- Wizard-и як `ir.actions.act_window` з `target="new"`

## Data Flow
UI (views) -> ORM (models) -> DB, з додатковими діями через wizard-и.
