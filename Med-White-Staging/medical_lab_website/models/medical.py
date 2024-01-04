
from odoo import fields, models


class MedicalConfig(models.Model):
    _inherit = 'medical.config'

    is_online_reception = fields.Boolean("Is Online Reception")
