import argparse
import boto3
import json


from collections import Counter

# Instance filter
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},' \
      '{{"Field": "operatingSystem", "Value": "Linux", "Type": "TERM_MATCH"}},' \
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},' \
      '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},' \
      '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}}]'
#EBS filter
FLT2 = '[{{"Field": "productFamily", "Value": "Storage", "Type": "TERM_MATCH"}},' \
       '{{"Field": "volumeType", "Value": "{e}", "Type": "TERM_MATCH"}},' \
       '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}}]'


def get_infra(cluster, region):
    client = boto3.client('ec2', region_name=region)
    ec2_resource = boto3.resource('ec2', region_name=region)
    reservations = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ["*" + cluster + "*"]}])
    instances = [i for l in reservations['Reservations'] for i in l['Instances']]
    # instance types of "running" machines
    types = [i['InstanceType'] for i in instances if i['State']['Code'] == 16]
    # Using Counter to count unique values
    formatted_types = Counter(types)
    print(cluster + ' infra: ')
    for v, c in formatted_types.items():
        print('\t{0}\t{1}'.format(c, v))

    # EBS mounts for "running" instances, currently count only "gp2"
    ebs = [y['Ebs']['VolumeId'] for i in instances if i['State']['Code'] == 16 for y in i['BlockDeviceMappings']]
    ebs_size = [ec2_resource.Volume(id).size for id in ebs if ec2_resource.Volume(id).volume_type == 'gp2']
    total_ebs_size = sum(ebs_size)
    formatted_ebs_size = Counter(ebs_size)
    print('SSD disks: ')
    for v, c in formatted_ebs_size.items():
        print('\t{0}\t{1}'.format(c, v))
    # print("Total EBS size:\n\t{0} GB".format(total_ebs_size))

    return types, total_ebs_size


def get_instance_price(region_name, instance):
    client = boto3.client('pricing', region_name='us-east-1')
    f = FLT.format(r=region_name, t=instance)
    data = client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f))
    od = json.loads(data['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']


def get_ebs_price(region_name):
    client = boto3.client('pricing', region_name='us-east-1')
    f2 = FLT2.format(r=region_name, e='General Purpose')
    data2 = client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f2))
    od = json.loads(data2['PriceList'][0])['terms']['OnDemand']
    id1 = list(od)[0]
    id2 = list(od[id1]['priceDimensions'])[0]
    return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']

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
    parser.add_argument("-r,--region", dest="region", nargs=1, type=str, required=True, help="Cluster region")
    parser.add_argument("-c,--cluster", dest="cluster", nargs=1, type=str, required=True, help="Cluster name")
    args = parser.parse_args()

    region = args.region[0]
    cluster = args.cluster[0]
    monthly = 0
    infra = get_infra(cluster, region)

    for i in infra[0]:
        price = get_instance_price(aws_region(region), i)
        monthly += float(price) * 732

    print('Monthly costs for EC2 instances: ${0:.2f}'.format(monthly))
    total_ebs_cost = int(infra[1]) * float(get_ebs_price(aws_region(region)))
    print('Monthly costs for EBS: ${0}'.format(total_ebs_cost))
    print('Total monthly cost: ${0:.2f}'.format(monthly + total_ebs_cost))


