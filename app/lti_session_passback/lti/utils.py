from collections import OrderedDict

from logging import getLogger
logger = getLogger('root')

from app.main.checks_config.parser import sld_num

TITLE = 'context_title'
RETURN_URL = 'launch_presentation_return_url'
USERNAME = 'ext_user_username'
PERSON_NAME = 'lis_person_name_full'
ROLES = 'roles'
ADMIN_ROLE = 'Instructor'
CUSTOM_PARAM_PREFIX = 'custom_'
PASSBACK_PARAMS = ('lis_outcome_service_url', 'lis_result_sourcedid', 'oauth_consumer_key')

from app.bd_helper.bd_helper import ConsumersDBManager

def get_param(data, key):
    if key in data:
        return data[key]
    else:
        raise KeyError("{} doesn't include {}.".format(data, key))


def get_title(data): return get_param(data, TITLE)


def get_return_url(data): return get_param(data, RETURN_URL)


def get_username(data): return get_param(data, USERNAME)


def get_person_name(data): return get_param(data, PERSON_NAME)


def create_consumers(consumer_dict):
    for key, secret in consumer_dict.items():
        ConsumersDBManager.add_consumer(key, secret)

def parse_consumer_info(key_str, secret_str):
    keys = key_str.split(',')
    secrets = secret_str.split(',')

    if len(keys) != len(secrets):
        raise Exception(f"len(consumer_keys) != len(consumer_secrets): '{key_str}' vs '{secret_str}'")

    return { key: secret for key, secret in zip(keys, secrets) }

def get_role(data, default_role=False):
    try:
        return get_param(data, ROLES).split(',')[0] == ADMIN_ROLE
    except:
        return default_role

def get_exc_info(data):
    task_title = get_param(data, 'resource_link_title')
    task_id = get_param(data, 'resource_link_id')
    un = f"{get_username(data)}_{get_param(data, 'tool_consumer_instance_guid')}"
    return dict(zip(['title', 'id', 'username'], [task_title, task_id, un]))

def get_custom_params(data):
    return { key[len(CUSTOM_PARAM_PREFIX):]: data[key] for key in data if key.startswith(CUSTOM_PARAM_PREFIX) }

def get_criteria_from_launch(data):
    all_checks = ('slides_number', 'slides_enum', 'slides_headers', 'goals_slide',
                  'probe_slide', 'actual_slide', 'conclusion_slide', 'slide_every_task',
                  'conclusion_actual', 'conclusion_along', 'detect_additional')
    custom = get_custom_params(data)
    task_info = get_exc_info(data)
    detect_additional = custom.get('detect_additional', 'True')
    criteria = dict((k, custom[k]) for k in all_checks if k in custom)
    eval_criteria = launch_sanity_check(criteria, detect_additional, task_info)

    return eval_criteria

def extract_passback_params(data):
    params = {}
    for param_key in PASSBACK_PARAMS:
        if param_key in data:
            params[param_key] = data[param_key]
        else:
            raise KeyError("{} doesn't include {}. Must inslude: {}".format(data, param_key, PASSBACK_PARAMS))
    return params

def launch_sanity_check(criteria, detect_additional, task_info):
    try:
        order =  ['slides_number', 'slides_enum', 'slides_headers', 'goals_slide',
                  'probe_slide', 'actual_slide', 'conclusion_slide', 'conclusion_actual', 'conclusion_along',
                  'slide_every_task'] #
        
        eval_criteria = OrderedDict((key, eval(value)) for key, value in criteria.items() if key not in ('slides_number', 'detect_additional'))
    except NameError:
        logger.warning("Error in declared launch values is present in {0}(id={1}). {2}'s checks will be defaulted".format(*task_info.values()))
        return dict()

    int_false_checks = ['slide_every_task', 'conclusion_actual']
    check_types = {
        **dict.fromkeys(['slides_enum', 'slides_headers', 'goals_slide', 'detect_additional', 'probe_slide',
                         'actual_slide', 'conclusion_slide', 'conclusion_along'], (bool)),
        **dict.fromkeys(int_false_checks, (int, bool))
        }

    failed_types = [k for k, v in eval_criteria.items() if not isinstance(v, check_types[k]) and k != 'slides_number']
    [failed_types.append(check) for check in int_false_checks if criteria.get(check) == 'True']

    slides_number = criteria.get('slides_number', 'bsc')
    detect_additional = True if not isinstance(eval(detect_additional), bool) else eval(detect_additional)
    if slides_number not in ['bsc', 'msc', 'False'] and not isinstance(eval(slides_number), (list)):
        failed_types.append('slides_number')
    else:
        eval_criteria.update({'slides_number': {'sld_num': sld_num.get(slides_number, None) or eval(slides_number),
                                          'detect_additional': detect_additional} if slides_number != 'False' else False})
        eval_criteria.move_to_end('slides_number', last = False)

    if failed_types:
        [eval_criteria.pop(key, None) for key in failed_types] #
        logger.warning(f"The following check types don't match their designated types: {', '.join(failed_types)}.")
        logger.warning("They will be set to default for task {0}(id={1}) in {2}'s checks".format(*task_info.values()))

    reordered_dict = {k: eval_criteria.get(k, False) for k in order}

    return reordered_dict
