# -*- coding: utf-8 -*-

import calendar
from odoo import api, fields, models
import base64
import xlsxwriter
import io


class EmployeeAccuralBalanceWizard(models.TransientModel):
    _name = 'employee.accural.balance.wizard'
    _description = 'Employee Accural Balance Wizard'

    # date_from = fields.Date("From Date", default=fields.Date.today, required=True)
    # date_to = fields.Date("To Date", default=fields.Date.today, required=True)
    filename = fields.Binary()
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    # holiday_status_id = fields.Many2one('hr.leave.type', string='Time Off Type', domain=[('valid', '=', True)])
    current_total_balance = fields.Float('Current Leave Balance')
    working_days_balance = fields.Float('Working Days Balance')
    total_accured_balance = fields.Float('Total Accured Balance')
    eos_balance = fields.Float(related="employee_id.eos_balance")
    date_joining = fields.Date(related="employee_id.date_joining")
    allocation_value = fields.Float('Allocation Value')
    allocation_type = fields.Selection([
                        ('day', 'Day'),
                        ('week', 'Week'),
                        ('month', 'Month')],
                        string='Allocation Type')

    @api.onchange('employee_id', 'date')
    def onchange_employee_id(self):
        self.current_total_balance = 0.0
        self.working_days_balance = 0.0
        self.total_accured_balance = 0.0
        self.allocation_value = 0.0
        self.allocation_type = False
        if self.employee_id and self.date:
            data = self.get_all_data(self.employee_id)
            if data:
                data = data[0]
                self.current_total_balance = data['current_total_balance']
                self.working_days_balance = data['working_days_balance']
                self.total_accured_balance = data['total_accured_balance']
                self.allocation_value = data['allocation_value']
                self.allocation_type = data['allocation_type']

    def print_pdf(self):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['employee_id', 'date'])[0]
        data['employee_data'] = self.get_all_data(self.employee_id)
        return self.env.ref('boutiqaat_reports.action_all_employee_leave_accural_balance').report_action(self, data=data)
        # return self.env.ref('boutiqaat_reports.action_employee_leave_accural_balance').report_action(self, data=data)

    # def get_data(self):
    #     Leave = self.env['hr.leave.report']
    #     LeaveType = self.env['hr.leave.type']

    #     holiday_status = LeaveType.search([('code', '=', 'ANNUAL')])

    #     working_days_balance = 0.0
    #     allocation_value = 0.0
    #     total_accured_balance = 0.0
    #     allocation_type = ''
    #     alloc_type = ''

    #     balance_leaves = Leave.search([
    #         ('employee_id', '=', self.employee_id.id),
    #         ('holiday_status_id', 'in', holiday_status.ids),
    #         ('state', '=', 'validate')
    #     ])
    #     working_days_balance = 0.0
    #     current_total_balance = sum(balance_leaves.mapped('number_of_days'))

    #     today = fields.Date.today()

    #     worked_days = (self.date - today).days
    #     if worked_days <= 0.0:
    #         worked_days = 0.0

    #     if self.employee_id.contract_id:
    #         working_days = 0.0
    #         allocation_value = self.employee_id.contract_id.leave_allocation
    #         allocation_type = self.employee_id.contract_id.allocation_type
    #         if allocation_type == 'month':
    #             month_days = calendar.monthrange(self.date.year, self.date.month)[1]
    #             working_days = worked_days / month_days
    #         elif allocation_type == 'week':
    #             working_days = worked_days / 7
    #         elif allocation_type == 'day':
    #             working_days = worked_days
    #         working_days_balance = allocation_value * working_days

    #         if allocation_type == 'month':
    #             alloc_type = 'Month'
    #         elif allocation_type == 'day':
    #             alloc_type = 'Day'
    #         elif allocation_type == 'week':
    #             alloc_type = 'Week'
    #     total_accured_balance = (current_total_balance + working_days_balance)

    #     return {
    #         'employee': self.employee_id.name,
    #         'holiday_status': holiday_status.name,
    #         'current_total_balance': round(current_total_balance, 2),
    #         'total_accured_balance': round(total_accured_balance, 2),
    #         'working_days_balance': round(working_days_balance, 2),
    #         'eos_bal': self.employee_id.eos_balance,
    #         'allocation_value': allocation_value,
    #         'allocation_type': allocation_type,
    #         'alloc_type': alloc_type,
    #     }

    def print_all_pdf(self):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['employee_id', 'date'])[0]
        employee_data = self.get_all_data()
        data['employee_data'] = employee_data
        return self.env.ref('boutiqaat_reports.action_all_employee_leave_accural_balance').report_action(self, data=data)

    def get_all_data(self, employees=None):
        Leave = self.env['hr.leave.report']
        LeaveType = self.env['hr.leave.type']

        holiday_status = LeaveType.search([('code', '=', 'ANNUAL')])
        today = fields.Date.today()
        worked_days = (self.date - today).days
        if worked_days <= 0.0:
            worked_days = 0.0
        if not employees:
            employees = self.env['hr.employee'].search([])
        data = []
        for line in employees:
            alloc_type = ''
            balance_leaves = Leave.search([
                ('employee_id', '=', line.id),
                ('holiday_status_id', 'in', holiday_status.ids),
                ('state', '=', 'validate')
            ])
            working_days_balance = 0.0
            current_total_balance = sum(balance_leaves.mapped('number_of_days'))
            allocation_value = 0.0
            allocation_type = 0.0
            if line.contract_id:
                working_days = 0.0
                allocation_value = line.contract_id.leave_allocation
                allocation_type = line.contract_id.allocation_type
                if allocation_type == 'month':
                    month_days = calendar.monthrange(self.date.year, self.date.month)[1]
                    working_days = worked_days / month_days
                    alloc_type = 'Month'
                elif allocation_type == 'week':
                    working_days = worked_days / 7
                    alloc_type = 'Week'
                elif allocation_type == 'day':
                    working_days = worked_days
                    alloc_type = 'Day'
                working_days_balance = allocation_value * working_days
            total_accured_balance = (current_total_balance + working_days_balance)
            data.append({
                'employee': line.name,
                'holiday_status': holiday_status.name,
                'current_total_balance': round(current_total_balance, 2),
                'total_accured_balance': round(total_accured_balance, 2),
                'working_days_balance': round(working_days_balance, 2),
                'allocation_value': allocation_value,
                'allocation_type': allocation_type,
                'alloc_type': alloc_type,
                'eos_bal': line.eos_balance,
                'eos_bf_5': line.contract_id.eos_bf_5_year_days,
                'eos_af_5': line.contract_id.eos_after_5_year_days,
                'date_joining': line.date_joining
            })
        return data

    def action_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        def get_date_format(date):
            return date.strftime(date_format) if date else ''

        sheet = workbook.add_worksheet('%s' % ('Sales-POS Payment By Journal'))
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 15)
        # sheet.set_column(2, 5, 18)
        sheet.set_column("C:I", 25)
        # sheet style
        heading = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        # bold = workbook.add_format({'bold': True})
        format_right = workbook.add_format({'bold': True, 'align': 'right', 'bg_color': '#c0c0c0'})
        format_left = workbook.add_format({'bold': True, 'bg_color': '#c0c0c0'})
        # style = workbook.add_format({})
        # Main Info

        sheet.merge_range(0, 0, 0, 4, 'Employee Balance', heading)

        # # Header
        col = 0
        sheet.write(3, col, "Employee", format_left)
        col += 1
        sheet.write(3, col, "Joining Date", format_left)
        col += 1
        sheet.write(3, col, "EoS Bfr 5yr (days/month)", format_right)
        col += 1
        sheet.write(3, col, "EoS Afr 5yr(days/month)", format_right)
        col += 1
        sheet.write(3, col, "Leave Allocation", format_right)
        col += 1
        sheet.write(3, col, "Current Leave Balance", format_right)
        col += 1
        sheet.write(3, col, "Working Leave Balance", format_right)
        col += 1
        sheet.write(3, col, "Total Leave Balance", format_right)
        col += 1
        sheet.write(3, col, "Current EoS Balance (days)", format_right)
        col += 1
        row, col = 4, 0
        locations = self.get_all_data()
        for line in locations:
            row += 1
            col = 0
            sheet.write(row, col, line.get('employee') or '')
            col += 1
            sheet.write(row, col, get_date_format(line.get('date_joining')) or 0)
            col += 1
            sheet.write(row, col, line.get('eos_bf_5') or 0)
            col += 1
            sheet.write(row, col, line.get('eos_af_5') or 0)
            col += 1
            sheet.write(row, col, line.get('allocation_value') or 0)
            col += 1
            sheet.write(row, col, line.get('current_total_balance') or 0)
            col += 1
            sheet.write(row, col, line.get('working_days_balance') or 0)
            col += 1
            sheet.write(row, col, line.get('total_accured_balance') or 0)
            col += 1
            sheet.write(row, col, line.get('eos_bal') or 0)
            col += 1

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()
        self.filename = file_base

        file_name = 'Employee Accural Balance.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
            % (self._name, self.id, file_name),
        }
