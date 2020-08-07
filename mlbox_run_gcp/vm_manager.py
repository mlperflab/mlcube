#!/usr/bin/env python

"""Example of using the Compute Engine API to create and delete instances.
Creates a new compute engine instance and uses it to apply a caption to
an image.
    https://cloud.google.com/compute/docs/tutorials/python-guide
For more information, see the README.md under /compute.
"""

import argparse
import os
import time

import googleapiclient.discovery
from six.moves import input


# [START list_instances]
def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None
# [END list_instances]


# Example machine type: 'zones/{}/machineTypes/n1-standard-8'.format(zone)
# machine_type


# self.source_disk_image = 'projects/tf-benchmark-dashboard/global/images/ubuntu-1804-cuda10-20191003'
class VMConfig:
    def __init__(self, project, zone, name, machine_type):
      self.project = project
      self.zone = zone
      self.name = name
      self.machine_type = machine_type
      self.source_disk_image = 'projects/tf-benchmark-dashboard/global/images/ubuntu-1804-cuda10-20191003'

    def get_config(self):
        self.config = {
            'name': self.name,
            'machineType': self.machine_type,

            # Specify the boot disk and the image to use as a source.
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': self.source_disk_image,
                    }
                }
            ],

            # Specify a network interface with NAT to access the public
            # internet.
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],

            # Allow the instance to access cloud storage and logging.
            'serviceAccounts': [{
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/logging.write'
                ]
            }],

            # Metadata is readable from the instance and allows you to
            # pass configuration from deployment scripts to instances.
            'metadata': {
             #   'items': [{
             #       # Startup script is automatically executed by the
             #       # instance upon startup.
             #       'key': 'startup-script',
             #       'value': self.startup_script
             #   }, {
             #       'key': 'url',
             #       'value': self.image_url
             #   }, {
             #       'key': 'text',
             #       'value': self.image_caption
             #   }, {
             #       'key': 'bucket',
             #       'value': self.bucket
             #   }]
            }
        }
        return self.config



# [START create_instance]
def create_instance(compute, vm_config):
    # Get the latest Debian Jessie image.
    #image_response = compute.images().getFromFamily(
    #    project='debian-cloud', family='debian-9').execute()
    #source_disk_image = image_response['selfLink']

    # Configure the machine
    # machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
    #startup_script = open(
    #     os.path.join(
    #         os.path.dirname(__file__), 'startup-script.sh'), 'r').read()
    # image_url = "http://storage.googleapis.com/gce-demo-input/photo.jpg"
    # image_caption = "Ready for dessert?"


    return compute.instances().insert(
        project=vm_config.project,
        zone=vm_config.zone,
        body=vm_config.get_config()).execute()
# [END create_instance]


# [START delete_instance]
def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()
# [END delete_instance]


# [START wait_for_operation]
def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)
# [END wait_for_operation]


# [START run]
def main(project, bucket, zone, instance_name, wait=True):
    compute = googleapiclient.discovery.build('compute', 'v1')

    print('Creating instance.')

    # operation = create_instance(compute, project, zone, instance_name, bucket)
    vm_config = VMConfig(zone=zone, project=project)
    operation = create_instance(compute, vm_config)
    wait_for_operation(compute, project, zone, operation['name'])

    instances = list_instances(compute, project, zone)

    print('Instances in project %s and zone %s:' % (project, zone))
    for instance in instances:
        print(' - ' + instance['name'])

    print("""
Instance created.
It will take a minute or two for the instance to complete work.
Check this URL: http://storage.googleapis.com/{}/output.png
Once the image is uploaded press enter to delete the instance.
""".format(bucket))

    if wait:
        input()

    print('Deleting instance.')

    operation = delete_instance(compute, project, zone, instance_name)
    wait_for_operation(compute, project, zone, operation['name'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--name', default='demo-instance', help='New instance name.')

    args = parser.parse_args()

    config = {
        'project_id': 'tf-benchmark-dashboard',
        'zone': 'us-west1-a',
        'bucket_name': '', # TODO remove me
    }

    main(config['project_id'], config['bucket_name'], config['zone'], instance_name=args.name)
# [END run]
