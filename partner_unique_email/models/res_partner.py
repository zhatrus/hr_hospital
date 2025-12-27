from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    email_normalized = fields.Char(
        string="Normalized Email",
        index=True,
        copy=False,
        help="Lowercase, trimmed email used for uniqueness constraint.",
    )

    _sql_constraints = [
        (
            "email_normalized_uniq",
            "unique(email_normalized)",
            "Email must be unique across partners.",
        ),
    ]

    @staticmethod
    def _normalize_email(email):
        return (email or "").strip().lower() or False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "email" in vals:
                vals["email_normalized"] = self._normalize_email(vals.get("email"))
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if "email" in vals:
            vals["email_normalized"] = self._normalize_email(vals.get("email"))
        return super().write(vals)

    @api.constrains("email_normalized")
    def _check_unique_email_normalized(self):
        for partner in self:
            if not partner.email_normalized:
                continue
            duplicate = self.search_count([
                ("email_normalized", "=", partner.email_normalized),
                ("id", "!=", partner.id),
            ])
            if duplicate:
                raise ValidationError(
                    "Email must be unique across partners (case-insensitive)."
                )
