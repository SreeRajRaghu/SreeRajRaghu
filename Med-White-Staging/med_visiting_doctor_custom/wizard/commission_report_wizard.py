# -*- coding: utf-8 -*-

import base64
import io
import xlsxwriter
from odoo import fields, models, _
from odoo.exceptions import UserError


class CommissionReportWizard(models.TransientModel):
    _name = 'commission.report.wizard'
    _description = 'Commission Report'

    filename = fields.Binary()
    date_from = fields.Date('Date From', required=True)
    date_to = fields.Date('Date To', required=True)
    resource_id = fields.Many2one('medical.resource', string='Resource', domain=[('is_visiting_doctor', '=', True)])

    def action_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('%s' % 'Journal Entries Report.xlsx')
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_format_name = workbook.add_format({'font_size': 12})
        cell_text_format_amount = workbook.add_format({'align': 'right', 'border': 1, 'border_color': '#bfbfbf', 'font_size': 13})
        cell_text_format_total_bold = workbook.add_format({'align': 'right', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13, 'bg_color': '#c0c0c0'})
        cell_text_format1 = workbook.add_format({'align': 'center', 'border': 1, 'bg_color': '#d2ebfc', 'bold': True, 'font_size': 13})
        cell_text_format2 = workbook.add_format({'align': 'center', 'border': 1,'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})
        cell_text_format_total = workbook.add_format({'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13, 'bg_color': '#c0c0c0'})

        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 17)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 41)
        worksheet.set_column('E:E', 46)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 18)
        worksheet.set_column('H:H', 18)
        worksheet.set_column('I:I', 18)
        worksheet.set_column('J:J', 18)
        worksheet.set_column('K:K', 18)
        worksheet.set_column('L:L', 18)
        worksheet.set_column('M:M', 18)

        worksheet.merge_range('C2:D2', "Visiting Doctors Commission Report", cell_text_format2)

        worksheet.write(4, 2, 'Invoice Partner', cell_text_format2)
        worksheet.write(4, 3, self.resource_id.name, cell_text_format)
        worksheet.write(5, 2, 'Start Date', cell_text_format2)
        worksheet.write(5, 3, self.date_from.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(6, 2, 'End Date', cell_text_format2)
        worksheet.write(6, 3, self.date_to.strftime("%d/%m/%Y"), cell_text_format)

        records = self.env['account.move'].search([('invoice_date', '>=', self.date_from),
                                                   ('invoice_date', '<=', self.date_to),
                                                   ('resource_id', '=', self.resource_id.id),
                                                   ('state', '=', 'posted'),
                                                   ('type', '=', 'out_invoice')])
        bill_records = self.env['account.move'].search([('invoice_date', '>=', self.date_from),
                                                        ('invoice_date', '<=', self.date_to),
                                                        ('resource_id', '=', self.resource_id.id),
                                                        ('partner_id', '=', self.resource_id.partner_id.id),
                                                        ('state', '=', 'posted'),
                                                          ('type', '=', 'in_invoice')])

        row = 11
        grand_total = 0
        sub_gross = 0
        sl_no = 0
        if records:
            worksheet.merge_range('A9:A10', 'Sl No.', cell_text_format1)
            worksheet.merge_range('B9:B10', 'Date', cell_text_format1)
            worksheet.merge_range('C9:C10', 'Invoice', cell_text_format1)
            worksheet.merge_range('D9:D10', 'Patient Name', cell_text_format1)
            worksheet.merge_range('E9:E10', 'Product', cell_text_format1)
            worksheet.merge_range('F9:F10', 'Gross', cell_text_format1)
            worksheet.merge_range('G9:G10', 'Discount', cell_text_format1)
            worksheet.merge_range('H9:H10', 'Total Sign', cell_text_format1)
            worksheet.merge_range('I9:I10', 'Due', cell_text_format1)
            worksheet.merge_range('J9:J10', 'Product Cost', cell_text_format1)
            worksheet.merge_range('K9:K10', 'Quantity', cell_text_format1)
            worksheet.merge_range('L9:L10', 'Cost Total', cell_text_format1)
            worksheet.merge_range('M9:M10', 'Net Total', cell_text_format1)
            for rec in records:
                sl_no += 1
                total = 0
                sub_cost = 0
                worksheet.write(row, 0, sl_no, cell_text_format)
                worksheet.write(row, 1, rec.invoice_date.strftime("%d/%m/%Y"), cell_text_format)
                worksheet.write(row, 2, rec.name, cell_text_format_name)
                worksheet.write(row, 3, rec.partner_id.name, cell_text_format_name)
                worksheet.write(row, 9, rec.amount_total_gross, cell_text_format_name)

                for line in rec.invoice_line_ids:
                    cost = line.product_id.standard_price * line.quantity
                    worksheet.write(row, 4, line.product_id.name, cell_text_format_name)
                    worksheet.write(row, 5, line.price_unit, cell_text_format_name)
                    worksheet.write(row, 6, line.discount_fixed, cell_text_format_name)
                    worksheet.write(row, 7, line.price_subtotal, cell_text_format_name)
                    worksheet.write(row, 9, line.product_id.standard_price, cell_text_format_name)
                    worksheet.write(row, 10, line.quantity, cell_text_format_name)
                    worksheet.write(row, 11, cost, cell_text_format_name)
                    total += line.price_subtotal
                    sub_cost += cost
                    row += 1
                sub_total = total - sub_cost
                worksheet.write(row, 3, "Total", cell_text_format_total)
                worksheet.write(row, 4, "", cell_text_format_total)
                worksheet.write(row, 5, "", cell_text_format_total)
                worksheet.write(row, 6, "", cell_text_format_total)
                worksheet.write(row, 7, "%.3f" % total, cell_text_format_total_bold)
                worksheet.write(row, 8, "%.3f" % rec.amount_residual, cell_text_format_total)
                worksheet.write(row, 9, "", cell_text_format_total)
                worksheet.write(row, 10, "", cell_text_format_total)
                worksheet.write(row, 11, "%.3f" % sub_cost, cell_text_format_total_bold)
                worksheet.write(row, 12, "%.3f" % abs(sub_total), cell_text_format_total_bold)
                row += 2
                grand_total += abs(sub_total)
                sub_gross += total
            worksheet.write(row, 3, "Grand Total", cell_text_format_total)
            worksheet.write(row, 7, "%.3f" % abs(sub_gross), cell_text_format_total_bold)
            worksheet.write(row, 12, "%.3f" % abs(grand_total), cell_text_format_total_bold)
            row += 5
            if self.resource_id.percentage_or == 'percentage':
                percentage = grand_total * self.resource_id.percentage
                worksheet.write(row, 3, "Commission percentage :", cell_text_format_total)
                worksheet.write(row, 4, "%.1f" % abs(self.resource_id.percentage*100) + "%", cell_text_format_total)
                row += 1
                worksheet.write(row, 3, "The commission for %s" % self.resource_id.name, cell_text_format_total)
                worksheet.write(row, 4, "%.3f" % abs(percentage), cell_text_format_total)
            elif self.resource_id.percentage_or == 'by_value':
                value = self.resource_id.discount_line_ids.filtered(lambda p: p.from_ <= grand_total <= p.to_)
                if not value:
                    raise UserError(_("Please set commission percentage for the Resource"))
                percentage = grand_total * value.percentage
                worksheet.write(row, 3, "Commission percentage", cell_text_format_total)
                worksheet.write(row, 4, "%.1f" % abs(value.percentage*100) + "%", cell_text_format_total)
                row += 1
                worksheet.write(row + 1, 3, "The commission for %s" % self.resource_id.name, cell_text_format_total)
                worksheet.write(row + 1, 4, "%.3f" % abs(percentage), cell_text_format_total)
        row += 10
        if bill_records:

            worksheet.merge_range('A%s:A%s' % (row, row+1), 'Sl No.', cell_text_format1)
            worksheet.merge_range('B%s:B%s' % (row, row+1), 'Date', cell_text_format1)
            worksheet.merge_range('C%s:C%s' % (row, row+1), 'Bill', cell_text_format1)
            worksheet.merge_range('D%s:D%s' % (row, row+1), 'Expense Name', cell_text_format1)
            worksheet.merge_range('E%s:E%s' % (row, row+1), 'Total', cell_text_format1)
            worksheet.merge_range('F%s:F%s' % (row, row+1), 'Due', cell_text_format1)
            row += 1
            s_no = 0
            sum_of_bill = 0
            sum_due = 0
            for rec in bill_records:
                s_no += 1
                worksheet.write(row, 0, s_no, cell_text_format)
                worksheet.write(row, 1, rec.invoice_date.strftime("%d/%m/%Y"), cell_text_format)
                worksheet.write(row, 2, rec.name, cell_text_format_name)
                sum_bill = 0
                for line in rec.invoice_line_ids:
                    worksheet.write(row, 3, line.name, cell_text_format_name)
                    worksheet.write(row, 4, line.price_subtotal, cell_text_format_name)
                    sum_bill += line.price_subtotal
                    row += 1
                worksheet.write(row, 3, "Total", cell_text_format_total)
                worksheet.write(row, 4, "%.3f" % sum_bill, cell_text_format_total_bold)
                worksheet.write(row, 5, "%.3f" % rec.amount_residual, cell_text_format_total_bold)
                sum_of_bill += sum_bill
                sum_due += rec.amount_residual
                row += 2
            if len(bill_records) != 1:
                worksheet.write(row, 3, "Total", cell_text_format_total)
                worksheet.write(row, 4, "%.3f" % sum_of_bill, cell_text_format_total_bold)
                worksheet.write(row, 5, "%.3f" % sum_due, cell_text_format_total_bold)

            row += 1

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Commission Report'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
                   % (self._name, self.id, file_name),
        }


