from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LabTests(models.Model):
    _name = 'medical.pcr.test'
    _description = 'Lab PCR Tests'
    _inherit = ['mail.thread']
    _order = "date_requested desc"

    name = fields.Char(string='Lab Test #', readonly=True, tracking=True, copy=False)
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.company)
    company_code = fields.Selection(related="appointment_id.config_id.company_code")

    partner_id = fields.Many2one(
        'res.partner', store=True, string='Patient', help="Patient Name", readonly=True,
        tracking=True)
    civil_code = fields.Char(related="partner_id.civil_code")
    gender = fields.Selection(related="partner_id.gender")
    country_id = fields.Many2one(related="partner_id.country_id")
    nationality_id = fields.Many2one(related="partner_id.nationality_id")
    mobile = fields.Char(related="partner_id.mobile")
    phone = fields.Char(related="partner_id.phone")

    appointment_id = fields.Many2one(
        'medical.order', store=True, string='Appointment',
        readonly=True, tracking=True,
        domain="[('partner_id','=',partner_id),('is_app_pcr','=',True)]")
    pcr_qr_code = fields.Char(related="appointment_id.pcr_qr_code", store=True, copy=False)
    qr_image = fields.Binary(related="appointment_id.qr_image")

    appointment_line_id = fields.Many2one(
        'medical.order.line', string='Appointments Line', help="Appointments Line",
        readonly=True, tracking=True,
        domain="[('partner_id','=',partner_id),('medical_type','=','pcr')]")
    product_id = fields.Many2one(
        related="appointment_line_id.product_id", store=True, tracking=True)
    date_requested = fields.Datetime(
        string='Sample Taken', readonly=True, default=fields.Datetime.now, copy=False, tracking=True)
    date_received = fields.Datetime(
        string='Sample Received', readonly=True, copy=False, tracking=True)
    date_in_lab = fields.Datetime(
        string='Sample In Lab', readonly=True, copy=False, tracking=True)
    date_inprogress = fields.Datetime(string='Collected (InProgress) On', copy=False, readonly=True, tracking=True)
    date_confirmed = fields.Datetime(string='Confirmed On', copy=False, readonly=True, tracking=True)
    # date_done = fields.Datetime(string='Completed On', copy=False, readonly=True, tracking=True)
    date_completed = fields.Datetime("Completion Date", tracking=True, copy=False)

    batch_no = fields.Char("Batch No.", tracking=True)

    state = fields.Selection([
        ('draft', 'Sample Taken'),
        ('transit', 'In Transit'),
        ('received', 'Received'),
        ('in_lab', 'In Lab'),
        ('inprogress', 'Under Process'),
        ('confirmed', 'Confirmed'),
        ('done', 'Signed Out'),
        ('cancel', 'Cancelled'),
    ], string='State', readonly=True, default='draft', tracking=True, copy=False)

    employee_id = fields.Many2one("hr.employee", string="Technician", tracking=True, copy=False)

    pcr_result = fields.Selection([
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('equivocal', 'Equivocal'),
        ('rejected', 'Rejected')], string='PCR Result', copy=False, tracking=True)

    is_pcr_result_user = fields.Boolean("Is PCR Result", compute="_compute_is_pcr_result_user")
    pcr_result_note = fields.Text("PCR Result Note", copy=False, tracking=True)
    pcr_result_date = fields.Datetime("PCR Result Date", copy=False, tracking=True)
    pcr_result_user_id = fields.Many2one("res.users", string="PCR Result Updated By", copy=False, tracking=True)

    resource_id = fields.Many2one(
        "medical.resource", string="Ref. Doctor",
        readonly=True, tracking=True)

    def open_bulk_scan(self, to_action):
        view_ref = ''
        wiz = TranserWiz = self.env['pcr.transfer']
        print ('____ to_action : ', to_action, self.mapped('state'), self)
        if to_action == 'to_inprogress':
            if self.filtered(lambda r: r.state != 'in_lab'):
                raise UserError(_("Only In Lab sample(s) can be taken for Under Process."))
            view_ref = 'medical_pcr.wiz_pcr_lab_to_inprogress'
        elif to_action == 'to_confirmed':
            if self.filtered(lambda r: r.state != 'inprogress'):
                raise UserError(_("Only Under Process sample(s) can be taken for the result."))
            view_ref = 'medical_pcr.wiz_pcr_received_to_confirmed'
        if view_ref:
            action = self.env.ref(view_ref)
            wiz = TranserWiz.create({
                'action': to_action,
                'line_ids': [(0, 0, {
                    'pcr_test_id': rec.id,
                    'pcr_result': rec.pcr_result,
                }) for rec in self]
            })
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pcr.transfer',
                'res_id': wiz.id,
                'view_id': action.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('medical.pcr.test')
        vals['name'] = sequence or '/NoSequence'
        record = super(LabTests, self).create(vals)
        if not vals.get('resource_id') and vals.get('appointment_id') and record.appointment_id.resource_id:
            record.resource_id = record.appointment_id.resource_id
        return record

    def write(self, vals):
        if vals.get('pcr_result'):
            vals['pcr_result_date'] = fields.Datetime.now()
            vals['pcr_result_user_id'] = self.env.uid

        res = super(LabTests, self).write(vals)
        if vals.get('pcr_result'):
            self.mapped('appointment_id').write({'pcr_result': vals['pcr_result']})
        return res

    def unlink(self):
        raise UserError(_("PCR Test cannot be deleted, You can cancel it."))

    # Fetching lab test types
    # @api.onchange('test_type_id')
    # def onchange_test_type_id(self):
    #     values = self.onchange_test_type_id_values(self.test_type_id.id if self.test_type_id else False)
    #     return values
    @api.constrains('state', 'pcr_result')
    def _check_constrain(self):
        for rec in self.filtered(lambda r: r.state in ['confirmed', 'done'] and not r.pcr_result):
            raise UserError(_('Confirmed or Sign-Out not possible until you update PCR Result.'))

    def action_send_sms(self):
        records = self.filtered(lambda r: r.state == 'done')
        for appointment in records.mapped('appointment_id'):
            appointment.send_result_by_sms()

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_in_transit(self):
        records = self.filtered(lambda r: r.state == 'draft')
        records.write({'state': 'transit'})

    def action_received(self, batch=None):
        records = self.filtered(lambda r: r.state in ('transit'))
        vals = {'state': 'received', 'date_received': fields.Datetime.now()}
        if batch:
            vals.update({'batch_no': batch})
        records.write(vals)

    def action_in_lab(self, batch=None):
        records = self.filtered(lambda r: r.state == 'received')
        vals = {'state': 'in_lab', 'date_in_lab': fields.Datetime.now()}
        if batch:
            vals.update({'batch_no': batch})
        records.write(vals)

    def action_inprogress(self, batch=None):
        records = self.filtered(lambda r: r.state == 'in_lab')
        if not batch and records.filtered(lambda r: not r.batch_no):
            raise UserError(_("Batch No. required to make it Under Process."))
        vals = {'state': 'inprogress', 'date_inprogress': fields.Datetime.now()}
        if batch:
            vals['batch_no'] = batch
        records.write(vals)

    def action_confirmed(self):
        records = self.filtered(lambda r: r.state == 'inprogress')
        records.write({'state': 'confirmed', 'date_confirmed': fields.Datetime.now()})

    def action_done(self):
        records = self.filtered(lambda r: r.state == 'confirmed')
        records.write({'state': 'done', 'date_completed': fields.Datetime.now()})

    def action_cancel(self):
        self.write({
            'state': 'cancel',
            'date_completed': False,
            'pcr_result': False,
        })

    def action_reset(self):
        self.write({
            'state': 'draft',
            'date_completed': False,
            'pcr_result': False
        })

    @api.onchange('appointment_id')
    def onchange_appointments(self):
        res = {}
        if self.appointment_id:
            if self.appointment_id.partner_id:
                self.partner_id = self.appointment_id.partner_id

            res['domain'] = {
                'appointment_line_id': [('id', 'in', self.appointment_id.line_ids.ids)],
                'partner_id': [('id', 'in', self.appointment_id.partner_id.ids)]
            }
        return res

    def _compute_is_pcr_result_user(self):
        is_pcr_result_mgr = self.env.user.has_group('medical_pcr.group_virology_technician')
        for rec in self:
            rec.is_pcr_result_user = is_pcr_result_mgr

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        res = super(LabTests, self)._name_search(name, args, operator, limit, name_get_uid)
        rec_ids = list(map(lambda r: r[0], res or [])) or []
        args = args or []
        try:
            int_name = int(name)
            new_rec_ids = set(rec_ids) - set([int_name])
            product_ids = self._search([
                    ('id', 'not in', list(new_rec_ids)),
                    '|',
                    ('appointment_id', '=', int_name),
                    ('pcr_qr_code', 'ilike', name)
                ] + args,
                limit=limit, access_rights_uid=name_get_uid)
        except:
            product_ids = self._search([
                ('id', 'not in', rec_ids),
                ('pcr_qr_code', 'ilike', name)] + args,
                limit=limit, access_rights_uid=name_get_uid)
        return res + models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))
