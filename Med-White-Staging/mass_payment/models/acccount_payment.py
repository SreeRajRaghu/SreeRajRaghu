# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_method = fields.Selection([
                        ('bank', 'Bank'),
                        ('check', 'Check')],
                        string='Payment Method Type',
                        default='bank')
    checkbook_no_id = fields.Many2one('check.book', string='Checkbook No')
    check_no = fields.Char('Check Number')
    check_type = fields.Selection([
                    ('manual', 'Manual'),
                    ('auto', 'Auto')], string='Check Type')
    check_number_new = fields.Char('Check Number')
    check_number = fields.Char(readonly=False)

    def _get_amount_text(self, amount):
        amount_txt = ''
        amount_text = self.currency_id.amount_to_text(amount)
        if 'And' in amount_text:
            amount_text = amount_text.replace('And', '')
        amount_replaced_text = amount_text.replace('Fils', '')

        if 'and' in amount_text:
            amount_txt = amount_replaced_text
            return amount_txt.replace('and', 'and Fils') + ' Only'
        else:
            return amount_replaced_text + ' Only'

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            self.check_type = self.journal_id.check_type

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        journal = self.journal_id
        if self.payment_method == 'check' and journal.check_request \
                and journal.check_type == 'auto' and journal.check_book_ids:
            res = False
            for checkbook in journal.check_book_ids:
                res = True
                if checkbook.total_used_no < checkbook.to_no:
                    diff = (checkbook.to_no - checkbook.total_used_no)
                    if not diff or diff <= journal.remain_check:
                        res = False
                        if not checkbook.sent:
                            check_template = self.env.ref('mass_payment.email_template_checkbook_reminder_mail')
                            if check_template:
                                check_template.send_mail(journal.id, force_send=True)
                                checkbook.write({'sent': True})
            if not res:
                warning = {
                    'title': _('Warning'),
                    'message': 'Please order new check book'
                }
                return {
                    'warning': warning
                }

    def copy(self, default=None):
        self.ensure_one()
        self._onchange_payment_method()
        return super(AccountPayment, self).copy(default)

    def _check_no(self, journal, check_book, check_no):
        CheckbookCancel = self.env['check.book.cancel']
        find_check_no = CheckbookCancel.search([
            ('bank_journal_id', '=', journal),
            ('check_book_no_id', '=', check_book),
            ('check_no', '=', check_no)])
        if find_check_no:
            check_no += 1
            self._check_no(journal, check_book, check_no)
        return check_no

    @api.model
    def create(self, vals):
        Journal = self.env['account.journal']
        AccountPaymentMethod = self.env['account.payment.method']
        if vals.get('payment_type') == 'outbound':
            journal = Journal.browse(vals['journal_id'])
            # checkbook = journal.check_book_ids[0]
            payment_method = AccountPaymentMethod.browse(vals['payment_method_id'])
            if journal.check_type == 'auto' and payment_method.code in ('check', 'check_printing'):
                res = False
                for checkbook in journal.check_book_ids:
                    if checkbook.total_used_no == 0:
                        check_no = checkbook.from_no
                        res = self._check_no(vals['journal_id'], checkbook.id, check_no)
                        checkbook.write({
                            'total_used_no': res
                        })
                        vals['check_number'] = res
                        vals['checkbook_no_id'] = checkbook.id
                        break
                    else:
                        if checkbook.total_used_no < checkbook.to_no:
                            checkno = (checkbook.total_used_no + 1)
                            res = self._check_no(vals['journal_id'], checkbook.id, checkno)
                            if res:
                                vals['check_number'] = res
                                vals['checkbook_no_id'] = checkbook.id
                                checkbook.write({
                                    'total_used_no': res
                                })
                                break
                            else:
                                continue
                            # vals['check_no'] = res
                if not res:
                    raise UserError(_('Check number reached its last number'))
        return super(AccountPayment, self).create(vals)

    def payment_print(self):
        print ("I am here:::", self, self.payment_method)
        if self.payment_method == 'bank':
            return self.env.ref('mass_payment.action_report_transfer').report_action(self)

        elif self.payment_method == 'check':
           # print ("else:::::::::::::")
            return self.env.ref('mass_payment.action_report_checkbook').report_action(self)

    def payment_voucher_print(self):
        # return self.env['report'].get_action(self, 'mass_payment.report_mass_payment')
        data = {}
        return self.env.ref('mass_payment.action_report_mass_payment').report_action(self, data=data)
