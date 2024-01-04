from odoo import fields, models


class LabTestDepartment(models.Model):
    _inherit = 'medical.labtest.department'

    stamp_image = fields.Binary("Stamp")
    sign_image = fields.Binary("Signature")