
from odoo import api, fields, models, _
from odoo.exceptions import UserError
# from odoo.exceptions import UserError
import logging
# from odoo.addons.medical_js.controllers.medical import ORDER_FIELDS
from odoo.addons.medical_pcr.controllers.main import PCR_FIELDS
import qrcode
import base64
from io import BytesIO
from datetime import timedelta

# ORDER_FIELDS += [
#     "pcr_appointments_type", 'is_airways_staff', 'is_vaccinated', 'pcr_type', 'quarantine_station_id', 'airline_selection_id',
#     'airline_number', 'travel_date', 'additional_notes', 'swab_location_id', 'airline_selection_id', 'medical_id',
#     'cough', 'fever', 'breath', 'aches', 'throat', 'diarrhea', 'headache', 'nose', 'taste'
# ]
P_DEPT = [('icu', 'ICU'), ('er', 'ER'), ('ward', 'Medical Ward'), ('or', 'OR'), ('op', 'OP')]


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_app_pcr = fields.Boolean(related="medical_order_id.is_app_pcr", store=True)
    is_app_vaccine = fields.Boolean(related="medical_order_id.is_app_vaccine", store=True)


class MedicalConfig(models.Model):
    _inherit = 'medical.config'

    allow_pcr_test = fields.Boolean("PCR Workflow ?")
    enable_lab_center = fields.Boolean("Is Collection Center ?")

    pcr_center_id_list = fields.Char("Enter at least one ID type")
    calendar_views = fields.Char(default="listDay,listWeek,listMonth")
    calendar_default_view = fields.Char(default="listDay")
    pcr_emp_id = fields.Many2one("hr.employee", string="Employee")

    def allow_appointment_from_last_pcr(self, partner_id, start_time=False, except_ids=False):
        start_time = start_time or fields.Datetime.now()
        except_ids = except_ids or []

        company = self.env.company
        dur_days = company.pcr_test_duration
        if self.company_code == 'pcr' and dur_days > 0:
            last_dt = start_time - timedelta(days=dur_days)
            prev_appointment = self.env['medical.order'].sudo().search([
                ('partner_id', '=', partner_id),
                ('state', 'not in', ['cancel', 'no_show', 'no_answer']),
                ('id', 'not in', except_ids),
                ('is_app_pcr', '=', True),
                ('start_time', '>=', last_dt),
                ('pcr_result', '=', 'positive'),
            ], limit=1)
            if prev_appointment:
                return False
        return True


