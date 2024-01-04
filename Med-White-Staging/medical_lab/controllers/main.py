from odoo import http
from odoo.http import request
from odoo.http import content_disposition


class Report(http.Controller):

    @http.route('/lab/<idx>', type='http', auth='public')
    def get_qr_idx(self, idx=None, **kw):
        if not idx:
            return 'No idx'
        order = request.env['medical.order'].sudo().search([('id', '=', int(idx))])
        data = {
            'docs': order.sudo(),
            'model': 'medical.order',
            'doc_ids': order.ids
        }
        if not order:
            return 'Appointment Not Found.'
        pdf, _ = request.env.ref('medical_lab.action_report_appointment_all_labtest').sudo().render_qweb_pdf(
            res_ids=order.ids, data=data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', "inline; file_name="+content_disposition(str('Appointment') + '.pdf'))
        return response
