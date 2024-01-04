# coding: utf-8

from odoo import models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        result = super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)
        result.update({
            'analytic_tag_ids': line.slip_id.contract_id.analytic_tag_ids.ids,
            'branch_id': line.slip_id.contract_id.branch_id.id,
        })
        return result
