# -*- coding: utf-8 -*-

from odoo import fields, models


class MedicalConfig(models.Model):
    _inherit = 'medical.config'

    time_off_type_id = fields.Many2one('hr.leave.type', string="Time Off Type")
