# coding: utf-8
import calendar
from odoo import fields, models
import base64
import xlsxwriter
import io


class EmployeeAccuralBalanceWizard(models.TransientModel):
    _inherit = 'employee.accural.balance.wizard'

    def get_all_data(self, employees=None):
        Leave = self.env['hr.leave.report']
        LeaveType = self.env['hr.leave.type']

        holiday_status = LeaveType.search([('code', '=', 'ANNUAL')])
        unpaid_holiday_status = LeaveType.search([('code', '=', 'UNPAID')])
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
            leaves_taken = Leave.search([
                ('employee_id', '=', line.id),
                ('holiday_status_id', 'in', holiday_status.ids),
                ('state', '=', 'validate'),
                ('leave_type', '=', 'request'),
            ])
            unpaid_leaves = Leave.search([
                ('employee_id', '=', line.id),
                ('holiday_status_id', 'in', unpaid_holiday_status.ids),
                ('state', '=', 'validate'),
                ('leave_type', '=', 'request'),
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
               	'tot_salary': line.contract_id.wage,
               	'analytic_account': line.contract_id.analytic_account_id.display_name,
               	'section': line.section_id.display_name,
               	'department': line.department_id.display_name,
                'eos_bf_5': line.contract_id.eos_bf_5_year_days,
                'eos_af_5': line.contract_id.eos_after_5_year_days,
                'date_joining': line.date_joining,
                'tags': ', '.join(line.category_ids.mapped('name')),
                'leaves_taken': sum(map(abs, leaves_taken.mapped('number_of_days'))),
                'unpaid_leaves_taken': sum(map(abs, unpaid_leaves.mapped('number_of_days')))
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
        sheet.set_column("C:Z", 25)
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
        sheet.write(3, col, "Department", format_left)
        col += 1
        sheet.write(3, col, "Section", format_left)
        col += 1
        sheet.write(3, col, "Analytic Account", format_left)
        col += 1
        sheet.write(3, col, "Tags", format_left)
        col += 1
        sheet.write(3, col, "Annual Leaves Taken (Days)", format_left)
        col += 1
        sheet.write(3, col, "Unpaid Leaves Taken (Days)", format_left)
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
        sheet.write(3, col, "Contract Salary", format_right)
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
            sheet.write(row, col, line.get('department') or '')
            col += 1
            sheet.write(row, col, line.get('section') or '')
            col += 1
            sheet.write(row, col, line.get('analytic_account') or '')
            col += 1
            sheet.write(row, col, line.get('tags') or '')
            col += 1
            sheet.write(row, col, line.get('leaves_taken') or '')
            col += 1
            sheet.write(row, col, line.get('unpaid_leaves_taken') or '')
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
            sheet.write(row, col, line.get('tot_salary') or 0)
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
