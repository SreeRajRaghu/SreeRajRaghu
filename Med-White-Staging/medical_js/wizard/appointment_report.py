# -*- coding: utf-8 -*-
import base64
import io
import xlsxwriter
from odoo import fields, models,_

class MedicalAppointments(models.TransientModel):
    _name = 'medical.appointments.details.wizard'
    _description = 'Appointment Resource Branch Status Details Report'

    filename = fields.Binary()
    start_date = fields.Date(required=True, default=fields.Date.context_today, string='Start Date')
    end_date = fields.Date(required=True, default=fields.Date.context_today, string='End Date')
    branch_ids = fields.Many2many("medical.clinic", required=True, string="Branches")
    resource_ids = fields.Many2many('medical.resource', string='Resource')
    state_ids = fields.Many2many('medical.state',string='State')
    user_ids = fields.Many2many("res.users","res_users_id",string="Users")

    def convert_UTC_TZ(self, UTC_datetime):
        if not self.env.user.tz:
            raise Warning(ERREUR_FUSEAU)
        local_tz = pytz.timezone(self.env.user.tz)
        date = UTC_datetime
        date = pytz.utc.localize(date, is_dst=None).astimezone(local_tz)
        return date.strftime(FORMAT_DATE)

    def get_order_lines(self):

        

        domain = [('date_order', '>=', self.start_date), ('date_order','<=',self.end_date)]
        if self.resource_ids.ids:
            domain += [('resource_id', 'in', self.resource_ids.ids)]

        if self.branch_ids.ids:
            domain += [('clinic_id', 'in', self.branch_ids.ids)]

        if self.user_ids.ids:
            domain += [('user_id', 'in', self.user_ids.ids)]

        if self.state_ids.ids:
            domain += [('state', 'in', self.state_ids.mapped('name'))]

        medical_orders = self.env['medical.order'].search(domain)
        return medical_orders

    def action_xlsx(self):
        status_dict = {'draft': 'Draft',
        'paid': 'Paid',
        'confirmed': 'Confirmed',
        'arrived': 'Arrived',
        'cancel': 'Cancelled',
        'done': 'Posted',
        'invoiced': 'Invoiced',
        'late': 'Late',
        'in': 'In',
        'out': 'Out',
        'no_answer': 'No Answer',
        'no_show': 'No Show'}

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        style_bold_border = workbook.add_format({
            'text_wrap': False,
            'valign': 'middle',
            'bold': True,
        })
        sheet = workbook.add_worksheet('%s'% (''))
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 2, 20)
        sheet.set_column(3, 3, 50)
        sheet.set_column(4, 9, 20)

        # sheet style
        heading = workbook.add_format({'bold': True, 'align': 'center', 'border': 1})
        bold = workbook.add_format({'bold': True, })
        cell = workbook.add_format({'bold': True, })
        total = workbook.add_format({'bold': True, 'align': 'right'})
        # Main Info
        sheet.merge_range(0, 1, 0, 5, '', heading)

        col = 1
        sheet.write(4, col, "Appointment Ref", cell)
        col += 1
        sheet.write(4, col, "File No", cell)
        col += 1
        sheet.write(4, col, "Civil ID", cell)
        col += 1
        sheet.write(4, col, "Description", cell)
        col += 1
        sheet.write(4, col, "Mobile", cell)
        col += 1
        sheet.write(4, col, "Total Amount ", cell)
        col += 1
        sheet.write(4, col, "Paid", cell)
        col += 1
        sheet.write(4, col, "Due", cell)
        col += 1
        sheet.write(4, col, "Status", cell)
        col += 1

        row, col = 4, 0
        medical_orders = self.get_order_lines()
        users_of_orders = medical_orders.mapped('user_id')
        for user in users_of_orders:
            row += 2
            col = 0 
            sheet.write(4, col, "SalesPersone", cell)
            sheet.write(row, col, user.name,cell or '')
            orders = medical_orders.filtered(lambda o: o.user_id.id == user.id)
            for order in orders:
                for line in order.line_ids:
                    row += 1
                    col = 1
                    sheet.write(row, col,line.product_id.default_code or '')
                    col += 1
                    sheet.write(row, col, order.file_no or '')
                    col += 1
                    sheet.write(row, col, order.partner_id.civil_code or '')
                    col += 1
                    sheet.write(row, col, line.product_id.name or '')
                    col += 1
                    sheet.write(row, col, order.partner_id.mobile or '')
                    col += 1
                    sheet.write(row, col, line.subtotal or 0)
                    col += 1
                    sheet.write(row, col, line.amount_paid or 0)
                    col += 1
                    sheet.write(row, col, line.amount_due or 0)
                    col += 1
                    sheet.write(row, col, status_dict[order.state]  or '')
                    col += 1

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Appointment Report.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
            % (self._name, self.id, file_name),
        }
