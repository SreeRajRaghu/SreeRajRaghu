from odoo import models, fields


class ResCompanyInherit(models.Model):

    _inherit = 'res.company'

    location_id = fields.Many2one('stock.location', string='Main Store')


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    location_id = fields.Many2one('stock.location', readonly=False, related='company_id.location_id', string="Main Store")
