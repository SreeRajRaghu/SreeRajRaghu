# -*- coding: utf-8 -*-

from odoo import models


class ReportEOS(models.AbstractModel):
    _name = 'report.hr_employee_eos.report_hr_eos'
    _description = "Report EOS"

    def _get_report_values(self, docids, data=None):
        if not docids and data.get('ids'):
            docids = data['ids']
        records = self.env['hr.employee'].browse(docids)
        return {
            'doc_ids': records.ids,
            'doc_model': 'hr.employee',
            'docs': records,
        }
