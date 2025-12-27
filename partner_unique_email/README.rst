Partner Unique Email
====================

Prevents duplicate partner emails across the system by normalizing and enforcing uniqueness on partner email addresses.

Features
--------
- Normalizes emails (trim + lowercase) into a stored field.
- Enforces uniqueness across all partners (companies and contacts).
- Allows multiple empty emails (constraint applies only when email is set).

Usage
-----
- Install the module.
- When creating or editing partners, duplicate emails (case-insensitive, trimmed) will raise a validation error.

Compatibility
-------------
- Tested on Odoo 17.0.

License
-------
LGPL-3
