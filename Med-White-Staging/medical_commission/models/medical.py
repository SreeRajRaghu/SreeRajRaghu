# -*- coding: utf-8 -*-
from odoo import fields, models, _


class MedicalResource(models.Model):
    _inherit = 'medical.resource'

    commission_inside = fields.Float(string="Commission Inside (%)")
    commission_outside = fields.Float(string="Commission Outside (%)")

    commission_disc_inside = fields.Float(string="Commission Inside Discounted (%)")
    commission_disc_outside = fields.Float(string="Commission Outside Discounted (%)")


class AccountMove(models.Model):
    _inherit = 'account.move'

    commission_for_move_id = fields.Many2one("account.move", string="Commission Ref")
    commission_move_ids = fields.One2many("account.move", "commission_for_move_id", string="Commission Moves")
    product_id = fields.Many2one(related="invoice_line_ids.product_id")

    def _compute_commission_move(self):
        for rec in self:
            move_id = False
            if rec.commission_move_ids:
                move_id = rec.commission_move_ids[0].id
            rec.last_commission_move_id = move_id

    def button_draft(self):
        super(AccountMove, self).button_draft()
        for move in self.filtered(lambda m: m.type == 'out_invoice'):
            move.commission_move_ids.write({'ref': ''})
            move.commission_move_ids.filtered(lambda m: m.state == 'posted').button_cancel()

    def button_cancel(self):
        super(AccountMove, self).button_cancel()
        for move in self.filtered(lambda m: m.type == 'out_invoice'):
            move.commission_move_ids.write({'ref': ''})
            move.commission_move_ids.filtered(lambda m: m.state in 'posted').button_cancel()

    def create_vendor_bill(self):
        for move in self.filtered(lambda m: m.resource_id.partner_id and m.type == 'out_invoice'):
            inv_lines = []

            resource = move.resource_id

            for line in move.invoice_line_ids.filtered(lambda l: l.product_id.test_type != 'None'):
                test_type = line.product_id.test_type
                amount = 0
                if (line.discount or line.discount_fixed):
                    if test_type == 'outside' and resource.commission_disc_outside:
                        amount = line.price_subtotal * resource.commission_disc_outside / 100
                    elif test_type == 'inside' and resource.commission_disc_inside:
                        amount = line.price_subtotal * resource.commission_disc_inside / 100
                else:
                    if test_type == 'outside' and resource.commission_outside:
                        amount = line.price_subtotal * resource.commission_outside / 100
                    elif test_type == 'inside' and resource.commission_inside:
                        amount = line.price_subtotal * resource.commission_inside / 100

                if amount:
                    inv_lines.append({
                        'product_id': line.product_id.id,
                        'name': _('Commission: %s') % (line.product_id.default_code),
                        'quantity': 1,
                        'price_unit': amount,
                        'analytic_account_id': resource.analytic_account_id.id
                    })

            if inv_lines:
                vals = {
                    'partner_id': resource.partner_id.id,
                    'commission_for_move_id': move.id,
                    'invoice_origin': move.medical_order_id.name,
                    'type': 'in_invoice',
                    'invoice_date': move.invoice_date,
                    'invoice_date_due': move.invoice_date_due,
                    'invoice_user_id': move.invoice_user_id.id,
                    'ref': move.name,
                    'company_id': move.company_id.id,
                    'resource_id': resource.id,
                    'fiscal_position_id': resource.partner_id.property_account_position_id.id,
                    'invoice_payment_term_id': resource.partner_id.property_payment_term_id.id,
                    'invoice_line_ids': [(0, 0, line) for line in inv_lines],
                }
                commission_move = self.create(vals)
                commission_move.action_post()
                move.write({'commission_for_move_id': commission_move.id})

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.create_vendor_bill()
        return res
