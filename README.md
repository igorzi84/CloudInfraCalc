# CloudInfraCalc

Cloud infra costs calculator - goes through instances in AWS account by tag and calculates instance and EBS costs

## Getting Started

### Prerequisites

This script requires boto3 module
```
pip install boto3
```
AWS credentials should be configured as described:
```
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
```

### Runnning the script

Run python with -r region, -n tag_name -v tag_value

Script will fetch all instances in AWS account with tag_name like \*tag_value\* and will calculate instance and EBS costs

```
python cost_reporter.py -r us-east-1 -n Name -v worker

worker infra: 
	9	r4.xlarge
SSD disks: 
	gp2         1350GB
	standard      72GB
Monthly costs for EC2 instances: $1752.41
Monthly costs for EBS: $138
Total monthly cost: $1890.41
```

### Runnning the script in Docker - TBD

