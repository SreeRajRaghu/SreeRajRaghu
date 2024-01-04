
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_allocate_eos = fields.Boolean(string='Auto Allocate EOS', config_parameter="hr_employee_eos.auto_allocate_eos")
