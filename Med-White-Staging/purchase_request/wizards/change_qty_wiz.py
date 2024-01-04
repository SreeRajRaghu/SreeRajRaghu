from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class ChangeQty(models.TransientModel):
    _name = 'change.qty.wiz'
    _description = 'Change Quantity'

    request_line_ids = fields.Many2many('product.request.line', string="Products")
    reason = fields.Text('Reason')

    @api.model
    def default_get(self, fields_list):
        res = super(ChangeQty, self).default_get(fields_list)
        request = self.env['purchase.request']
        id = self._context.get('active_id')
        request_id = request.browse(id)
        res['request_line_ids'] = [(6, 0, [req.id for req in request_id.order_line_ids])]
        return res

    def action_change(self):
        log_note = ["<span style='color: blue;'>%s</span>" % self.reason]
        request = self.env['purchase.request']
        active_id = self._context.get('active_id')
        request_id = request.browse(active_id)
        for req in request_id.order_line_ids.filtered(lambda line: line.product_qty != line.changed_qty and line.changed_qty):
            log_note.append("<br/>%s - quantity changed from %s to %s" % (req.product_id.name, req.product_qty, req.changed_qty))
            req.product_qty = req.changed_qty
            req.changed_qty = 0
        request_id.message_post(body=log_note, subtype='mt_note')

