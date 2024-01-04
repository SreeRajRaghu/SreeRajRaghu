

from odoo import fields, models


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_loan_account = fields.Many2one('account.account', related='company_id.employee_loan_account', readonly=False, string="Employee Loan Account")
    employee_payable_account = fields.Many2one('account.account', related='company_id.employee_payable_account', readonly=False, string="Employee Payable Account")


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    employee_loan_account = fields.Many2one('account.account', string="Employee Loan Account")
    employee_payable_account = fields.Many2one('account.account', string="Employee Payable Account")
    
    
class AccountAssetInherit(models.Model):
    _inherit = 'account.asset'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', related="branch_id.analytic_account_id")

