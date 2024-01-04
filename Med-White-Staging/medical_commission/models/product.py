# -*- coding: utf-8 -*-
from odoo import fields, models

TEST_TYPE = [('None', 'N/A'), ('inside', 'Inside Test'), ('outside', 'Outside Test')]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    test_type = fields.Selection(TEST_TYPE, string="Test Type")


# class Product(models.Model):
#     _inherit = "product.product"

#     test_type = fields.Selection(TEST_TYPE, string="Test Type")
