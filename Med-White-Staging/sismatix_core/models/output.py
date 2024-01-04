# -*- coding:utf-8 -*-

from odoo import fields, models


class ModelOutput(models.TransientModel):
    _name = 'model.output'
    _description = 'Excel Report Output'

    name = fields.Char('File Name', size=256, readonly=True)
    filename = fields.Binary('File to Download', readonly=True)
    extension = fields.Char('Extension', default='xls')

    def download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/filename/%s.%s?download=true' % (
                self._name, self.id, self.name, self.extension),
            'target': 'new'
        }
