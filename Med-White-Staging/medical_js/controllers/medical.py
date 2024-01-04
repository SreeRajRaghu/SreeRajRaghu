from odoo import http, fields
from odoo.http import request
from odoo.tools.misc import flatten

import json
import logging

# from datetime import date
# from dateutil.relativedelta import relativedelta
# from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import content_disposition
# from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

# ORDER_FIELDS = [
#     "name", "start_time", "end_time", "state", "note",
#     "create_uid", "resource_id", "partner_id", "has_priority",
#     "pos_reference", "reminder_ids", "user_id", "invoice_note", "is_followup",
#     "amount_total", "handover_file_on", "printed_file_on", "optometrist_on", "reception_note", "sequence_no"]

# ORDER_LINE_FIELDS = [
#     "consumable_ids", "discount", "display_name", "duration", "is_medical_service",
#     "name", "price_subtotal", "price_subtotal_incl", "price_unit", "product_id",
#     "qty", "related_pkg_id", "session_count", "is_variant_price"]

ORDER_MIN_FIELDS = [
    'name', "start_time", "end_time", "state",
    "resource_id", "partner_id", "clinic_id", "discount", "passport_no",
    "invoice_note", "note", "file_no", "file_no2", "visit_type", "visit_opt_id", "config_id", "is_multi_order", "invoice_number", "invoice_state"
]

ORDER_FIELDS = [
    "name", "start_time", "end_time", "state", "note", "payment_ids", "is_multi_order", 'pricelist_id',
    "create_uid", "resource_id", "partner_id", "user_id", "clinic_id", "disc_reason_id",
    "invoice_note", "ui_reference", "is_readonly", "invoice_number", "file_no", "file_no2",
    "discount", "net_total", "amount_due", "amount_paid", "insurance_card_id", "sequence_no", "visit_type", "visit_opt_id",
    "patient_invoice_id", "insurance_invoice_id", "invoice_state", "ins_approval_no", "ins_ticket_no", "ins_ref", "ins_member",
    "date_confirm", "date_arrived", "duration_in_arrived", 'date_in', 'date_out', 'date_done', 'duration_out_in']

ORDER_LINE_FIELDS = [
    'order_id', 'product_id', 'qty', 'product_uom_id', 'consumable_ids',
    'subtotal', 'subtotal_wo_disc', 'duration',
    'start_time', 'note', 'discount_fixed', 'employee_id', 'multi_resource_id', 'multi_start_time',

    'price_unit_orig', 'price_unit', 'approved_price_unit', 'payable_price_unit', 'ins_price_unit',
    'is_insurance_applicable', 'pricelist_item_id', 'patient_share', 'patient_share_limit',
    'insurance_disc', 'apply_ins_disc',
    'amount_paid',
    "discount", "display_name", "duration", "session_count", "analytic_tag_ids", "analytic_account_id"]

PARTNER_FIELDS = [
    "name", "phone", "mobile", "gender", "marital", "file_no", "file_no2", "civil_code", 'passport_no', 'passport_name',
    "real_balance", "credit_limit", "total_due", "utm_source_id", "utm_medium_id", "area_id", "nationality_id"]

ADDRESS_FIELDS = ['street', 'street2', 'city', 'state_id', 'country_id', 'zip']
REMINDER_FIELDS = ['name', 'todo_date', 'description', 'state']
JS_PARTNER_FIELDS = [
    'name', 'ar_name', 'type', 'phone', 'mobile', 'email', 'street', 'street2', 'city', 'state_id', 'country_id',
    'birthday', 'file_no', "file_no2", 'passport_no', 'marital', 'person_status', 'comment', 'diagnosis_summary', 'gender',
    'child_ids', 'property_product_pricelist',
    'civil_code', 'parent_id', 'is_insurance_company', 'ins_running_card_ids', 'history', 'utm_source_id', 'utm_medium_id',
    'person_status', 'medical_attachment_ids', 'blocked_doctor_ids', 'app_no_show_count', 'app_cancelled_count', 'credit', 'total_due',
    'area', 'block', 'avenue', 'house', 'floor', 'apartment_no', 'blood_group', 'work_phone',
    'civil_id_issued', 'civil_id_expiry', 'civil_sponser', 'civil_paci_no',
    'area_kw_moh_code', 'governorate', 'street2', 'residence', "area_id", "nationality_id", 'passport_name'
]


