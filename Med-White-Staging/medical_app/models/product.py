# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalCategory(models.Model):
    _name = 'medical.category'
    _order = 'sequence, id'
    _description = 'Product Category'

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))

    name = fields.Char(string='Category Name', required=True, translate=True)
    parent_id = fields.Many2one('medical.category', string='Parent Category', index=True)
    child_ids = fields.One2many('medical.category', 'parent_id', string='Children Categories')
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of product categories.")
    image_128 = fields.Image("Image", max_width=128, max_height=128)
    product_ids = fields.One2many("product.product", "medical_categ_id", string="Products")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    def name_get(self):
        def get_names(cat):
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res
        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]


class ProductCategory(models.Model):
    _inherit = 'product.category'

    last_income_account_id = fields.Many2one('account.account', string='Last Deferred Revenue')
    discount_account_id = fields.Many2one('account.account', string='Discount account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    medical_categ_id = fields.Many2one('medical.category', string="Session Category")
    available_in_medical = fields.Boolean("Available In Session", default=True)
    is_medical_service = fields.Boolean(string='Is Session Service', default=False)
    is_medical_consumable = fields.Boolean(string='Is Session Consumable ?', default=False)
    # is_variant_price = fields.Boolean(string='Variant Price', default=False)
    duration = fields.Float(string='Duration', default=0.5)
    session_count = fields.Integer(string='No. Of Sessions', default=1)
    last_income_account_id = fields.Many2one('account.account', string='Last Deferred Revenue')
    discount_account_id = fields.Many2one('account.account', string='Discount account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')
    consumable_ids = fields.Many2many(
        'product.product', 'product_template_consumable_rel', 'parent_product_id', 'child_product_id',
        string='Mandatory Consumables', domain=[('is_medical_consumable', '=', True)])
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    next_app_after = fields.Integer("Next Appointment After")
