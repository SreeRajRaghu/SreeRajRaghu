from odoo import fields, models, _, api
from odoo.exceptions import UserError
import base64
import io
import xlsxwriter


class LabToLabReportWiz(models.TransientModel):
    _name = 'lab.lab.report.wizard'
    _description = 'Lab To Lab Report Wizard'

    filename = fields.Binary()
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.onchange('start_date', 'end_date', 'partner_id')
    def _onchange_date_field(self):
        if self.start_date and self.end_date:
            partner_list = self.env['account.move'].search([('invoice_date', '>=', self.start_date),
                                                            ('invoice_date', '<=', self.end_date),
                                                            ('state', '=', 'posted'),
                                                            ('is_insurance_invoice', '=', True)]).mapped('partner_id.id')
            if not partner_list:
                return {'domain': {'partner_id': []}}

            domain = [('id', 'in', partner_list)]
            return {'domain': {'partner_id': domain}}
        else:
            return {'domain': {'partner_id': []}}

    def action_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('%s' % 'Journal Entries Report.xlsx')
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_format_name = workbook.add_format({'font_size': 12})
        cell_text_format_amount = workbook.add_format({'align': 'right', 'border': 1, 'border_color': '#bfbfbf', 'font_size': 13})
        cell_text_format_total_bold = workbook.add_format({'align': 'right', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13, 'bg_color': '#c0c0c0'})
        cell_text_format1 = workbook.add_format({'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})
        cell_text_format_total = workbook.add_format({'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13, 'bg_color': '#c0c0c0'})

        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 49)
        worksheet.set_column('D:D', 41)
        worksheet.set_column('E:E', 16)

        worksheet.merge_range('C2:D2', "Lab-To-Lab Report", cell_text_format1)
        parent = self.partner_id.parent_id.name + ", " if self.partner_id.parent_id.name else ""

        worksheet.write(4, 2, 'Invoice Partner', cell_text_format1)
        worksheet.write(4, 3, parent + self.partner_id.name, cell_text_format)
        worksheet.write(5, 2, 'Start Date', cell_text_format1)
        worksheet.write(5, 3, self.start_date.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(6, 2, 'End Date', cell_text_format1)
        worksheet.write(6, 3, self.end_date.strftime("%d/%m/%Y"), cell_text_format)

        worksheet.merge_range('A9:A10', 'Sl No.', cell_text_format1)
        worksheet.merge_range('B9:B10', 'Invoice/Bill Date', cell_text_format1)
        worksheet.merge_range('C9:C10', 'Appointment - Patient Name', cell_text_format1)
        worksheet.merge_range('D9:D10', 'Test Name', cell_text_format1)
        worksheet.merge_range('E9:E10', 'Unit price', cell_text_format1)
        domain = [('invoice_date', '>=', self.start_date),
                  ('invoice_date', '<=', self.end_date),
                  ('state', '=', 'posted'),
                  ('is_insurance_invoice', '=', True),
                  ('partner_id', '=', self.partner_id.id)]

        records = self.env['account.move'].search(domain)
        if not records:
            raise UserError(_('No Records found!!!'))

        row = 11
        grand_total = 0
        sl_no = 0
        for rec in records:
            sl_no += 1
            total = 0
            worksheet.write(row, 0, sl_no, cell_text_format)
            worksheet.write(row, 1, rec.invoice_date.strftime("%d/%m/%Y"), cell_text_format)
            worksheet.write(row, 2, '  ' + rec.medical_order_id.file_no + ' - ' + rec.ref_invoice_id.partner_id.name, cell_text_format_name)
            for line in rec.invoice_line_ids:
                worksheet.write(row, 3, line.product_id.name, cell_text_format)
                worksheet.write(row, 4, "%.3f" % line.price_subtotal, cell_text_format_amount)
                total += line.price_subtotal
                grand_total += line.price_subtotal
                row += 1
            worksheet.write(row, 3, "Total", cell_text_format_total)
            worksheet.write(row, 4, "%.3f" % total, cell_text_format_total_bold)
            row += 2
        worksheet.write(row, 3, "Grand Total", cell_text_format_total)
        worksheet.write(row, 4, "%.3f" % grand_total, cell_text_format_total_bold)

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Lab To Lab Report.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
                   % (self._name, self.id, file_name),
        }
