# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Payment(models.Model):
    _inherit = 'account.payment'

    is_other_journal = fields.Boolean(compute="_compute_is_other_journal", store=True)
    med_config_id = fields.Many2one('medical.config', compute="_compute_med_config_id", store=True)
    company_code = fields.Selection(related="med_config_id.company_code", store=True)

    @api.depends('medical_order_id', 'session_id')
    def _compute_med_config_id(self):
        for rec in self:
            if rec.medical_order_id:
                rec.med_config_id = rec.medical_order_id.config_id.id
            else:
                rec.med_config_id = rec.session_id.config_id.id

    @api.depends('state')
    def _compute_is_other_journal(self):
        journal_id = int(self.env['ir.config_parameter'].sudo().get_param('dashboard.ignore.journal_id'))
        for rec in self:
            is_tick = False
            if journal_id and rec.invoice_ids.filtered(lambda r: r.journal_id.id == journal_id):
                is_tick = True
            rec.is_other_journal = is_tick


class Invoice(models.Model):
    _inherit = 'account.move'

    amount_total_gross = fields.Monetary("Gross Total", compute="_compute_total_discount", store=True)
    total_discount = fields.Monetary("Total Discount", compute="_compute_total_discount", store=True)
    swab_location_id = fields.Many2one(related="medical_order_id.swab_location_id", store=True)
    med_config_id = fields.Many2one(related="medical_order_id.config_id", store=True)
    company_code = fields.Selection(related="med_config_id.company_code", store=True)

    @api.depends(
        'invoice_line_ids', 'invoice_line_ids.price_subtotal', 'invoice_line_ids.discount', 'invoice_line_ids.discount_fixed')
    def _compute_total_discount(self):
        for rec in self:
            tot_disc = 0
            for line in rec.invoice_line_ids:
                disc = (line.price_unit * line.quantity) - line.price_subtotal
                tot_disc += disc
            rec.total_discount = tot_disc
            rec.amount_total_gross = rec.amount_total + tot_disc


class DashboardSettingsLine(models.Model):
    _inherit = 'dashboard.settings.line'

    visibility = fields.Selection(selection_add=[
        ('lab_dept', 'Department'),
        ('resource', 'Resource'),
        ('visit_opt', 'Visit Option'),
        ('pcr_dept', 'PCR: Department'),
        ('pcr_swab', 'PCR: Swab Location'),
        ('derma', 'Derma'),
    ])
    resource_id = fields.Many2one("medical.resource", string="Resource")
    visit_opt_id = fields.Many2one("visit.option", string="Visit Option")
    swab_location_id = fields.Many2one("swab.location", string="Swab Location")


class MedicalResource(models.Model):
    _inherit = 'medical.resource'

    dashboard_line_ids = fields.One2many('dashboard.settings.line', 'resource_id', string="Dashbaord Lines")

    def create_dashboard_box(self):
        DashboardLine = self.env['dashboard.settings.line']
        for record in self:
            box_vals = {
                'name': record.name,
                'color': 'primary',
                'visibility': 'resource',
                'model_id': self.env.ref('account.model_account_move').id,
                'field_id': self.env.ref('dashboard_data.field_account_move__amount_total_gross').id,
                'type': 'money',
                'custom_sql': '',
                'custom_sql_alias': '',
                'custom_sql_ids': '',
                'dashboard_id': self.env.ref('medical_dashboard.setting_object').id,
                'action_id': self.env.ref('medical_app.action_move_patient_out_invoice_type').id,
                'filter': "type = 'out_invoice' AND state = 'posted' AND resource_id = %s" % (record.id),
                'char_groups': '',
                'apply_create_date_filter': False,
                'date_field_name': 'invoice_date',
                'sequence': record.id,
                'resource_id': record.id,
            }
            if record.dashboard_line_ids:
                record.dashboard_line_ids.write(box_vals)
            else:
                DashboardLine.create(box_vals)

    def remove_dashboard_box(self):
        self.dashboard_line_ids.unlink()


