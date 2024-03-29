# -*- coding: utf-8 -*-

from odoo import models


class AccountTaxReport(models.TransientModel):
    _inherit = "account.common.report"
    _name = 'account.tax.report'
    _description = 'Tax Report'

    def _print_report(self, data):
        return self.env.ref('accounting_pdf_reports.action_report_account_tax').with_context(company_id=self.company_id.id).report_action(self, data=data)
