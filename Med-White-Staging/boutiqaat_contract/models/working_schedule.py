# -*- coding: utf-8 -*-

from pytz import timezone

from odoo import fields, models
from odoo.addons.resource.models.resource import datetime_to_string
from odoo.addons.resource.models.resource import string_to_datetime
from odoo.addons.resource.models.resource import Intervals


class WorkingSchedule(models.Model):
    _inherit = "resource.calendar"

    rot_rate = fields.Float("Regular Overtime Rate", default=1)
    wot_rate = fields.Float("Week Off Overtime Rate", default=1)
    pot_rate = fields.Float("Public Holiday Overtime Rate", default=1)
    week_days = fields.Float('Week Days')

    def _leave_intervals(self, start_dt, end_dt, resource=None, domain=None, tz=None):
        """ Return the leave intervals in the given datetime range.
            The returned intervals are expressed in specified tz or in the calendar's timezone.
        """
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()

        # for the computation, express all datetimes in UTC
        if self.env.context.get('global_only'):
            resource_ids = [False]
        else:
            resource_ids = [resource.id, False] if resource else [False]

        if domain is None:
            domain = [('time_type', '=', 'leave')]
        domain = domain + [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('date_from', '<=', datetime_to_string(end_dt)),
            ('date_to', '>=', datetime_to_string(start_dt)),
        ]

        # retrieve leave intervals in (start_dt, end_dt)
        tz = tz if tz else timezone((resource or self).tz)
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)
        result = []
        for leave in self.env['resource.calendar.leaves'].search(domain):
            dt0 = string_to_datetime(leave.date_from).astimezone(tz)
            dt1 = string_to_datetime(leave.date_to).astimezone(tz)
            result.append((max(start_dt, dt0), min(end_dt, dt1), leave))

        return Intervals(result)