class MedicalOrder(models.Model):
    _inherit = "medical.order"

    sample_taken_emp_id = fields.Many2one("hr.employee", string="Sampal Taken By")
    # company_code = fields.Selection(related="company_id.company_code")
    pcr_test_ids = fields.One2many("medical.pcr.test", "appointment_id", string="PCR Tests")
    pcr_test_count = fields.Integer("PCR Test Count", compute="_compute_pcr_test_count")
    pcr_test_state = fields.Selection(related="pcr_test_ids.state", store=True)
    sample_taken_date = fields.Datetime(related='pcr_test_ids.date_requested')

    send_sms = fields.Boolean('Send SMS ?')
    sms_sent = fields.Boolean('SMS Sent')

    passport_no = fields.Char(related="partner_id.passport_no")
    pcr_appointments_type = fields.Selection([
        ('arrival', 'Arrival'),
        ('departure', 'Departure')],
        string='Travel', tracking=True)
    is_airways_staff = fields.Boolean(string='Airways Staff', tracking=True)
    is_vaccinated = fields.Boolean(string='Is Vaccinated', tracking=True)
    pcr_type = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow')],
        string='Immune Type', tracking=True)
    swab_type = fields.Selection([
        ('nasal', 'Nasal'), ('salaiva', 'Salaiva')], string="Swab Type", tracking=True)
    is_traveller_swab = fields.Boolean("Is Traveller Swab ?", tracking=True)

    quarantine_station_id = fields.Many2one('quarantine.station', string="Quarantine Station", tracking=True)
    airline_selection_id = fields.Many2one(
        "airline.selection", string="Airline Selection", tracking=True)
    airline_number = fields.Char('Airline Number', tracking=True)
    travel_date = fields.Date(string="Travel Date", tracking=True)
    additional_notes = fields.Text("Notes")
    qr_image = fields.Binary("QR Code", copy=False)
    qr_cert_image = fields.Binary("QR Certificate Img", copy=False, compute="_compute_cert_img")
    qr_result_url_image = fields.Binary("QR Result Img", copy=False, compute="_compute_cert_img")
    pcr_qr_code = fields.Char(string="PCR QR", readonly=True, copy=False, tracking=True)
    swab_location_id = fields.Many2one('swab.location', 'Collection Center', tracking=True)
    medical_id = fields.Char('Medical ID', tracking=True)
    origin_country_id = fields.Many2one("res.country", string="Country of Origin", tracking=True)

    is_symptomatic = fields.Boolean("Is Symptomatic ?", tracking=True)
    cough = fields.Boolean(string='Dry Cough')
    fever = fields.Boolean(string='Fever')
    breath = fields.Boolean(string='Shortness of Breath')
    aches = fields.Boolean(string='Fatigue/Muscle Aches')
    throat = fields.Boolean(string='Sore Throat')
    diarrhea = fields.Boolean(string='Diarrhea')
    headache = fields.Boolean(string='Headache')
    nose = fields.Boolean(string='Runny Nose')
    taste = fields.Boolean(string='Loss of smell/taste')

    has_recent_tranvel = fields.Boolean("Recent Travel History ?", tracking=True)
    recent_travel_country_id = fields.Many2one("res.country", string="Recent Country Arriving From")
    recent_travel_date = fields.Date("Recent Travel Date")

    in_contact_with_suspected = fields.Boolean("Contact of a confirmed / suspected case ?", tracking=True)
    in_contact_ids = fields.One2many("medical.contact.list", "medical_order_id", string="In Contact With")

    is_health_worker = fields.Boolean("Is Health Worker ?", tracking=True)
    patient_residence_type = fields.Selection(
        [('private', 'Private'), ('hostel', 'Nursing Hostel')], string='Patient Residence Type')
    patient_work_place = fields.Selection([('public', 'Public Hospital'), ('phc', 'PHC'), ('private', 'Private Hospital')], string='Place of Work')
    patient_department = fields.Selection(P_DEPT, string="Department")
    patient_work_center_name = fields.Char("Work Center Name")
    patient_work_region = fields.Char("Workplace Health Region")

    pcr_result = fields.Selection([
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('equivocal', 'Equivocal'),
        ('rejected', 'Rejected')], string='PCR Result', copy=False, tracking=True)

    is_pcr_result_user = fields.Boolean("Is PCR Result", compute="_compute_is_pcr_result_user")
    pcr_result_note = fields.Text("PCR Result Note", copy=False, tracking=True)
    pcr_result_date = fields.Datetime("PCR Result Date", copy=False, tracking=True)
    pcr_result_user_id = fields.Many2one("res.users", string="PCR Result Updated By", copy=False, tracking=True)
    next_appointment_id = fields.Many2one("medical.order", string="Next Appointment", copy=False, tracking=True)

    is_app_pcr = fields.Boolean(compute="_compute_is_pcr_app", store=True)
    is_app_vaccine = fields.Boolean(compute="_compute_is_pcr_app", store=True)

    vaccine_batch_no = fields.Char("Vaccine Batch No.", tracking=True)
    vaccine_dose = fields.Selection(related="line_ids.product_id.vaccine_dose")

    def action_create_invoice_wrapper(self):
        self.ensure_one()
        if self.is_traveller_swab and self.is_app_pcr and self.partner_id:
            document_type_ids = self.partner_id.mapped('medical_attachment_ids.attachment_type_id').filtered(lambda t: t.attachment_type == 'passport')
            if not document_type_ids:
                raise UserError(_('Please Upload Passport of the Patient'))
        return super().action_create_invoice_wrapper()

    def send_result_by_sms(self):
        if self.config_id.company_code:
            sms_config = self.env['sms.config'].sudo().search([('company_code','=',self.config_id.company_code)], limit=1)
        else:
            sms_config = self.env['sms.config'].sudo().search([], limit=1)
        if not self.pcr_result:
            return {'error': 'PCR Result Not Defined'}
        msg_template = self.env['sms.sms.template'].sudo().search([('code', '=', self.pcr_result)], limit=1)
        if sms_config and msg_template:
            WSMSConfig = self.env['wizard.sms.send'].sudo()
            sms_vals = {}
            recipients = self.partner_id.phone or self.partner_id.mobile
            if not recipients:
                return {'error': 'Receipient has not contact number.'}
            try:
                test_id = self.pcr_test_ids[0].id
                msg = msg_template.sudo().render([test_id])[test_id]
                sms_vals = {
                    'config_id': sms_config.id,
                    'contact_list': recipients,
                    'keep_sms_history': True,
                    'language': msg_template.language,
                    'message': msg,
                }
                wizard = WSMSConfig.sudo().create(sms_vals)
                logging.info("SMS Result: Sending:  %s - %s \n %s" % (self.name, recipients, sms_vals))
                wizard.sudo().send_sms()
                # self.write({'sms_sent': True})
                self.sudo().message_post(body=msg)
                return {'success': True}
            except Exception as e:
                logging.error("ERROR: Appointment: Send SMS %s - %s \n %s" % (self.name, sms_vals, str(e)))
                return {'error': str(e)}
        return {'error': 'Please configure the SMS Provider'}

    def send_invoice_by_sms(self):
        if self.config_id.company_code:
            sms_config = self.env['sms.config'].sudo().search([('company_code','=',self.config_id.company_code)], limit=1)
        else:
            sms_config = self.env['sms.config'].sudo().search([], limit=1)
        if not self.patient_invoice_id:
            return {'error': 'Appointment not Invoiced.'}
        msg_template = self.env['sms.sms.template'].sudo().search([('code', '=', 'INVOICE')], limit=1)
        if sms_config and msg_template:
            WSMSConfig = self.env['wizard.sms.send'].sudo()
            sms_vals = {}
            recipients = self.partner_id.phone or self.partner_id.mobile
            if not recipients:
                return {'error': 'Receipient has not contact number.'}
            try:
                app_ids = self.ids
                msg = msg_template.sudo().render(app_ids)[app_ids[0]]
                sms_vals = {
                    'config_id': sms_config.id,
                    'contact_list': recipients,
                    'keep_sms_history': True,
                    'language': msg_template.language,
                    'message': msg,
                }
                wizard = WSMSConfig.sudo().create(sms_vals)
                logging.info("SMS Invoice: Sending:  %s - %s \n %s" % (self.name, recipients, sms_vals))
                wizard.sudo().send_sms()
                # self.write({'sms_sent': True})
                self.sudo().message_post(body=msg)
                return {'success': True}
            except Exception as e:
                logging.error("ERROR: Appointment: Send SMS %s - %s \n %s" % (self.name, sms_vals, str(e)))
                return {'error': str(e)}

        return {'error': 'Please configure the SMS Provider'}

    def _compute_pcr_test_count(self):
        for rec in self:
            rec.pcr_test_count = len(rec.pcr_test_ids.ids)

    def _compute_is_pcr_result_user(self):
        is_pcr_result_mgr = self.env.user.has_group('medical_pcr.group_manage_pcr_result')
        for rec in self:
            rec.is_pcr_result_user = is_pcr_result_mgr

    @api.depends('line_ids', 'line_ids.product_id', 'line_ids.product_id.medical_categ_id', 'line_ids.product_id.medical_categ_id.medical_type')
    def _compute_is_pcr_app(self):
        for rec in self:
            lines = rec.line_ids.filtered(lambda l: l.medical_type == 'pcr')
            rec.is_app_pcr = bool(len(lines.ids))

            lines = rec.line_ids.filtered(lambda l: l.medical_type == 'vaccine')
            rec.is_app_vaccine = bool(len(lines.ids))

    @api.constrains('start_time', 'pcr_appointments_type', 'partner_id')
    def check_pcr_appointment(self):
        # if self.check_last_appoitment()
        company = self.env.company
        dur_days = company.pcr_test_duration
        for rec in self.filtered(lambda r: r.is_app_pcr and r.start_time):
            print ("__ rec.config_id : ", rec.config_id.company_code, rec.config_id)
            if rec.config_id.company_code == 'pcr' and not rec.config_id.allow_appointment_from_last_pcr(rec.partner_id.id, rec.start_time, rec.ids):
                raise UserError(_('You cannot book second PCR Appointment before %s days from last Appointment.') % (dur_days))

    # @api.constrains('line_ids.product_id', 'line_id')
    # def check_same_product(self):
    #     company_code = self.env.company.company_code
    #     if company_code == 'pcr':
    #         for rec in self.filtered(lambda r: len(r.line_ids.ids) > 1):
    #             products = rec.line_ids.mapped('product_id')
    #             print ('____ products : ', products, rec.line_ids)
    #             if len(products.ids) != len(rec.line_ids.ids):
    #                 raise UserError(_("Same service in one Appointment is not allowed."))

    @api.constrains('travel_date', 'pcr_appointments_type', 'partner_id')
    def check_pcr_travel_date(self):
        company = self.env.company
        dur_days = company.test_before_travel_days
        if dur_days > 0:
            for rec in self.filtered(lambda r: r.company_code == 'pcr' and r.pcr_appointments_type and r.travel_date and r.start_time):
                if rec.pcr_appointments_type == 'departure':
                    if rec.travel_date < rec.start_time.date():
                        raise UserError(_('Travel date must be in future to the Appointment'))
                    duration = rec.travel_date - rec.start_time.date()
                    if duration.days < dur_days:
                        raise UserError(_("Your test must be process before %s days to your travel date") % (dur_days))
                # else:
                #     if rec.travel_date > rec.start_time.date():
                #         raise UserError(_('Travel date must be in past to the Appointment'))

    def pre_update_data(self, vals):
        if vals.get('pcr_qr_code') and vals['pcr_qr_code']:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
            base_url = '%s/qr/%s' % (base_url, vals['pcr_qr_code'])
            vals['qr_image'] = self.generate_qr_code(base_url)
        return vals

    def _compute_cert_img(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        for rec in self.sudo():
            if rec.pcr_qr_code:
                base_url = '%s/pcr/%s' % (base_url, rec.pcr_qr_code)
                img_vals = {
                    'appointment_id': rec.id,
                    'first_name': rec.partner_id.name or '',
                    'passport_number': rec.partner_id.passport_no or '',
                    'civil_id': rec.partner_id.civil_code or '',
                    'Cert_URL': base_url,
                    'phone': rec.partner_id.phone or '',
                    'Source': rec.partner_id.utm_source_id.name or '',
                    "Country": rec.partner_id.country_id.name or '',
                }
                rec.qr_cert_image = self.generate_qr_code(img_vals)
                rec.qr_result_url_image = self.generate_qr_code(base_url)
            else:
                rec.qr_cert_image = False
                rec.qr_result_url_image = ''

    def write(self, vals):
        if vals.get('pcr_result'):
            vals['pcr_result_date'] = fields.Datetime.now()
            vals['pcr_result_user_id'] = self.env.uid

        vals = self.pre_update_data(vals)
        res = super(MedicalOrder, self).write(vals)

        if vals.get('pcr_result'):
            self.schedule_next_appointment()
        for rec in self.filtered(lambda o: o.is_app_pcr and not o.pcr_qr_code):
            rec.pcr_qr_code = self.env['ir.sequence'].next_by_code('medical.order.pcr')
        return res

    def create(self, vals):
        vals = self.pre_update_data(vals)
        record = super(MedicalOrder, self).create(vals)
        if record.is_app_pcr and not record.pcr_qr_code:
            record.pcr_qr_code = self.env['ir.sequence'].next_by_code('medical.order.pcr')
        return record

    def schedule_next_appointment(self):
        company = self.env.company
        if company.pcr_condition_ids:
            for rec in self.filtered(lambda r: r.start_time):
                rule = company.get_next_app_rule(rec)
                if rule and rule.next_appointment:
                    next_dt = rec.start_time + timedelta(days=rule.next_appointment)
                    if rec.next_appointment_id:
                        rec.next_appointment_id.write({'start_time': next_dt, 'is_followup': True})
                        new_app = rec.next_appointment_id
                    else:
                        new_app = rec.copy({'start_time': next_dt, 'is_followup': True})
                        rec.write({'next_appointment_id': new_app.id})

                    if new_app and rule.discount:
                        new_app.line_ids.sudo().write({'discount': rule.discount})

    def generate_qr_code(self, url=None):
        if not url and self.pcr_qr_code:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
            base_url = '%s/qr/%s' % (base_url, self.pcr_qr_code)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_img = base64.b64encode(temp.getvalue())
        return qr_img

    def generate_order_qr(self, emp_id):
        self.sample_taken_emp_id = int(emp_id)
        self.ensure_one()
        dt = self.log_time('handover_file_on')
        if self.is_app_pcr:
            PCRTest = self.env['medical.pcr.test']
            for line in self.line_ids.filtered(lambda l: l.medical_type == 'pcr'):
                # existing_pcr_test = PCRTest.search([('appointment_line_id')])
                if line.pcr_test_ids and line.pcr_test_ids.filtered(lambda l: l.state != 'cancel'):
                    self.message_post(body="PCR Taken, Skipped to create test again.")
                    continue
                vals = {
                    'appointment_id': self.id,
                    'appointment_line_id': line.id,
                    'partner_id': self.partner_id.id,
                    'resource_id': self.resource_id.id,
                    'date_requested': dt,
                }
                PCRTest.create(vals)
        return self.pcr_qr_code

    @api.model
    def _order_fields(self, ui_order):
        afields = super(MedicalOrder, self)._order_fields(ui_order)

        for k in PCR_FIELDS:
            if k in ui_order:
                afields[k] = ui_order.get(k) or None

        if ui_order.get('in_contact_ids'):
            new_contact_list = []
            ContactList = self.env['medical.contact.list']
            for line in ui_order.get('in_contact_ids'):
                line_id = line.get('id') and line.pop('id')
                if line_id:
                    ContactList.browse(line_id).exists().write(line)
                else:
                    new_contact_list.append((0, 0, line))
            if new_contact_list:
                afields['in_contact_ids'] = new_contact_list
        return afields

    def action_print_pcr_result(self):
        self.ensure_one()


class MedicalOrderLine(models.Model):
    _inherit = "medical.order.line"

    medical_type = fields.Selection(related="product_id.medical_categ_id.medical_type", store=True)
    pcr_test_ids = fields.One2many("medical.pcr.test", "appointment_line_id", string="PCR Tests")
