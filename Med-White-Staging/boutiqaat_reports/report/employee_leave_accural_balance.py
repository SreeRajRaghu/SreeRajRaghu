# -*- coding: utf-8 -*-

from odoo import api, models


class EmployeeAccuralBalance(models.AbstractModel):
    _name = 'report.boutiqaat_reports.report_employee_leave_accural_balance'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        employee_data = data.get('employee_data')
        employee_data.update({'date': data['form'].get('date', '')})
        combined_data = {
            'date': data['form'].get('date', ''),
            'employee_data': employee_data
        }
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'employee_data': employee_data,
            'combined_data': combined_data,
        }

# class allEmployeeAccuralBalance(models.AbstractModel):
#     _name = 'report.boutiqaat_reports.report_employee_leave_accural_balance'

#     @api.model
#     def _get_report_values(self, docids, data=None):
#         model = self.env.context.get('active_model')
#         docs = self.env[model].browse(self.env.context.get('active_id'))
#         employee_data = data.get('employee_data')
#         combined_data = {
#             'date': data['form'].get('date', ''),
#             'employee_data': employee_data
#         }
#         return {
#             'doc_ids': docids,
#             'doc_model': model,
#             'data': data,
#             'docs': docs,
#             'combined_data': combined_data,
#         }
