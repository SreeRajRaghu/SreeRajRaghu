from odoo import models, fields, api
from datetime import datetime


class DailyExams(models.Model):
    _name = 'daily.exam'
    _description = 'Daily Examination Module'

    course_id = fields.Many2one('ss.course', 'Course')
    standard_id = fields.Many2one('ss.standard', 'Standard')
    division_id = fields.Many2one('ss.division', 'Division')
    subject_id = fields.Many2one('ss.subject', 'subject')
    faculty_id = fields.Many2one('hr.employee', 'Faculty')
    tag = fields.Selection([('Daily Exam', 'Daily Exam'), ('Weekly Exam', 'Weekly Exam')], string='Tag')
    total_mark = fields.Integer('Total Mark')
    pass_mark = fields.Integer('Pass Mark')
    description = fields.Char('Description')
    date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate'), ('generate', 'Generate')], default='draft')
    student_detail_id = fields.One2many('student.det', 'exam_id', string='Student Details')
    name = fields.Char(string="Name", compute='onchange_exam', store=True)
    code = fields.Char(string="Code", compute='onchange_exam', store=True)

    @api.one
    @api.depends('tag', 'subject_id', 'date')
    def onchange_exam(self):
        today_date = datetime.strptime(str(self.date), '%Y-%m-%d').strftime('%d/%m/%Y')
        if self.tag and self.subject_id:
            self.name = self.tag + '-' + self.subject_id.name + '(' + today_date + ')'
            self.code = self.tag + '-' + self.subject_id.code + '(' + today_date + ')'

    def action_set_draft(self):
        self.state = 'draft'
        for lines in self.student_detail_id:
            lines.unlink()

    @api.multi
    def action_confirm(self):
        for student in self.student_detail_id:
            student_exam_list = [(0, 0, {
                'student_id': student.student_id.name,
                'date': self.date,
                'subject_id': self.subject_id.id,
                'total_mark': self.total_mark,
                'mark_obtained': student.mark_obtained,
                'feed_back': student.feed_back,
                'status': student.status,
                'tag': self.tag,
                'faculty_id': self.faculty_id.id
            })]
            student.student_id.daily_line_ids = student_exam_list
        self.state = 'generate'

    @api.multi
    def action_validate(self):
        stud_list = []
        student_details = []
        stu_list = []
        student_list = self.env['ss.student'].search(
            [('course_id', '=', self.course_id.id), ('standard_id', '=', self.standard_id.id),
             ('division_id', '=', self.division_id.id), ('course_id', '=', self.course_id.id),
             ('academic_status', '=', 'Active'), ('id', 'not in', self.student_detail_id.mapped('student_id').ids)])
        if self.subject_id.is_elective:
            for stud in student_list:
                for sub in stud.elective_subject_ids:
                    if self.subject_id.id == sub.id:
                        stud_list.append(stud)
            student_all = stud_list
        else:
            student_all = student_list
        for student in student_all:
            stu_list.append(student)
            student_details.append((0, 0, {'exam_id': self.id, 'student_id': student.id,
                                           'admission_no': student.admission_no, 'status': 'present'}))
        self.student_detail_id = student_details
        self.state = 'validate'
        return {'status': "Success"}

    def get_exam_details_for_faculty(self):
        exams = self.env['daily.exam'].search([('faculty_id', '=', self.id)])
        return [{'id': exam.id,
                 'name': exam.name,
                 'course_id': exam.course_id.name,
                 'standard_id': exam.standard_id.name,
                 'division_id': exam.division_id.name,
                 'subject_id': exam.subject_id.name,
                 'faculty_id': exam.faculty_id.name,
                 'tag': exam.tag,
                 'total_mark': exam.total_mark,
                 'description': exam.description,
                 'pass_mark': exam.pass_mark,
                 'state': exam.state,
                 'date': exam.date,
                 'student_details': [{
                     'exam_line_id': stud.id,
                     'student_id': stud.student_id.id,
                     'student_name': stud.student_id.name,
                     'admission_no': stud.admission_no,
                     'status': stud.status,
                     'mark_obtained': stud.mark_obtained,
                     'feed_back': stud.feed_back} for stud in exam.student_detail_id]
                 } for exam in exams]

    @api.model
    def create(self, vals):
        res = super(DailyExams, self).create(vals)
        res.action_validate()
        return res

    @api.model
    def create_daily_exams(self, vals):
        self.create({
            'course_id': vals['course_id'],
            'standard_id': vals['standard_id'],
            'division_id': vals['division_id'],
            'subject_id': vals['subject_id'],
            'faculty_id': vals['faculty_id'],
            'tag': vals['tag'],
            'total_mark': vals['total_mark'],
            'pass_mark': vals['pass_mark'],
            'description': vals['description'],
            'date': vals['date']
                  })
        return {'state': "Success"}

    def write_exam_mark(self, vals):
        for res in vals[0]['student_details']:
            line = self.env['student.det'].browse(res['exam_line_id'])
            line.write({
                "status": res['status'],
                "mark_obtained": res['mark_obtained'],
                "feed_back": res['feed_back'],
            })
            self.state = 'generate'
        return "success"


class ExamDetails(models.Model):
    _name = 'student.det'
    _description = 'Daily exam Student lines'

    exam_id = fields.Many2one('daily.exam', string='Exam')
    student_id = fields.Many2one('ss.student', string='Student')
    admission_no = fields.Integer('Admission Number')
    course_id = fields.Many2one('ss.course', related='student_id.course_id', string='Course')
    standard_id = fields.Many2one('ss.standard', related='student_id.standard_id', string='Standard')
    division_id = fields.Many2one('ss.division', related='student_id.division_id', string='Division')
    mark_obtained = fields.Integer('Mark Obtained')
    feed_back = fields.Char('Feedback')
    status = fields.Selection([('present', 'Present'), ('absent', 'Absent')], string='Status')

    def student_result(self):
        student = self.env['student.det'].search([('student_id', '=', self.id)])
        values = [{'exam_id': stud.id,
                   'student_id': stud.student_id.id,
                   'student_name': stud.student_id.name,
                   'exam_name': stud.exam_id.name,
                   'admission_no': stud.admission_no,
                   'subject_id': stud.exam_id.subject_id.id,
                   'subject_name': stud.exam_id.subject_id.name,
                   'faculty_id': stud.exam_id.faculty_id.id,
                   'faculty_name': stud.exam_id.faculty_id.name,
                   'tag': stud.exam_id.tag,
                   'total_mark': stud.exam_id.total_mark,
                   'pass_mark': stud.exam_id.pass_mark,
                   'date': stud.exam_id.date,
                   'description': stud.exam_id.description,
                   'status': stud.status,
                   'mark_obtained': stud.mark_obtained,
                   'feed_back': stud.feed_back,
                   } for stud in student if stud.exam_id.state == 'generate']
        return values
