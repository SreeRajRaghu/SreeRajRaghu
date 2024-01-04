
from odoo import api, models


class ReportResourceDetails(models.AbstractModel):
    _name = 'report.medical_pcr.pcr_qr_custom_report'
    _description = "Report PCR QR"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        if not data.get('docs'):
            orders = self.env['medical.order'].sudo().browse(docids)
            data.update({
                'docs': orders,
                'model': 'medical.order',
            })
        return data


class VaccineDetails(models.AbstractModel):
    _name = 'report.medical_pcr.vaccine_certificate'
    _description = "Report Vaccine Certi"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        if not data.get('docs'):
            orders = self.env['medical.order'].sudo().browse(docids)
            data.update({
                'docs': orders,
                'model': 'medical.order',
            })
        return data


class PCRCerti(models.AbstractModel):
    _name = 'report.medical_pcr.appointment_pcr_certificate'
    _description = "Report Vaccine Certi"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        if not data.get('docs'):
            orders = self.env['medical.order'].sudo().browse(docids)
            data.update({
                'docs': orders,
                'model': 'medical.order',
            })
        return data
