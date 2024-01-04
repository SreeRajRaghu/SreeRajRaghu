from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _


class WizardPayment(models.TransientModel):
    _name = 'make.payment'

    @api.model
    def default_get(self, fields):
        res = super(WizardPayment, self).default_get(fields)
        loan = self.env['hr.loan']
        loan_id = self.env.context.get('active_id')
        if loan_id:
            loan = loan.browse(loan_id)
            res['amount'] = loan.balance_amount
            res['loan_id'] = loan.id
            res['partner_id'] = loan.partner_id.id
            res['approved_journal'] = loan.approved_journal.id
            res['branch_id'] = loan.partner_id.branch_id.id
            res['employee_id'] = loan.employee_id.id
            res['name'] = loan.name + " - " + loan.partner_id.name
        return res

    amount = fields.Float(string='Pending Amount')
    loan_id = fields.Many2one('hr.loan', string="Loan")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_id = fields.Many2one('res.partner', string='Partner')
    branch_id = fields.Many2one('res.branch', string='Branch')
    approved_journal = fields.Many2one('account.move', string="Approved JE")
    payment_date = fields.Date('Payment Date')
    name = fields.Char(string='Name')
    journal_id = fields.Many2one('account.journal', string='Payment Journal')

    def action_make_payment(self):
        move_lines_to_reconcile = self.env['account.move.line']
        move = self.approved_journal.line_ids
        move_lines_to_reconcile += move.filtered(
            lambda s: s.account_id.reconcile and s.account_id.internal_type in ('payable', 'receivable'))
        payment_method = self.env['account.payment.method'].sudo().search(
            [('code', '=', 'manual'), ('payment_type', '=', 'outbound')], limit=1)
        other_payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner_id.id if self.partner_id.id else self.user_company.default_other_payment_partner_id.id,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'journal_id': self.journal_id.id,
            'payment_method_id': payment_method.id
        })
        other_payment.post()
        self.loan_id.payment_id = other_payment.id
        other_payment.move_line_ids[0].move_id.branch_id = self.branch_id.id
        other_payment.move_line_ids[0].move_id.ref = _('%s - %s') % (self.loan_id.name, self.employee_id.name),
        for move_id in other_payment.move_line_ids:
            move_id.branch_id = move.partner_id.branch_id.id
        move_lines_to_reconcile += other_payment.move_line_ids.filtered(
            lambda s: s.account_id.reconcile and s.account_id.internal_type in ('payable', 'receivable'))

        move_lines_to_reconcile.reconcile()

