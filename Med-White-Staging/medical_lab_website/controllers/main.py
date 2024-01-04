from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv.expression import OR
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        pid = request.env.user.partner_id.id
        def_domain = [('resource_id.partner_id', '=', pid)]

        LabTest = request.env['medical.lab.test'].sudo()
        lab_test_total = LabTest.search_count(
            def_domain + [('state', '!=', 'cancelled')])
        lab_test_executed = LabTest.search_count(
            def_domain + [('state', 'in', ['handover'])])
        lab_test_in_progress = LabTest.search_count(
            def_domain + [('state', 'in', ['draft', 'inprogress'])])
        lab_test_completed = LabTest.search_count(
            def_domain + [('state', '=', 'completed')])

        lab_test_not_attended = request.env['medical.order'].sudo().search_count([
            ('medical_lab_test_ids', '=', False),
            ('state', '!=', 'cancel'),
            ('resource_id.partner_id', '=', pid)
        ])

        # ['draft','inprogress']
        values.update({
            'lab_test_total': lab_test_total,
            'lab_test_executed': lab_test_executed,
            'lab_test_in_progress': lab_test_in_progress,
            'lab_test_completed': lab_test_completed,
            'lab_test_not_attended': lab_test_not_attended,
        })
        return values

    def _get_mandatory_billing_fields(self):
        return ["name", "email", "phone"]

    def _get_mandatory_shipping_fields(self):
        return ["name", "city", "country_id"]

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "street", "city", "country_id"]

    @http.route(['/medical/lab/create'], type='json', auth="user", website=True)
    def lab_test_create(self, **kw):
        order = kw.get('order_vals')

        open_session = request.env['medical.session'].sudo().search([
            ('state', '=', 'opened'),
            ('config_id.is_online_reception', '=', True),
            ('company_id.company_code', '=', 'lab')], limit=1)

        if not open_session:
            raise UserError(_('Contact Admin: Online Reception session is not started.'))

        patient = Partner = request.env['res.partner'].sudo()

        if order.get('civil_id'):
            patient = Partner.sudo().search(
                [('civil_code', '=', order.get('civil_id'))], limit=1)

        if not patient:
            patient = Partner.sudo().create({
                'civil_code': order.get('civil_id'),
                'mobile': order.get('mobile'),
                'phone': order.get('phone'),
                'name': order.get('partner_name'),
                'gender': order.get('gender'),
             })

        doctor = request.env.user.sudo().partner_id
        if not doctor.sudo().medical_resource_ids:
            resource = request.env['medical.resource'].sudo().create({
                'name': doctor.sudo().name,
                'resource_type': 'free',
                'partner_id': doctor.id,
            })
        else:
            resource = doctor.sudo().medical_resource_ids[0]

        orderlines = []
        for prod_id in order.get('orderlines') or []:
            try:
                prod = request.env['product.product'].sudo().browse(int(prod_id))
                price = prod.price or prod.lst_price
                orderlines.append((0, 0, {
                    'product_id': prod.id,
                    'name': prod.display_name,
                    'qty': 1,
                    'product_uom_id': prod.uom_id.id,
                    'price_unit': price,
                }))
            except:
                pass

        vals = {
            'partner_id': patient.id,
            'line_ids': orderlines,
            'resource_id': resource.id,
            'session_id': open_session.id,
            'clinic_id': open_session.config_id.clinic_id.id,
            'note': order.get('app_notes'),
        }
        medical_order = request.env['medical.order'].sudo().create(vals)
        return {
            'appointment': medical_order.id
        }

    @http.route(['/book_appointment'], type='http', auth="user", website=True)
    def book_appointment(self, **kw):
        all_categories = request.env['product.category'].sudo().search([('publish', '=', True)])
        products = request.env['product.product'].sudo().search([('sale_ok', '=', True), ('categ_id.publish', '=', True)])
        return request.render('medical_lab_website.book_appointment', {
                'sale_ok_products': products,
                'all_categories': all_categories,
            })

    @http.route(['/my/appointment', '/my/appointment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_appointment(self, page=1, date_begin=None, date_end=None, sortby=None, not_attended=None, search=None, search_in=None, **kw):

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Appointment = request.env['medical.order'].sudo()
        domain = [('resource_id.partner_id', '=', partner.id)]

        if not_attended:
            domain += [('medical_lab_test_ids', '=', False)]

        searchbar_sortings = {
            'recent': {'label': _('Recent Appointment'), 'order': 'start_time desc'},
            'patient': {'label': _('Patient'), 'order': 'partner_id'},
            'state': {'label': _('Stage'), 'order': 'state'},
        }

        searchbar_inputs = {
            'content': {
                'input': 'content',
                'label': _('Search <span class="nolabel"> (in Content)</span>'),
                'domain': ['|', ('name', 'ilike', search), ('partner_id.name', 'ilike', search)]},
            'name': {
                'input': 'name',
                'label': _('Search in Name'),
                'domain': [('partner_id.name', 'ilike', search)]
            },
            'civil_id': {
                'input': 'civil_id', 'label':
                _('Search in Civil ID'), 'domain':
                [('partner_id.civil_code', 'ilike', search)]},
            'mobile': {
                'input': 'mobile',
                'label': _('Search Mobile'),
                'domain': ['|', ('partner_id.mobile', 'ilike', search), ('partner_id.phone', 'ilike', search)]},
        }

        # default sortby order
        sortby = sortby or 'recent'
        search_in = search_in or 'content'
        if search:
            if search_in == 'content':
                domain += ['|', ('name', 'ilike', search), ('partner_id.name', 'ilike', search)]
            domain += searchbar_inputs.get(search_in, {}).get('domain') or []

        order = searchbar_sortings.get(sortby, {}).get('order') or 'start_time desc'

        # count for pager
        request_count = Appointment.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/appointment",
            url_args={'date_begin': date_begin,
                      'date_end': date_end, 'sortby': sortby},
            total=request_count,
            page=page,
            step=self._items_per_page
        )
        appointments = Appointment.search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'requests': appointments.sudo(),
            'page_name': 'appointment',
            'pager': pager,
            'archive_groups': False,
            'default_url': '/my/appointment',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render("medical_lab_website.portal_my_appointment", values)

    @http.route(['/my/lab/test/<string:req_type>', '/my/lab/test/<string:req_type>/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_labtest(self, page=1, req_type=None, date_begin=None, date_end=None, sortby=None, search=None, search_in=None, **kw):

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        LabTest = request.env['medical.lab.test'].sudo()
        domain = [('resource_id.partner_id', '=', partner.id)]

        searchbar_sortings = {
            'recent': {'label': _('Recent Test'), 'order': 'date_requested desc'},
            'patient': {'label': _('Patient'), 'order': 'partner_id'},
            'state': {'label': _('Stage'), 'order': 'state'},
        }

        searchbar_inputs = {
            'content': {
                'input': 'content',
                'label': _('Search <span class="nolabel"> (in Content)</span>'),
                'domain': ['|', ('name', 'ilike', search), ('partner_id.name', 'ilike', search)]},
            'name': {
                'input': 'name',
                'label': _('Search in Name'),
                'domain': [('partner_id.name', 'ilike', search)]
            },
            'civil_id': {
                'input': 'civil_id', 'label':
                _('Search in Civil ID'), 'domain':
                [('partner_id.civil_code', 'ilike', search)]},
            'mobile': {
                'input': 'mobile',
                'label': _('Search Mobile'),
                'domain': ['|', ('partner_id.mobile', 'ilike', search), ('partner_id.phone', 'ilike', search)]},
        }

        req_type = req_type or 'total'
        search_domain = []
        if req_type == 'total':
            search_domain = OR([search_domain, [('state', '!=', 'cancelled')]])
        if req_type == 'executed':
            search_domain = OR([search_domain, [('state', 'in', ['handover'])]])
        if req_type == 'progress':
            search_domain = OR([search_domain, [('state', 'in', ['draft', 'inprogress'])]])
        if req_type == 'completed':
            search_domain = OR([search_domain, [('state', 'in', ['completed'])]])
        domain += search_domain

        # default sortby order
        sortby = sortby or 'recent'
        search_in = search_in or 'content'
        if search:
            if search_in == 'content':
                domain += ['|', ('name', 'ilike', search), ('partner_id.name', 'ilike', search)]
            domain += searchbar_inputs.get(search_in, {}).get('domain') or []

        order = searchbar_sortings.get(sortby, {}).get('order') or 'date_requested desc'

        request_count = LabTest.search_count(domain)

        # count for pager
        pager = portal_pager(
            url="/my/lab/test/%s" % (req_type),
            url_args={'date_begin': date_begin,
                      'date_end': date_end, 'sortby': sortby},
            total=request_count,
            page=page,
            step=self._items_per_page
        )
        lab_tests = LabTest.search(
            domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'date': date_begin,
            'requests': lab_tests.sudo(),
            'page_name': 'appointment',
            'pager': pager,
            'archive_groups': False,
            'default_url': '/my/lab/test/',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
            'type': req_type,
        })
        return request.render("medical_lab_website.portal_my_lab_test", values)

    @http.route(['/appointment/details/<model("medical.order"):order_id>'], type='http', auth="user", website=True)
    def portal_appointment_details(self, order_id=None, **kw):
        order = order_id.sudo()
        Attachment = request.env['ir.attachment'].sudo()
        attachments = Attachment.search([
            ('res_id', '=', order.id),
            ('res_model', '=', 'medical.order'),
        ])
        attachments |= Attachment.search([
            ('res_id', 'in', order.medical_lab_test_ids.ids),
            ('res_model', '=', 'medical.lab.test'),
        ])
        values = {
            'appointment': order,
            'page_name': 'appointment',
            'attachments': attachments,
        }
        return request.render("medical_lab_website.portal_appointment_details", values)

    @http.route(['/appointment/new'], type='http', auth="user", website=True)
    def portal_appointment_new(self, order_id=None, **kw):
        values = {'page_name': 'appointment_new', }
        return request.render("medical_lab_website.portal_appointment_new", values)

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env['account.move']

        domain = [
            ('type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')),
            ('partner_id', '=', request.env.user.partner_id.id),
        ]

        searchbar_sortings = {
            'date': {'label': _('Invoice Date'), 'order': 'invoice_date desc'},
            'duedate': {'label': _('Due Date'), 'order': 'invoice_date_due desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('account.move', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        invoice_count = AccountInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        invoices = AccountInvoice.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_invoices_history'] = invoices.ids[:100]

        values.update({
            'date': date_begin,
            'invoices': invoices,
            'page_name': 'invoice',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/invoices',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("account.portal_my_invoices", values)
