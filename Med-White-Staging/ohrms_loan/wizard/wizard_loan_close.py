# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardLoanClose(models.TransientModel):
    _name = 'wizard.loan.close'

    @api.model
    def default_get(self, fields):
        res = super(WizardLoanClose, self).default_get(fields)
        Loan = self.env['hr.loan']
        loan_id = self.env.context.get('active_id')
        if loan_id:
            loan = Loan.browse(loan_id)
        if loan.exists():
            if 'amount_pending' in fields:
                lines = loan.loan_lines.filtered(lambda x: not x.paid)
                amount_pending = sum(lines.mapped('amount'))
                res['amount_pending'] = amount_pending
        return res

    amount_pending = fields.Float('Pending Amount', default=0.0)
    remaining_amount = fields.Float('Remaing Amount', default=0.0)
    amount_to_pay = fields.Float('Amount to Pay', default=0.0)
    installment = fields.Integer('Number of Installment', default=0)
    payment_date = fields.Date('Payment Start Date')
    reference = fields.Char('Reference')

    @api.onchange('amount_pending', 'amount_to_pay')
    def onchange_amount(self):
        self.remaining_amount = 0.0
        if self.amount_pending > 0.0:
            self.remaining_amount = self.amount_pending - self.amount_to_pay

    @api.constrains('amount_pending', 'amount_to_pay')
    def _constraint_amount_pay(self):
        for record in self:
            if record.amount_to_pay > record.amount_pending:
                raise UserError(_("Amount to Pay must not be greater than Pending Amount!"))

    def action_settlement(self):
        self.ensure_one()
        Loan = self.env['hr.loan']
        loan_id = self.env.context.get('active_id')
        if loan_id:

            month_start_date = fields.Date.from_string(datetime.today().replace(day=1))

            if self.payment_date < month_start_date:
                UserError(_("Payment Start Date must be greater than current month!"))

            loan = Loan.browse(loan_id)
            loan.loan_lines.filtered(lambda x: not x.paid).unlink()

            self.env['hr.loan.line'].create({
                'date': self.payment_date,
                'amount': self.amount_to_pay,
                'employee_id': loan.employee_id.id,
                'loan_id': loan.id,
                'paid': True,
                'reference': self.reference,
            })

            date_start = datetime.strptime(str(self.payment_date), '%Y-%m-%d') + relativedelta(months=1)
            amount = self.remaining_amount / self.installment

            for i in range(1, self.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id
                })
                date_start = date_start + relativedelta(months=1)

            loan.action_close()
        return True
