# -*- coding: utf-8 -*-

from odoo import fields, models


class AttendanceUploadLog(models.Model):
    _name = 'att.upload.log'
    _description = "Attendance Upload Log"
    _order = "create_date desc"

    name = fields.Char("File Name")
    file = fields.Binary("File")
    skipped_count = fields.Integer("Skipped Lines")
    skipped_text = fields.Text("Skipped Text")
    ignored_count = fields.Integer("Ignored Lines")
    ignored_text = fields.Text("Ignored Text")
    no_emp_count = fields.Integer("Employee Not Found Lines")
    no_emp_text = fields.Text("Employee Not Found Text")

    attendance_ids = fields.One2many("hr.attendance", "att_log_id", string="Attendances")
    attendance_count = fields.Integer("Total Uploaded Attendance", compute="_compute_attendance_count")

    def _compute_attendance_count(self):
        for rec in self:
            rec.attendance_count = len(rec.attendance_ids.ids)
