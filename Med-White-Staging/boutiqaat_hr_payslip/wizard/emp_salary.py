# coding: utf-8

import base64
from io import BytesIO
import xlsxwriter
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import fields, models, _
from odoo.addons.hr_default.model.hr_default import SEL_RELIGION


PAYSLIP_STATE = {
    'draft': 'Draft',
    'verify': 'Waiting',
    'done': 'Done',
    'cancel': 'Cancel',
}

LEAVE_ALC_TYPE = {
    'day': "Day",
    'week': "Week",
    'month': 'Month',
}


class WizardEmpSalMasterReport(models.TransientModel):
    _name = 'wizard.emp.salary'
    _description = 'Emp. Sal Master Wizard'

    department_ids = fields.Many2many('hr.department', string='Departments')
    final_date = fields.Date("Upto Date", default=fields.Date.today)
    export_data = fields.Binary()
    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self.env.company)

    def print_excel_emp_master(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        today = fields.Date.today()

        def get_date_format(date):
            return date.strftime(date_format) if date else ''

        domain = [
            ('company_id', '=', self.company_id.id),
        ]
        if self.department_ids:
            domain += [('department_id', 'in', self.department_ids.ids)]

        payslips_heading = [
            'S/N', 'English Name', 'Arabic Name', 'Employee ID', 'Company', 'Work Location', 'Work Address', 'Department',
            'Date of Birth', 'Age (Years)', 'Job Position', 'Manager', 'Coach', 'Section', 'Grade', 'Nationality',
            'Gender', 'Civil ID Number', 'Certification Level', 'Religion',
            'Date of Joining', 'End of probation period', 'Service time (Days)',

            'Basic Salary',
            'Housing/Accomodation', 'Transport Allowance', 'Mobile Allowance', 'Meal Allowance',
            'Motor Vehicle Allowance', 'Driver & Fuel Allowance',
            'Books Allowance', 'Special / Other Allowance', 'Commission', 'PF Allowances', 'Night Shift Allowance',
            'Total Salary',

            'Leave entitlement of the year', 'Leave eligibility', 'Leave amount as of today',
            'EOS entitlement of the year', 'EOS expense of the year', 'EOS entitlement by the end date', 'EOS expense by the end date',
            'Net salary of this month',

            'Medical license number', 'Medical license expiration date', 'Residency expiration date', 'Mobile number', 'Phone number',
            'Emergency Contract', 'Emergency Contract Mobile'
        ]

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet("Employee Master")
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 2, 25)
        worksheet.set_column(3, 45, 18)

        style_bold_border = workbook.add_format({
            'text_wrap': 1,
            'valign': 'middle',
            'border': True,
            'bold': True,
        })

        style_bold_border_center = workbook.add_format({
            'text_wrap': 1,
            'valign': 'top',
            'border': True,
            'bold': True,
            'align': 'center',
        })
        # style_normal_right = workbook.add_format({
        #     'align': 'right',
        # })
        currency_format = workbook.add_format({'num_format': '#,###0.000'})

        row = 2
        col = 1
        worksheet.write(row, col, _('Company:'), style_bold_border)
        col += 1
        worksheet.write(row, col, self.company_id.name, style_bold_border)

        row += 1
        col = 1
        worksheet.write(row, col, _('Printed On:'), style_bold_border)
        col += 1
        worksheet.write(row, col, get_date_format(today), style_bold_border)
        row += 1
        col = 1
        worksheet.write(row, col, _('Data Upto:'), style_bold_border)
        final_date = self.final_date or today
        col += 1
        worksheet.write(row, col, get_date_format(final_date), style_bold_border)

        # Header
        row += 2
        col = 0
        start_row = row
        table_header_line = payslips_heading
        for heading in payslips_heading:
            worksheet.write(row, col, heading, style_bold_border_center)
            col += 1

        row += 1
        col = 0

        employees = self.env['hr.employee'].sudo().search(domain)

        count = 0
        Leave = self.env['hr.leave.report'].sudo()
        Payslip = self.env['hr.payslip'].sudo()
        # LeaveType =
        holiday_status = self.env['hr.leave.type'].search([('code', '=', 'ANNUAL')])
        for emp in employees:
            count += 1
            contract = emp.contract_id
            per_day_salary = contract.get_per_day_salary()

            col = 0
            worksheet.write(row, col, count)
            col += 1
            worksheet.write(row, col, emp.name or '')
            col += 1
            worksheet.write(row, col, emp.arabic_name or '')
            col += 1
            worksheet.write(row, col, emp.identification_id or '')
            col += 1
            worksheet.write(row, col, emp.company_id.name or '')
            col += 1
            worksheet.write(row, col, emp.work_location or '')
            col += 1
            worksheet.write(row, col, emp.work_address or '')
            col += 1
            worksheet.write(row, col, emp.department_id.name or '')
            col += 1
            worksheet.write(row, col, get_date_format(emp.birthday or ''))
            col += 1
            age = ''
            if emp.birthday:
                age = relativedelta(today, emp.birthday).years
            worksheet.write(row, col, age or '')
            col += 1
            worksheet.write(row, col, emp.job_id.name or '')
            col += 1
            worksheet.write(row, col, emp.parent_id.name or '')
            col += 1
            worksheet.write(row, col, emp.coach_id.name or '')
            col += 1
            worksheet.write(row, col, emp.section_id.name or '')
            col += 1
            worksheet.write(row, col, emp.grade_id.name or '')
            col += 1
            worksheet.write(row, col, emp.country_id.name or '')

            col += 1
            worksheet.write(row, col, (emp.gender or '').capitalize())
            col += 1
            worksheet.write(row, col, emp.civil_id or '')
            col += 1
            worksheet.write(row, col, emp.certificate_level or '')
            col += 1
            worksheet.write(row, col, dict(SEL_RELIGION).get(emp.religion, ''))
            col += 1
            worksheet.write(row, col, get_date_format(emp.date_joining or ''))
            col += 1
            worksheet.write(row, col, get_date_format(contract.trial_date_end or ''))
            col += 1
            worksheet.write(row, col, emp.eos_tot_year_days or '')

            # Salary
            col += 1
            worksheet.write(row, col, contract.wage or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.housing_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.transport_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.mobile_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.meal_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.motor_vehicle_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.driver_fuel_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.books_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.special_other_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.commission or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.pf_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.night_shift_allowance or '', currency_format)
            col += 1
            worksheet.write(row, col, contract.total_salary or '', currency_format)

            # Leave
            leave_al = 0
            if contract.leave_allocation > 0:
                mul = 12
                if contract.allocation_type == 'day':
                    mul = 365
                if contract.allocation_type == 'week':
                    mul = 52.14
                leave_al = contract.leave_allocation * mul

            col += 1
            worksheet.write(row, col, leave_al or '')

            balance_leaves = Leave.search([
                ('employee_id', '=', emp.id),
                ('holiday_status_id', 'in', holiday_status.ids),
                ('state', '=', 'validate'),
                '|',
                ('date_to', '<=', str(final_date) + ' 23:59:59'),
                ('date_to', '=', False),
            ])
            current_total_balance = sum(balance_leaves.mapped('number_of_days'))

            col += 1
            worksheet.write(row, col, current_total_balance or '')
            col += 1
            tot_leave_salary = current_total_balance * per_day_salary
            worksheet.write(row, col, tot_leave_salary or 0, currency_format)

            eos_end_year = eos_end_today = 0
            if emp.date_joining and contract.eos_after_5_year_days and contract.eos_bf_5_year_days:
                eoy = datetime.strptime('%s-12-31' % (today.year), '%Y-%m-%d').date()

                eos_days_net_year = ((eoy - emp.date_joining).days - emp.eos_tot_leaves) / 365
                eos_days_a_month_eoy = contract.eos_after_5_year_days if eos_days_net_year > 5 else contract.eos_bf_5_year_days
                eos_end_year = eos_days_net_year * eos_days_a_month_eoy * 12

                eos_years_net_today = ((final_date - emp.date_joining).days - emp.eos_tot_leaves) / 365
                eos_days_a_month = contract.eos_after_5_year_days if eos_years_net_today > 5 else contract.eos_bf_5_year_days
                eos_end_today = eos_days_a_month * eos_years_net_today * 12

            # EoS
            col += 1
            worksheet.write(row, col, eos_end_year or '', currency_format)
            col += 1
            tot_eos_salary_year = eos_end_year * per_day_salary
            worksheet.write(row, col, tot_eos_salary_year or '', currency_format)

            col += 1
            worksheet.write(row, col, eos_end_today or '', currency_format)
            col += 1
            tot_eos_salary_today = eos_end_today * per_day_salary
            worksheet.write(row, col, tot_eos_salary_today or '', currency_format)

            col += 1
            # net_salary = contract.total_salary + tot_leave_salary + tot_eos_salary_today
            domain = [
                ('employee_id', '=', emp.id), ('state', '=', 'done'),
                ('date_from', '<=', final_date), ('date_to', '>=', final_date),
            ]
            payslip = Payslip.search(domain, limit=1)
            worksheet.write(row, col, payslip.net_wage or '', currency_format)

            # Other
            col += 1
            worksheet.write(row, col, emp.medical_license or '')
            col += 1
            worksheet.write(row, col, get_date_format(emp.ml_expiry))
            col += 1
            worksheet.write(row, col, get_date_format(emp.residency_expiry_date))
            col += 1
            worksheet.write(row, col, emp.mobile_phone or '')
            col += 1
            worksheet.write(row, col, emp.phone or '')
            col += 1
            worksheet.write(row, col, emp.emergency_contact or '')
            col += 1
            worksheet.write(row, col, emp.emergency_phone or '')
            row += 1

        table = []
        for h in table_header_line:
            col = {'header': h}
            table.append(col)

        worksheet.add_table(start_row, 0, row + 1, len(table_header_line) - 1, {
            'total_row': 1,
            'columns': table,
            'style': 'Table Style Light 9',
            'first_column': True,
        })
        workbook.close()
        export_data = base64.b64encode(fp.getvalue())
        fp.close()

        self.write({"export_data": export_data})

        file_name = "%s-Emp-Salary-Master.xls" % (str(fields.Date.today()))

        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/%s/%s?download=true'
            % (self._name, self.id, 'export_data', file_name),
        }
