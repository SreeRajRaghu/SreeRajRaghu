# -*- coding: utf-8 -*-

from odoo import fields, models


class MedicalPatientAttachment(models.Model):
    _name = 'medical.patient.attachment'
    _description = 'Medical Patient Attachment'

    name = fields.Char(string="Description", required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one('res.partner', string='Patient', required=True)
    attachment_type_id = fields.Many2one('medical.attachment.type', string="Document Type")
    ir_attachment_id = fields.Many2one('ir.attachment', string='Medical Attachment', domain="[('res_model', '=', 'res.partner')]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
