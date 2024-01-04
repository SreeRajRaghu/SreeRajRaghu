from odoo import fields, models


class LabTestInherit(models.Model):
    _inherit = 'medical.lab.test'

    clinic_id = fields.Many2one(related='appointment_id.clinic_id')