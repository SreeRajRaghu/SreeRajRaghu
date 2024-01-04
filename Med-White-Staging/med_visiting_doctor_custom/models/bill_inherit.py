# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from pytz import timezone, UTC
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MedicalResource(models.Model):
    _inherit = 'medical.resource'

    discount_line_ids = fields.One2many('discount.line', 'discount_id', string="Dashbaord Lines")
    is_visiting_doctor = fields.Boolean('Is Visiting Doctor?')
    percentage_or = fields.Selection([('percentage', 'Percentage'), ('by_value', 'By Values')], string='Percentage Or By Value')
    percentage = fields.Float('Percentage')

    @api.onchange('percentage_or')
    def onchange_percentage(self):
        if self.percentage_or == 'percentage':
            self.percentage = False


class DiscountLines(models.Model):
    _name = 'discount.line'
    _description = 'Commission Details'

    discount_id = fields.Many2one('medical.resource')
    from_ = fields.Integer('From')
    to_ = fields.Integer('To')
    percentage = fields.Float('Percentage')
