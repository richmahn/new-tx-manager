from __future__ import print_function, unicode_literals
import json
import datetime
from libraries.models.manifest import TxManifest
from libraries.app.app import App


class ProjectSearch(object):
    INVALID_URL_ERROR = 'Project not found for: '
    INVALID_LANG_URL_ERROR = 'Language not found for: '
    DB_ACCESS_ERROR = 'Could not access view counts for: '

    def __init__(self):
        self.error = None
        self.criterion = None

    def search_projects(self, criterion):
        """
        search for repos in manifest that match criterion
        :param criterion:
        :return:
        """
        App.logger.debug("Start: search_repos: " + json.dumps(criterion))

        self.criterion = json.loads(json.dumps(criterion))  # clone so we can modify

        try:
            selection = App.db().query(TxManifest)

            for k in self.criterion:
                v = self.criterion[k]
                selection = self.apply_filters(selection, k, v)
                if selection is None:
                    return None

            if 'sort_by' in self.criterion:
                db_key = getattr(TxManifest, self.criterion['sort_by'], None)
                if db_key:
                    selection = selection.order_by(db_key)

            if 'sort_by_reversed' in self.criterion:
                db_key = getattr(TxManifest, self.criterion['sort_by_reversed'], None)
                if db_key:
                    selection = selection.order_by(db_key.desc())

        except Exception as e:
            self.log_error('Failed to create a query: ' + str(e))
            return None

        limit = 100 if 'matchLimit' not in self.criterion else self.criterion['matchLimit']
        results = selection.limit(limit).all()  # get all matching
        data = []
        if results:
            App.logger.debug('Returning search result count of {0}')

            returned_fields = "repo_name, user_name, title, lang_code, manifest, last_updated, views" \
                if "returnedFields" not in self.criterion else self.criterion["returnedFields"]
            returned_fields = returned_fields.split(',')

            # copy wanted fields from this result item
            for result in results:
                item = {}
                for key in returned_fields:
                    key = key.strip()
                    if hasattr(result, key):
                        item[key] = getattr(result, key)
                        if isinstance(item[key], datetime.datetime):
                            item[key] = str(item[key])
                data.append(item)

        else:  # record is not present
            App.logger.debug('No entries found in search')

        App.db_close()
        return data

    def apply_filters(self, selection, key, value):
        try:
            if key == "minViews":
                selection = selection.filter(TxManifest.views >= parse_int(value, 1))
            elif key == "daysForRecent":
                days = parse_int(value, 1)
                current = datetime.datetime.now()
                offset = -days * 24 * 60 * 60  # in seconds
                recent_in_seconds = current + datetime.timedelta(seconds=offset)
                selection = selection.filter(TxManifest.last_updated >= recent_in_seconds)
            elif (key == "repo_name") or (key == "user_name") or (key == "title") or (key == "manifest"):
                selection = set_contains_string_filter(selection, key, value)
            elif key == "time":
                selection = set_contains_string_filter(selection, "last_updated", value)
            elif key == "resID":
                selection = selection.filter(TxManifest.resource_id.contains(value))
            elif key == "resType":
                selection = selection.filter(TxManifest.resource_type.contains(value))
            elif key == "languages":
                selection = set_contains_set_filter(selection, "lang_code", value)
            elif key == 'full_text':
                selection = selection.filter((TxManifest.user_name.contains(value))
                                             | (TxManifest.repo_name.contains(value))
                                             | (TxManifest.manifest.contains(value)))
            elif key == "returnedFields" or key == "sort_by" or key == "sort_by_reversed" or key == "matchLimit":
                pass  # skip this item
            else:
                pass  # Allow unsupported fields to be ignored

        except Exception as e:
            self.log_error('Failed to apply filter (key,value): ({0},{1}): '.format(key, value) + str(e))
            return None

        return selection

    def log_error(self, msg):
        self.error = msg
        App.logger.debug(msg)


def set_contains_string_filter(selection, key, value):
    db_key = getattr(TxManifest, key, None)
    selection = selection.filter(db_key.contains(value))
    return selection


def set_contains_set_filter(selection, key, value):
    db_key = getattr(TxManifest, key, None)
    if value[:1] == '[':
        filter_set_str = value[1:].split(']')
        filter_set = filter_set_str[0].split(',')
        selection = selection.filter(db_key.in_(filter_set))
    else:
        selection = selection.filter(db_key.like(value))

    return selection


def parse_int(s, default_value=None):
    try:
        return int(s)
    except ValueError:
        return default_value
