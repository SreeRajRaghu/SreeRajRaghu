# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    user_type_id = fields.Many2one(related="account_id.user_type_id", string="Account Type", store=True)


class account_payment(models.Model):
    _inherit = "account.payment"

    def _get_amount_text(self, amount):
        text = super(account_payment, self)._get_amount_text(amount)
        text = text.replace(' Fils', '')
        return text.replace(',', '')


class AccountChartOfAccountReport(models.AbstractModel):
    _inherit = "account.coa.report"

    @api.model
    def _get_lines(self, options, line_id=None):
        return super(AccountChartOfAccountReport, self.with_context(print_mode=True))._get_lines(options, line_id)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_amount_text(self, amount):
        amount_txt = ''
        amount_text = self.currency_id.amount_to_text(amount)
        if 'And' in amount_text:
            amount_text = amount_text.replace('And', '')
        amount_replaced_text = amount_text.replace('Fils', '')

        if 'and' in amount_text:
            amount_txt = amount_replaced_text
            # return amount_txt.replace('and', 'and Fils') + ' Only'
            return amount_txt + ' Fils Only'
        else:
            return amount_replaced_text + ' Only'
