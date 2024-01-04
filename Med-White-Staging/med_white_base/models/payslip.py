
from odoo import models,  _
from odoo.exceptions import UserError


class Payslip(models.Model):
    _inherit = "hr.payslip"

    def action_payslip_done(self):
        contracts = self.mapped('contract_id').filtered(lambda c: not c.analytic_account_id)
        if contracts:
            raise UserError(_(
                'Please set the Analytic Account in below employee contracts.\n%s') % ('\n'.join(contracts.mapped('employee_id.name'))))
        return super().action_payslip_done()
