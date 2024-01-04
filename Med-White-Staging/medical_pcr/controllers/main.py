from odoo import http, models
from odoo.addons.medical_js.controllers.medical import MedicalController, ORDER_MIN_FIELDS, ORDER_FIELDS
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo.http import content_disposition

NEW_FIELDS = [
    'handover_file_on', 'pcr_qr_code', 'is_app_pcr', 'is_app_vaccine', 'vaccine_batch_no',
    'pcr_type', 'swab_type', 'swab_location_id',
    'send_sms', 'sms_sent', 'sample_taken_emp_id', 'pcr_test_state']

ORDER_FIELDS += NEW_FIELDS
ORDER_MIN_FIELDS += NEW_FIELDS

PCR_FIELDS = [
    "pcr_appointments_type", 'is_airways_staff', 'is_vaccinated', 'pcr_type', 'quarantine_station_id',
    'airline_number', 'travel_date', 'additional_notes', 'swab_location_id', 'airline_selection_id', 'medical_id',
    'cough', 'fever', 'breath', 'aches', 'throat', 'diarrhea', 'headache', 'nose', 'taste', 'is_traveller_swab', 'is_symptomatic',
    'swab_type', 'passport_no',
    'origin_country_id',
    'has_recent_tranvel', 'recent_travel_country_id',
    'recent_travel_date',
    'in_contact_with_suspected',

    'is_health_worker', 'patient_residence_type', 'patient_work_place', 'patient_department',
    'patient_work_center_name', 'patient_work_region',

    'send_sms', 'sms_sent',
]


class PCRController(MedicalController):

    @http.route('/pcr/order/details', type="json", auth='user')
    def get_pcr_details(self, order_id=None, ui_ref=None, partner_id=False, config_id=False, **kw):
        Order = request.env['medical.order']
        if order_id:
            medical_order = Order.browse(int(order_id))
        if ui_ref:
            medical_order = Order.search([
                '|',
                ('ui_reference', '=', "REF %s" % (ui_ref or '')),
                ('name', '=', ui_ref),
            ], limit=1)
        data = {'is_allowed': True}
        if medical_order.exists():
            pcr_data = medical_order.read(PCR_FIELDS)[0]
            pcr_data.update({
                'in_contact_list': medical_order.in_contact_ids and medical_order.in_contact_ids.read(['name', 'phone']) or []
            })
            data.update({'pcr_data': pcr_data})
        elif partner_id and config_id:
            if not request.env['medical.config'].browse(config_id).sudo().allow_appointment_from_last_pcr(
                    partner_id=partner_id):
                data.update({'is_allowed': False})
        return data


class CustomerPortal(CustomerPortal):

    @http.route('/pcr/order/report/<model("medical.order"):order_id>', type='http', auth="user", website=True, csrf=False)
    def get_pcr_order_report(self, order_id):
        medical_order = request.env['medical.order'].browse(int(order_id))
        values = {'order': medical_order}
        return request.render("medical_pcr.prc_report_portal", values)


class Report(http.Controller):

    @http.route('/qr/<code>', type='http', auth='public')
    def get_qr_code(self, code=None, **kw):
        if not code:
            return 'No Code'
        order = request.env['medical.order'].sudo().search([('pcr_qr_code', '=', code)])
        data = {
            'docs': order,
            'model': 'medical.order',
        }
        if not order:
            return 'Appointment Not Found.'
        pdf, _ = request.env.ref('medical_pcr.action_appointment_pcr_qr').sudo().render_qweb_pdf(order, data=data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', "inline; file_name="+content_disposition(str(code or 'Appointment') + '.pdf'))
        return response

    @http.route('/pcr/<code>', type='http', auth='public')
    def get_pcr_result(self, code=None, **kw):
        if not code:
            return 'No Code'
        order = request.env['medical.order'].sudo().search([('pcr_qr_code', '=', code)], limit=1)
        data = {
            'docs': order.sudo(),
            'model': 'medical.order',
        }
        if not order:
            return 'Appointment Not Found.'
        pdf, _ = request.env.ref('medical_pcr.action_report_pcr_certi_from_appointment').sudo().render_qweb_pdf(order.sudo(), data=data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', "inline; file_name="+content_disposition(str(code or 'Appointment') + '.pdf'))
        return response

    @http.route('/vaccine/<code>', type='http', auth='public')
    def get_vaccine(self, code=None, **kw):
        if not code:
            return 'No Code'
        order = request.env['medical.order'].sudo().search([('id', '=', code)], limit=1)
        data = {
            'docs': order.sudo(),
            'model': 'medical.order',
        }
        if not order:
            return 'Appointment Not Found.'
        pdf, _ = request.env.ref('medical_pcr.action_vaccine_certificate').sudo().render_qweb_pdf(order.sudo(), data=data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', "inline; file_name="+content_disposition(str(code or 'Appointment') + '.pdf'))
        return response

    @http.route('/invoice/<code>', type='http', auth='public')
    def get_invoice(self, code=None, **kw):
        if not code:
            return 'No Code'
        order = request.env['medical.order'].sudo().search([('pcr_qr_code', '=', code)], limit=1)
        invoice = order.patient_invoice_id.sudo()
        if not invoice:
            return '404 : Not Found'
        data = {
            'docs': invoice.id,
            'model': 'account.move',
        }
        # if not order:
        #     return 'Invoice Not Found.'
        pdf, _ = request.env.ref('medical_report.account_patient_invoices').sudo().render_qweb_pdf(invoice.sudo().ids, data=data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', "inline; file_name="+content_disposition(str(code or 'Invoice') + '.pdf'))
        return response
