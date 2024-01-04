# -*- coding: utf-8 -*-

import xlrd
import base64
from datetime import datetime
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)
company_id = 2


class ImportEmployeeWizard(models.TransientModel):
    _name = 'import.employee.wizard'
    _description = 'Employee Wizard'

    file = fields.Binary('File')
    name = fields.Char('File Name')

    def import_data(self):
        self.ensure_one()
        Employee = self.env['hr.employee']
        Department = self.env['hr.department']
        Job = self.env['hr.job']
        Section = self.env['hr.section']

        wb = xlrd.open_workbook(file_contents=base64.decodestring(self.file))
        sheet_names = wb.sheet_names()

        if 'Employee' in sheet_names:
            sheet = wb.sheet_by_name('Employee')
            for r in range(1, sheet.nrows):
                data = sheet.row_values(r)
                print ("Employee :: ", data[:35])

                if not any(data[:5]):
                    continue

                name = str(data[1]).strip()
                print ("name::::::", name)
                identification_id = str(data[0]).strip()
                emp = Employee.search([
                    ('identification_id', '=', identification_id),
                    ('name', '=', name)], limit=1)
                if emp:
                    print ('___ Skipped Employee: ', emp)
                    continue
                print ("identification_id::::::", identification_id)
                arabic_name = data[2]
                print ("arabic_name::", arabic_name)
                work_address = data[3]

                print ("work_address:::::", work_address)
                work_location = data[4]
                print ("work_location::::::", work_location)
                work_email = data[5]
                print ("work_email:::", work_email)
                mobile_phone = data[6]
                if mobile_phone:
                    if '/' in str(mobile_phone):
                        aa = str(mobile_phone).split('.')
                        mobile_phone = str(aa[0])
                    elif '-' in str(mobile_phone) or '+' in str(mobile_phone) or ' ' in str(mobile_phone):
                        aa = str(mobile_phone).split('.')
                        mobile_phone = str(aa[0])
                    else:
                        if mobile_phone != '-':
                            mobile_phone = str(mobile_phone).split('.')[0]
                        else:
                            mobile_phone = '-'

                work_phone = ''
                if data[7]:
                    work_phone_str = str(data[7]).split('.')
                    work_phone = work_phone_str[0]
                    print ("work_phone:::::", work_phone)

                department = data[8]
                print ("department:::::", department)
                department_id = Department.search([('name', '=', department)], limit=1)
                if not department_id:
                    department_id = Department.create({'name': department})

                section = data[9]
                print ("section:::::", section)
                section_id = Section.search([('name', '=', section)], limit=1)
                if not section_id:
                    section_id = Section.create({'name': section})

                position = data[10]
                print ("position::::::", position)
                position_id = Job.search([('name', '=', position)], limit=1)
                if not position_id:
                    position_id = Job.create({
                        'name': position
                    })

                manager1 = data[11]
                print ("manager1:::", manager1)

                manager2 = data[12]
                print ("manager2::::::", manager2)

                tz = str(data[13])
                print ("tx:::::::", tz)
                counry = data[14]
                country_id = self.env['res.country'].search([('name', '=', counry)], limit=1)
                if not country_id:
                    country_id = self.env['res.country'].create({
                        'name': counry
                    })

                passport_id = data[15]
                print ("passport::::::::::", passport_id)

                bank_account_id = str(data[16]).strip()

                gender_type = data[17]
                if gender_type == 'Male':
                    gender = 'male'
                else:
                    gender = 'female'
                print ("gender::::", gender)

                martial_type = data[18]
                martial = 'married'
                if martial_type == 'Single':
                    martial = 'single'

                print ("martial:::::", martial)
                children = data[19]

                print ("child:::::::::::er", children)

                private_address = str(data[20]).strip()

                emergency_contact = data[21]
                print ("emergency_contact::", emergency_contact)
                emergency_phone = ''
                if data[22]:
                    phone = str(data[22])
                    if '/' in str(phone):
                        aa = str(phone).split('.')
                        emergency_phone = str(aa[0])
                    elif '-' in str(phone) or '+' in str(phone) or ' ' in str(phone):
                        aa = str(phone).split('.')
                        emergency_phone = str(aa[0])
                    else:
                        if phone != '-':
                            emergency_phone = str(phone).split('.')[0]
                        else:
                            emergency_phone = '-'

                print ("emergency_phone:::::", emergency_phone)

                birth_date = data[23] or False
                print ("birth_date::::::", birth_date)
                if birth_date:
                    # birth_date = datetime.strptime(birth_date, "%d/%m/%Y").strftime('%Y-%m-%d')
                    if isinstance(birth_date, float):
                        year, month, day, hour, minute, second = xlrd.xldate_as_tuple(birth_date, wb.datemode)
                        birth_date = datetime(year, month, day)
                    else:
                        print ("birth_date::::", birth_date)
                        birth_date = datetime.strptime(birth_date, "%d/%m/%Y").strftime('%Y-%m-%d')
                        print ("birth_date::::::::", birth_date)

                place_of_birth = str(data[24])
                print ("place_of_birth:::", place_of_birth)
                place_of_birth_id = self.env['res.country'].search([('name', '=', place_of_birth)], limit=1)
                if not place_of_birth_id:
                    place_of_birth_id = self.env['res.country'].create({
                        'name': place_of_birth
                    })

                country_of_birth = data[25]
                print ("country_of_birth::::", country_of_birth)
                country_of_birth_id = self.env['res.country'].search([('name', '=', country_of_birth)], limit=1)
                if not country_of_birth_id:
                    country_of_birth_id = self.env['res.country'].create({
                        'name': place_of_birth
                    })

                visa_no = ''
                if data[26]:
                    _visa_no = data[26]
                    if isinstance(_visa_no, str):
                        visa_no = str(_visa_no)
                    else:
                        visa_no = str(int(_visa_no))
                    print ("visa_no:::::", visa_no)

                permit_no = ''
                if data[27]:
                    _no = data[27]
                    if isinstance(_no, str):
                        permit_no = str(_no)
                    else:
                        permit_no = str(int(_no))
                    print ("per:::::", permit_no)

                visa_expire_date = False
                if data[28]:
                    visa_expire = data[28]
                    if isinstance(visa_expire, float):
                        year, month, day, hour, minute, second = xlrd.xldate_as_tuple(visa_expire, wb.datemode)
                        visa_expire_date = datetime(year, month, day)
                    else:
                        print ("visa_expire::::", visa_expire)

                        visa_expire_date = datetime.strptime(visa_expire, "%d/%m/%Y").strftime('%Y-%m-%d')
                        print ("visa_expire_date::::::::", visa_expire_date)

                certificate = data[29]
                print ("certificate:::::", certificate)
                study_field = data[30]
                print ("study_field::::", study_field)
                study_school = data[31]
                print ("study_school", study_school)
                company_assets = data[32]

                if name:
                    vals = {
                        'identification_id': identification_id,
                        'name': str(name).strip(),
                        'arabic_name': str(arabic_name).strip(),
                        'work_address': work_address,
                        'work_location': work_location,
                        'work_email': work_email,
                        'work_phone': work_phone,
                        'mobile_phone': mobile_phone,
                        'department_id': department_id.id,
                        'section_id': section_id.id,
                        'job_id': position_id.id,
                        'tz': tz,
                        'country_id': country_id.id,
                        'passport_id': passport_id,
                        'bank_number': bank_account_id,
                        'gender': gender,
                        'marital': martial,
                        'children': children,
                        'private_address': private_address,
                        'emergency_contact': str(emergency_contact).strip(),
                        'emergency_phone': emergency_phone,
                        'birthday': birth_date,
                        'place_of_birth': place_of_birth,
                        'country_of_birth': country_of_birth_id.id,
                        'visa_no': visa_no,
                        'permit_no': permit_no,
                        'visa_expire': visa_expire_date,
                        'certificate_level': str(certificate),
                        'study_field': str(study_field),
                        'study_school': str(study_school),
                        'company_assets': company_assets,
                    }
                    # print ("vals:::::")
                    # from pprint import pprint
                    print('__________ vals : ', vals)
                    # pprint(vals)
                    # import pdb
                    # pdb.set_trace()
                    Employee.create(vals)

            # Assign Line Manager 1, Line Manager 2
            for r in range(1, sheet.nrows):
                data = sheet.row_values(r)
                if not any(data[:5]):
                    continue

                employee = Employee.search([('name', '=', data[1])], limit=1)
                if employee:
                    first = Employee.search([('name', '=', data[11])], limit=1)
                    second = Employee.search([('name', '=', data[12])], limit=1)
                    print ('___ Assign Manager : ', data[1], data[11], data[12], first, second)

                    employee.write({
                        'parent_id': first.id,
                        'coach_id': second.id,
                    })
        else:
            _logger.warning("__ 'Employee' Sheet Not Found")
        # Department
        if 'Department' in sheet_names:
            sheet = wb.sheet_by_name('Department')
            for r in range(1, sheet.nrows):
                data = sheet.row_values(r)
                if not any(data[:3]):
                    continue
                print ("Department : ", data[:3])

                dept = Department.search([('name', '=', str(data[0]).strip())], limit=1)
                parent_dept = Department.search([('name', '=', str(data[1]).strip())], limit=1)
                manager = Employee.search([('name', '=', str(data[2]).strip())], limit=1)
                if dept and (parent_dept or manager):
                    if dept.id != parent_dept.id:
                        dept.write({
                            'manager_id': manager.id,
                            'parent_id': parent_dept.id,
                        })
        else:
            _logger.warning("__ 'Department' Sheet Not Found")
        # Job Position
        if 'Job Position' in sheet_names:
            sheet = wb.sheet_by_name('Job Position')
            for r in range(1, sheet.nrows):
                data = sheet.row_values(r)
                if not any(data[:3]):
                    continue
                print ("Position : ", data[:3])

                position = Job.search([('name', '=', str(data[0]).strip())], limit=1)
                dept = Department.search([('name', '=', str(data[1]).strip())], limit=1)
                # manager = Employee.search([('name', '=', str(data[2]).strip())], limit=1)
                if position and dept:
                    position.write({
                        'department_id': dept.id,
                    })
        else:
            _logger.warning("__ 'Job Position' Sheet Not Found")
        return {'type': 'ir.actions.act_window_close'}
