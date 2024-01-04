# coding: utf-8

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class NotifyTriggersInherit(models.Model):
    _inherit = "notif.trigger"

    def _do_sms(self, records):
        self.ensure_one()
        try:
            cr = self.env.cr
            if self.trigger_once:
                sql = "SELECT res_id FROM sms_history WHERE res_id in %s AND notif_trigger_id='%s'"
                cr.execute(sql, (tuple(map(str, records.ids)), self.id))
                found_ids = cr.fetchall()
                if found_ids:
                    records = records.filtered(lambda r: r.id not in set(map(lambda a: int(a[0]), found_ids)))
            for rec in records:
                recipients = self.sudo().get_contact_list(rec)
                wizard = self.env['wizard.sms.send'].create({
                    'config_id': self.sms_config_id.id,
                    'contact_list': recipients.get('numbers'),
                    'keep_sms_history': self.keep_sms_history,
                    'message': self.msg_template_id.render([rec.id])[rec.id],
                    'res_id': rec.id,
                    'language': self.msg_template_id.language,
                    'notif_trigger_id': self.id,
                })
                wizard.send_sms()
        except Exception as e:
            _logger.error("Exception while sending traceback by SMS:\n%s", e)
