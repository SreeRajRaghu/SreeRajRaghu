# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Picking(models.Model):
    _inherit = 'stock.picking'

    return_picking_id = fields.Many2one('stock.picking', string='Return Picking', tracking=True)
    medical_order_id = fields.Many2one('medical.order', string="Medical Order", tracking=True)
    is_med_returned = fields.Boolean("Is Medical Returned", tracking=True)


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')


class Move(models.Model):
    _inherit = 'stock.move'

    medical_order_line_id = fields.Many2one('medical.order.line', string="Medical Order Line")

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        result = super(Move, self)._generate_valuation_lines_data(
            partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)

        picking_type_id = self.picking_id and self.picking_id.picking_type_id
        if result.get('credit_line_vals') and picking_type_id:
            result['credit_line_vals'].update({
                'analytic_account_id': picking_type_id.analytic_account_id.id,
                'analytic_tag_ids': picking_type_id.analytic_tag_ids.ids,
            })

        if result.get('debit_line_vals') and picking_type_id:
            result['debit_line_vals'].update({
                'analytic_account_id': picking_type_id.analytic_account_id.id,
                'analytic_tag_ids': picking_type_id.analytic_tag_ids.ids,
            })

        if result.get('price_diff_line_vals') and picking_type_id:
            result['price_diff_line_vals'].update({
                'analytic_account_id': picking_type_id.analytic_account_id.id,
                'analytic_tag_ids': picking_type_id.analytic_tag_ids.ids,
            })
        return result


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    medical_type_id = fields.Many2one('stock.picking.type', string="Operation Type")

    def _get_sequence_values(self):
        sequence_values = super(Warehouse, self)._get_sequence_values()
        sequence_values.update({
            'medical_type_id': {
                'name': self.name + ' ' + _('Picking Appointment'),
                'prefix': self.code + '/APP/',
                'padding': 5,
                'company_id': self.company_id.id,
            }
        })
        return sequence_values

    def _get_picking_type_update_values(self):
        picking_type_update_values = super(Warehouse, self)._get_picking_type_update_values()
        picking_type_update_values.update({
            'medical_type_id': {'default_location_src_id': self.lot_stock_id.id}
        })
        return picking_type_update_values

    def _get_picking_type_create_values(self, max_sequence):
        picking_type_create_values, max_sequence = super(Warehouse, self)._get_picking_type_create_values(max_sequence)
        picking_type_create_values.update({
            'medical_type_id': {
                'name': _('Appointment Orders'),
                'code': 'outgoing',
                'default_location_src_id': self.lot_stock_id.id,
                'default_location_dest_id': self.env.ref('stock.stock_location_customers').id,
                'sequence': max_sequence + 1,
                'sequence_code': 'MED',
                'company_id': self.company_id.id,
            }
        })
        return picking_type_create_values, max_sequence + 2

    @api.model
    def _create_missing_medical_picking_types(self):
        warehouses = self.env['stock.warehouse'].search([('medical_type_id', '=', False)])
        for warehouse in warehouses:
            new_vals = warehouse._create_or_update_sequences_and_picking_types()
            warehouse.write(new_vals)
