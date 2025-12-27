from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    email_normalized = fields.Char(
        string="Normalized Email",
        compute="_compute_email_normalized",
        store=True,
        index=True,
        readonly=False,
        help="Lowercase, trimmed email used for uniqueness constraint.",
    )

    _sql_constraints = [
        (
            "email_normalized_uniq",
            "unique(email_normalized)",
            "Email must be unique across partners.",
        ),
    ]

    @api.depends("email")
    def _compute_email_normalized(self):
        for partner in self:
            email = (partner.email or "").strip().lower()
            partner.email_normalized = email or False
