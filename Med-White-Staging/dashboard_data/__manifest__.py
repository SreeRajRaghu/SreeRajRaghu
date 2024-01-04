{
    'name': 'Med-White Dashboard Data',
    'version': '13.2',
    'category': '',
    'sequence': 10,
    'summary': 'Dashboard Data',
    'author': 'Sismatix',
    'website': 'sismatix.com',
    'depends': [
        'medical_dashboard', "account_invoice_fixed_discount", "account", "medical_pcr"
    ],
    'description': "",
    'data': [
        'views/menu.xml',
        'views/resource_views.xml',

        # Don't change
        'data/dashboard_line_xml.xml',
        'data/dashboard_lab_req_dept_data.xml',
        'data/resource_data.xml',
        'data/radiology_data.xml',
        'data/pcr_data.xml',
        'data/derma_lines.xml',
    ],
}
