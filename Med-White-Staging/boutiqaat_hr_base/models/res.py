
from odoo import fields, models


class PassportHistory(models.Model):
    _inherit = 'res.bank'

    branch_name = fields.Char("Branch Name")
