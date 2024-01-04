# -*- coding: utf-8

from odoo import fields, models


class LastAction(models.Model):
    _name = "last.action"
    _description = "Last Action"

    name = fields.Char(required=True)
    use_in_state = fields.Selection([
        ('no_show', 'No Show'), ('no_answer', 'No Answer')
        ], required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
