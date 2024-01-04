# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    need_ref = fields.Boolean("Need Reference ?")


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    branch_id = fields.Many2one('medical.clinic', string="Branch")
    prepaid_card_id = fields.Many2one("partner.prepaid.card", string="Prepaid Card", domain="[('partner_id','=',partner_id)]")

    move_link_ids = fields.One2many("account.move.payment.link", "payment_id", string="Account Move Link")
    payment_history_ids = fields.Many2many(
        "aml.payment.history", "account_payment_aml_payment_history_rel",
        "account_payment_id", "aml_payment_history_id",
        string="Payment History")

    payment_balance = fields.Monetary(compute='_compute_payment_remain', readonly=True, store=True)

    @api.depends(
        "move_line_ids", "state", "move_line_ids.matched_debit_ids.debit_move_id.debit", "move_line_ids.matched_credit_ids.credit_move_id.credit")
    def _compute_payment_remain(self):
        for payment in self:
            amount_remain = 0
            if payment.state in ['posted', 'reconciled']:
                amount_remain = payment.amount
                if payment.payment_type == 'inbound':
                    reconciled_move_lines = payment.move_line_ids.mapped('matched_debit_ids.debit_move_id')
                    amount_paid = sum(reconciled_move_lines.mapped('debit'))

                    amount_remain = (payment.amount - amount_paid)
                elif payment.payment_type == 'outbound':
                    reconciled_move_lines = payment.move_line_ids.mapped('matched_credit_ids.credit_move_id')
                    amount_paid = sum(reconciled_move_lines.mapped('credit'))
                    amount_remain = (payment.amount - amount_paid)
                # else:
                #     reconciled_move_lines = payment.move_line_ids.mapped('matched_debit_ids.debit_move_id')
                #     amount_paid = sum(reconciled_move_lines.mapped('debit'))
                #     amount_remain = (payment.amount - amount_paid)

                if amount_remain < 0.0:
                    amount_remain = 0.0
            payment.payment_balance = amount_remain

    def open_payment_distribution(self):
        self.ensure_one()
        action = self.env.ref('medical_js.aml_payment_history_action').read()[0]
        action.update({
            'domain': [('id', 'in', self.payment_history_ids.ids)],
        })
        return action

    def action_draft(self):
        super(AccountPayment, self).action_draft()
        self.remove_aml_amount_paid()

    def update_aml_amount_paid(self, invoice_lines):
        # lines = self.env['account.move.line']
        PaymentLink = self.env['account.move.payment.link']
        PayHistory = self.env['aml.payment.history']
        aml_ids = list(map(lambda a: int(a), invoice_lines.keys()))
        lines = self.env['account.move.line'].browse(aml_ids)
        # Update AML -> Amount Paid
        for line in lines:
            amount = invoice_lines.get(str(line.id))
            amount_paid = line.amount_paid
            line.write({
                'amount_paid': amount_paid + amount
            })

            PayHistory.create({
                'payment_ids': [(4, _id) for _id in self.ids],
                'move_line_id': line.id,
                'amount': amount,
            })

        for payment in self:
            balance = payment.amount
            for aml_id_str, amount in invoice_lines.items():
                if not amount:
                    continue
                aml_id = int(aml_id_str)

                payment.write({
                    'paid_move_line_ids': [(4, aml_id)],
                    'medical_order_id': lines and lines[0].medical_order_id.id,
                })
                amount = min(balance, amount)
                balance -= amount
                vals = {
                    'payment_id': payment.id,
                    'move_line_id': aml_id,
                    'amount': amount,
                }
                PaymentLink.create(vals)

                invoice_lines[aml_id_str] -= amount

                if balance <= 0:
                    break
        return lines

    def remove_aml_amount_paid(self):
        lines = self.env['account.move.line']
        to_unlink = self.env['account.move.payment.link']

        cr = self.env.cr
        for payment in self:
            balance = payment.amount

            payment.move_link_ids.mapped('move_line_id.payment_history_ids').write({'active': False})
            for link in payment.move_link_ids:
                aml = link.move_line_id
                amount = min(balance, link.amount)
                amount = min(amount, aml.price_subtotal)

                # NO Sql Because of other depends compute fields
                cr.execute("""
                    UPDATE account_move_line
                        SET
                            amount_paid = amount_paid - %s,
                            amount_pay_status = CASE WHEN (amount_paid - %s) > 0 THEN 'partially_paid'
                                                ELSE 'unpaid' END
                    WHERE id = %s RETURNING amount_paid""", (amount, amount, aml.id))
                result = cr.fetchone()
                if result:
                    aml.medical_order_line_id.write({'amount_paid': result[0]})

                to_unlink += link
                balance = balance - amount

                lines += aml
                if balance == 0:
                    break

        to_unlink.write({'active': False})
        self.write({
            'medical_order_id': False,
            'paid_move_line_ids': False
        })
        return lines


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_history_ids = fields.One2many('aml.payment.history', 'invoice_id', string="Payment History Distribution")
    prepaid_card_id = fields.Many2one("partner.prepaid.card", string="Prepaid Card", domain="[('partner_id','=',partner_id)]")
    disc_reason_id = fields.Many2one(related="medical_order_id.disc_reason_id", store=True)

    def register_refund_invoice(self, refund_lines, payment_lines, cancel_remaining=False):
        self.ensure_one()
        ReverseWiz = self.env['account.move.reversal'].create({
            'move_id': self.id,
            'refund_method': 'refund',
            'journal_id': self.medical_order_id.config_id.invoice_journal_id.id,
        })

        action = ReverseWiz.reverse_moves()
        rev_move_id = action.get('res_id')
        reversed_move = self.browse(rev_move_id)
        MoveLine = self.env['account.move.line']

        # Update Refund amount in Refunded Lines
        new_refunded_lines = []
        print ('____ cancel_remaining : ', cancel_remaining, reversed_move)
        if True:
            # AMoveLine = self.env['account.move.line']
            if len(reversed_move.invoice_line_ids.mapped('product_id.id')) != len(reversed_move.invoice_line_ids.ids):
                for line in reversed_move.invoice_line_ids:
                    for ref_line in refund_lines:
                        exist = list(filter(
                            lambda a: a.get('orig_aml_id') == ref_line['aml_id'], new_refunded_lines))
                        if exist:
                            continue

                        if line.product_id.id == ref_line['product_id']:
                            orig_aml_line = MoveLine.browse(ref_line['aml_id'])
                            order_line = orig_aml_line.medical_order_line_id
                            if order_line:
                                order_line = order_line.copy({'qty': 0})
                            unit_price = line.price_unit if cancel_remaining else ref_line['refund']
                            new_line = {
                                'product_id': ref_line['product_id'],
                                'name': line.name,
                                'analytic_account_id': line.analytic_account_id.id,
                                'analytic_tag_ids': [(4, _id) for _id in line.analytic_tag_ids.ids],
                                'move_id': reversed_move.id,
                                'price_unit': unit_price,
                                'orig_aml_id': ref_line['aml_id'],
                                'medical_order_line_id': order_line.id,
                                'refund_aml_id': line.id,
                            }
                            new_refunded_lines.append(new_line)
            else:
                for line in reversed_move.invoice_line_ids:
                    for ref_line in refund_lines:
                        if line.product_id.id == ref_line['product_id']:
                            orig_aml_line = MoveLine.browse(ref_line['aml_id'])
                            order_line = orig_aml_line.medical_order_line_id
                            if order_line:
                                order_line = order_line.copy({'qty': 0, 'duration': 0})
                            unit_price = line.price_unit if cancel_remaining else ref_line['refund']
                            new_line = {
                                'product_id': ref_line['product_id'],
                                'name': line.name,
                                'analytic_account_id': line.analytic_account_id.id,
                                'analytic_tag_ids': [(4, _id) for _id in line.analytic_tag_ids.ids],
                                'move_id': reversed_move.id,
                                'price_unit': unit_price,
                                'orig_aml_id': ref_line['aml_id'],
                                'medical_order_line_id': order_line.id,
                            }
                            new_refunded_lines.append(new_line)

            if new_refunded_lines:
                for l in new_refunded_lines:
                    l.pop('refund_aml_id', False)
                # reversed_move.invoice_line_ids.unlink()
                reversed_move.invoice_line_ids = False
                aml_line = [(5, 0)]
                aml_line += [(0, 0, vals) for vals in new_refunded_lines]
                reversed_move.write({'invoice_line_ids': aml_line})
        # Post
        reversed_move.action_post()

        # pay_lines = reversed_move._compute_payments_widget_to_reconcile_info()
        # if pay_lines and pay_lines.get(reversed_move.id):
        #     move_lines = pay_lines.get(reversed_move.id)
        #     from pprint import pprint
        #     print('____ pay_lines : ')
        #     pprint(pay_lines)
        #     import pdb
        #     pdb.set_trace()

        # Register Payment
        # outbound
        # out_refund
        ctx = dict(self.env.context, **{
            'default_payment_type': 'outbound',
            'default_partner_type': 'customer',
            # 'active_ids': self.ids,
        })
        payments = Payment = self.env['account.payment']
        Journal = self.env['account.journal']

        cmp_currency = self.env.user.company_id.currency_id
        def_vals = Payment.with_context(ctx).default_get(['payment_method_id', 'payment_type', 'payment_method_code'])
        for line in payment_lines or []:

            journal_id = int(line.get('journal_id'))
            journal = Journal.browse(journal_id)
            amount = line.get('amount')
            partner_id = line.get("partner_id") or self.partner_id.id
            communication = self.name or line.get("communication")

            vals = dict(def_vals, **{
                'payment_type': 'outbound',
                'partner_type': 'customer',
                'payment_date': fields.Date.today(),
                'partner_id': partner_id,
                'amount': amount,
                'journal_id': journal_id,
                'medical_order_id': int(line['medical_order_id'] or self.medical_order_id.id),
                'communication': communication,
                'currency_id': cmp_currency.id,
                'invoice_ids': [(4, rev_move_id)],
                'payment_method_id': journal.inbound_payment_method_ids and journal.inbound_payment_method_ids[0].id,
            })
            if journal.currency_id:
                vals.update({
                    'currency_id': journal.currency_id.id,
                })
            payments += Payment.with_context(ctx).create(vals)
        payments.post()

        # lines = self.env['account.move.line']
        if refund_lines:
            invoice_lines = {}
            for line in refund_lines:
                ref_line = reversed_move.invoice_line_ids.filtered(lambda r: r.orig_aml_id.id == line['aml_id'])
                if ref_line:
                    invoice_lines.setdefault(str(ref_line.id), line['refund'] * -1)

            payments.update_aml_amount_paid(invoice_lines)
        return

    def js_assign_outstanding_line(self, line_id):
        if not self._context.get('is_from_js') and self.type == 'out_invoice':
            raise UserError(_('You can not reconcile payment from here. Please add by service/product in session.'))
        res = super(AccountMove, self).js_assign_outstanding_line(line_id)
        return res

    def js_assign_outstanding_line_wrapper(self, line_id, invoice_lines):
        tot = sum(list(invoice_lines.values()))
        self.with_context(amount_from=tot, is_from_js=True).js_assign_outstanding_line(line_id)
        AMLine = self.env['account.move.line'].sudo()

        aml_line = AMLine.browse(line_id)
        payment = aml_line.payment_id

        # Only for Bayan: Moved to bayan_medical
        # payment.write({'payment_date': fields.Date.today()})

        if payment.prepaid_card_id:
            self.prepaid_card_id = payment.prepaid_card_id

        if invoice_lines and payment:
            payment.update_aml_amount_paid(invoice_lines)

        order = payment.medical_order_id

        if order and order.amount_due == 0 and order.state != 'paid':
            order.write({"state": 'paid'})

        # return {
        #     'invoice_lines': lines.read(['amount_paid', 'amount_pay_status'])
        # }

    def button_draft(self):
        super(AccountMove, self).button_draft()
        for move in self.filtered(lambda r: r.payment_history_ids):
            # is_insurance_invoice
            move.payment_history_ids.write({'active': False})

    def cancel_appointment(self):
        if self.medical_order_id.state == 'cancel':
            raise UserError(_('The Appointment is already in %s state.') % self.medical_order_id.state)
        else:
            self.medical_order_id.state = 'cancel'
            for test in self.medical_order_id.medical_lab_test_ids:
                test.state = 'cancelled'

    def action_post(self):
        res = super(AccountMove, self).action_post()

        # Package - Deffered Revenue

        # Payment History and Distribution
        PayHistory = self.env['aml.payment.history']
        for invoice in self.filtered('is_insurance_invoice'):
            for line in invoice.invoice_line_ids:
                PayHistory.create({
                    'payment_ids': [],
                    'move_line_id': line.id,
                    'amount': line.price_subtotal,
                })
        return res

    def unlink(self):
        appointments = self.mapped('medical_order_id')
        res = super(AccountMove, self).unlink()
        appointments.write({'is_readonly': False, 'state': 'draft'})
        return res

    def add_uninvoiced_order(self, order_id):
        self.ensure_one()
        MedOrder = self.env['medical.order']
        order = MedOrder.sudo().browse(order_id)
        invoice_line_ids = []
        for line in order.line_ids:
            inv_line_vals = (0, 0, order._prepare_invoice_line_vals(line))
            invoice_line_ids.append(inv_line_vals)

        self.write({'invoice_line_ids': invoice_line_ids})
        order.write({'patient_invoice_id': self.id, 'state': 'invoiced', 'is_readonly': True})

        return order.get_invoice_data(order_id=order_id)

    def button_cancel(self):
        for invoice in self:
            order_id = invoice.medical_order_id.id
            inv_lines = invoice.invoice_line_ids.filtered(lambda line: line.medical_order_id.id != order_id)
            inv_lines.mapped('medical_order_id').write({'patient_invoice_id': False})
        super(AccountMove, self).button_cancel()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payment_link_ids = fields.One2many("account.move.payment.link", "move_line_id", string="Payment Link")
    payment_history_ids = fields.One2many('aml.payment.history', 'move_line_id', string="Payment History Distribution")
    employee_id = fields.Many2one(related="medical_order_line_id.employee_id")
    orig_aml_id = fields.Many2one('account.move.line', string="Refunded From AML")
    refund_amount = fields.Float(compute="_compute_refund_amount", store=True)
    refund_aml_ids = fields.One2many("account.move.line", "orig_aml_id")

    @api.depends('orig_aml_id', 'refund_aml_ids')
    def _compute_refund_amount(self):
        for rec in self:
            rec.refund_amount = sum(rec.refund_aml_ids.filtered(lambda line: line.move_id.state == 'posted').mapped('price_subtotal'))

    def unreconcile_payment(self):
        payment = self.payment_id
        if payment:
            payment.remove_aml_amount_paid()
        self.remove_move_reconcile()

    def cancel_payment(self, payment_id=None):
        self.unreconcile_payment()
        payment = self.payment_id
        payment.unreconcile()

        # Check the methods
        # Even cancelled payments are appearing in outstanding amount
        payment.action_draft()
        payment.cancel()