class VisitOpt(models.Model):
    _inherit = 'visit.option'

    dashboard_line_ids = fields.One2many('dashboard.settings.line', 'visit_opt_id', string="Dashbaord Lines")

    def create_dashboard_box(self):
        DashboardLine = self.env['dashboard.settings.line']
        for record in self:
            box_vals = {
                'name': "%s : Count" % (record.name),
                'color': 'primary',
                'visibility': 'visit_opt',
                'model_id': self.env.ref('account.model_account_move').id,
                'field_id': self.env.ref('account.field_account_move__id').id,
                'type': 'qty',
                'custom_sql': '',
                'custom_sql_alias': '',
                'custom_sql_ids': '',
                'dashboard_id': self.env.ref('medical_dashboard.setting_object').id,
                'action_id': self.env.ref('medical_app.action_move_patient_out_invoice_type').id,
                'filter': "type = 'out_invoice' AND state = 'posted' AND visit_opt_id = %s" % (record.id),
                'char_groups': '',
                'apply_create_date_filter': False,
                'date_field_name': 'invoice_date',
                'sequence': record.id,
                'visit_opt_id': record.id,
            }
            # if record.dashboard_line_ids:
            #     record.dashboard_line_ids.write(box_vals)
            # else:
            DashboardLine.create(box_vals)

            box_vals = {
                'name': "%s : Amount" % (record.name),
                'color': 'primary',
                'visibility': 'visit_opt',
                'model_id': self.env.ref('account.model_account_move').id,
                'field_id': self.env.ref('dashboard_data.field_account_move__amount_total_gross').id,
                'type': 'money',
                'custom_sql': '',
                'custom_sql_alias': '',
                'custom_sql_ids': '',
                'dashboard_id': self.env.ref('medical_dashboard.setting_object').id,
                'action_id': self.env.ref('medical_app.action_move_patient_out_invoice_type').id,
                'filter': "type = 'out_invoice' AND state = 'posted' AND visit_opt_id = %s" % (record.id),
                'char_groups': '',
                'apply_create_date_filter': False,
                'date_field_name': 'invoice_date',
                'sequence': record.id,
                'visit_opt_id': record.id,
            }
            # if record.dashboard_line_ids:
            #     record.dashboard_line_ids.write(box_vals)
            # else:
            DashboardLine.create(box_vals)

    def remove_dashboard_box(self):
        self.dashboard_line_ids.unlink()


class SwabLocation(models.Model):
    _inherit = 'swab.location'

    dashboard_line_ids = fields.One2many('dashboard.settings.line', 'swab_location_id', string="Dashbaord Lines")

    def create_dashboard_box(self):
        DashboardLine = self.env['dashboard.settings.line']
        for record in self:
            box_vals = {
                'name': "%s : Count" % (record.name),
                'color': 'primary',
                'visibility': 'pcr_swab',
                'model_id': self.env.ref('account.model_account_move').id,
                'field_id': self.env.ref('account.field_account_move__id').id,
                'type': 'qty',
                'custom_sql': '',
                'custom_sql_alias': '',
                'custom_sql_ids': '',
                'dashboard_id': self.env.ref('medical_dashboard.setting_object').id,
                'action_id': self.env.ref('medical_app.action_move_patient_out_invoice_type').id,
                'filter': "type = 'out_invoice' AND state = 'posted' AND swab_location_id = %s" % (record.id),
                'char_groups': '',
                'apply_create_date_filter': False,
                'date_field_name': 'invoice_date',
                'sequence': record.id,
                'swab_location_id': record.id,
            }
            # if record.dashboard_line_ids:
            #     record.dashboard_line_ids.write(box_vals)
            # else:
            DashboardLine.create(box_vals)

            box_vals = {
                'name': "%s : Amount" % (record.name),
                'color': 'primary',
                'visibility': 'pcr_swab',
                'model_id': self.env.ref('account.model_account_move').id,
                'field_id': self.env.ref('dashboard_data.field_account_move__amount_total_gross').id,
                'type': 'money',
                'custom_sql': '',
                'custom_sql_alias': '',
                'custom_sql_ids': '',
                'dashboard_id': self.env.ref('medical_dashboard.setting_object').id,
                'action_id': self.env.ref('medical_app.action_move_patient_out_invoice_type').id,
                'filter': "type = 'out_invoice' AND state = 'posted' AND swab_location_id = %s" % (record.id),
                'char_groups': '',
                'apply_create_date_filter': False,
                'date_field_name': 'invoice_date',
                'sequence': record.id,
                'swab_location_id': record.id,
            }
            # if record.dashboard_line_ids:
            #     record.dashboard_line_ids.write(box_vals)
            # else:
            DashboardLine.create(box_vals)

    def remove_dashboard_box(self):
        self.dashboard_line_ids.unlink()
