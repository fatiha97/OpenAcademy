url = "http://localhost:8013"
db = "fatihaafalahBD"
username = "fatihaafalah1997@gmail.com"
password = "admin"
import xmlrpclib
info = xmlrpclib.ServerProxy('https://demo.odoo.com/start').start()
common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
common.version()
uid = common.authenticate(db, username, password, {})
models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
models.execute_kw(db, uid, password,
    'res.partner', 'check_access_rights',
    ['read'], {'raise_exception': False})
models.execute_kw(db, uid, password,
    'openacademy.session', 'search',
    [[]])
models.execute_kw(db, uid, password,
    'openacademy.course', 'search',
    [[]])
#creation
id = models.execute_kw(db, uid, password, 'openacademy.course', 'create', [{
    'name': "securite",'responsible_id':2}])
id = models.execute_kw(db, uid, password, 'openacademy.session', 'create', [{'name': "New session",
'duration':6,'seats':10,'course_id':3}])
#count
models.execute_kw(db, uid, password,
    'openacademy.session', 'search_count',
[[]])

#affichage de ts les attendees
ids = models.execute_kw(db, uid, password,
    'openacademy.session', 'search',
    [[]])
ids_attendees = models.execute_kw(db, uid, password,
    'openacademy.session', 'read',
    [ids], {'fields': ['attendee_ids']})
models.execute_kw(db, uid, password,'res.partner', 'search_read',[[['id', 'in', ids_attendees[0]['attendee_ids']]]], {'fields': ['name']})
#affecter les attendees a une session qui a comme id=1
models.execute_kw(db, uid, password, 'openacademy.session', 'write', [[1], {
    'attendee_ids': [8,9,10,11,12]
}])
#suppression
models.execute_kw(db, uid, password, 'openacademy.course', 'unlink', [[1]])
#update
models.execute_kw(db, uid, password, 'openacademy.course', 'write', [[2], {
    'name': "java"
}])





