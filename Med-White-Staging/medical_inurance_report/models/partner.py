# -*- coding: utf-8 -*-

from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    ins_report_format = fields.Selection([
        ('al_ahleia_ins', 'Al-Ahleia Ins'),  # On Invoice
        ('metlife_alico', 'METLIFE (Alico)'),  # On Line
        ('national_takaful', 'National Takaful'),  # On Invoice
        ('mednet', 'Mednet'),  # On Invoice
        ('gulf_takaful', 'Gulf Takaful'),  # On Invoice
        ('bahrain_kuwait_insurance', 'BAHRAIN KUWAIT INSURANCE'),  # On Invoice
        ('kuwait_ins', 'Kuwait Ins.'),  # On Invoice
        ('gig', 'GIG'),  # On Invoice
        ('wapmed', 'WAPMED'),  # On Invoice
        ('globemed', 'GlobeMed'),  # On Line
        ('nas', 'NAS'),  # On Invoice
        ('saudi_arabian_ins_co_saico', 'Saudi Arabian Ins. Co. (SAICO)'),  # On Line
    ], string="Insurance Report Format")

    report_commercial_disc = fields.Float("Report Commercial Discount", default=15)
    report_service_fees = fields.Float(string="Report Service Fees", default=2)
