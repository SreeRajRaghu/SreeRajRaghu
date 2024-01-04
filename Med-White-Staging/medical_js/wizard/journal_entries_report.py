from odoo import fields, models
import base64
import io
import xlsxwriter


class JournalEntriesWiz(models.TransientModel):
    _name = 'journal.entries.report.wizard'
    _description = 'Journal Entries Report'

    filename = fields.Binary()
    start_date = fields.Date(default=fields.Date.context_today, string='Start Date')
    end_date = fields.Date(default=fields.Date.context_today, string='End Date')
    account_id = fields.Many2one('account.account', string='Account')

    def action_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('%s' % 'Journal Entries Report.xlsx')
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_amount_format = workbook.add_format({'align': 'right', 'font_size': 11})
        cell_text_amount_format_bold = workbook.add_format({'align': 'right', 'bold': True, 'font_size': 11})
        cell_text_format1 = workbook.add_format(
            {'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})
        cell_text_size_format = workbook.add_format(
            {'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 15})
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 13)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 45)
        worksheet.set_column('E:E', 42)
        worksheet.set_column('F:F', 23)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 18)
        worksheet.set_column('I:I', 18)
        worksheet.set_column('J:J', 18)

        worksheet.write(5, 3, 'Start Date', cell_text_format1)
        worksheet.write(5, 4, self.start_date.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(5, 6, 'End Date', cell_text_format1)
        worksheet.write(5, 7, self.end_date.strftime("%d/%m/%Y"), cell_text_format)

        worksheet.merge_range('A9:A10', 'Move Name', cell_text_format1)
        worksheet.merge_range('B9:B10', 'Date', cell_text_format1)
        worksheet.merge_range('C9:C10', 'Reference', cell_text_format1)
        worksheet.merge_range('D9:D10', 'Account', cell_text_format1)
        worksheet.merge_range('E9:E10', 'Partner', cell_text_format1)
        worksheet.merge_range('F9:F10', 'Branch', cell_text_format1)
        worksheet.merge_range('G9:G10', 'Analytic Account', cell_text_format1)
        worksheet.merge_range('H9:H10', 'Debit', cell_text_format1)
        worksheet.merge_range('I9:I10', 'Credit', cell_text_format1)
        worksheet.merge_range('J9:J10', 'Status', cell_text_format1)

        row = 11
        if self.account_id:
            self._cr.execute("""SELECT  move_id.name, aml.date, aml.ref, account_id.code, account_id.name, partner_id.name, branch_id.name,analytic_account_id.name, aml.debit, aml.credit, aml.parent_state
                    FROM  account_move_line aml 
                    LEFT JOIN account_account account_id ON aml.account_id = account_id.id 
                    LEFT JOIN res_partner partner_id ON aml.partner_id = partner_id.id 
                    LEFT JOIN account_analytic_account analytic_account_id ON aml.analytic_account_id = analytic_account_id.id 
                    LEFT JOIN account_move move_id ON aml.move_id = move_id.id 
                    LEFT JOIN res_branch branch_id ON aml.branch_id = branch_id.id
                    WHERE aml.parent_state='posted' AND aml.date >= %s AND aml.date<= %s AND account_id=%s order by aml.date""", (str(self.start_date), str(self.end_date), self.account_id.id))
        else:
            self._cr.execute("""SELECT move_id.name, aml.date, aml.ref, account_id.code, account_id.name, partner_id.name, branch_id.name,analytic_account_id.name, aml.debit, aml.credit, aml.parent_state
                    FROM  account_move_line aml 
                    LEFT JOIN account_account account_id ON aml.account_id = account_id.id 
                    LEFT JOIN res_partner partner_id ON aml.partner_id = partner_id.id 
                    LEFT JOIN account_analytic_account analytic_account_id ON aml.analytic_account_id = analytic_account_id.id 
                    LEFT JOIN account_move move_id ON aml.move_id = move_id.id 
                    LEFT JOIN res_branch branch_id ON aml.branch_id = branch_id.id
                    WHERE aml.parent_state='posted' AND aml.date >= %s AND aml.date<= %s order by aml.date""", (str(self.start_date), str(self.end_date)))
        entries = self._cr.fetchall()
        credit_total = 0
        debit_total = 0
        for rec in entries:
            worksheet.write(row, 0, rec[0], cell_text_format)
            worksheet.write(row, 1, rec[1].strftime("%d/%m/%Y"), cell_text_format)
            worksheet.write(row, 2, rec[2], cell_text_format)
            worksheet.write(row, 3, rec[3] + '-' + rec[4], cell_text_format)
            worksheet.write(row, 4, rec[5], cell_text_format)
            worksheet.write(row, 5, rec[6], cell_text_format)
            worksheet.write(row, 6, rec[7], cell_text_format)
            worksheet.write(row, 7, "%.3f" % rec[8], cell_text_amount_format)
            worksheet.write(row, 8, "%.3f" % rec[9], cell_text_amount_format)
            worksheet.write(row, 9, 'Posted' if rec[10] == 'posted' else '', cell_text_format)
            debit_total += rec[8]
            credit_total += rec[9]
            row += 1
        worksheet.write(row + 1, 6, "Total", cell_text_format1)
        worksheet.write(row + 1, 7, "%.3f" % debit_total,
                        cell_text_amount_format_bold)
        worksheet.write(row + 1, 8, "%.3f" % credit_total,
                        cell_text_amount_format_bold)

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Journal Entries Report.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
                   % (self._name, self.id, file_name),
        }
