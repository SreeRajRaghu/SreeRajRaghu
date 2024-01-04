from odoo import fields, models, _, api
from odoo.exceptions import UserError


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    res_branch_id = fields.Many2one('res.branch', string='Branch')
    is_discount = fields.Boolean('Discount Applicable')
    discount_account_id = fields.Many2one('account.account', string='Account')
    discount_amount = fields.Monetary('Discount Amount')
    payment_difference = fields.Monetary(compute='_compute_payment_difference', readonly=True)

    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'payment_type', 'is_discount', 'discount_amount')
    def _compute_payment_difference(self):
        draft_payments = self.filtered(lambda p: p.invoice_ids and p.state == 'draft')
        for pay in draft_payments:
            if pay.is_discount and pay.discount_amount:
                payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount + pay.discount_amount
            else:
                payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
            pay.payment_difference = pay._compute_payment_amount(pay.invoice_ids, pay.currency_id, pay.journal_id,
                                                                 pay.payment_date) - payment_amount
        (self - draft_payments).payment_difference = 0

    def _prepare_payment_moves(self):
        all_move_vals = []
        for payment in self:
            if payment.amount <= payment.discount_amount and payment.is_discount:
                raise UserError(_('Discount Amount is greater than payment amount!!!'))
            company_currency = payment.company_id.currency_id
            move_names = payment.move_name.split(
                payment._get_move_name_transfer_separator()) if payment.move_name else None

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                liquidity_line_account = payment.journal_id.default_debit_account_id
            else:
                counterpart_amount = -payment.amount
                liquidity_line_account = payment.journal_id.default_credit_account_id

            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id,
                                                       payment.payment_date)
                write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id,
                                                                 payment.payment_date)
                currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                if payment.journal_id.currency_id == company_currency:
                    # Single-currency
                    liquidity_line_currency_id = False
                else:
                    liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount

            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    if payment.is_discount:
                        payment.invoice_ids.payment_amount += payment.amount
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))
                if payment.invoice_ids and payment.is_discount:
                    payment.invoice_ids.is_discount = True
                    payment.invoice_ids.payment_discount_amount += payment.discount_amount
            # Compute 'name' to be used in liquidity line.
            if payment.payment_type == 'transfer':
                liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
            else:
                liquidity_line_name = payment.name

            move_vals = {}
            # ==== 'inbound' / 'outbound' ====
            if payment.journal_id.is_bank_charge and payment.payment_type == 'inbound':
                bank_charge = payment.journal_id.bank_account.name
                move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'journal_id': payment.journal_id.id,
                    'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                    'partner_id': payment.partner_id.id,
                    'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                    'line_ids': [
                        # Receivable / Payable / Transfer line.
                        (0, 0, {
                            'name': rec_pay_line_name,
                            'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                            'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity line.
                        (0, 0, {
                            'name': liquidity_line_name,
                            'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance - payment.journal_id.amount < 0.0 and -balance - payment.journal_id.amount if payment.journal_id.charge_type == 'amount' else
                            balance - (balance * payment.journal_id.percentage / 100) < 0.0 and round(-balance - (
                                        -balance * payment.journal_id.percentage / 100), 3),
                            'credit': balance > 0.0 and balance or 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': liquidity_line_account.id,
                            'payment_id': payment.id,
                        }),
                        # Bank side charge
                        (0, 0, {
                            'name': bank_charge,
                            'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': payment.journal_id.amount if payment.journal_id.charge_type == 'amount'
                            else round(-balance - (-balance - (-balance * payment.journal_id.percentage / 100)), 3),
                            'credit': 0.0,
                            'date_maturity': payment.payment_date,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.journal_id.bank_account.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }
            elif payment.is_discount and payment.discount_account_id and payment.discount_amount:
                move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'journal_id': payment.journal_id.id,
                    'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                    'partner_id': payment.partner_id.id,
                    'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                    'line_ids': [
                        # Receivable / Payable / Transfer line.
                        (0, 0, {
                            'name': rec_pay_line_name,
                            'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                            'credit': balance + write_off_balance - payment.discount_amount < 0.0 and -balance - write_off_balance - (-payment.discount_amount) or 0.0,
                            'date_maturity': payment.payment_date,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity line.
                        (0, 0, {
                            'name': liquidity_line_name,
                            'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance - payment.discount_amount < 0.0 and -balance,
                            'credit': balance > 0.0 and balance or 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': liquidity_line_account.id,
                            'payment_id': payment.id,
                        }),
                        # Discount
                        (0, 0, {
                            'name': "Discount",
                            'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': payment.discount_amount,
                            'credit': 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.discount_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }
            elif payment.payment_type == 'outbound' or payment.payment_type == 'inbound':
                move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'journal_id': payment.journal_id.id,
                    'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                    'partner_id': payment.partner_id.id,
                    'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                    'line_ids': [
                        # Receivable / Payable / Transfer line.
                        (0, 0, {
                            'name': rec_pay_line_name,
                            'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                            'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.id,
                            'account_id': payment.destination_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity line.
                        (0, 0, {
                            'name': liquidity_line_name,
                            'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.id,
                            'account_id': liquidity_line_account.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }
            if payment.payment_type == 'transfer':
                move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'journal_id': payment.journal_id.id,
                    'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                    'partner_id': payment.partner_id.id,
                    'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                    'line_ids': [
                        # Receivable / Payable / Transfer line.
                        (0, 0, {
                            'name': rec_pay_line_name,
                            'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                            'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity line.
                        (0, 0, {
                            'name': liquidity_line_name,
                            'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': liquidity_line_account.id,
                            'payment_id': payment.id,
                        })]}
            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

            if move_names:
                move_vals['name'] = move_names[0]

            all_move_vals.append(move_vals)

            # ==== 'transfer' ====
            if payment.payment_type == 'transfer':
                journal = payment.destination_journal_id

                # Manage custom currency on journal for liquidity line.
                if journal.currency_id and payment.currency_id != journal.currency_id:
                    # Custom currency on journal.
                    liquidity_line_currency_id = journal.currency_id.id
                    transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id,
                                                                payment.payment_date)
                else:
                    # Use the payment currency.
                    liquidity_line_currency_id = currency_id
                    transfer_amount = counterpart_amount

                transfer_move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment.destination_journal_id.id,
                    'branch_id': payment.res_branch_id.id if payment.res_branch_id.id else payment.invoice_ids[0].branch_id.id,
                    'line_ids': [
                        # Transfer debit line.
                        (0, 0, {
                            'name': payment.name,
                            'amount_currency': -counterpart_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.company_id.transfer_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity credit line.
                        (0, 0, {
                            'name': _('Transfer from %s') % payment.journal_id.name,
                            'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_journal_id.default_credit_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }

                if move_names and len(move_names) == 2:
                    transfer_move_vals['name'] = move_names[1]

                all_move_vals.append(transfer_move_vals)
        return all_move_vals
