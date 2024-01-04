# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    @api.model
    def _default_patient_seq_id(self):
        return self.env.ref('medical_app.seq_patient_file_sequence', raise_if_not_found=False)

    @api.model
    def _default_employee_seq_id(self):
        return self.env.ref('medical_app.employee_id_sequence', raise_if_not_found=False)

    logo2 = fields.Binary("Header ")
    img_footer = fields.Binary("Footer Image")

    cash_header_img = fields.Binary("Cash Invoice Header")
    cash_footer_img = fields.Binary("Cash Invoice Footer")
    invoice_patient_header_img = fields.Binary("Insurance Invoice Patient Header")
    invoice_patient_footer_img = fields.Binary("Insurance Invoice Patient Footer")
    invoice_company_header_img = fields.Binary("Insurance Invoice Company Header")
    invoice_company_footer_img = fields.Binary("Insurance Invoice Company Footer")

    # invoice_img = fields.Binary("Invoice Header Image")
    # invoice_footer_image = fields.Binary("Invoice Footer Image")

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code')

    auto_patient_sequence = fields.Selection([
        ('automatic', 'Automatic'),
        ('manual', 'Manual (on request)')],
        string='Auto Patient File Sequence',
        default='manual')
    patient_seq_id = fields.Many2one("ir.sequence", string="Patient File Sequence", default=_default_patient_seq_id)
    employee_seq_id = fields.Many2one("ir.sequence", string="Employee Sequence", default=_default_employee_seq_id)

    auto_derma_sequence = fields.Selection([
        ('automatic', 'Automatic'),
        ('manual', 'Manual (on request)')],
        string='Auto Derma File Sequence',
        default='manual')
    derma_seq_id = fields.Many2one("ir.sequence", string="Derma File Sequence")

    depends_on = fields.Selection([
        ('file_no', 'File No'), ('file_no2', 'Derma File No')], default="file_no",
        string="Depends on File No")

    # Always set some default value for these kind of restricting fields.
    max_apmt_no_show = fields.Integer("Warn after Max. reach No Show", default=15)
    max_apmt_cancel = fields.Integer("Warn after Max. reach Cancellation", default=15)

    @api.model
    def create(self, vals):
        record = super(Company, self).create(vals)
        self.env['ir.sequence'].create({
            'name': 'Medical Session for %s' % record.name,
            'prefix': 'SESSION/%(year)s/%(month)s/',
            'code': 'medical.session',
            'company_id': record.id,
            'padding': 5,
        })
        return record
