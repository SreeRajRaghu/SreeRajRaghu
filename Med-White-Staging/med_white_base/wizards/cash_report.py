# -*- coding: utf-8 -*-
# import operator
# import itertools
from itertools import groupby
from odoo import fields, models, _
import base64
import io
import xlsxwriter


class CashReport(models.TransientModel):
    _name = 'cash.report.details.wizard'
    _description = 'Cash Report Details Report'

    start_date = fields.Date(required=True, string='Start Date')
    end_date = fields.Date(required=True, string='End Date')
    medical_config_ids = fields.Many2many('medical.config')
    report_type = fields.Selection([
        ("gold", 'Gold'), ("normal", 'Normal')],
        default="normal", string="Report Type")

    def get_report_data(self):
        domain = [
            ('partner_type', '=', 'customer'),
            ('payment_type', '!=', 'transfer'),
            ('payment_date', '>=', self.start_date), ('payment_date', '<=', self.end_date)]

        if self.medical_config_ids:
            domain += [('med_config_id', 'in', self.medical_config_ids.ids)]

        payments = self.env['account.payment'].search(domain, order="payment_date")
        all_journal = payments.mapped('journal_id')
        all_journal_dict = {}
        for journal in all_journal:
            all_journal_dict[journal.id] = {'name': journal.name, 'amount': 0.0}

        result = []

        for line in payments:
            amount = line.amount
            if line.payment_type == 'outbound':
                amount = -(amount)
            payment_line = {
                'receipt': line.name,
                'file_no': line.partner_id.file_no if line.med_config_id.depends_on == 'file_no' else line.partner_id.file_no2,
                'patient_name': line.partner_id.name,
                'referal': line.partner_id.utm_medium_id and line.partner_id.utm_medium_id.name or '',
                'payment_date': line.payment_date,
                'amount': amount,
                'payment_type': line.payment_type,
                'journal_id': line.journal_id,
            }
            history_data = []
            for history in line.payment_history_ids:
                history_line = {
                    'default_code': history.move_line_id.product_id.default_code,
                    'name': history.move_line_id.product_id.name,
                    'resource_name': history.medical_order_resource_id.name,
                    'amount': -1 * history.amount if line.payment_type == 'outbound' else history.amount
                }
                history_data.append(history_line)
            payment_line['history_data'] = history_data
            result.append(payment_line)
        return result, all_journal_dict

    def generate_report(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        def get_date_format(date):
            return date.strftime(date_format) if date else ''

        report_data, all_journal_dict = self.get_report_data()

        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)

        style_bold_font_border = workbook.add_format({
            'valign': 'vjustify',
            'bg_color': '#C5C5C5',
            'bold': True})

        style_bold_heading_font_border = workbook.add_format({
            'valign': 'vjustify',
            'bold': True,
            'align': 'center'})

        currency_format = workbook.add_format({'num_format': '#,###0.000'})
        currency_bold_format = workbook.add_format({'num_format': '#,###0.000', 'bold': True})
        background_format = workbook.add_format({
            'bg_color': '#C5C5C5',
            'num_format': '#,###0.000',
        })

        worksheet = workbook.add_worksheet(_('Cash Report'))
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 10)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 5, 25)
        worksheet.set_column(6, 6, 10)
        worksheet.set_column(7, 7, 15)
        worksheet.set_column(8, 8, 15)
        worksheet.set_column(9, 9, 15)
        worksheet.set_column(10, 10, 15)
        worksheet.set_column(11, 11, 15)
        worksheet.set_column(12, 12, 15)

        row = 1
        col = 0
        worksheet.merge_range(row, col, row, col + 10, "Cash Report", style_bold_heading_font_border)

        row = row + 1
        col = 0

        date_range = "From " + get_date_format(self.start_date) + " To " + get_date_format(self.end_date)
        worksheet.merge_range(row, col, row, col + 10, date_range, style_bold_heading_font_border)

        row = row + 1

        total_payment = 0.0
        total_history_payment = 0.0
        total_insurance_payment = 0.0
        for line in report_data:
            row += 2
            col = 0
            worksheet.write(row, col, "Receipt#", style_bold_font_border)
            col += 1
            worksheet.write(row, col, line.get('receipt'), style_bold_font_border)
            col += 1
            worksheet.write(row, col, "File#", style_bold_font_border)
            col += 1
            worksheet.write(row, col, line.get('file_no'), style_bold_font_border)
            col += 1
            worksheet.write(row, col, "Patient Name", style_bold_font_border)
            col += 1
            worksheet.write(row, col, line.get('patient_name'), style_bold_font_border)
            col += 1
            worksheet.write(row, col, "Date", style_bold_font_border)
            col += 1
            worksheet.write(row, col, get_date_format(line.get('payment_date')), style_bold_font_border)
            col += 1
            amount = line.get('amount')
            total_payment += amount
            worksheet.write(row, col, amount, background_format)
            col += 1
            worksheet.write(row, col, "Payment", style_bold_font_border)
            col += 1
            worksheet.write(row, col, "Insurance", style_bold_font_border)
            col += 1
            worksheet.write(row, col, "Referal#", style_bold_font_border)
            col += 1
            worksheet.write(row, col, line.get('referal'), style_bold_font_border)
            col += 1
            for history in line.get("history_data"):
                row += 1
                col = 0
                worksheet.merge_range(row, col, row, col + 2, history.get('default_code'))
                col += 3
                worksheet.merge_range(row, col, row, col + 3, history.get('name'))
                col += 4
                worksheet.merge_range(row, col, row, col + 1, history.get('resource_name'))
                history_amount = history.get('amount')
                total_history_payment += history_amount
                col += 2
                worksheet.write(row, col, history_amount, currency_format)
                insurance_amount = line.get('insurance_amount', 0.0)
                total_insurance_payment += insurance_amount
                col += 1
                worksheet.write(row, col, insurance_amount, currency_format)

        row += 2
        col = 0
        worksheet.write(row, col, "Payments Count")
        col += 1
        worksheet.write(row, col, len(report_data))
        col += 7
        worksheet.write(row, col, total_payment, currency_bold_format)
        col += 1
        worksheet.write(row, col, total_history_payment, currency_bold_format)
        row += 2

        report_data.sort(key=lambda a: a['journal_id'].id)
        for journal, lines in groupby(report_data, key=lambda a: a['journal_id']):
            row += 1
            lines = list(lines)
            tot = sum(list(map(lambda a: a['amount'], lines)))
            col = 0
            worksheet.write(row, col, journal.name, style_bold_font_border)
            col += 1
            worksheet.write(row, col, tot, currency_bold_format)

        workbook.close()
        file_base = base64.b64encode(fp.getvalue())
        fp.close()

        output = self.env['model.output'].create({
            'name': 'Cash Report',
            'filename': file_base
        })
        return output.download()
