#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import boto3
import json
import sys

from botocore.exceptions import ClientError
from collections import Counter
from itertools import groupby
from operator import itemgetter

# Instance filter
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
      '{{"Field": "operatingSystem", "Value": "Linux", "Type": "TERM_MATCH"}},' \
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
      '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}}]'
# EBS filter
FLT2 = '[{{"Field": "productFamily", "Value": "Storage", "Type": "TERM_MATCH"}},' \
       '{{"Field": "volumeType", "Value": "{e}", "Type": "TERM_MATCH"}},' \
       '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}}]'


def get_infra(region, tag_name, tag_value):
    client = boto3.client('ec2', region_name=region)
    ec2_resource = boto3.resource('ec2', region_name=region)
    try:
        reservations = client.describe_instances(Filters=[{'Name': "tag:" + tag_name,
                                                           'Values': ["*" + tag_value + "*"]}])
    except ClientError as error:
        print("Unexpected error: {}".format(error.response['Error']['Message']))
        print("Error Code: {}".format(error.response['Error']['Code']))
        exit(error.response['ResponseMetadata']['HTTPStatusCode'])

    instances = [i for l in reservations['Reservations'] for i in l['Instances']]
    # instance types of "running" machines
    types = [i['InstanceType'] for i in instances if i['State']['Code'] == 16]
    # Using Counter to count unique values
    formatted_types = Counter(types)
    print(tag_value + ' infra: ')
    for v, c in formatted_types.items():
        print('\t{0}\t{1}'.format(c, v))

    # EBS mounts for "running" instances, currently count only "gp2"
    ebs = [y['Ebs']['VolumeId'] for i in instances if i['State']['Code'] == 16 for y in i['BlockDeviceMappings']]
    # Fetching all EBS disks and summing them by type, sums is dict of 'type':size
    ebs_disks = [(ec2_resource.Volume(id).volume_type, ec2_resource.Volume(id).size) for id in ebs]
    first = itemgetter(0)
    ebs_sums = {(k, sum(item[1] for item in tups_to_sum))
                for k, tups_to_sum in groupby(sorted(ebs_disks, key=first), key=first)}
    print('SSD disks: ')
    for k, v in ebs_sums:
        print('\t{0: <10} {1: >5}GB'.format(k, v))

    return types, ebs_sums


def get_instance_price(region_name, instance):
    client = boto3.client('pricing', region_name='us-east-1')
    f = FLT.format(r=region_name, t=instance)
    try:
        data = client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f))
    except ClientError as error:
        print("Unexpected error: {}".format(error.response['Error']['Message']))
        print("Error Code: {}".format(error.response['Error']['Code']))
        exit(error.response['ResponseMetadata']['HTTPStatusCode'])
    od = json.loads(data['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']


def get_ebs_price(region_name, type):
    client = boto3.client('pricing', region_name='us-east-1')
    f2 = FLT2.format(r=region_name, e=aws_ebs_volume_types(type))
    try:
        data2 = client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f2))
    except ClientError as error:
        print("Unexpected error: {}".format(error.response['Error']['Message']))
        print("Error Code: {}".format(error.response['Error']['Code']))
        exit(error.response['ResponseMetadata']['HTTPStatusCode'])
    od = json.loads(data2['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']


def aws_ebs_volume_types(type):
    ebs_volume_types = {'gp2': 'General Purpose', 'io1': 'Provisioned IOPS', 'st1': 'Throughput Optimized',
                        'sc1': 'Cold',
                        'standard': 'Magnetic'}
    return ebs_volume_types[type]


def aws_region(region):
    aws_regions = {'us-east-2': 'US East (Ohio)', 'us-east-1': 'US East (N. Virginia)',
                   'us-west-1': 'US West (N. California)',
                   'us-west-2': 'US West (Oregon)', 'ap-northeast-1': 'Asia Pacific (Tokyo)',
                   'ap-northeast-2': 'Asia Pacific (Seoul)', 'ap-northeast-3': 'Asia Pacific (Osaka-Local)',
                   'ap-south-1': 'Asia Pacific (Mumbai)', 'ap-southeast-1': 'Asia Pacific (Singapore)',
                   'ap-southeast-2': 'Asia Pacific (Sydney)', 'ca-central-1': 'Canada (Central)',
                   'cn-north-1': 'China (Beijing)', 'cn-northwest-1': 'China (Ningxia)',
                   'eu-central-1': 'EU (Frankfurt)',
                   'eu-west-1': 'EU (Ireland)', 'eu-west-2': 'EU (London)', 'eu-west-3': 'EU (Paris)',
                   'sa-east-1': 'South America (São Paulo)'}
    return aws_regions[region]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--region', dest='region', nargs=1, type=str, required=True, help="Region")
    parser.add_argument('-n', '--tag_name', dest="tag_name", nargs=1, type=str, required=True, help="Tag name")
    parser.add_argument('-v', '--tag_value', dest='tag_value', nargs=1, type=str, required=True, help="Tag value")
    args = parser.parse_args()

    region = args.region[0]
    tag_name = args.tag_name[0]
    tag_value = args.tag_value[0]
    monthly_instances_cost = 0
    monthly_ebs_cost = 0
    infra = get_infra(region, tag_name, tag_value)

    for i in infra[0]:
        monthly_instances_cost += float(get_instance_price(aws_region(region), i)) * 732

    for type, size in infra[1]:
        monthly_ebs_cost += int(size * float(get_ebs_price(aws_region(region), type)))

    print('Monthly costs for EC2 instances: ${0:.2f}'.format(monthly_instances_cost))
    print('Monthly costs for EBS: ${0}'.format(monthly_ebs_cost))
    print('Total monthly cost: ${0:.2f}'.format(monthly_instances_cost + monthly_ebs_cost))

