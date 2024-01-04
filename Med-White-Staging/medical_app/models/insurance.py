# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class InsuranceCard(models.Model):
    _name = 'insurance.card'
    _description = 'Insurance Card'

    name = fields.Char("Card Name/No", required=True, default='101')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', string='Patient', required=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Insurance Scheme', required=True,
        domain="[('insurance_company_id', '=', insurance_company_id)]")
    # patient_share = fields.Float(related='pricelist_id.patient_share', string='Patient Share', readonly=True)
    # patient_share_limit = fields.Float(related='pricelist_id.patient_share_limit', string='Patient Share Limit', readonly=True)
    # insurance_disc = fields.Float(related='pricelist_id.insurance_disc', string='Insurance Company Discount', readonly=True)
    # apply_ins_disc = fields.Selection(related='pricelist_id.apply_ins_disc')
    insurance_company_id = fields.Many2one(
        'res.partner',
        domain="[('is_insurance_company', '=', True), ('parent_id', '=', main_company_id)]",
        string="Insurance Company")
    main_company_id = fields.Many2one(
        'res.partner',
        domain="[('is_insurance_company', '=', True), ('parent_id', '=', False)]",
        string="Main Insurance Company")

    issue_date = fields.Date('Issue Date')
    expiry_date = fields.Date('Expiry Date')
    state = fields.Selection([('pending', 'Pending'), ('running', 'Running'), ('expired', 'Expired'), ('paused', 'Paused')], default="pending")
    file_no = fields.Char(related='partner_id.file_no', string='File No.', store=True)
    file_no2 = fields.Char(related='partner_id.file_no2', store=True)
    civil_code = fields.Char(related='partner_id.civil_code', string='Civil Code', store=True)
    member_id = fields.Char('Member ID')
    ins_based_on = fields.Selection(related="pricelist_id.ins_based_on", store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    invoice_ids = fields.One2many("account.move", "insurance_card_id", string="Invoices")

    def check_is_expired(self, dt=None):
        if not self:
            return False
        dt = dt or fields.Date.today()
        return self.expiry_date < dt

    def action_running(self):
        self.filtered(lambda i: i.state in ('pending', 'paused')).write({'state': 'running'})

    def action_paused(self):
        self.filtered(lambda i: i.state == 'running').write({'state': 'paused'})

    def validate_insurace_cards(self, vals):
        today = fields.Date.today()
        if vals.get('issue_date') or vals.get('expiry_date'):
            for rec in self:
                if rec.issue_date <= today and rec.expiry_date >= today:
                    rec.write({'state': 'running'})
                elif rec.expiry_date < today:
                    rec.write({'state': 'expired'})

    @api.model
    def create(self, vals):
        card = super(InsuranceCard, self).create(vals)
        card.validate_insurace_cards(vals)
        return card

    def unlink(self):
        if self.mapped('invoice_ids'):
            raise UserError("You cannot delete the Insurance Card, Invoices are linked with the card.")
        return super().unlink()

    def write(self, vals):
        res = super(InsuranceCard, self).write(vals)
        self.validate_insurace_cards(vals)
        f_list = ['partner_id', 'pricelist_id', 'insurance_company_id', 'main_company_id']
        for rec in self.filtered('invoice_ids'):
            for fk in f_list:
                if fk in vals.keys():
                    raise UserError("You cannot change card if there is an Invoice linked with it.")
        return res

    def apply_insurance_total(self, amount_total):
        ins_price_unit = 0
        patient_share_price = amount_total
        ins_vals = {}
        if self.ins_based_on == 'total' and amount_total > 0:
            scheme = self.pricelist_id
            if scheme.insurance_disc >= 0:
                if scheme.apply_ins_disc == 'with':
                    ins_price_unit = amount_total * (1 - scheme.insurance_disc / 100)
                    patient_share_price = amount_total * (scheme.patient_share / 100)
                    ins_price_unit = ins_price_unit - patient_share_price
                else:
                    # AFTER
                    ins_price_unit = amount_total * (1 - scheme.insurance_disc / 100)
                    patient_share_price = ins_price_unit * (scheme.patient_share / 100)
                    ins_price_unit = ins_price_unit - patient_share_price

                limit_type = scheme.share_limit_type

                if limit_type and scheme.patient_share_limit:
                    if limit_type == 'min':
                        limit_amount = max(patient_share_price, scheme.patient_share_limit)
                    else:
                        limit_amount = min(patient_share_price, scheme.patient_share_limit)
                    patient_share_price = limit_amount
                    ins_price_unit = ins_price_unit - (limit_amount - patient_share_price)

        ins_vals.update({
            'approved_tot_price': amount_total,
            'payable_tot_price': patient_share_price,
            'ins_tot_price': ins_price_unit
        })
        return ins_vals

    def apply_insurance_rule(self, product, qty=1, approved_amt=0):
        scheme = self.pricelist_id
        pricelist_price, item_id = scheme.get_product_price_rule(product, qty, self.partner_id)
        if approved_amt:
            pricelist_price = approved_amt
        pricelist_item = self.env['product.pricelist.item'].browse(item_id)
        ins_price_unit = ins_fixed = 0
        patient_share_price = pricelist_price
        ins_vals = {}
        if item_id:
            ins_vals = pricelist_item.read([
                'patient_share', 'patient_share_limit', 'insurance_disc', 'apply_ins_disc',
                'share_limit_type', 'ins_fixed'])[0]
            ins_vals.pop('id')

            ins_fixed = ins_vals['ins_fixed']
            if ins_fixed:
                patient_share_price = ins_fixed / qty
                ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
                ins_price_unit = ins_price_unit - patient_share_price
            elif ins_vals['insurance_disc'] >= 0:
                if ins_vals['apply_ins_disc'] == 'with':
                    ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
                    patient_share_price = pricelist_price * (ins_vals['patient_share'] / 100)
                    ins_price_unit = ins_price_unit - patient_share_price
                else:
                    ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
                    # Patint Share AFTER - Insurance Discount
                    patient_share_price = ins_price_unit * (ins_vals['patient_share'] / 100)
                    ins_price_unit = ins_price_unit - patient_share_price
            limit_type = ins_vals['share_limit_type']

            if limit_type and ins_vals['patient_share_limit']:

                # Revise Amounts

                if scheme.ins_based_on == 'total':
                    patient_share_price = patient_share_price * qty
                if limit_type == 'min':
                    limit_amount = max(patient_share_price, ins_vals['patient_share_limit'])
                else:
                    limit_amount = min(patient_share_price, ins_vals['patient_share_limit'])
                patient_share_price = limit_amount
                # ins_price_unit = ins_price_unit - (limit_amount - patient_share_price)

                # Insuranc Amount changed when when Patient Share has to Pay Max Min
                if ins_vals['apply_ins_disc'] == 'with':
                    ins_price_unit = pricelist_price * (1 - ins_vals['insurance_disc'] / 100)
                    ins_price_unit = ins_price_unit - patient_share_price
                else:
                    # AFTER
                    ins_price_unit = pricelist_price - patient_share_price
                    ins_price_unit = ins_price_unit * (1 - ins_vals['insurance_disc'] / 100)

        ins_vals.update({
            'pricelist_item_id': item_id,
            'price_unit': patient_share_price,
            'ins_price_unit': ins_price_unit,
            'ins_fixed': ins_fixed,
        })
        return ins_vals

    def check_insurance_total(self, line_by_products):
        scheme = self.pricelist_id
        insurance_disc = scheme.insurance_disc
        tot_line_approved = tot_qty = 0

        result_by_product = self.check_insurance(line_by_products)
        for pid, line in result_by_product.items():
            pricelist_item_id = line.get('pricelist_item_id')
            if pricelist_item_id:
                qty = line_by_products.get(str(pid), {}).get('qty') or 1
                tot_qty += qty
                tot_line_approved += line.get('approved_price_unit') * qty
        tot_ins_vals = self.apply_insurance_total(tot_line_approved)

        payable_tot_price = tot_ins_vals.get('payable_tot_price')
        PricelistItem = self.env['product.pricelist.item']

        for pid, line in result_by_product.items():
            qty = line_by_products.get(str(pid), {}).get('qty') or 1
            if line.get('ins_fixed'):
                price_unit = line['price_unit']
                ins_price_unit = line['approved_price_unit'] * (1 - insurance_disc / 100) - price_unit
                line['ins_price_unit'] = ins_price_unit
                # line['price_unit'] = price_unit
                continue

            pricelist_item_id = line.get('pricelist_item_id')
            if pricelist_item_id:
                ins_vals = PricelistItem.browse(pricelist_item_id).read([
                    'ins_fixed',
                    'insurance_disc', 'apply_ins_disc', 'patient_share', 'share_limit_type', 'patient_share_limit'])[0]
                ins_vals.pop('id')
                ins_vals = scheme.get_ins_values(line['approved_price_unit'], ins_vals)
                price_unit = payable_tot_price * line['approved_price_unit'] / tot_line_approved
                ins_disc = line['approved_price_unit'] * insurance_disc / 100
                ins_price_unit = line['approved_price_unit'] - ins_disc - price_unit

                if line['ins_fixed']:
                    if line['apply_ins_disc'] == 'with':
                        ins_price_unit = ins_price_unit - price_unit
                    else:
                        ins_price_unit = line['approved_price_unit'] * (1 - ins_vals['insurance_disc'] / 100)
                        ins_price_unit = ins_price_unit - price_unit

                line.update({
                    'price_unit': price_unit,
                    'ins_price_unit': ins_price_unit,
                })
        return result_by_product

    def check_insurance(self, line_by_products):
        self.ensure_one()
        """
            {
                <prod_id>: {
                    'qty': 1,
                    'approved_amt': 0,
                    'is_insurance_applicable': True,
                },
                <prod_id>: {
                    'qty': 1,
                    'approved_amt': 0
                },
            }
            # line_by_products: [{'prod_id': 1, 'qty': 2, 'approved_amt': false|100}]
        """
        Product = self.env['product.product'].sudo()
        result_by_product = {}
        for pid, line in line_by_products.items():
            pid = int(pid)
            if not line.get('qty'):
                continue
            product = Product.browse(pid)
            result = self._check_insurance_wrapper(product, line['qty'], line.get('approved_amt') or 0, line.get('is_insurance_applicable'))
            result_by_product.update({
                pid: result
            })
        return result_by_product

    def _check_insurance_wrapper(self, product, qty=1, approved_amt=0, is_insurance_applicable=True):
        insurance_card = self
        price = approved_amt or product.lst_price
        result = {
            'price_unit_orig': price,
            'price_unit': price,
            'approved_price_unit': price,
            # 'description': self._get_computed_name(),
            # 'analytic_account_id': order.resource_id.analytic_account_id.id,
            # 'analytic_tag_ids': product.analytic_tag_ids.ids,
            'ins_price_unit': 0,
        }
        if product and is_insurance_applicable and insurance_card:
            price = product.with_context(
                quantity=qty,
                pricelist=insurance_card.pricelist_id.id,
                uom=product.uom_id.id
            ).price
            result.update({
                'price_unit_orig': price,
                'price_unit': price,
            })
            if not approved_amt:
                result.update({'approved_price_unit': price})
            price_result = insurance_card.apply_insurance_rule(product, qty, approved_amt)
            result.update(price_result)
        return result
