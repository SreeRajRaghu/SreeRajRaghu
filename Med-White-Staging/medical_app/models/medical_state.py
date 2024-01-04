# -*- coding: utf-8 -*-

from odoo import fields, models
from .medical_order import ORDER_STATES


class MedicalState(models.Model):
    _name = 'medical.state'
    _description = 'Session State'
    _order = 'sequence, name, id'

    name = fields.Selection(ORDER_STATES, default='draft', required=True)
    sequence = fields.Integer(string='Sequence', default=1)
    s_color = fields.Char(string='Color Code')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('uniq_state_name', 'unique (name, company_id)', 'State must be unique per company.')
    ]
