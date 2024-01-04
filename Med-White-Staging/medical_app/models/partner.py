# -*- coding: utf-8 -*-
import re


from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.osv.expression import get_unaccent_wrapper


class Area(models.Model):
    _name = 'res.area'
    _description = "Address Area"

    name = fields.Char(required=True)
    code = fields.Char()

    _sql_constraints = [
        ('uniq_group_name', 'unique (code)', 'Area Code must be unique.')
    ]


class Medium(models.Model):
    _inherit = 'utm.medium'

    utm_source_id = fields.Many2one('utm.source', string="Source")


class Partner(models.Model):
    _inherit = 'res.partner'

    area = fields.Char()
    area_id = fields.Many2one("res.area", string="Area")
    block = fields.Char()
    avenue = fields.Char()
    house = fields.Char(string="Building")
    floor = fields.Char()
    apartment_no = fields.Char("Unit No.")
    blood_group = fields.Char("Blood Group")
    work_phone = fields.Char("Contact 3")
    civil_id_issued = fields.Date("Civil ID Issued")
    civil_id_expiry = fields.Date("Civil ID Expiry")
    civil_sponser = fields.Char("Sponser (Civil ID)")
    civil_paci_no = fields.Char("PACI Number")
    area_kw_moh_code = fields.Char()
    governorate = fields.Char("Governorate")
    street2 = fields.Char("Full Address")
    residence = fields.Char("Residence")
    file_depends_on = fields.Selection(related="company_id.depends_on")

    GENDER = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    MARITAL = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Legal Cohabitant'),
        ('widower', 'Widower'),
        ('divorced', 'Divorced'),
    ]

    birthday = fields.Date('Date of Birth')
    age = fields.Integer(compute="_compute_age", string="Age", help="Age in Years")
    nationality_id = fields.Many2one('res.country', string='Nationality')
    file_no = fields.Char(string='File No.')
    file_no2 = fields.Char(string='Derma File No')
    gender = fields.Selection(GENDER, string='Gender')
    marital = fields.Selection(MARITAL, string='Marital')
    real_balance = fields.Float(string="Real Balance", readonly=True)
    person_status = fields.Selection(
        [("normal", "Normal"), ("vip", "Very Important Person (VIP)")],
        default="normal", string="Person Importance")
    civil_code = fields.Char("Civil ID")
    diagnosis_summary = fields.Text("Diagnosis Summary")
    fax = fields.Char("Fax")
    first_visit = fields.Date(string='First Visit Date', compute='_compute_first_visit')
    last_visit = fields.Date(string='Last Visit Date')
    last_medical_order_id = fields.Many2one('medical.order', string='Last Appointment', compute="_compute_last_medical_order")
    medical_attachment_ids = fields.One2many('medical.patient.attachment', 'partner_id', string='Attachments')
    # running_pkg_ids = fields.One2many(
    #     "customer.package", "partner_id", string="Running Packages",
    #     domain=[('state', '=', 'running')])

    ar_name = fields.Char("Arabic Name")
    app_no_show_count = fields.Integer(compute='_compute_appointment_state_count', store=True)
    app_cancelled_count = fields.Integer(compute='_compute_appointment_state_count', store=True)
    due_payment = fields.Float()

    # insurance
    is_insurance_company = fields.Boolean('Is Insurance Company')
    pricelist_ids = fields.One2many('product.pricelist', 'insurance_company_id', 'Pricelists')
    insurance_card_ids = fields.One2many('insurance.card', 'partner_id', 'Insurances')
    ins_running_card_ids = fields.One2many(
        'insurance.card', 'partner_id', string='Running Insurances',
        domain="[('state', '=', 'running')]")
    appointment_ids = fields.One2many('medical.order', 'partner_id', string='Appointments')
    appointment_count = fields.Integer(compute='_compute_appointments')
    auto_patient_sequence = fields.Selection(related="company_id.auto_patient_sequence")
    auto_derma_sequence = fields.Selection(related="company_id.auto_derma_sequence")
    history = fields.Text()
    blocked_doctor_ids = fields.Many2many('medical.resource', 'blocked_patient_by_doctor', 'patient_id', 'resource_id', string="Blocked By Resource")

    utm_source_id = fields.Many2one('utm.source', string="Source")
    utm_medium_id = fields.Many2one('utm.medium', string="Referral", domain="[('utm_source_id', '=', utm_source_id)]")
    passport_no = fields.Char("Passport")

    _sql_constraints = [
        ('civil_code_uniq', 'unique (civil_code)', 'Civil Code must be unique!'),
        ('file_no_uniq', 'unique (file_no)',  'File number must be unique!'),
        ('file_no2_uniq', 'unique (company_id, file_no2)',  'Derma File number must be unique!'),
        ('passport_no_uniq', 'unique (passport_no)',  'Passport No. must be unique!'),
    ]

    @api.onchange('is_insurance_company')
    def _onchange_is_insurance_company(self):
        if not self.is_insurance_company:
            self.parent_id = False
            self.pricelist_ids = [(5, 0, 0)]

    def _compute_first_visit(self):
        Order = self.env['medical.order']
        for record in self:
            o = Order.search([('partner_id', '=', record.id)], limit=1, order='start_time asc')
            record.first_visit = o.start_time

    @api.depends('appointment_ids')
    def _compute_appointments(self):
        for record in self:
            record.appointment_count = len(record.appointment_ids)

    def _compute_last_medical_order(self):
        Order = self.env['medical.order']
        for record in self:
            o = Order.search([('partner_id', '=', record.id)], limit=1, order='start_time desc')
            record.last_medical_order_id = o.id

    @api.depends('birthday')
    def _compute_age(self):
        for partner in self:
            if partner.birthday:
                partner.age = relativedelta(fields.Date.today(), partner.birthday).years
            else:
                partner.age = 0

    @api.depends('appointment_ids', 'appointment_ids.state')
    def _compute_appointment_state_count(self):
        grouped_data = self.env['medical.order'].read_group(
            [('partner_id', 'in', self.ids), ('state', 'in', ('no_show', 'cancel'))],
            ['id', 'partner_id', 'state'],
            ['partner_id', 'state'],
            lazy=False)
        parnter_by_id = {p.id: p for p in self}
        for data in grouped_data:
            pid = data['partner_id'][0]
            state = data['state']
            if state == 'no_show':
                parnter_by_id[pid].app_no_show_count = data['__count']
            elif state == 'cancel':
                parnter_by_id[pid].app_cancelled_count = data['__count']

    def set_birthday_from_civil(self, civil_code):
        if not civil_code or len(civil_code) < 10:
            return
        cur_year = int(fields.Datetime.now().strftime('%y'))
        year, month, day = civil_code[1:3], civil_code[3:5], civil_code[5:7]
        try:
            if (int(year) > cur_year):
                year = "19%s" % year
            else:
                year = "20%s" % year
            self.write({'birthday': '%s-%s-%s' % (year, month, day)})
        except Exception as e:
            import logging
            logging.error(e)
            pass

    @api.model
    def create(self, values):
        company = self.env.user.company_id
        if company.auto_patient_sequence == 'automatic':
            values['file_no'] = self.get_next_file_number(company.depends_on)

        if company.auto_derma_sequence == 'automatic':
            values['file_no2'] = self.get_next_file_number(company.depends_on)

        record = super(Partner, self).create(values)
        if values.get('civil_code'):
            record.set_birthday_from_civil(values['civil_code'])
        return record

    def write(self, values):
        res = super(Partner, self).write(values)
        if values.get('civil_code'):
            self.set_birthday_from_civil(values['civil_code'])
        if values.get('civil_code'):
            PCRTest = self.env['medical.pcr.test'].sudo()
            for rec in self:
                if rec.civil_code != values.get('civil_code'):
                    partner_count = PCRTest.search_count([('partner_id', 'in', self.ids), ('state', '!=', 'cancel')])
                    if partner_count:
                        raise UserError(_("You can not update Civil Code because they have PCR Test"))
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if 'quick_load_limit' in self.env.context:
            limit = self.env.context['quick_load_limit'] or None
        return super(Partner, self).search_read(domain, fields, offset, limit, order)

    def get_next_file_number(self, depends_on=False):
        company = self.env.user.company_id
        depends_on = depends_on or company.depends_on
        if depends_on == 'file_no' and company.patient_seq_id:
            return company.patient_seq_id._next()
        elif depends_on == 'file_no2' and company.derma_seq_id:
            return company.derma_seq_id._next()
        else:
            raise UserError('Patient File Sequence is missing')

    def action_assign_file_no(self):
        depends_on = self.env.company.depends_on
        if depends_on == 'file_no' and self.file_no:
            raise UserError('File no is already assigned.')
        if depends_on == 'file_no2' and self.file_no2:
            raise UserError('Derma File no is already assigned.')
        self.write({depends_on: self.get_next_file_number(depends_on)})

    def action_redirect_to_appointment(self):
        self.ensure_one()
        action = self.env.ref('medical_app.action_medical_order').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    def action_redirect_to_insurance_card(self):
        self.ensure_one()
        action = self.env.ref('medical_app.action_insurance_card').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    def is_blocked_by_doctor(self, doctor_ids):
        self.ensure_one()
        if set(self.blocked_doctor_ids.ids) & set(doctor_ids):
            return True
        return False

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        self = self.with_user(name_get_uid or self.env.uid)
        # as the implementation is in SQL, we force the recompute of fields if necessary
        self.recompute(['display_name'])
        self.flush()
        if args is None:
            args = []
        order_by_rank = self.env.context.get('res_partner_search_mode')
        if (name or order_by_rank) and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            self.check_access_rights('read')
            where_query = self._where_calc(args)
            self._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            from_str = from_clause if from_clause else 'res_partner'
            where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '

            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]

            unaccent = get_unaccent_wrapper(self.env.cr)

            fields = self._get_name_search_order_by_fields()

            query = """SELECT res_partner.id
                         FROM {from_str}
                      {where} ({email} {operator} {percent}
                           OR {display_name} {operator} {percent}
                           OR {mobile} {operator} {percent}
                           OR {phone} {operator} {percent}
                           OR {ar_name} {operator} {percent}
                           OR {reference} {operator} {percent}
                           OR {file_no} {operator} {percent}
                           OR {file_no2} {operator} {percent}
                           OR {vat} {operator} {percent})
                           -- don't panic, trust postgres bitmap
                     ORDER BY {fields} {display_name} {operator} {percent} desc,
                              {display_name}
                    """.format(from_str=from_str,
                               fields=fields,
                               where=where_str,
                               operator=operator,
                               email=unaccent('res_partner.email'),
                               ar_name=unaccent('res_partner.ar_name'),
                               display_name=unaccent('res_partner.display_name'),
                               mobile=unaccent('res_partner.mobile'),
                               phone=unaccent('res_partner.phone'),
                               reference=unaccent('res_partner.ref'),
                               file_no=unaccent('res_partner.file_no'),
                               file_no2=unaccent('res_partner.file_no2'),
                               percent=unaccent('%s'),
                               vat=unaccent('res_partner.vat'),)

            where_clause_params += [search_name]*8  # for email / display_name, reference, ar_name, file_no, file_no2
            where_clause_params += [re.sub('[^a-zA-Z0-9]+', '', search_name) or None]  # for vat
            where_clause_params += [search_name]  # for order by
            if limit:
                query += ' limit %s'
                where_clause_params.append(limit)
            self.env.cr.execute(query, where_clause_params)
            partner_ids = [row[0] for row in self.env.cr.fetchall()]

            if partner_ids:
                return models.lazy_name_get(self.browse(partner_ids))
            else:
                return []
        return super(Partner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)
