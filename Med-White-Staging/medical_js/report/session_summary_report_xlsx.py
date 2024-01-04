from odoo import models
import io
import base64


class PartnerXlsx(models.AbstractModel):
    _name = 'report.medical_js.session_summary_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, doc):
        sheet_name = 'session_details.xlsx'
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_amount_format = workbook.add_format({'align': 'right', 'font_size': 11})
        cell_text_amount_format_bold = workbook.add_format({'align': 'right','bold': True, 'font_size': 11})
        cell_text_format1 = workbook.add_format({'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})
        cell_text_size_format = workbook.add_format({'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 15})

        worksheet = workbook.add_worksheet(sheet_name)
        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 42)
        worksheet.set_column('C:C', 28)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 23)
        worksheet.set_column('F:F', 17)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 26)
        worksheet.set_column('I:I', 18)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)
        worksheet.set_column('M:M', 18)

        worksheet.merge_range('E2:E3', 'Session Summary', cell_text_size_format)
        worksheet.merge_range('F2:G3', doc.name, cell_text_size_format)
        worksheet.write(5, 3, 'Responsible Person', cell_text_format1)
        worksheet.write(5, 4, doc.user_id.name, cell_text_format)
        worksheet.write(6, 3, 'Scheduler', cell_text_format1)
        worksheet.write(6, 4, doc.config_id.name, cell_text_format)
        worksheet.write(5, 6, 'Opening Date', cell_text_format1)
        worksheet.write(5, 7, doc.start_at.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(6, 6, 'Closing Date', cell_text_format1)
        worksheet.write(6, 7, doc.stop_at.strftime("%d/%m/%Y") if doc.start_at else "", cell_text_format)

        worksheet.merge_range('A9:A10', 'Date', cell_text_format1)
        worksheet.merge_range('B9:B10', 'Customer', cell_text_format1)
        worksheet.merge_range('C9:C10', 'Payment Number', cell_text_format1)
        worksheet.merge_range('D9:D10', 'Journal', cell_text_format1)
        worksheet.merge_range('E9:E10', 'Amount', cell_text_format1)
        worksheet.merge_range('F9:F10', 'Status', cell_text_format1)
        worksheet.merge_range('G9:G10', 'Company', cell_text_format1)
        worksheet.merge_range('H9:H10', 'Payment Reference', cell_text_format1)
        worksheet.merge_range('I9:I10', 'Invoice Number', cell_text_format1)
        worksheet.merge_range('J9:J10', 'Invoice Date', cell_text_format1)
        worksheet.merge_range('K9:K10', 'Invoice Amount', cell_text_format1)
        worksheet.merge_range('L9:L10', 'Due Amount', cell_text_format1)
        worksheet.merge_range('M9:M10', 'Invoice Status', cell_text_format1)

        row = 11
        total = 0
        invoice_total = 0
        invoice_due = 0
        payment_state = {'draft': 'Draft', 'posted': 'Validated', 'sent': 'Sent', 'reconciled': 'Reconciled', 'cancelled': 'Cancelled'}
        invoice_state = {'draft': 'Draft', 'posted': 'Posted', 'cancel': 'Cancelled'}

        for rec in doc.payment_ids:
            worksheet.write(row, 0, rec.payment_date.strftime("%d/%m/%Y"), cell_text_format)
            worksheet.write(row, 1, rec.partner_id.name, cell_text_format)
            worksheet.write(row, 2, rec.name, cell_text_format)
            worksheet.write(row, 3, rec.journal_id.name, cell_text_format)
            worksheet.write(row, 4, "%.3f" % rec.amount, cell_text_amount_format)
            worksheet.write(row, 5, payment_state[rec.state], cell_text_format)
            worksheet.write(row, 6, rec.company_id.name, cell_text_format)
            worksheet.write(row, 7, rec.communication, cell_text_format)
            total += rec.amount
            invoice_ids = rec.invoice_ids
            if not len(rec.invoice_ids) == 1:
                for invoice in invoice_ids:
                    row += 1
                    worksheet.write(row, 8, invoice.name, cell_text_format)
                    worksheet.write(row, 9, invoice.invoice_date.strftime("%d/%m/%Y"), cell_text_format)
                    worksheet.write(row, 10, "%.3f" % invoice.amount_total, cell_text_amount_format)
                    worksheet.write(row, 11, "%.3f" % invoice.amount_residual, cell_text_amount_format)
                    worksheet.write(row, 12, invoice_state[invoice.state], cell_text_format)
                    invoice_total += invoice.amount_total
                    invoice_due += invoice.amount_residual
            else:
                worksheet.write(row, 8, invoice_ids[0].name, cell_text_format)
                worksheet.write(row, 9, invoice_ids[0].invoice_date.strftime("%d/%m/%Y"), cell_text_format)
                worksheet.write(row, 10, "%.3f" % invoice_ids[0].amount_total, cell_text_amount_format)
                worksheet.write(row, 11, "%.3f" % invoice_ids[0].amount_residual, cell_text_amount_format)
                worksheet.write(row, 12, invoice_state[invoice_ids[0].state], cell_text_format)
                invoice_total += invoice_ids[0].amount_total
                invoice_due += invoice_ids[0].amount_residual
            row += 1
        worksheet.write(row+1, 3, "Total", cell_text_format1)
        worksheet.write(row+1, 4, "%.3f" % total, cell_text_amount_format_bold)
        worksheet.write(row+1, 9, "Total", cell_text_format1)
        worksheet.write(row+1, 10, "%.3f" % invoice_total, cell_text_amount_format_bold)
        worksheet.write(row+1, 11, "%.3f" % invoice_due, cell_text_amount_format_bold)

            