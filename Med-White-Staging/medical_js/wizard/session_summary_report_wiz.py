from odoo import fields, models
import base64
import io
import xlsxwriter


class MedicalSessionWiz(models.TransientModel):
    _name = 'medical.session.details.wizard'
    _description = 'Medical Session Details Report'

    filename = fields.Binary()
    start_date = fields.Date(required=True, default=fields.Date.context_today, string='Start Date')
    end_date = fields.Date(required=True, default=fields.Date.context_today, string='End Date')

    def get_medical_sessions(self):
        medical_sessions = self.env['medical.session'].search([('start_at', '>=', self.start_date.strftime('%Y-%m-%d 00:00:00')),
                                                               ('stop_at', '<=', self.end_date.strftime('%Y-%m-%d 23:59:59')),
                                                               ('state', '=', 'closed')])
        return medical_sessions

    def action_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        payment_state = {'draft': 'Draft', 'posted': 'Validated', 'sent': 'Sent', 'reconciled': 'Reconciled',
                         'cancelled': 'Cancelled'}
        invoice_state = {'draft': 'Draft', 'posted': 'Posted', 'cancel': 'Cancelled'}
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_amount_format = workbook.add_format({'align': 'right', 'font_size': 11})
        cell_text_amount_format_bold = workbook.add_format({'align': 'right', 'bold': True, 'font_size': 11})
        cell_text_format1 = workbook.add_format(
            {'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})
        cell_text_size_format = workbook.add_format(
            {'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 15})

        worksheet = workbook.add_worksheet('%s' % 'session_details.xlsx')
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 22)
        worksheet.set_column('C:C', 13)
        worksheet.set_column('D:D', 42)
        worksheet.set_column('E:E', 24)
        worksheet.set_column('F:F', 23)
        worksheet.set_column('G:G', 41)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 21)
        worksheet.set_column('J:J', 18)
        worksheet.set_column('K:K', 15)
        worksheet.set_column('L:L', 24)
        worksheet.set_column('M:M', 18)
        worksheet.set_column('N:N', 16)
        worksheet.set_column('O:O', 17)
        worksheet.set_column('P:P', 17)
        worksheet.set_column('Q:Q', 18)

        worksheet.write(5, 3, 'Start Date', cell_text_format1)
        worksheet.write(5, 4, self.start_date.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(5, 6, 'End Date', cell_text_format1)
        worksheet.write(5, 7, self.end_date.strftime("%d/%m/%Y"), cell_text_format)

        worksheet.merge_range('A9:A10', 'Responsible User', cell_text_format1)
        worksheet.merge_range('B9:B10', 'Session ID', cell_text_format1)
        worksheet.merge_range('C9:C10', 'Date', cell_text_format1)
        worksheet.merge_range('D9:D10', 'Customer', cell_text_format1)
        worksheet.merge_range('E9:E10', 'Payment Number', cell_text_format1)
        worksheet.merge_range('F9:F10', 'Journal', cell_text_format1)
        worksheet.merge_range('G9:G10', 'Journal Account', cell_text_format1)
        worksheet.merge_range('H9:H10', 'Branch', cell_text_format1)
        worksheet.merge_range('I9:I10', 'Amount', cell_text_format1)
        worksheet.merge_range('J9:J10', 'Status', cell_text_format1)
        worksheet.merge_range('K9:K10', 'Company', cell_text_format1)
        worksheet.merge_range('L9:L10', 'Payment Reference', cell_text_format1)
        worksheet.merge_range('M9:M10', 'Invoice Number', cell_text_format1)
        worksheet.merge_range('N9:N10', 'Invoice Date', cell_text_format1)
        worksheet.merge_range('O9:O10', 'Invoice Amount', cell_text_format1)
        worksheet.merge_range('P9:P10', 'Due Amount', cell_text_format1)
        worksheet.merge_range('Q9:Q10', 'Invoice Status', cell_text_format1)

        row = 11
        total = 0
        invoice_total = 0
        invoice_due = 0
        invoice_state = {'draft': 'Draft', 'posted': 'Posted', 'cancel': 'Cancelled'}
        sessions = self.get_medical_sessions()

        for rec in sessions:
            worksheet.write(row, 0, rec.user_id.name, cell_text_format)
            worksheet.write(row, 1, rec.name, cell_text_format)
            for payment in rec.payment_ids:
                worksheet.write(row, 2, payment.payment_date.strftime("%d/%m/%Y"), cell_text_format)
                worksheet.write(row, 3, payment.partner_id.name, cell_text_format)
                worksheet.write(row, 4, payment.name, cell_text_format)
                worksheet.write(row, 5, payment.journal_id.name, cell_text_format)
                worksheet.write(row, 6, payment.journal_id.default_debit_account_id.name, cell_text_format)
                worksheet.write(row, 7, payment.branch_id.name, cell_text_format)
                worksheet.write(row, 8, "%.3f" % payment.amount,
                                cell_text_amount_format)
                worksheet.write(row, 9, payment_state[payment.state], cell_text_format)
                worksheet.write(row, 10, payment.company_id.name, cell_text_format)
                worksheet.write(row, 11, payment.communication, cell_text_format)
                total += payment.amount
                invoice_ids = payment.invoice_ids
                if not len(payment.invoice_ids) == 1:
                    for invoice in invoice_ids:
                        row += 1
                        worksheet.write(row, 12, invoice.name, cell_text_format)
                        worksheet.write(row, 13, invoice.invoice_date.strftime("%d/%m/%Y"), cell_text_format)
                        worksheet.write(row, 14,
                                        "%.3f" % invoice.amount_total,
                                        cell_text_amount_format)
                        worksheet.write(row, 15,
                                        "%.3f" % invoice.amount_residual,
                                        cell_text_amount_format)
                        worksheet.write(row, 16, invoice_state[invoice.state], cell_text_format)
                        invoice_total += invoice.amount_total
                        invoice_due += invoice.amount_residual
                else:
                    worksheet.write(row, 12, invoice_ids[0].name, cell_text_format)
                    worksheet.write(row, 13, invoice_ids[0].invoice_date.strftime("%d/%m/%Y"), cell_text_format)
                    worksheet.write(row, 14,
                                    "%.3f" % invoice_ids[0].amount_total,
                                    cell_text_amount_format)
                    worksheet.write(row, 15,
                                    "%.3f" % invoice_ids[0].amount_residual,
                                    cell_text_amount_format)
                    worksheet.write(row, 16, invoice_state[invoice_ids[0].state], cell_text_format)
                    invoice_total += invoice_ids[0].amount_total
                    invoice_due += invoice_ids[0].amount_residual
                row += 1
        worksheet.write(row + 1, 7, "Total", cell_text_format1)
        worksheet.write(row + 1, 8, "%.3f" % total,
                        cell_text_amount_format_bold)
        worksheet.write(row + 1, 13, "Total", cell_text_format1)
        worksheet.write(row + 1, 14, "%.3f" % invoice_total,
                        cell_text_amount_format_bold)
        worksheet.write(row + 1, 15, "%.3f" % invoice_due,
                        cell_text_amount_format_bold)
        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Session Report.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
                   % (self._name, self.id, file_name),
        }
