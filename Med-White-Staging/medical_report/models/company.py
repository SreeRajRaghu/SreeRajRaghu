# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    med_cell_header_img = fields.Binary("Med Cell Header Image")
    report_qr_code = fields.Binary("QR Code")
