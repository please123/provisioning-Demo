#!/usr/bin/python
from __future__ import absolute_import, division, print_function
__metaclass__ = type


from time import sleep
from time import time

try:
  import botocore
except ImportError:
  pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.network import to_subnet
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.ec2 import HAS_BOTO
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible.module_utils.ec2 import compare_aws_tags
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, AWSRetry

def main():
  argument_spec = dict(
      name=dict(required=True),
      tags=dict(type='dict', aliases=['resource_tags']),
      state=dict(choices=['present', 'absent'], default='present'),
      scheme={'default': 'Server', 'required': False, 'choices': ['Lambda', 'Server', 'ECS']},
  )

  module = AnsibleAWSModule(
      argument_spec=argument_spec,
      supports_check_mode=True
  )

  if not HAS_BOTO:
    module.fail_json(msg='boto required for this module')

  region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
  if not region:
    module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")

  name = module.params.get('name')
  tags = module.params.get('tags')
  scheme = module.params['scheme']
  state = module.params.get('state')

  connection = module.client(
      'codedeploy',
      retry_decorator=AWSRetry.jittered_backoff(
          retries=8, delay=3, catch_extra_error_codes=['ApplicationAlreadyExistsException']
      )
  )

  if state == 'present':
    try:
      application = connection.create_application(applicationName=name,computePlatform=scheme)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
      changed=False
      module.exit_json(changed=changed, codedeploy={})
  elif state == 'absent':
    connection.delete_application(applicationName=name)

  changed=True
  module.exit_json(changed=changed, applicationId=application['applicationId'])

if __name__ == '__main__':
  main()