from odoo import fields, models


class SsStudentInherit(models.Model):
    _inherit = 'ss.student'

    daily_line_ids = fields.One2many('student.daily.exam', 'to_profile', string='Daily Exam Lines')


class StudentDailyExam(models.Model):
    _name = 'student.daily.exam'

    to_profile = fields.Many2one('ss.student')
    subject_id = fields.Many2one('ss.subject', 'subject')
    tag = fields.Selection([('Daily Exam', 'Daily Exam'), ('Weekly Exam', 'Weekly Exam')], string='Tag')
    total_mark = fields.Integer('Total Mark')
    date = fields.Date('Date', default=fields.Date.today())
    mark_obtained = fields.Integer('Mark Obtained')
    feed_back = fields.Char('Feedback')
    status = fields.Selection([('present', 'Present'), ('absent', 'Absent')], string='Status')
    faculty_id = fields.Many2one('hr.employee', 'Faculty')