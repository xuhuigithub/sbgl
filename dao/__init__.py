import traceback
import re

class DataNotFoundException(Exception):
    pass

class RequestFilterException(Exception):
    pass

class DataBaseCommitException(Exception):
    pass

class IllegalStateException(Exception):
    pass

filter_re = re.compile(r'filter\[(\w+)\]')

from database import db_session

class BaseDao:

    def handle_filter(self, query):
        from flask import request
        for key in request.args:
            value = request.args.get(key, None)
            if filter_re.match(key) and value is not None:
                try:
                    f = getattr(self, "handle_%s" %filter_re.match(key).groups()[0])
                except AttributeError as e:
                    raise RequestFilterException
                else:
                    query = f(query,value)
        return query

    def _try_commint(self):
        try:
            db_session.commit()
        except Exception as e:
            traceback.print_exc()
            db_session.rollback()
            raise DataBaseCommitException
    

    def get_paginated_list(self, results, url, start, limit):
        start = int(start)
        limit = int(limit)
        count = len(results)
        if count < start or limit < 0:
            return []
        # make response
        obj = {}
        obj['start'] = start
        obj['limit'] = limit
        obj['count'] = count
        # make URLs
        # make previous url
        if start == 1:
            obj['previous'] = ''
        else:
            start_copy = max(1, start - limit)
            limit_copy = start - 1
            obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)
        # make next url
        if start + limit > count:
            obj['next'] = ''
        else:
            start_copy = start + limit
            obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
        # finally extract result according to bounds
        obj['results'] = results[(start - 1):(start - 1 + limit)]
        return obj
