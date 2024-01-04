# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime
from odoo.exceptions import ValidationError


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    is_refund = fields.Boolean('Is Refund?')

    def refund_sheet(self):
        for payslip in self:
            already_refund_payslips = self.search([
                ('date_from', '<=', payslip.date_to),
                ('date_to', '>=', payslip.date_from),
                ('employee_id', '=', payslip.employee_id.id),
                ('id', '!=', payslip.id),
                ('state', 'in', ('verify', 'done')),
                ('is_refund', '=', True)
            ])
            if already_refund_payslips:
                raise ValidationError(_("For given period and employee already refund payslip exits!"))

            copied_payslip = payslip.copy(default={'credit_note': True, 'name': _('Refund: ') + payslip.name, 'is_refund': True})
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_done()
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'), (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    # def refund_sheet(self):
    #     result = super(HrPayslip, self).refund_sheet()
    #     for payslip in self:
    #         payslip.write({'is_refund': True})
    #     return result

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        # employee = self.employee_id
        # date_from = self.date_from
        # date_to = self.date_to
        # contract_ids = []

        # ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
        # locale = self.env.context.get('lang') or 'en_US'
        # self.name = _('Salary Slip of %s for %s') % (
        #     employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        # self.company_id = employee.company_id
        # print ('___ self.contract_id : ', self.contract_id)

        # if not self.env.context.get('contract') or not self.contract_id:
        #     contract_ids = self.get_contract(employee, date_from, date_to)
        #     if not contract_ids:
        #         return
        #     self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        # if not self.contract_id.struct_id:
        #     return
        # self.struct_id = self.contract_id.struct_id

        # # computation of the salary input
        # contracts = self.env['hr.contract'].browse(contract_ids)
        # worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        # worked_days_lines = self.worked_days_line_ids.browse([])
        # for r in worked_days_line_ids:
        #     worked_days_lines += worked_days_lines.new(r)
        # self.worked_days_line_ids = worked_days_lines
        # if contracts:
        #     input_line_ids = self.get_inputs(contracts, date_from, date_to)
        #     input_lines = self.input_line_ids.browse([])
        #     for r in input_line_ids:
        #         input_lines += input_lines.new(r)
        #     self.input_line_ids = input_lines
        return

    # def get_inputs(self, contract_ids, date_from, date_to):
    #     """This Compute the other inputs to employee payslip.
    #                        """
    #     res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
    #     contract_obj = self.env['hr.contract']
    #     emp_id = contract_obj.browse(contract_ids[0].id).employee_id
    #     lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])
    #     for loan in lon_obj:
    #         for loan_line in loan.loan_lines:
    #             if date_from <= loan_line.date <= date_to and not loan_line.paid:
    #                 for result in res:
    #                     if result.get('code') == 'LO':
    #                         result['amount'] = loan_line.amount
    #                         result['loan_line_id'] = loan_line.id
    #     return res

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        LoanLine = self.env['hr.loan.line']

        for payslip in self:
            loan_lines = LoanLine.search([
                ('employee_id', '=', payslip.employee_id.id),
                ('date', '>=', payslip.date_from),
                ('date', '<=', payslip.date_to),
                ('paid', '=', False)
            ], limit=1)
            loan_lines.write({'paid': True, 'payslip_id': payslip.id})
        return res
