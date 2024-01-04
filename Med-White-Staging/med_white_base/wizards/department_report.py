# -*- coding: utf-8 -*-
# import operator
# import itertools

from odoo import fields, models, _
import base64
import io
import xlsxwriter
from itertools import groupby


class DepartmentReport(models.TransientModel):
    _name = 'department.report.details.wizard'
    _description = 'Department Report Details Report'

    start_date = fields.Date(required=True, string='Start Date')
    end_date = fields.Date(required=True, string='End Date')
    resource_group_ids = fields.Many2many('medical.resource.group', string='Resource')
    report_type = fields.Selection([
        ("gold", 'Gold'), ("normal", 'Normal')],
        default="normal", string="Report Type")

    def get_report_data(self):
        domain = [
            ('exclude_from_invoice_tab', '=', False),
            ('move_id.company_code', '=', 'gold'),
            ('move_id.invoice_date', '>=', self.start_date), ('move_id.invoice_date', '<=', self.end_date)]

        if self.report_type == 'gold':
            domain += [('', '=', 'gold')]

        if self.resource_group_ids:
            domain.append(['medical_order_line_id.multi_resource_id.group_id', 'in', self.resource_group_ids.ids])
        lines = self.env['account.move.line'].search(domain)
        result = []
        for line in lines:
            line_data = line.read(['product_id', 'name', 'discount', 'price_subtotal', 'amount_paid', 'amount_due', 'medical_order_line_id', 'price_unit', 'quantity', 'discount_fixed'])[0]
            inv_data = line.move_id.read(['invoice_date', 'partner_id'])[0]
            line_data.update(inv_data)
            resource = line.medical_order_line_id.multi_resource_id or line.medical_order_id.resource_id
            partner = line.partner_id
            line_data.update({
                'resource': resource.name,
                'group': resource.group_id.name or 'Undefined',
                'partner': partner.display_name,
                'referal': partner.utm_medium_id and partner.utm_medium_id.name or '',
                'file_no': partner.file_no,
                'file_no2': partner.file_no2,
                'invoice_name': line.move_id.name,
            })
            result.append(line_data)
        return result

    def generate_report(self):
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet(_('Department Report'))

        worksheet.set_column(0, 1, 15)
        worksheet.set_column(2, 3, 25)
        # worksheet.set_column(2, 2, 15)
        # worksheet.set_column(3, 3, 25)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 5, 25)
        worksheet.set_column(6, 20, 10)

        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        def get_date_format(date):
            return date.strftime(date_format) if date else ''

        # style_bold_border_center = workbook.add_format({
        #     'text_wrap': 1,
        #     'valign': 'vjustify',
        #     'border': True,
        #     'bold': True,
        #     'align': 'center',
        # })

        style_bold_font_border = workbook.add_format({
            'valign': 'vjustify',
            'bold': True,
            'align': 'center',
            'border': True})

        # style_bold_font = workbook.add_format({
        #     'valign': 'vjustify',
        #     'bold': True,
        #     'align': 'center',
        # })

        currency_format = workbook.add_format({'num_format': '#,###0.000'})
        currency_format_bold = workbook.add_format({
            'num_format': '#,###0.000', 'bold': True,
            'align': 'center',
            'border': True})

        row = 1
        col = 0
        worksheet.write(row, col, _('From'))
        col += 1
        worksheet.write(row, col, get_date_format(self.start_date))

        row += 1

        col = 0
        worksheet.write(row, col, _('To'))
        col += 1
        worksheet.write(row, col, get_date_format(self.end_date))

        row += 2

        col = 0
        worksheet.write(row, col, _('Department'))
        col += 1
        departments = ''
        if self.resource_group_ids:
            departments = ','.join(self.resource_group_ids.mapped('name'))
        else:
            departments = 'ALL'
        worksheet.write(row, col, departments)

        row += 2
        col = 0
        worksheet.write(row, col, _('Date'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('File No'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Patient Name'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Referal'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Service Name'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Invoice'), style_bold_font_border)

        col += 1
        worksheet.write(row, col, _('Doctor'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Quantity'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Total Amount'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Discount'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Net'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Paid'), style_bold_font_border)
        col += 1
        worksheet.write(row, col, _('Due'), style_bold_font_border)

        move_lines = self.get_report_data()

        move_lines.sort(key=lambda a: a['group'])
        grouped_move_lines = groupby(move_lines, key=lambda a: a['group'])

        row += 1
        # tot_discount_fixed = 0
        for group, lines in grouped_move_lines:
            row += 1
            col = 0
            worksheet.write(row, col, 'Department', style_bold_font_border)
            col += 1
            worksheet.write(row, col, group or '', style_bold_font_border)

            tot_price_unit = 0
            tot_price_subtotal = 0
            tot_amount_paid = 0
            tot_amount_due = 0
            row += 1
            inv_lines = list(lines)
            inv_lines.sort(key=lambda a: a["invoice_date"])
            for line in inv_lines:
                price_unit = line['price_unit']
                quantity = line['quantity']
                discount_fixed = line['discount_fixed']
                price_subtotal = line['price_subtotal']
                amount_paid = line['amount_paid']
                amount_due = line['amount_due']
                discount = line['discount']
                row += 1
                col = 0
                worksheet.write(row, col, get_date_format(line['invoice_date']) or '')
                col += 1
                worksheet.write(row, col, line['file_no2'] or '')
                col += 1
                worksheet.write(row, col, line['partner'] or '')
                col += 1
                worksheet.write(row, col, line['referal'] or '')
                col += 1
                worksheet.write(row, col, line['name'] or '')
                col += 1
                worksheet.write(row, col, line['invoice_name'] or '')
                col += 1
                worksheet.write(row, col, line['resource'] or '')
                col += 1
                worksheet.write(row, col, line['quantity'] or 0)
                col += 1
                worksheet.write(row, col, price_unit * quantity, currency_format)
                col += 1
                worksheet.write(row, col, discount_fixed or (discount and str(discount) + ' %'), currency_format)
                col += 1
                worksheet.write(row, col, price_subtotal, currency_format)
                col += 1
                worksheet.write(row, col, amount_paid, currency_format)
                col += 1
                worksheet.write(row, col, amount_due, currency_format)

                tot_price_unit += (price_unit * quantity)
                # tot_discount_fixed += discount_fixed
                tot_price_subtotal += price_subtotal
                tot_amount_paid += amount_paid
                tot_amount_due += amount_due

            row += 1
            col = 8
            worksheet.write(row, col, tot_price_unit, currency_format_bold)
            col += 1
            col += 1
            worksheet.write(row, col, tot_price_subtotal, currency_format_bold)
            col += 1
            worksheet.write(row, col, tot_amount_paid, currency_format_bold)
            col += 1
            worksheet.write(row, col, tot_amount_due, currency_format_bold)

        workbook.close()
        file_base = base64.b64encode(fp.getvalue())
        fp.close()

        output = self.env['model.output'].create({
            'name': 'Department Report',
            'filename': file_base
        })
        return output.download()
