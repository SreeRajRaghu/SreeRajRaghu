# coding: utf-8

from odoo import fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
