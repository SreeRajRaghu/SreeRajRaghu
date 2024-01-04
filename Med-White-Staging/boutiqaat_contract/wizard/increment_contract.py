# -*- coding: utf-8 -*-
import base64
from io import BytesIO
import xlsxwriter
from odoo import fields, models, _


class IncrementContract(models.TransientModel):
    _name = "wiz.increment.contract"
    _description = "Wizard Increment Contract"

    date_from = fields.Date("From Date", default=fields.Date.today, required=True)
    date_to = fields.Date("To Date", default=fields.Date.today, required=True)
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    export_data = fields.Binary()

    def get_contract_details(self):
        domain = [('next_contract_id', '=', False)]
        if self.employee_ids:
            domain += [('employee_id', 'in', self.employee_ids.ids)]
        domain += [
            ('date_start', '>=', self.date_from),
            '|',
            ('date_end', '<=', self.date_to),
            ('date_end', '=', False),
        ]

        # Fetch Last Contracts (Whether Updated or Single Contracts)
        contracts = self.env['hr.contract'].search(domain, order="date_start")
        return contracts

    def action_increment_report(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format
        CONTRACT_STATES = {
            'draft': 'New',
            'open': 'Running',
            'close': 'Expired',
            'cancel': 'Cancelled',
            'upd': 'Updated',
        }

        def get_date_format(dt):
            return dt.strftime(date_format) if dt else ''

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        style_bold_border = workbook.add_format({
            'text_wrap': False,
            'valign': 'middle',
            'bold': True,
        })
        style_bold_border_center = workbook.add_format({
            'text_wrap': False,
            'valign': 'top',
            'border': True,
            'bold': True,
            'align': 'center',
        })
        style_title = workbook.add_format({
            'text_wrap': False,
            'valign': 'top',
            'bold': True,
            'align': 'center',
        })
        all_contracts = self.get_contract_details()

        user_date_from = get_date_format(self.date_from)
        user_date_to = get_date_format(self.date_to)

        worksheet = workbook.add_worksheet("Increment Contract Details")
        worksheet.set_column("A:I", 13)

        row = 1
        col = 3
        worksheet.write(row, col, _('Contract Increments :: From %s To %s') % (
            user_date_from, user_date_to), style_title)

        for emp in all_contracts.mapped('employee_id'):
            emp_contracts = all_contracts.filtered(lambda r: r.employee_id.id == emp.id)
            emp_name = emp.name
            emp_no = emp.identification_id
            calendar = emp.resource_calendar_id

            row += 3
            col = 0
            worksheet.write(row, col, _('Name:'), style_bold_border)
            col += 1
            # worksheet.merge_range(row, col, row, col + 2, emp_name, style_bold_border)
            worksheet.write(row, col, emp_name, style_bold_border)

            col = 3
            worksheet.write(row, col, _('Department:'), style_bold_border)
            col += 1
            # worksheet.merge_range(row, col, row, col + 1, emp.department_id.name, style_bold_border)
            worksheet.write(row, col, emp.department_id.name or '', style_bold_border)

            col = 5
            worksheet.write(row, col, _('Working Hours:'), style_bold_border)
            col += 1
            worksheet.write(row, col, calendar.name, style_bold_border)

            row += 1
            col = 0
            worksheet.write(row, col, _('Number:'), style_bold_border)
            col += 1
            worksheet.write(row, col, emp_no, style_bold_border)

            col = 3
            worksheet.write(row, col, _('Job Position:'), style_bold_border)
            col += 1
            # worksheet.merge_range(row, col, row, col + 1, emp.job_id.name, style_bold_border)
            worksheet.write(row, col, emp.job_id.name or '', style_bold_border)

            header_line = [
                {'name': _('Contract'), 'larg': 13, 'col': {}},
                {'name': _('Start Date'), 'larg': 13, 'col': {}},
                {'name': _('End Date'), 'larg': 13, 'col': {}},
                {'name': _('Total Salary'), 'larg': 13, 'col': {}},
                {'name': _('Diff'), 'larg': 15, 'col': {}},
                {'name': _('Status'), 'larg': 15, 'col': {}},
            ]
            row += 2
            col = 0
            start_row = row
            for h in header_line:
                worksheet.write(row, col, h['name'], style_bold_border_center)
                col += 1

            def add_contract_line(row, col, contract, prev_tot_salary=0):
                col = 0
                diff = prev_tot_salary - contract.total_salary
                worksheet.write(row, col, contract.name or '')
                col += 1
                worksheet.write(row, col, get_date_format(contract.date_start) or '')
                col += 1
                worksheet.write(row, col, get_date_format(contract.date_end) or '')
                col += 1
                worksheet.write(row, col, contract.total_salary or '')
                col += 1
                worksheet.write(row, col, prev_tot_salary and diff or '')
                col += 1
                worksheet.write(row, col, CONTRACT_STATES.get(contract.state) or '')

            exact_prev_contract_wage = 0
            for contract in emp_contracts:
                row += 2
                add_contract_line(row, col, contract, exact_prev_contract_wage)
                prev_contract = contract.prev_contract_id
                exact_prev_contract_wage = contract.total_salary

                while prev_contract:
                    row += 1
                    add_contract_line(row, col, prev_contract, exact_prev_contract_wage)
                    exact_prev_contract_wage = prev_contract.total_salary
                    prev_contract = prev_contract.prev_contract_id

            table = []
            for h in header_line:
                col = {}
                col['header'] = h['name']
                col.update(h['col'])
                table.append(col)

            worksheet.add_table(start_row, 0, row + 1, len(header_line) - 1, {
                'total_row': 1,
                'columns': table,
                'style': 'Table Style Light 9',
                'first_column': True,
            })

        workbook.close()
        export_data = base64.b64encode(fp.getvalue())
        fp.close()
        self.write({"export_data": export_data})

        file_name = "Increment-Report.xlsx"
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/%s/%s?download=true'
            % (self._name, self.id, 'export_data', file_name),
        }
