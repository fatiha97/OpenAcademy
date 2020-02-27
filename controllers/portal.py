# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        values['session_count'] = request.env['openacademy.session'].search_count(
            [('instructor_id', '=', request.env.user.partner_id.id)])
       # if values.get('sales_user', False):
       #     values['title'] = _("Salesperson")
        return values

    def _session_get_page_view_values(self, session, access_token, **kwargs):
        values = {
            'page_name': 'session',
            'session': session,
        }
        return self._get_page_view_values(session, access_token, values, 'my_sessions_history', False, **kwargs)

    @http.route(['/my/sessions', '/my/sessions/page/<int:page>'], type='http', auth="user", website=True)
    def my_openacademy_sessions(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = [('instructor_id', '=', request.env.user.partner_id.id)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'id': {'input': 'id', 'label': _('Search ID')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('openacademy.session', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', '=', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            domain += search_domain

        # pager
        sessions_count = request.env['openacademy.session'].search_count(domain)
        pager = portal_pager(
            url="/my/sessions",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=sessions_count,
            page=page,
            step=self._items_per_page
        )

        sessions = request.env['openacademy.session'].search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_sessions_history'] = sessions.ids[:100]

        values.update({
            'date': date_begin,
            'sessions': sessions,
            'page_name': 'session',
            'default_url': '/my/sessions',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render("openacademy.portal_openacademy_session", values)

    @http.route([
        "/openacademy/session/<int:session_id>",
        "/openacademy/session/<int:session_id>/<access_token>",
        '/my/session/<int:session_id>',
        '/my/session/<int:session_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def sessions_followup(self, session_id=None, access_token=None, **kw):
        try:
            session_sudo = self._document_check_access('openacademy.session', session_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._session_get_page_view_values(session_sudo, access_token, **kw)
        return request.render("openacademy.sessions_followup", values)


