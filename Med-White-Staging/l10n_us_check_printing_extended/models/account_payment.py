# -*- coding: utf-8 -*-

from odoo import api, fields, models


class account_payment(models.Model):
    _inherit = "account.payment"

    bank_letter_ref = fields.Char(
                        'Bank Letter Ref No',
                        tracking=True,
                        readonly=True,
                        states={'draft': [('readonly', False)]})
    check_number = fields.Char(readonly=False)
    internal_ref = fields.Char(
                        'Internal Reference',
                        tracking=True,
                        readonly=True,
                        states={'draft': [('readonly', False)]})
    check_date = fields.Date('Check Date')
    customer_check_date = fields.Date('Customer Check Date')
    vendor_invoice_number = fields.Char('Vednor Invoice Number', readonly=True,  states={'draft': [('readonly', False)]})

    def _check_fill_line(self, amount_str):
        return amount_str and (amount_str) or ''


class AccountMove(models.Model):
    _inherit = 'account.move'

    check_number = fields.Char('Check Number')
    check_date = fields.Date('Check Date')
    vendor_invoice_number = fields.Char(
                    'Vendor Invoice Number',
                    readonly=True,
                    tracking=True,
                    states={'draft': [('readonly', False)]})
