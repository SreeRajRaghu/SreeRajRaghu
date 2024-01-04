# -*- coding: utf-8 -*-

from odoo import fields, models


class DiscountReason(models.Model):
    _name = 'discount.reason'
    _description = "Discount Reason"

    name = fields.Char(required=True)
