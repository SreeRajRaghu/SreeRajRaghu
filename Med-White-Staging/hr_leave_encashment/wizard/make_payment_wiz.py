from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _


class WizardPayment(models.TransientModel):
    _name = 'make.encashment.payment'

    @api.model
    def default_get(self, fields):
        res = super(WizardPayment, self).default_get(fields)
        encashment = self.env['hr.encashment.history']
        active_id = self.env.context.get('active_id')
        if active_id:
            history = encashment.browse(active_id)
            res['amount'] = history.encashment_amount
            res['history_id'] = history.id
            res['partner_id'] = history.employee_id.user_id.partner_id.id
            res['approved_journal'] = history.journal_entry_id.id
            res['branch_id'] = history.branch_id.id
            res['employee_id'] = history.employee_id.id
            res['name'] = history.name + " - " + history.employee_id.name
        return res

    amount = fields.Float(string='Pending Amount')
    history_id = fields.Many2one('hr.encashment.history', string="Loan")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_id = fields.Many2one('res.partner', string='Partner')
    branch_id = fields.Many2one('res.branch', string='Branch')
    approved_journal = fields.Many2one('account.move', string="Approved JE")
    payment_date = fields.Date('Payment Date')
    name = fields.Char(string='Name')
    journal_id = fields.Many2one('account.journal', string='Payment Journal')

    def action_make_payment(self):
        if not self.partner_id:
            raise ValidationError(_('Please select user and partner for this employee'))
        move_lines_to_reconcile = self.env['account.move.line']
        move = self.approved_journal.line_ids
        move_lines_to_reconcile += move.filtered(
            lambda s: s.account_id.reconcile and s.account_id.internal_type in ('payable', 'receivable'))
        payment_method = self.env['account.payment.method'].sudo().search(
            [('code', '=', 'manual'), ('payment_type', '=', 'outbound')], limit=1)
        other_payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner_id.id if self.partner_id.id else self.env.user.company_id.partner_id.id,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'journal_id': self.journal_id.id,
            'payment_method_id': payment_method.id
        })
        other_payment.post()
        self.history_id.payment_entry_id = other_payment.id
        other_payment.move_line_ids[0].move_id.branch_id = self.branch_id.id
        other_payment.move_line_ids[0].move_id.ref = _('Pay - %s') % self.employee_id.name,
        for move_id in other_payment.move_line_ids:
            move_id.branch_id = move.partner_id.branch_id.id
        move_lines_to_reconcile += other_payment.move_line_ids.filtered(
            lambda s: s.account_id.reconcile and s.account_id.internal_type in ('payable', 'receivable'))

        move_lines_to_reconcile.reconcile()
        self.history_id.state = 'paid'

