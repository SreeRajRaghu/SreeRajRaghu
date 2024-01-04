# -*- coding: utf-8 -*-

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def _update_basic_wage_rule(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    kuwait_payroll = env.ref('boutiqaat_hr_payslip.payroll_structure_kuwait')
    basic_rule = kuwait_payroll.rule_ids.filtered(lambda r: r.code == 'BASIC')
    if basic_rule:
        basic_rule.write({
            'amount_python_compute': """
qty = payslip.calendar_working_days
result = employee.get_pay_amount_kuwait_payroll(payslip, contract.wage, qty)
"""
        })