def findWhere(data_list, k, v):
    for line in data_list:
        if line.get(k) and line[k] == v:
            return line
    return {}

ORDER_LINE_FIELDS += ['medical_lab_test_ids', 'lab_test_status']
ORDER_FIELDS += ['medical_lab_test_ids']


class MedicalController(http.Controller):
    @http.route('/medical/appointments', type='json', auth='user')
    def get_events(
            self, from_dtime, to_dtime, tz=None, partner_fields=None,
            branch_id=None, config_id=None, **kw):
        MedicalOrder = request.env['medical.order']
        search_condition = ''
        if branch_id:
            search_condition = " AND clinic_id = %s" % (int(branch_id))

        if config_id:
            sql = """
                SELECT 1
                FROM medical_config
                WHERE id = %s AND service_appointment_only = %s LIMIT 1
            """
            request.env.cr.execute(sql, (config_id, True))
            result = request.env.cr.fetchone()
            if result and result[0]:
                search_condition += " AND is_direct_sale = %s" % (False)

        sql = """
            SELECT id, id AS server_id
            FROM medical_order
            WHERE (start_time, end_time) OVERLAPS (%s, %s) AND state != 'cancel'
        """ + search_condition + " ORDER BY start_time DESC"
        request.env.cr.execute(sql, (from_dtime, to_dtime))
        orders = MedicalOrder.search([('id', 'in', flatten(request.env.cr.fetchall()))])
        partners = orders.mapped('partner_id').read(partner_fields or PARTNER_FIELDS)
        orders_data = orders.read(fields=ORDER_MIN_FIELDS + ['is_first', 'employee_id'])

        for order in orders:
            # order = orders.filtered(lambda o: o.id == order_dict['id'])
            order_dict = findWhere(orders_data, 'id', order.id)
            order_dict['order_lines'] = order.line_ids.filtered(
                lambda l: l.amount_paid >= 0).read(['product_id', 'qty', 'duration', 'multi_resource_id', 'multi_start_time'])
        _logger.info("__________ Get Appointments : BRANCH: %s Total: %s || %s - %s", branch_id, len(orders), from_dtime, to_dtime)
        return {
            'orders': orders_data,
            'partners': partners
        }

    @http.route('/event', type="json", auth='user')
    def get_event_details(self, order_id):
        order = request.env['medical.order'].sudo().browse(int(order_id))

        lines = []
        for line in order.line_ids.filtered(lambda l: l.amount_paid >= 0):
            line_data = line.read(ORDER_LINE_FIELDS)[0]
            line_data.update({
                "product": line.product_id.read(['name', 'list_price', 'standard_price', 'categ_id', 'default_code', 'barcode'])[0],
                "line_id": line.id,
            })
            lines.append(line_data)
        order_data = order.read(ORDER_FIELDS)[0]

        insurance_data = {}
        if order.insurance_card_id:
            insurance_data = order.insurance_card_id.read([
                'name', 'main_company_id', 'insurance_company_id', 'pricelist_id'])[0]

        order_data.update({
            "server_id": order.id,
            "order_lines": lines,
            "partner": order.partner_id.read(PARTNER_FIELDS)[0],
            "prev_appointment_date": order.last_order_id.start_time,
            "paymentlines": order.get_payment_details(),
            'insurance_data': insurance_data,
            # "invoice_id": order.patient_invoice_id.id,
            # "start_time": _convert_tz(order.start_time),
            "end_time": order.end_time or order.start_time,
            # "reminders": reminders,
            "complains": order.complain_ids and order.complain_ids.read() or [],
            "lab_reports": order.medical_lab_test_ids and order.medical_lab_test_ids.read([
                'name', 'state', 'employee_id', 'lab_department_id', 'test_type_id']) or [],
        })
        return order_data

    @http.route('/event/invoice', type="json", auth='user')
    def get_event_invoice(self, order_id=False, invoice_id=False):
        # timezone = request.env.user.partner_id.tz
        # lang = request.env.user.partner_id.lang or 'en_US'
        return request.env['medical.order'].get_invoice_data(order_id, invoice_id)

    @http.route('/event/reset', type="json", auth='user')
    def set_event_reset(self, order_id=False):
        # timezone = request.env.user.partner_id.tz
        # lang = request.env.user.partner_id.lang or 'en_US'
        order = request.env['medical.order'].sudo().browse([int(order_id)])
        order.action_cancel()
        order.action_reset()
        return self.get_event_details(order_id=order_id)

    # Supporting Features
    @http.route('/partner/events', type="json", auth='user')
    def partner_events(self, partner_id=None, **kw):
        orders_data = []
        orders = request.env['medical.order'].search([('partner_id', '=', partner_id)], order="start_time desc")

        for order in orders:
            app_data = {
                'id': order.id,
                'partner_id': order.partner_id.name,
                'start_time': order.start_time,
                'state': order.state,
                'resource_id': order.resource_id.name,
                'clinic_name': order.clinic_id.name or '',
                'lines': [{
                    'id': l.id,
                    'product_id': l.name or l.product_id.display_name,
                    'employee': l.employee_id.name or '',
                    'qty': l.qty,
                    'price_unit': l.payable_price_unit,
                    'discount': l.discount,
                    'price_subtotal_incl': l.subtotal} for l in order.line_ids],
                'consumables': [],
                'statement_ids': [{'id': s.id, 'journal_id': s.journal_id.name, 'amount': s.amount} for s in order.payment_ids],
                # 'history_ids': [
                #     {
                #         'id': h.id,
                #         'state': h.state,
                #         'modification_user_id': h.modification_user_id.name,
                #         'modification_dt': h.modification_time
                #     } for h in order.state_history_ids
                # ],
                'refunds': [],
                'pos_reference': order.ui_reference,
                'name': order.name,
                'invoice': {},
            }

            if order.patient_invoice_id:
                inv_data = order.patient_invoice_id.read([
                    'name', 'amount_total', 'amount_residual'])[0]
                app_data.update({
                    'invoice': inv_data
                })

            orders_data.append(app_data)
        return orders_data

    @http.route('/medical/consumables', type="json", auth='user')
    def get_consumables(self, medical_line_id=None, **kw):
        products_data = []
        logging.info("__ Consumables for : %s", medical_line_id)
        if medical_line_id:
            medical_line = request.env['medical.order.line'].sudo().browse(medical_line_id)
            if not medical_line:
                logging.info("Consumables: 404: No Line")
                return []
            products_data = medical_line.get_consumable_stock(medical_line)
        return products_data

    @http.route('/partner/packages', type="json", auth='user')
    def get_packages(self, partner_id=None, **kw):
        sql = """
            SELECT id, name, name, duration, state, partner_id, invoice_id,
        session_total, session_done, session_remaining, session_price,
        product_id
        FROM customer_package
        WHERE partner_id = %s AND state = 'running' AND session_remaining > 0
        """ % (partner_id)
        request.env.cr.execute(sql)
        rows = request.env.cr.dictfetchall()
        return rows

    @http.route('/partner/aging-report', type="json", auth="user")
    def partner_aging(self, partner_id=None, **kw):
        aging_data = {}
        if partner_id:

            AgingReport = request.env['report.account.report_agedpartnerbalance']

            partner = request.env['res.partner'].browse(partner_id)
            aging_data.update({
                'partner_id': partner.id,
                'partner_name': partner.name,
                'partner_credit': partner.credit_limit,
            })
            from_date = fields.Date.to_string(fields.Date.today())
            res, total, lines = AgingReport.with_context(
                    include_nullified_amount=True,
                    partner_ids=partner,
                )._get_partner_move_lines(['payable', 'receivable'], from_date, 'posted', 30)

            for aging in res:
                if aging['partner_id'] == partner_id:
                    for cnt in range(5):
                        aging_data[cnt] = {
                            'total': aging[str(cnt)],
                            'lines': []
                        }
                    aging_data[5] = {
                        'total': aging['direction'],
                        'lines': []
                    }
                    break
            adv_amount = 0
            for ln in lines.get(partner_id, []):
                move_line = ln['line']
                move = move_line.move_id
                aging_data[ln['period'] - 1]['lines'].append({
                    'amount': ln['amount'],
                    'move': move.name,
                    'date': move_line.date,
                    'due_date': move_line.date_maturity,
                    'invoice_id': move.id or '',
                    'medical_order_id': move.medical_order_id.id,
                    'ref': move.ref
                })
                if ln['amount'] < 0:
                    adv_amount += ln['amount']

            aging_data.update({'partner_advance': adv_amount})
        return aging_data

    @http.route('/partner/documents', type="json", auth='user')
    def partner_documents(self, partner_id=None, **kw):
        partner = request.env['res.partner'].sudo().browse(partner_id)
        documents = partner.medical_attachment_ids.read(['id', 'name', 'ir_attachment_id', 'attachment_type_id'])
        return documents

    @http.route('/get/patient_insurance_data', type="json", auth='user')
    def get_patient_insurance_data(self, partner_id=None, **kw):
        data = {
            'insurance': [],
            'insurance_company': [],
            'pricelist': []
        }
        if partner_id:
            data['insurance'] = request.env['insurance.card'].sudo().search_read(
                [('partner_id', '=', partner_id)],
                fields=['id', 'name', 'main_company_id', 'insurance_company_id', 'pricelist_id', 'issue_date', 'expiry_date'])
        data['insurance_company'] = request.env['res.partner'].sudo().search_read(
            [('is_insurance_company', '=', True)],
            fields=['id', 'name', 'pricelist_ids', 'parent_id'])
        data['pricelist'] = request.env['product.pricelist'].sudo().search_read(
            [('insurance_company_id', '!=', False)],
            fields=['id', 'name', 'insurance_company_id'])
        return data


