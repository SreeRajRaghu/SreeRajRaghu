# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    # is_by_hour = fields.Boolean('By Hour')

    @api.model
    def _get_default_rule_ids(self):
        """
        - Basic Salary = contract.wage instead of payslip.paid
        - Net Salary = + ToNetSalary
        """
        return [
            (0, 0, {
                'name': 'Basic Salary',
                'sequence': 1,
                'code': 'BASIC',
                'category_id': self.env.ref('hr_payroll.BASIC').id,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': """
qty = payslip.calendar_working_days
result = employee.get_pay_amount_kuwait_payroll(payslip, contract.wage, qty)
""",
            }),
            (0, 0, {
                'name': 'Gross',
                'sequence': 100,
                'code': 'GROSS',
                'category_id': self.env.ref('hr_payroll.GROSS').id,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': 'result = categories.BASIC + categories.ALW',
            }),
            (0, 0, {
                'name': 'Net Salary',
                'sequence': 200,
                'code': 'NET',
                'category_id': self.env.ref('hr_payroll.NET').id,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': 'result = categories.BASIC + categories.ALW + categories.DED + categories.ToNET',
            })
        ]

    rule_ids = fields.One2many(default=_get_default_rule_ids)
