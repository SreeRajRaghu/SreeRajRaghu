# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
            employee_id = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
            if self.env.context.get('default_employee_id'):
                employee_id = self.env.context['default_employee_id']
        result['employee_id'] = employee_id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today())
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    partner_id = fields.Many2one('res.partner', related="employee_id.user_id.partner_id", readonly=True, string="Partner")
    branch_id = fields.Many2one('res.branch', related="partner_id.branch_id", string="Branch")
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_loan_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount')
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount')
    approved_journal = fields.Many2one('account.move', string="Approved JE")
    payment_id = fields.Many2one('account.payment', string="Payment")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('close', 'Closed'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False)

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count([('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
                                                       ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_close(self):
        return self.write({'state': 'close'})

    def button_close(self):
        action = self.env.ref('ohrms_loan.action_wizard_loan_close').read()[0]
        return action

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                if not self.env.user.company_id.employee_loan_account and not self.env.user.company_id.employee_payable_account:
                    raise ValidationError(_("Please select accounts for Employee Loan Account and Employee Payable Account"))
                journal = self.env['account.journal'].search([('type', '=', 'general')])[0]
                move_vals = {
                    'date': datetime.today(),
                    'ref': self.name + "-" + self.employee_id.name,
                    'journal_id': journal.id,
                    'currency_id': self.company_id.currency_id.id,
                    'partner_id': self.partner_id.id,
                    'branch_id': self.partner_id.branch_id.id if self.partner_id.branch_id else None,
                    'line_ids': [
                        # Receivable
                        (0, 0, {
                            'name': self.name + "-" + self.employee_id.name,
                            'debit': self.loan_amount if self.loan_amount else 0.0,
                            'credit':  0.0,
                            'partner_id': self.partner_id.id,
                            'branch_id':  self.partner_id.branch_id.id if self.partner_id.branch_id else None,
                            'account_id': self.env.user.company_id.employee_loan_account.id,
                        }),
                        # Payable
                        (0, 0, {
                            'name': self.name + "-" + self.employee_id.name,
                            'debit': 0.0,
                            'credit': self.loan_amount if self.loan_amount else 0.0,
                            'partner_id': self.partner_id.commercial_partner_id.id,
                            'branch_id': self.partner_id.branch_id.id if self.partner_id.branch_id else None,
                            'account_id': self.env.user.company_id.employee_payable_account.id,
                        }),
                    ],
                }
                journal_entry = self.env['account.move'].create(move_vals)
                journal_entry.post()
                self.approved_journal = journal_entry.id
                self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        LoanLine = self.env['hr.loan.line']
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                LoanLine.create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
        return True


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
    reference = fields.Char('Reference')


class AssetInheritWiz(models.TransientModel):
    _name = 'asset.modify'

    name = fields.Text(string='Reason')
    asset_id = fields.Many2one(string="Asset", comodel_name='account.asset', required=True,
                               help="The asset to be modified by this wizard", ondelete="cascade")
    method_number = fields.Integer(string='Number of Depreciations', required=True)
    method_period = fields.Selection([('1', 'Months'), ('12', 'Years')], string='Number of Months in a Period',
                                     help="The amount of time between two depreciations")
    value_residual = fields.Monetary(string="Depreciable Amount", help="New residual amount for the asset")
    salvage_value = fields.Monetary(string="Not Depreciable Amount", help="New salvage amount for the asset")
    currency_id = fields.Many2one(related='asset_id.currency_id')
    date = fields.Date(default=fields.Date.today(), string='Date')
    need_date = fields.Boolean(compute="_compute_need_date")
    gain_value = fields.Boolean(compute="_compute_gain_value",
                                help="Technical field to know if we should display the fields for the creation of gross increase asset")
    account_asset_id = fields.Many2one('account.account', string="Asset Gross Increase Account")
    account_asset_counterpart_id = fields.Many2one('account.account')
    account_depreciation_id = fields.Many2one('account.account')
    account_depreciation_expense_id = fields.Many2one('account.account')
    branch_id = fields.Many2one('res.branch', string="Branch")
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account",
                                          required=False,)

    @api.depends('asset_id', 'value_residual', 'salvage_value')
    def _compute_need_date(self):
        for record in self:
            value_changed = self.value_residual + self.salvage_value != self.asset_id.value_residual + self.asset_id.salvage_value
            record.need_date = (self.env.context.get('resume_after_pause') and record.asset_id.prorata) or value_changed

    @api.depends('asset_id', 'value_residual', 'salvage_value')
    def _compute_gain_value(self):
        for record in self:
            record.gain_value = self.value_residual + self.salvage_value > self.asset_id.value_residual + self.asset_id.salvage_value


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        Loan = self.env['hr.loan']
        for rec in self:
            loans = Loan.search([('employee_id', '=', rec.id)])
            rec.loan_count = len(loans)
            rec.loan_balance = round(sum(loans.mapped('balance_amount')), 4)
            rec.loan_total = round(sum(loans.mapped('total_amount')), 4)
            rec.total_paid_amount = round(sum(loans.mapped('total_paid_amount')), 4)

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
    loan_balance = fields.Float(string='Loan Balance', compute='_compute_employee_loans', digits=(16, 4))
    loan_total = fields.Float(string='Loan Total', compute='_compute_employee_loans', digits=(16, 4))
    loan_total_paid = fields.Float(string='Loan Total', compute='_compute_employee_loans', digits=(16, 4))

    def action_hr_employee_loan_request(self):
        self.ensure_one()
        action = self.env.ref('ohrms_loan.act_hr_employee_loan_request').read()[0]
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {
            'default_employee_id': self.id,
            'search_default_employee_id': self.id,
        }
        return action
