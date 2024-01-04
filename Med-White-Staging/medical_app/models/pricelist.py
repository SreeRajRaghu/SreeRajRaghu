# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


APPLY_INS_DISC_SELECTION = [('after', _('After')), ('with', _('With'))]
APPLY_INS_DISC_STRING = 'Calculate Patient Share'
APPLY_INS_DISC_HELP = """
        After :
        - Calculate Patient Share After Insurance Company Discount
        - 100 - 20% = 80/- (DED10%) KD: 8/- = 72/-
        With :
        - Calculate Patient Share and Insurance Company Discount Togather
        - KD: 100 - 20% - (DED10%) KD:10/ = 70 /-
        """


class Pricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'product.pricelist']

    currency_id = fields.Many2one(trackin=True)
    company_id = fields.Many2one(default=lambda self: self.env.company, tracking=True)
    insurance_company_id = fields.Many2one(
        'res.partner', string="Insurance Company",
        domain="[('is_insurance_company', '=', True)]", tracking=True)
    insurance_parent_id = fields.Many2one(related="insurance_company_id.parent_id", store=True, tracking=True)
    scheme_code = fields.Char("Scheme Code", tracking=True)

    patient_share = fields.Float("Patient's Share", help="If value <= 0 then it will be ignored.", tracking=True)

    share_limit_type = fields.Selection([('min', 'Min'), ('max', 'Max')], string="Share Limit Type", tracking=True)
    patient_share_limit = fields.Float("Patient Share Limit", help="If value <= 0 then it will be ignored.", tracking=True)
    insurance_disc = fields.Float("Insurance Company Discount", tracking=True)
    apply_ins_disc = fields.Selection(
        APPLY_INS_DISC_SELECTION, default='after',
        string=APPLY_INS_DISC_STRING, required=True,
        help=APPLY_INS_DISC_HELP, tracking=True)

    ins_based_on = fields.Selection([
        ('total', 'Total'), ('line', 'Per Service Line')],
        default='line', string="Insurance Based On", tracking=True)

    need_approval = fields.Boolean("Need Approval ?", tracking=True)
    resource_ids = fields.One2many("medical.resource", "pricelist_id", string="Resources", tracking=True)

    def action_update_all_lines(self):
        self.ensure_one()
        self.item_ids.write({
            'patient_share': self.patient_share,
            'patient_share_limit': self.patient_share_limit,
            'insurance_disc': self.insurance_disc,
            'apply_ins_disc': self.apply_ins_disc,
            'share_limit_type': self.share_limit_type,
        })

    def get_ins_values(self, pricelist_price, ins_vals):
        """
            ins_fixed
            insurance_disc
            apply_ins_disc
            patient_share
            share_limit_type
            patient_share_limit
        """
        ins_fixed = ins_vals.get('ins_fixed')
        if ins_fixed:
            patient_share_price = ins_fixed
            ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
            ins_price_unit = ins_price_unit - patient_share_price
        elif ins_vals['insurance_disc'] >= 0:
            if ins_vals['apply_ins_disc'] == 'with':
                ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
                patient_share_price = pricelist_price * (ins_vals['patient_share'] / 100)
                ins_price_unit = ins_price_unit - patient_share_price
            else:
                # AFTER
                ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
                patient_share_price = ins_price_unit * (ins_vals['patient_share'] / 100)
                ins_price_unit = ins_price_unit - patient_share_price

        limit_type = ins_vals['share_limit_type']

        if limit_type:
            if limit_type == 'min':
                limit_amount = max(patient_share_price, ins_vals['patient_share_limit'])
            else:
                limit_amount = min(patient_share_price, ins_vals['patient_share_limit'])
            patient_share_price = limit_amount
            ins_price_unit = ins_price_unit - (limit_amount - patient_share_price)
        ins_vals.update({
            'price_unit': patient_share_price,
            'ins_price_unit': ins_price_unit
        })
        return ins_vals


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    patient_share = fields.Float("Patient's Share", help="If value <= 0 then it will be ignored.")
    share_limit_type = fields.Selection([('min', 'Min'), ('max', 'Max')], string="Share Limit Type")
    ins_fixed = fields.Float("Fixed Ins. Amount")
    patient_share_limit = fields.Float("Patient Share Limit", help="If value <= 0 then it will be ignored.")
    insurance_disc = fields.Float("Insurance Company Discount")
    apply_ins_disc = fields.Selection(
        APPLY_INS_DISC_SELECTION, default='after',
        string=APPLY_INS_DISC_STRING, required=True,
        help=APPLY_INS_DISC_HELP)

    insurance_company_id = fields.Many2one(related="pricelist_id.insurance_company_id")

    @api.constrains('product_tmpl_id', 'pricelist_id')
    def _check_duplicate_product(self):
        for item in self:
            duplicate_items = self.search([
                ('id', '!=', item.id),
                ('product_tmpl_id', '=', item.product_tmpl_id.id),
                ('pricelist_id', '=', item.pricelist_id.id),
            ])
            if duplicate_items:
                raise ValidationError("Duplicate product in pricelist %s is not allowed." % item.product_tmpl_id.name)

    @api.constrains('patient_share', 'insurance_disc')
    def _constrains_patient_share_ins_cmp_disc(self):
        for item in self:
            if item.patient_share < 0 or item.patient_share > 100:
                raise ValidationError(_('Patient Share must be between 0 and 100.'))
            if item.insurance_disc < 0 or item.insurance_disc > 100:
                raise ValidationError(_('Insurance Company Discount must be between 0 and 100.'))
