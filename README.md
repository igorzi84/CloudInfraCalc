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

Run python with -r/--region region, -n/--tag_name tag_name -v/--tag_value tag_value

Script will fetch all instances in AWS account with tag_name like \*tag_value\* and will calculate instance and EBS costs

```
python cost_reporter.py -r us-east-1 -n Name -v worker

worker infra: 
	9	r4.xlarge
Disks: 
	gp2         1350GB
	standard      72GB
Monthly costs for EC2 instances: $1752.41
Monthly costs for EBS: $138
Total monthly cost: $1890.41
```

### Runnning the script in Docker


1. git clone https://github.com/igorzi84/CloudInfraCalc.git
2. cd CloudInfraCalc
2. docker build -t cost_reporter .
3. docker run -e AWS_ACCESS_KEY_ID=<> -e AWS_SECRET_ACCESS_KEY=<> -it cost_reporter --region us-east-1 --tag_name Name --tag_value 
worker

```
worker infra:
        5       r4.xlarge
        2       r4.2xlarge
Disks:
        gp2         1350GB
        standard      56GB
Monthly costs for EC2 instances: $1752.41
Monthly costs for EBS: $137
Total monthly cost: $1889.41
```
