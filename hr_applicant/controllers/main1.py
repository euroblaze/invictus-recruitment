# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
import pytz
from babel.dates import format_datetime, format_date
from odoo.addons.portal.controllers.portal import CustomerPortal
from werkzeug.urls import url_encode

from odoo import http, _, fields
from odoo.http import request
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.tools.misc import get_lang
import logging
from odoo.addons.http_routing.models.ir_http import slug
import requests

_logger = logging.getLogger(__name__)


class PortalApplicant(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'cv_count' in counters:
            uid = http.request.env.context.get('uid')
            user = http.request.env['res.users'].sudo().browse(uid)
            cv_count = len(user.applicant_cv_ids)
            values['cv_count'] = cv_count
            events = http.request.env['calendar.event'].search([('user_id', '=', user.id)])
            values['scheduled_count'] = len(events)

        return values


class WebsiteHrRecruitment(http.Controller):

    @http.route([
        '/profiles',
        '/profiles?',
        '''/profiles/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def profiles(self, **kwargs):
        _logger.info(kwargs)
        number_of_results = 100
        uid = http.request.env.context.get('uid')
        user = http.request.env['res.users'].sudo().browse(uid)
        if 'technology' in kwargs:
            request.session['technology'] = kwargs['technology']
            search_applicants = request.env['hr.applicant'].sudo() \
                .search(['|', ('categ_ids.name', 'ilike', kwargs['technology']),
                         ('key_skills', 'ilike', kwargs['technology']), '|', ('active', '=', True),
                         ('active', '=', False)]) \
                .sorted(lambda r: r.years_of_experience, reverse=True)
            number_of_results = len(search_applicants)
            placeholder = kwargs['technology']
        else:
            request.session['technology'] = 0
            search_applicants = request.env['hr.applicant'].sudo().search(
                ['|', ('active', '=', True), ('active', '=', False)], limit=number_of_results) \
                .sorted(lambda r: r.years_of_experience, reverse=True)
            count = request.env['hr.applicant'].sudo().search_count([])
            placeholder = f"Search {count} number of profiles"
        for applicant in search_applicants:
            if isinstance(applicant.partner_name, str) and applicant.partner_name.split(" ")[0] in applicant.name:
                position = applicant.name.find(applicant.partner_name.split(" ")[0])
                applicant.name = applicant.name[:position]
        applicants = search_applicants
        return request.render('hr_applicant.profiles', {
            'applicants': applicants,
            'number': number_of_results,
            'placeholder_value': placeholder,
            'user': user,
        })

    @http.route('''/profile/<model("hr.applicant"):applicant>''', type='http', auth="public", website=True)
    def profile_detail(self, applicant, **kw):
        uid = http.request.env.context.get('uid')
        user = http.request.env['res.users'].sudo().browse(uid)
        status = False
        if 'section' in kw:
            rcs = request.env['requested.changes'].sudo().search(
                [('recruiter', '=', user.id), ('applicant', '=', applicant.id)])
            messages = {
                'summary': 'Please update your Summary,check it <a href="' + applicant.sudo().get_url() + '?update= summary' +
                           kw['section'] + '#' + kw['section'] + '">here</a>',
                'project': 'Please update your Projects,check it <a href="' + applicant.sudo().get_url() + '?update= project' +
                           kw['section'] + '#' + kw['section'] + '">here</a>',
                'education': 'Please update your Education,check it <a href="' + applicant.sudo().get_url() + '?update= education' +
                             kw['section'] + '#' + kw['section'] + '">here</a>',
                'technical': 'Please update your Technical Skills,check it <a href="' + applicant.sudo().get_url() + '?update= technical' +
                             kw['section'] + '#' + kw['section'] + '">here</a>',
                'certificates': 'Please update your Certificates,check it <a href="' + applicant.sudo().get_url() + '?update= certificates' +
                                kw['section'] + '#' + kw['section'] + '">here</a>',
                'all_sections': 'Please update your CV,check it <a href="' + applicant.sudo().get_url() + '?update= all_sections' +
                                kw['section'] + '#' + kw['section'] + '">here</a>',

            }

            if kw['section'] in messages:
                for rc in rcs:
                    vals = {
                        'subject': 'Update your Cv on Invictus',
                        'body_html': messages[kw['section']],

                        'email_to': applicant.email_from,
                        'auto_delete': False,
                        'email_from': rc.recruiter.partner_id.email,
                    }

                    mail_id = request.env['mail.mail'].sudo().create(vals)
                    mail_id.sudo().send()

            status = True

            if not rcs:
                rcs.sudo().create({
                    'recruiter': user.id,
                    'applicant': applicant.id
                })
            if not applicant.date_cv_request:
                applicant.sudo().send_update_mail()
                applicant.sudo().write({
                    'date_cv_request': datetime.now() + timedelta(days=2),
                    'max_reminders': 5,
                })

        tech = 0
        if 'technology' in request.session:
            tech = request.session['technology']
            next_applicant = request.env['hr.applicant'].sudo().search(
                ['&', ('id', '>', applicant.id), '|', ('categ_ids.name', 'ilike', tech), ('key_skills', 'ilike', tech)],
                order="id asc", limit=1)
            previous_applicant = request.env['hr.applicant'].sudo().search(
                ['&', ('id', '<', applicant.id), '|', ('categ_ids.name', 'ilike', tech), ('key_skills', 'ilike', tech)],
                order="id desc",
                limit=1)
        else:
            next_applicant = request.env['hr.applicant'].sudo().search([('id', '>', applicant.id)], order="id asc",
                                                                       limit=1)
            previous_applicant = request.env['hr.applicant'].sudo().search([('id', '<', applicant.id)], order="id desc",
                                                                           limit=1)

        if applicant.key_skills:
            key_skills = applicant.key_skills.split(',')
        else:
            key_skills = None

        return request.render("hr_applicant.detail", {
            'applicant': applicant,
            'nav_filter': tech,
            'next_applicant': next_applicant,
            'previous_applicant': previous_applicant,
            'key': key_skills,
            'is_internal_user': request.env.user.has_group('base.group_user'),
            'status': status,
        })

    @http.route('''/<model("hr.applicant"):applicant>''', type='http', auth="user", website=True)
    def open_applicant(self, applicant):
        _logger.info('HERE HERE HERE')
        return request.redirect(f'web#id={applicant.id}'
                                f'&action=364&model=hr.applicant&view_type=form&cids=1&menu_id=261')

    @http.route('''/mail/<model("hr.applicant"):applicant>''', type='http', auth="public", website=True)
    def mail_send(self, applicant, **kwargs):
        uid = http.request.env.context.get('uid')
        user = http.request.env['res.users'].sudo().browse(uid)
        if 'email' in kwargs:
            template_id = request.env.ref('applicant_tracking_system.mail_suggest_anonymous').id
            template = request.env['mail.template'].sudo().browse(template_id)
            template.email_to = kwargs['email']
            template.send_mail(applicant.id, force_send=True)
            user.write({'applicant_cv_ids': [(4, applicant.id, False)]})
            lead = request.env['crm.lead'].sudo().search([('email_from', '=', kwargs['email'])])
            if not lead:
                crm_lead = {
                    'name': applicant.partner_name,
                    'email_from': kwargs['email'],
                    'contact_name': kwargs['name'],
                    'phone': kwargs['phone_number'],
                    'partner_name': kwargs['company_name'],
                }
                request.env['crm.lead'].sudo().create(crm_lead)
            return request.render("hr_applicant.detail", {
                'applicant': applicant,
            })
        else:
            return request.render("hr_applicant.mail", {
                'applicant': applicant,
                'user': user,
            })

    @http.route([
        '/calendar',
        '/calendar/<model("hr.applicant"):applicant>',
        '/calendar/<model("calendar.appointment.type"):appointment_type>',
    ], type='http', auth="public", website=True, sitemap=True)
    def calendar_appointment_choice(self, appointment_type=None, employee_id=None, message=None, **kwargs):
        if not appointment_type:
            country_code = request.session.geoip and request.session.geoip.get('country_code')
            if country_code:
                suggested_appointment_types = request.env['calendar.appointment.type'].sudo().search([
                    '|', ('country_ids', '=', False),
                    ('country_ids.code', 'in', [country_code])])
            else:
                suggested_appointment_types = request.env['calendar.appointment.type'].sudo().search([])
            if not suggested_appointment_types:
                return request.render("website_calendar.setup", {})
            appointment_type = suggested_appointment_types[0]
        else:
            suggested_appointment_types = appointment_type
        suggested_employees = []
        if employee_id and int(employee_id) in appointment_type.sudo().employee_ids.ids:
            suggested_employees = request.env['hr.employee'].sudo().browse(int(employee_id)).name_get()
        elif appointment_type.assignation_method == 'chosen':
            suggested_employees = appointment_type.sudo().employee_ids.name_get()
        return request.render("website_calendar.index", {
            'appointment_type': appointment_type,
            'suggested_appointment_types': suggested_appointment_types,
            'message': message,
            'selected_employee_id': employee_id and int(employee_id),
            'suggested_employees': suggested_employees,
        })

    @http.route(['/calendar/get_appointment_info'], type='json', auth="public", methods=['POST'], website=True)
    def get_appointment_info(self, appointment_id, prev_emp=False, **kwargs):
        appt = request.env['calendar.appointment.type'].sudo().browse(int(appointment_id)).sudo()
        result = {
            'message_intro': appt.message_intro,
            'assignation_method': appt.assignation_method,
        }
        if result['assignation_method'] == 'chosen':
            selection_template = request.env.ref('website_calendar.employee_select')
            result['employee_selection_html'] = selection_template._render({
                'appointment_type': appt,
                'suggested_employees': appt.employee_ids.name_get(),
                'selected_employee_id': prev_emp and int(prev_emp),
            })
        return result

    @http.route(['/calendar/<model("calendar.appointment.type"):appointment_type>/appointment',
                 '/calendar/<model("hr.applicant"):applicant>/'
                 '<model("calendar.appointment.type"):appointment_type>/appointment'], type='http',
                auth="public", website=True, sitemap=True)
    def calendar_appointment(self, applicant=None, appointment_type=None, employee_id=None, timezone=None, failed=False,
                             **kwargs):
        if applicant:
            admin = request.env['hr.employee'].sudo().browse(int(1))[0]
            admin.applicant_id = applicant
        request.session['timezone'] = timezone or appointment_type.appointment_tz
        employee = request.env['hr.employee'].sudo().browse(int(employee_id)) if employee_id else None
        appointment_type.max_schedule_days = 45
        slots = appointment_type.sudo()._get_appointment_slots(request.session['timezone'], employee)
        return request.render("hr_applicant.appointment_applicant", {
            'appointment_type': appointment_type,
            'timezone': request.session['timezone'],
            'failed': failed,
            'slots': slots,
        })

    @http.route(['/hr_calendar/<model("calendar.appointment.type"):appointment_type>/info'], type='http', auth="public",
                website=True, sitemap=True)
    def hr_calendar_appointment_form(self, appointment_type, employee_id, date_time, **kwargs):

        partner_data = {}
        if request.session.uid:
            partner_data = request.env.user.partner_id.read(fields=['name', 'mobile', 'country_id', 'email', ])[0]

        day_name = format_datetime(datetime.strptime(date_time, dtf), 'EEE', locale=get_lang(request.env).code)
        date_formated = format_datetime(datetime.strptime(date_time, dtf), locale=get_lang(request.env).code)
        if 'id' in partner_data:
            this_partner = request.env['res.partner'].sudo().browse(partner_data['id'])
            partner_data[
                'company_name'] = this_partner.parent_id.name if this_partner.parent_id else this_partner.company_name

        return request.render("hr_applicant.appointment_form", {
            'partner_data': partner_data,
            'appointment_type': appointment_type,
            'datetime': date_time,
            'datetime_locale': day_name + ' ' + date_formated,
            'datetime_str': date_time,
            'employee_id': employee_id,

        })

    @http.route(['/calendar/<model("calendar.appointment.type"):appointment_type>/info'], type='http',
                auth="public",
                website=True, sitemap=True)
    def calendar_appointment_form(self, appointment_type, employee_id, date_time, **kwargs):
        partner_data = {}
        if request.env.user.partner_id != request.env.ref('base.public_partner'):
            partner_data = request.env.user.partner_id.read(fields=['name', 'mobile', 'country_id', 'email'])[0]
        day_name = format_datetime(datetime.strptime(date_time, dtf), 'EEE', locale=get_lang(request.env).code)
        date_formated = format_datetime(datetime.strptime(date_time, dtf), locale=get_lang(request.env).code)
        return request.render("website_calendar.appointment_form", {
            'partner_data': partner_data,
            'appointment_type': appointment_type,
            'datetime': date_time,
            'datetime_locale': day_name + ' ' + date_formated,
            'datetime_str': date_time,
            'employee_id': employee_id,
            'countries': request.env['res.country'].search([]),
        })

    @http.route(['/calendar/<model("calendar.appointment.type"):appointment_type>/submit'], type='http',
                auth="public",
                website=True, method=["POST"])
    def calendar_appointment_submit(self, appointment_type, datetime_str, employee_id, name, phone, email,
                                    country_id=False, **kwargs):
        timezone = request.session['timezone']
        tz_session = pytz.timezone(timezone)
        date_start = tz_session.localize(fields.Datetime.from_string(datetime_str)).astimezone(pytz.utc)
        date_end = date_start + relativedelta(hours=appointment_type.appointment_duration)

        # check availability of the employee again (in case someone else booked while the client was entering the form)
        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        print(employee.applicant_id.id)
        if employee.user_id and employee.user_id.partner_id:
            if not employee.user_id.partner_id.calendar_verify_availability(date_start, date_end):
                return request.redirect('/calendar/%s/appointment?failed=employee' % appointment_type.id)

        country_id = int(country_id) if country_id else None
        country_name = country_id and request.env['res.country'].browse(country_id).name or ''
        partner = request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)
        if partner:
            if not partner.calendar_verify_availability(date_start, date_end):
                return request.redirect('/calendar/%s/appointment?failed=partner' % appointment_type.id)
            if not partner.mobile or len(partner.mobile) <= 5 and len(phone) > 5:
                partner.write({'mobile': phone})
            if not partner.country_id:
                partner.country_id = country_id
        else:
            partner = partner.create({
                'name': name,
                'country_id': country_id,
                'mobile': phone,
                'email': email,

            })

        description = (_('Country: %s') + '\n' +
                       _('Mobile: %s') + '\n' +
                       _('Email: %s') + '\n') % (country_name, phone, email)
        for question in appointment_type.question_ids:
            key = 'question_' + str(question.id)
            if question.question_type == 'checkbox':
                answers = question.answer_ids.filtered(lambda x: (key + '_answer_' + str(x.id)) in kwargs)
                description += question.name + ': ' + ', '.join(answers.mapped('name')) + '\n'
            elif kwargs.get(key):
                if question.question_type == 'text':
                    description += '\n* ' + question.name + ' *\n' + kwargs.get(key, False) + '\n\n'
                else:
                    description += question.name + ': ' + kwargs.get(key) + '\n'

        categ_id = request.env.ref('website_calendar.calendar_event_type_data_online_appointment')
        alarm_ids = appointment_type.reminder_ids and [(6, 0, appointment_type.reminder_ids.ids)] or []
        partner_ids = list(set([employee.user_id.partner_id.id] + [partner.id]))
        event = request.env['calendar.event'].sudo().create({
            'name': _('%s with %s') % (appointment_type.name, name),
            'start': date_start.strftime(dtf),
            'start_date': date_start.strftime(dtf),
            'stop': date_end.strftime(dtf),
            'allday': False,
            'duration': appointment_type.appointment_duration,
            'description': description,
            'alarm_ids': alarm_ids,
            'location': appointment_type.location,
            'partner_ids': [(4, pid, False) for pid in partner_ids],
            'categ_ids': [(4, categ_id.id, False)],
            'appointment_type_id': appointment_type.id,
            'user_id': employee.user_id.id,
            'applicant_id': employee.applicant_id.id
        })
        event.attendee_ids.write({'state': 'accepted'})
        crm_lead = {
            'name': partner.name,
            'email_from': partner.email,
            'phone': partner.mobile
        }
        request.env['crm.lead'].sudo().create(crm_lead)
        return request.redirect('/calendar/view/' + event.access_token + '?message=new')

    @http.route(['/calendar/view/<string:access_token>'], type='http', auth="public", website=True)
    def calendar_appointment_view(self, access_token, edit=False, message=False, **kwargs):
        event = request.env['calendar.event'].sudo().search([('access_token', '=', access_token)], limit=1)
        if not event:
            return request.not_found()
        timezone = request.session.get('timezone')
        if not timezone:
            timezone = request.env.context.get(
                'tz') or event.appointment_type_id.appointment_tz or event.partner_ids and event.partner_ids[0].tz
            request.session['timezone'] = timezone
        tz_session = pytz.timezone(timezone)

        date_start_suffix = ""
        format_func = format_datetime
        if not event.allday:
            url_date_start = fields.Datetime.from_string(event.start).strftime('%Y%m%dT%H%M%SZ')
            url_date_stop = fields.Datetime.from_string(event.stop).strftime('%Y%m%dT%H%M%SZ')
            date_start = fields.Datetime.from_string(event.start).replace(tzinfo=pytz.utc).astimezone(tz_session)
        else:
            url_date_start = url_date_stop = fields.Date.from_string(event.start_date).strftime('%Y%m%d')
            date_start = fields.Date.from_string(event.start_date)
            format_func = format_date
            date_start_suffix = _(', All Day')

        locale = get_lang(request.env).code
        day_name = format_func(date_start, 'EEE', locale=locale)
        date_start = day_name + ' ' + format_func(date_start, locale=locale) + date_start_suffix
        details = event.appointment_type_id and event.appointment_type_id.message_confirmation or event.description or ''
        params = {
            'action': 'TEMPLATE',
            'text': event.name,
            'dates': url_date_start + '/' + url_date_stop,
            'details': html2plaintext(details.encode('utf-8'))
        }
        if event.location:
            params.update(location=event.location.replace('\n', ' '))
        encoded_params = url_encode(params)
        google_url = 'https://www.google.com/calendar/render?' + encoded_params

        return request.render("website_calendar.appointment_validated", {
            'event': event,
            'datetime_start': date_start,
            'google_url': google_url,
            'message': message,
            'edit': edit,
        })

    @http.route(['/calendar/cancel/<string:access_token>'], type='http', auth="public", website=True)
    def calendar_appointment_cancel(self, access_token, **kwargs):
        event = request.env['calendar.event'].sudo().search([('access_token', '=', access_token)], limit=1)
        if not event:
            return request.not_found()
        if fields.Datetime.from_string(
                event.allday and event.start_date or event.start) < datetime.now() + relativedelta(
            hours=event.appointment_type_id.min_cancellation_hours):
            return request.redirect('/calendar/view/' + access_token + '?message=no-cancel')
        event.unlink()
        return request.redirect('/calendar?message=cancel')

    @http.route(['/calendar/ics/<string:access_token>.ics'], type='http', auth="public", website=True)
    def calendar_appointment_ics(self, access_token, **kwargs):
        event = request.env['calendar.event'].sudo().search([('access_token', '=', access_token)], limit=1)
        if not event or not event.attendee_ids:
            return request.not_found()
        files = event._get_ics_file()
        content = files[event.id]
        return request.make_response(content, [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Length', len(content)),
            ('Content-Disposition', 'attachment; filename=Appoinment.ics')
        ])

    @http.route('''/profile/<model("hr.applicant"):applicant>''', type='http', auth="public", website=True)
    def requested_cv(self, **kw):
        rc = request.env['requested.changes'].sudo().search(
            [('applicant', '=', kw['applicant']), ('recruiter', '=', request.session.uid)])
        if not rc:
            rc.sudo().create({'applicant': kw['applicant'],
                              'recruiter': request.session.uid})
