from odoo import fields, models, api, _
from odoo.exceptions import UserError


class IssueAvailableQty(models.TransientModel):
    _name = 'issue.available.qty.wiz'
    _description = 'Issue Available Quantity'

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    request_line_ids = fields.Many2many('product.request.line', string="Products", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(IssueAvailableQty, self).default_get(fields_list)
        request = self.env['purchase.request']
        id = self._context.get('active_id')
        request_id = request.browse(id)
        res['request_line_ids'] = [(6, 0, [req.id for req in request_id.order_line_ids if req.available_qty > 0])]
        return res

    def action_issue(self):
        stock_pick = self.env['stock.picking']
        request = self.env['purchase.request']
        active_id = self._context.get('active_id')
        request_id = request.browse(active_id)
        destination_location = self.picking_type_id.default_location_dest_id
        if not destination_location:
            raise UserError(_('Please select destination location in operation type !!!'))
        source_location = self.env.user.company_id.location_id
        if self.picking_type_id:
            picking_vals = {
                'picking_type_id': self.picking_type_id.id,
                'location_id': source_location.id,
                'location_dest_id': destination_location.id,
                'branch_id': request_id.branch_id.id,
                'origin': request_id.name,
                'move_lines': [(0, 0, {
                                'name':  req.product_id.name,
                                'product_id':  req.product_id.id,
                                'product_uom_qty': req.product_qty if req.product_qty <= req.available_qty else req.available_qty,
                                'product_uom':  req.product_id.uom_id.id,
                                'picking_id': self.picking_type_id.id,
                                'location_id': source_location.id,
                                'location_dest_id': destination_location.id,
                                'state': 'draft',
                            }) for req in request_id.order_line_ids.filtered(lambda move: move.available_qty > 0 and not move.is_issued)]}

            picking = stock_pick.create(picking_vals)
            picking.action_confirm()
            picking.action_assign()
            picking.button_validate()
            picking.purchase_request_id = request_id.id
        for req in request_id.order_line_ids.filtered(lambda move: move.available_qty > 0 and not move.is_issued):
            req.product_qty = req.product_qty - req.available_qty if req.available_qty < req.product_qty else req.product_qty
            req.is_issued = True if req.available_qty >= req.product_qty else False
        request_id.is_issued = True

