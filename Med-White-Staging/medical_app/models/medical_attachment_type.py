# -*- coding: utf-8 -*-

from odoo import fields, models


class MedicalAttachmentType(models.Model):
    _name = 'medical.attachment.type'
    _description = 'Medical Attachment Type'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    attachment_type = fields.Selection([
        ('civilId', 'CivilId'),
        ('passport', 'Passport'),
        ('other', 'Other'),
    ], required=True, default='civilId')
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
