{
'name':'Applicant tracking system',
'description':'Extension of the recrutment module to track cv on databese. There were made some improvements of this module, some fields were modified, some extra functionalities are added',
'author':'Simplify-ERP®',
'category':'recruitment',
'summary':'This module allows the applicants to update the CV they have uploaded without having an access to the erp-simplify',
'images':"static/src/img/recycling-symbol-icon-twotone-light-green.png",
'depends':['base', 'hr_recruitment', 'mail', 'website', 'website_form', 'website_partner'],
'data':['views/form_view.xml',
        'views/send_buttons.xml',
        'reports/applicantCV.xml', 'reports/report_template.xml', 'reports/anonymousCV.xml', 'mails/updateCV.xml',
        'mails/suggestCV.xml', 'mails/suggestCV_anonymous.xml', 'views/updateCV.xml', 'views/settings.xml',
        'security/ir.model.access.csv',
        # 'data/automation.xml',
        # 'views/actions.xml',
        'mails/updateCV_first_time.xml',
        ]
 }
