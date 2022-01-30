import logging
logger = logging.getLogger('root_logger')
from app.main.checks_config.parser import sld_num
from typing import Optional, Union, TypeVar
from pydantic import BaseModel, ValidationError, validator, root_validator

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
    custom = get_custom_params(data)
    task_info = get_exc_info(data)
    eval_criteria = launch_sanity_check(custom, task_info)

    return eval_criteria

def extract_passback_params(data):
    params = {}
    for param_key in PASSBACK_PARAMS:
        if param_key in data:
            params[param_key] = data[param_key]
        else:
            raise KeyError("{} doesn't include {}. Must inslude: {}".format(data, param_key, PASSBACK_PARAMS))
    return params

class Criteria(BaseModel):
    slides_number: Union[str, bool, list] = sld_num['bsc']  #faulty
    detect_additional: bool = True
    slides_enum: bool = True
    slides_headers: bool = True
    goals_slide: bool = True
    probe_slide: bool = True
    actual_slide: bool = True
    conclusion_slide: bool = True
    slide_every_task: Union[bool, int] = 50
    conclusion_actual: Union[bool, int] = 50
    conclusion_along: bool = True

    class Config:
      validate_assignment = True
      validate_all = True

    @validator('slides_number')
    def slides_num_validator(cls, value):
        if value not in ['bsc', 'msc', False] and type(value) != list:
            allowed_type = cls.__fields__['slides_number'].type_
            raise ValueError(f'should be of {allowed_type}(str: "bsc", "msc")')
        return sld_num[value] if type(value) == str else value

    @validator('slide_every_task', 'conclusion_actual')
    def esc_true_validator(cls, value):
        if value == True:
            allowed_type = cls.__fields__['conclusion_actual'].type_
            raise ValueError(f'should be of {allowed_type}(bool: only False to disable)')
        return value

    @root_validator()
    def check_failing(cls, values):
        present = values.keys()
        required = set(cls.__fields__.keys()) #!
        failing_keys = required.difference(present)
        if failing_keys:
          raise ValueError(f'Issues are present in the fields: {failing_keys}')
        return values

    @root_validator()
    def _set_fields(cls, values):
        values['slides_number'] = {'sld_num': values.get('slides_number', None),
                                   'detect_additional': values.get('detect_additional', None)}
        values.pop('detect_additional', None)
        return values

def launch_sanity_check(custom, task_info):
    try:
        criteria = Criteria.parse_obj(custom)
    except ValidationError as e:
        errors = e.errors()
        for i in errors:
            custom.pop(i['loc'][0], None)
            field_err = (
                         f"Error in {i['loc'][0]}: {i['msg']}[{i['type']}]. "
                         f"Defaulting for task {task_info['title']}, id={task_info['id']}."
            )
            logger.warning(field_err)

        criteria = Criteria.parse_obj(custom)

    return criteria.dict()
