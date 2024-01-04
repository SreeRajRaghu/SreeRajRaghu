from odoo import models, fields, _


class MedicalConfig(models.Model):
    _inherit = 'medical.config'

    scheduler_id = fields.Many2one(comodel_name="mssql.config", string="Mssql", required=False, )