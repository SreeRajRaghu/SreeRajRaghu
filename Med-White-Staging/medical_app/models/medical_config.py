# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MedicalConfig(models.Model):
    _name = 'medical.config'
    _description = 'Medical Configuration'

    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

    def _default_picking_type_id(self):
        wh = self._default_warehouse_id()
        return wh.medical_type_id.id

    def _default_location_id(self):
        wh = self._default_warehouse_id()
        return wh.lot_stock_id.id

    def _default_employees(self):
        return self.env.user.employee_ids.ids

    def _default_employee_id(self):
        emp_ids = self._default_employees()
        return emp_ids and emp_ids[0]

    def _default_sale_journal(self):
        return self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id), ('code', '=', 'MEDI')], limit=1)

    def _default_invoice_journal(self):
        return self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id)], limit=1)

    def _default_sequence(self):
        return self.env.ref('medical_app.seq_patient_reception', False)

    def _default_pricelist(self):
        return self.env['product.pricelist'].search([
            ('insurance_company_id', '=', False),
            ('currency_id', '=', self.env.company.currency_id.id)], limit=1)

    name = fields.Char(required=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    allowed_pricelist_ids = fields.Many2many(
        'product.pricelist', required=True, default=_default_pricelist,
        domain="[('insurance_company_id', '=', False), ('currency_id', '=', currency_id)]")
    pricelist_id = fields.Many2one('product.pricelist', domain="[('id', 'in', allowed_pricelist_ids)]", required=True, default=_default_pricelist)
    currency_id = fields.Many2one(related="pricelist_id.currency_id")

    journal_ids = fields.Many2many('account.journal', string="Payment Journals", domain="[('type', 'in', ['bank', 'cash'])]", required=True)

    location_id = fields.Many2one(
        'stock.location', required=True, string="Stock Location",
        domain="[('usage', '=', 'internal')]", default=_default_location_id)
    warehouse_id = fields.Many2one(
        'stock.warehouse', required=True, string="Warehouse",
        domain="[('usage', '=', 'internal')]", default=_default_warehouse_id)
    sequence_id = fields.Many2one('ir.sequence', copy=False, string="Appointment Sequence", required=True, default=_default_sequence)
    current_session_id = fields.Many2one('medical.session', string="Current Session", compute="_compute_current_session")
    depends_on = fields.Selection([
        ('file_no', 'File No'), ('file_no2', 'Derma File No')], default="file_no",
        string="Depends on File No")

    # Calendar
    start_time = fields.Float(default=9)
    end_time = fields.Float(default=15)

    # Resource
    resource_ids = fields.Many2many('medical.resource', string="Resources")
    clinic_id = fields.Many2one('medical.clinic', string='Branch')
    working_hour_id = fields.Many2one('resource.calendar', string='Working Hours')

    # session
    state = fields.Selection([('draft', _('Draft')), ('running', _('Running'))], default='draft')
    user_id = fields.Many2one('res.users', string='Current User', default=lambda self: self.env.uid)
    last_closing_date = fields.Datetime()
    show_resume = fields.Boolean(compute="_compute_show_resume")
    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default=lambda self: self.env.company.company_code)

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        default=_default_picking_type_id,
        domain="[('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)]",
        ondelete='restrict')

    employee_ids = fields.Many2many(
        "hr.employee",
        domain="[('is_medical_user','=',True)]",
        string="Allowed Employees", default=_default_employees)
    default_employee_id = fields.Many2one("hr.employee", string="Default Employee", default=_default_employee_id)

    default_collection_center_id = fields.Many2one('swab.location', string='Default Collection Center')
    default_visit_option_id = fields.Many2one('visit.option', string='Default Visit Option')

    journal_id = fields.Many2one(
        'account.journal', string='Sales Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal used to post sales entries.",
        default=_default_sale_journal)

    invoice_journal_id = fields.Many2one(
        'account.journal', string='Invoice Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal used to create invoices.",
        default=_default_invoice_journal)
    allowed_user_ids = fields.Many2many('res.users', 'rel_medical_config_allowed_users', 'medical_id', 'user_id', string="Allowed Users")
    enable_app_complain = fields.Boolean("Enable Appointment Complain")
    pricelist_need_password = fields.Boolean("Pricelist: Manager Password ?")
    cons_opr_type_id = fields.Many2one("stock.picking.type", string="Consumable Operation Type")

    # Reporting
    logo2 = fields.Binary("Header Image")
    img_footer = fields.Binary("Footer Image")

    cash_header_img = fields.Binary("Cash Invoice Header")
    cash_footer_img = fields.Binary("Cash Invoice Footer")
    invoice_patient_header_img = fields.Binary("Insurance Invoice Patient Header")
    invoice_patient_footer_img = fields.Binary("Insurance Invoice Patient Footer")
    invoice_company_header_img = fields.Binary("Insurance Invoice Company Header")
    invoice_company_footer_img = fields.Binary("Insurance Invoice Company Footer")

    resource_emp_ids = fields.Many2many(
        'hr.employee', 'hr_employee_resource_medical_config_rel',
        string="Tech:Resource Emp List",
        compute="_compute_resource_emp_ids")
    # fiscal_position_ids = fields.Many2many(
    #     'account.fiscal.position', string='Fiscal Positions',
    #     help='This is useful for restaurants with onsite and take-away services that imply specific tax rates.')
    # default_fiscal_position_id = fields.Many2one('account.fiscal.position', string='Default Fiscal Position')

    _sql_constraints = [
        ('name_user_id', 'unique (user_id)', _("You are already logged in another session. !")),
    ]

    header_main_logo = fields.Binary('Header Main Logo')
    header_sub_logo = fields.Binary('Header Sub Logo')

    def _compute_resource_emp_ids(self):
        for rec in self:
            emp_ids = set(rec.employee_ids.ids) | set(rec.resource_ids.mapped('emp_ids.id'))
            print ('____ emp_ids : ', emp_ids)
            rec.resource_emp_ids = [(4, _id) for _id in emp_ids]

    def _compute_show_resume(self):
        uid = self.env.uid
        for rec in self:
            rec.show_resume = rec.user_id.id == uid

    @api.onchange('clinic_id')
    def onchange_clinic_id(self):
        if self.clinic_id:
            self.resource_ids = False
            self.resource_ids = self.clinic_id.resource_ids

    def _compute_current_session(self):
        Session = self.env['medical.session']
        for rec in self:
            session = Session.search([
                ('state', '=', 'opened'), ('config_id', '=', rec.id)], limit=1)
            rec.current_session_id = session

    def open_existing_ui(self):
        pass

    def close_session(self):
        return {
            'name': _('Sessions'),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.session',
            'view_mode': 'form',
            'res_id': self.current_session_id.id,
            'domain': [('config_id', 'in', self.ids)],
        }

    def open_ui(self):
        self.ensure_one()
        if not self.resource_ids or not self.clinic_id.resource_ids:
            raise ValidationError(_('Add atleast one resource in scheduler and clinic.'))
        if not self.default_employee_id:
            raise ValidationError(_('Please assign default employee before you start.'))
        if self.state == 'draft':
            self.start_session()
        elif self.env.uid != self.user_id.id:
            raise ValidationError(_("Session is already in use by another user."))

    def start_session(self):
        self.ensure_one()
        if not self.current_session_id:
            self.current_session_id.create({'config_id': self.id})
        self.write({"user_id": self.env.uid, 'state': 'running', 'last_closing_date': False})

    def action_view_order(self):
        return {
            'name': _('Appointments'),
            'res_model': 'medical.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('medical_app.view_medical_order_tree').id, 'tree'),
                (self.env.ref('medical_app.view_medical_order_form').id, 'form'),
                ],
            'type': 'ir.actions.act_window',
            'domain': [('config_id', 'in', self.ids)],
        }

    def action_view_sessions(self):
        return {
            'name': _('Sessions'),
            'type': 'ir.actions.act_window',
            'res_model': 'medical.session',
            'view_mode': 'tree,form',
            'domain': [('config_id', 'in', self.ids)],
        }
