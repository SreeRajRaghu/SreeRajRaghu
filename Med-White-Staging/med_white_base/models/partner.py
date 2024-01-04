# -*- coding: utf-8 -*-

from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _clean_website(self, website):
        return website