class Report(http.Controller):

    # Refer /point_of_sale/main.py
    # report.point_of_sale.report_saledetails

    @http.route('/medical/report', type='http', auth='user')
    def custom_reports(self, **kw):
        report_tag = json.loads(kw.get('report_tag'))
        report_data = json.loads(kw.get('report_data'))
        filename = report_tag.pop('filename') or "filename"
        report_model = report_tag.pop('report_model')
        report_tag_id = report_tag.pop('report_tag_id')
        r = request.env[report_model]
        pdf, _ = request.env.ref(report_tag_id).with_context(**kw).render_qweb_pdf(r, data=report_data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', content_disposition(filename + '.pdf'))
        response.set_cookie('fileToken', kw.get('token'))
        return response

    @http.route('/medical/report', type='http', auth='user')
    def get_reports(self, report_model, report_tag_id, **kw):
        r = request.env[report_model]
        pdf, _ = request.env.ref(report_tag_id).with_context(**kw).render_qweb_pdf(r)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/medical/report/<int:resource_id>/appointments', type='http', auth='public')
    def get_resource_appointments(self, resource_id, dt, **kw):
        model = request.env['report.medical_js.medical_resource_report_template'].sudo()
        data = {
            'resource_ids': [resource_id],
            'date_start': dt,
            'date_stop': dt
        }
        pdf, _ = request.env.ref('medical_js.appointment_resource_details_report').with_context(**kw).sudo().render_qweb_pdf(model, data=data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        response.headers.add('Content-Disposition', "inline; file_name="+content_disposition('Appointments - ' + str(dt) + '.pdf'))
        return response
