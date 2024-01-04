# -*- coding: utf-8 -*-

from odoo import api, models


class Card(models.Model):
    _inherit = 'insurance.card'

    @api.model
    def create_from_medical_ui(self, vals):
        ins_id = vals.pop('id', False)
        insurance_data = []
        if ins_id:
            card = self.browse(ins_id)
            card.write(vals)
        else:
            card = self.create(vals)
        insurance_data = card.read()
        return insurance_data and insurance_data[0] or {}

    def check_insurance_wrapper(self, line_by_products):
        print ('_ self.ins_based_on : ', self.ins_based_on)
        if self.ins_based_on == 'total':
            return self.check_insurance_total(line_by_products)
        else:
            return self.check_insurance(line_by_products)
