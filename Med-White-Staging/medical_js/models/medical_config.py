# -*- coding: utf-8 -*-

from uuid import uuid4
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class MedicalConfig(models.Model):
    _inherit = 'medical.config'

    def _get_group_admin(self):
        return self.env.ref('medical_app.group_medical_admin')

    def _get_group_cashier(self):
        return self.env.ref('medical_app.group_medical_cashier')

    def _get_group_user(self):
        return self.env.ref('medical_app.group_medical_user')

    def _get_group_invoice_reset(self):
        return self.env.ref('medical_app.group_invoice_reset')

    def _get_group_invoice_paid_edit(self):
        return self.env.ref('medical_app.group_invoice_paid_edit')

    uuid = fields.Char(
        readonly=True, default=lambda self: str(uuid4()),
        help='A globally unique identifier for this session configuration, used to prevent conflicts in client-generated data.')

    group_medical_admin_id = fields.Many2one(
        'res.groups', string='Reception Admin Group', default=_get_group_admin,
        help='This field is there to pass the id of the pos manager group to the Reception client.')

    group_medical_cashier_id = fields.Many2one(
        'res.groups', string='Reception Manager Group', default=_get_group_cashier,
        help='This field is there to pass the id of the pos manager group to the Reception client.')
    group_medical_user_id = fields.Many2one(
        'res.groups', string='Reception User Group', default=_get_group_user,
        help='This field is there to pass the id of the pos user group to the Reception client.')
    group_medical_invoice_reset = fields.Many2one(
        'res.groups', string='Invoice Reset', default=_get_group_invoice_reset,
        help='This field is there to pass the id of the pos user group to the Reception client.', readonly=True)
    group_medical_invoice_paid_edit = fields.Many2one(
        'res.groups', string='Invoice Paid or Reconciled Edit', default=_get_group_invoice_paid_edit,
        help='This field is there to pass the id of the pos user group to the Reception client.', readonly=True)

    enable_insurance = fields.Boolean("Enable Insurance")
    enable_login = fields.Boolean("Enable Login Screen ?")
    allow_price_change = fields.Boolean("Allow Price Change ?")
    allow_multi_appointments = fields.Boolean("Multi Appointment Creatation ?")
    allow_tips = fields.Boolean("Allow Tips ?")
    allow_package = fields.Boolean("Allow Package ?")
    allow_refund = fields.Boolean("Allow Refund ?")
    allow_global_disc = fields.Boolean("Allow Global Discount ?")
    report_color_style = fields.Text("Report Color Style", default="#132769")
    report_background_style = fields.Text("Report Background Style", default="#132769")

    allow_time_off = fields.Boolean("Allow Time Off ?")
    # time_off_type_id = fields.Many2one('hr.leave.type', string="Time Off Type")

    enable_visit_option = fields.Boolean("Enable Visit Option", default=True)
    enable_prepaid_card = fields.Boolean("Enable Prepaid Cards")

    show_resource_late = fields.Boolean("Indicate Resource Late")

    strict_working_schedule = fields.Boolean("Strict To Working Schedule", default=True)

    inv_validation_on = fields.Selection([
        ('app', "Validation Of Appointment"), ('inv', 'Validation Of Invoice')],
        string="Post Invoice On", default="app")

    tip_prod_id = fields.Many2one('product.product', string="Tip Product", domain="[('type', '=', 'service')]")

    suggest_uninvoiced_orders = fields.Boolean("Suggest UnInvoiced Appointments ?", help="""System will give you all uninvoiced appointments on Invoice Screen.
        And you can create Single Invoice for Multiple Appointments""")
    enable_line_analytics = fields.Boolean("Enable Analytics")
    enable_followup = fields.Boolean("Enable Follow Up")
    enable_complain = fields.Boolean("Enable Complain")

    enable_qty = fields.Boolean("Enable Quantity", default=True)

    enable_line_select_emp = fields.Boolean("Enable Employee Selection On Line")
    enable_line_consumable = fields.Boolean("Enable Product Consumable On Line")
    enable_show_cust_order_lines = fields.Boolean("Show Orderline History")
    allowed_dept_ids = fields.Many2many('hr.department', string="Allowed Employee Departments")
    req_one_service = fields.Boolean("Atleast One Service Required ?")
    req_patient_civil = fields.Boolean("Civil ID/Passport Required ?")
    req_patient_phone = fields.Boolean("Phone/Mobile Required ?")
    req_patient_nationality = fields.Boolean("Nationality Required ?")
    req_patient_gender = fields.Boolean("Gender Required ?")

    req_patient_gender_on_arrive = fields.Boolean("Gender Required on Arrive ?")
    req_patient_fulladdress_on_arrive = fields.Boolean("Full Address Required on Arrive ?")
    req_patient_bday_on_arrive = fields.Boolean("Birth Date Required on Arrive ?")
    req_patient_civil_on_arrive = fields.Boolean("Civil ID/Passport Required on Arrive ?")
    req_patient_file_on_arrive = fields.Boolean("File No Required on Arrive ?")

    auto_refresh_interval = fields.Float("Auto Refresh", default=1)
    limit_categ_ids = fields.Many2many("medical.category", string="Session Categories")

    # fullcalendar configuration
    calendar_views = fields.Char("Calendar Views", default="", help="Comma Separated View Names")
    calendar_default_view = fields.Char("Default View", default="resourceTimeGridDay")
    calendar_license_key = fields.Char(
        "Calendar License Key",
        default="GPL-My-Project-Is-Open-Source")

    calendar_slot_duration = fields.Integer(help='Slot Duration (In Minutes)', default=15)
    calendar_slotEventOverlap = fields.Boolean("Slot Event Overlap", default=True)
    auto_refresh_calendar = fields.Float("Auto Refresh Calendar (MM:SS)", default=3)

    restrict_prev_date_appointment = fields.Boolean("Restrict Previous Date Appointment")
    service_appointment_only = fields.Boolean("Show Service Appointments Only in Calendar")
    show_branch_selection = fields.Boolean("Show Branch Selection", default=True)
    restrict_duplicate_product = fields.Boolean("Restrict Duplicate Product")

    def open_existing_ui(self):
        return self.open_ui()

    def open_ui(self):
        super(MedicalConfig, self).open_ui()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url':   '/medical/web?config_id=%d' % self.id,
        }

    @api.onchange('allow_time_off')
    def _onchange_allow_time_off(self):
        if self.allow_time_off:
            hr_holiday_installed = self.env['ir.module.module'].search([
                ('name', '=', 'hr_holidays'), ('state', '=', 'installed')])
            if not hr_holiday_installed:
                self.allow_time_off = False
                raise ValidationError(_("To use time off you must need to install 'hr_holidays'."))

    def get_late_resources(self, dt):
        GRACE_MINUTES = 0
        if not self.show_resource_late:
            return {}

        sql = """
        SELECT
            a.employee_id, TO_CHAR(avg(a.check_in - a.actual_in), 'HH:MI')
        FROM hr_attendance AS a
        WHERE
        DATE(a.check_in) = %s
        AND (a.check_in - a.actual_in)::interval > %s
        GROUP BY a.employee_id
        """

        self.env.cr.execute(sql, (dt, str(GRACE_MINUTES) + ' minutes'))
        fetched_rows = self.env.cr.fetchall()
        _logger.info("____ Late Resources : %s :: %s", len(fetched_rows), fetched_rows)
        result = {}
        for item in fetched_rows:
            res_id = self.get_resource_id(item[0])
            if res_id:
                result[res_id] = item[1]
        return result

    def get_resource_id(self, emp_id):
        sql = """
        SELECT
            id
        FROM medical_resource
        WHERE hr_staff_id = %s AND active = true LIMIT 1
        """
        self.env.cr.execute(sql, (emp_id,))
        emp_id = self.env.cr.fetchone()
        return emp_id and emp_id[0]

    def get_resource_timeoff(self, dt):
        if not self.allow_time_off:
            return []
        sql = """
        SELECT
            id, employee_id, date_from, date_to, state, name
        FROM hr_leave
        WHERE state = 'validate' AND (DATE(date_to) = %s OR %s BETWEEN DATE(date_from) AND DATE(date_to))
        """
        self.env.cr.execute(sql, (dt, dt))
        fetched_rows = self.env.cr.dictfetchall()

        for row in fetched_rows:
            row['resource_id'] = self.get_resource_id(row['employee_id'])
        _logger.info("____ Get TimeOff : %s = %s :: %s", dt, len(fetched_rows), fetched_rows)
        return fetched_rows


class MedicalSession(models.Model):
    _inherit = 'medical.session'

    sequence_number = fields.Integer(
        string='Order Sequence Number',
        help='A sequence number that is incremented with each order', default=1)
    login_number = fields.Integer(
        string='Login Sequence Number',
        help='A sequence number that is incremented each time a user resumes the session', default=1)

    rescue = fields.Boolean("Rescue Session ?")

    def login(self):
        self.ensure_one()
        login_number = self.login_number + 1
        self.write({
            'login_number': login_number,
        })
        return login_number

    def add_sequence_number(self):
        self.env.cr.execute('UPDATE medical_session SET sequence_number = sequence_number + 1 WHERE ID = %s', (self.id,))
