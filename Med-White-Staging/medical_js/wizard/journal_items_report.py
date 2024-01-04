from odoo import fields, models, _
import base64
import io
import xlsxwriter

from odoo.exceptions import UserError


class JournalEntriesWiz(models.TransientModel):
    _name = 'journal.items.report.wizard'
    _description = 'Journal Items Report'

    filename = fields.Binary()
    start_date = fields.Date(default=fields.Date.context_today, string='Start Date')
    end_date = fields.Date(default=fields.Date.context_today, string='End Date')
    account_id = fields.Many2one('account.account', string='Account')

    def action_xlsx_journal_item_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('%s' % 'Journal Entries Report.xlsx')
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_amount_format = workbook.add_format({'align': 'right', 'font_size': 11})
        cell_text_amount_format_bold = workbook.add_format({'align': 'right', 'bold': True, 'font_size': 11})
        cell_text_format1 = workbook.add_format(
            {'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})

        account_query = ''
        if self.account_id:
            account_query = """ AND "aml".account_id = %s""" % (str(self.account_id.id))

        self._cr.execute("""SELECT move_name,aml.date as date,aml.ref as ref,coa.code as acc_code,coa.name as acc_name,pnr.name as partner,brn.name as branch,anl.name as analytic_account,debit,credit,parent_state,pnr.phone as phone
                            from account_move_line aml
                            LEFT JOIN account_account coa on coa.id = aml.account_id
                            LEFT JOIN res_branch brn on brn.id = aml.branch_id 
                            LEFT JOIN account_analytic_account anl on anl.id = aml.analytic_account_id
                            LEFT JOIN account_move move_id on move_id.id = aml.move_id
                            LEFT JOIN res_partner pnr on pnr.id = move_id.partner_id
                            WHERE aml.parent_state = 'posted' 
                            AND aml.date >= %s AND aml.date<= %s
                            """ + account_query + """
                            AND aml.company_id = %s 
                            ORDER BY aml.date ASC""",
                         (str(self.start_date), str(self.end_date), self.env.user.company_id.id))
        entries = self._cr.fetchall()
        if not entries:
            raise UserError(_("No records Found!!!"))

        worksheet.write(5, 1, 'Start Date', cell_text_format1)
        worksheet.write(5, 2, self.start_date.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(6, 1, 'End Date', cell_text_format1)
        worksheet.write(6, 2, self.end_date.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 13)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 16)
        worksheet.set_column('E:E', 47)
        worksheet.set_column('F:F', 42)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 18)
        worksheet.set_column('J:J', 18)
        worksheet.set_column('K:K', 18)

        worksheet.merge_range('A9:A10', 'Move Name', cell_text_format1)
        worksheet.merge_range('B9:B10', 'Date', cell_text_format1)
        worksheet.merge_range('C9:C10', 'Reference', cell_text_format1)
        worksheet.merge_range('D9:D10', 'Account Code', cell_text_format1)
        worksheet.merge_range('E9:E10', 'Account Name', cell_text_format1)
        worksheet.merge_range('F9:F10', 'Partner', cell_text_format1)
        worksheet.merge_range('G9:G10', 'Branch', cell_text_format1)
        worksheet.merge_range('H9:H10', 'Analytic Account', cell_text_format1)
        worksheet.merge_range('I9:I10', 'Debit', cell_text_format1)
        worksheet.merge_range('J9:J10', 'Credit', cell_text_format1)
        worksheet.merge_range('K9:K10', 'Status', cell_text_format1)

        row = 11
        credit_total = 0
        debit_total = 0
        for rec in entries:
            worksheet.write(row, 0, rec[0], cell_text_format)
            worksheet.write(row, 1, rec[1].strftime("%d/%m/%Y"), cell_text_format)
            worksheet.write(row, 2, rec[2], cell_text_format)
            worksheet.write(row, 3, rec[3], cell_text_format)
            worksheet.write(row, 4, rec[4], cell_text_format)
            worksheet.write(row, 5, rec[5], cell_text_format)
            worksheet.write(row, 6, rec[6], cell_text_format)
            worksheet.write(row, 7, rec[7], cell_text_format)
            worksheet.write(row, 8, "%.3f" % rec[8], cell_text_amount_format)
            worksheet.write(row, 9, "%.3f" % rec[9], cell_text_amount_format)
            worksheet.write(row, 10, 'Posted' if rec[10] == 'posted' else '', cell_text_format)
            debit_total += rec[8]
            credit_total += rec[9]
            row += 1
        worksheet.write(row + 1, 7, "Total", cell_text_format1)
        worksheet.write(row + 1, 8, "%.3f" % debit_total,
                        cell_text_amount_format_bold)
        worksheet.write(row + 1, 9, "%.3f" % credit_total,
                        cell_text_amount_format_bold)

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Journal Items Report.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
                   % (self._name, self.id, file_name),
        }

    def action_xlsx_customer_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('%s' % 'Journal Entries Report.xlsx')
        cell_text_format = workbook.add_format({'align': 'center', 'font_size': 12})
        cell_text_format1 = workbook.add_format(
            {'align': 'center', 'border': 1, 'border_color': '#bfbfbf', 'bold': True, 'font_size': 13})

        self._cr.execute("""SELECT pnr.name as partner, pnr.phone as phone, am.name as name, brn.name as branch
                                from account_move am
                                LEFT JOIN res_branch brn on brn.id = am.branch_id 
                                LEFT JOIN res_partner pnr on pnr.id = am.partner_id
                                WHERE am.state = 'posted' 
                                AND am.date >= %s AND am.date<= %s
                                AND am.company_id = %s 
                                AND am.type = 'out_invoice' 
                                ORDER BY pnr.name ASC""",
                         (str(self.start_date), str(self.end_date), self.env.user.company_id.id))
        entries = self._cr.fetchall()
        if not entries:
            raise UserError(_("No records Found!!!"))

        worksheet.write(5, 1, 'Start Date', cell_text_format1)
        worksheet.write(5, 2, self.start_date.strftime("%d/%m/%Y"), cell_text_format)
        worksheet.write(6, 1, 'End Date', cell_text_format1)
        worksheet.write(6, 2, self.end_date.strftime("%d/%m/%Y"), cell_text_format)

        worksheet.set_column('A:A', 40)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 19)

        worksheet.merge_range('A9:A10', 'Partner', cell_text_format1)
        worksheet.merge_range('B9:B10', 'Phone', cell_text_format1)
        worksheet.merge_range('C9:C10', 'Invoice Name', cell_text_format1)
        worksheet.merge_range('D9:D10', 'Branch', cell_text_format1)

        row = 11
        for rec in entries:
            worksheet.write(row, 0, rec[0], cell_text_format)
            worksheet.write(row, 1, rec[1], cell_text_format)
            worksheet.write(row, 2, rec[2], cell_text_format)
            worksheet.write(row, 3, rec[3], cell_text_format)
            row += 1

        workbook.close()
        file_base = base64.b64encode(output.getvalue())
        output.close()

        self.filename = file_base
        file_name = 'Customers Invoice Report.xlsx'
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s?download=true'
                   % (self._name, self.id, file_name),
        }
