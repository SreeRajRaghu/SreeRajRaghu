# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MultiOrder(models.Model):
    _name = 'medical.multi.order'
    _description = 'Multi Appointments'
    _order = "create_date desc"
