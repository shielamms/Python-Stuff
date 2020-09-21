import boto3

print('This script will test authorization and authentication to your AWS environment through the assume_role API\n')

role_arn = input('Role ARN: ')
mfa_id = input('Your MFA ID: ')
mfa_token = input('MFA Token Code (from authenticator): ')

client = boto3.client('sts')

print('Assuming role...')

role = client.assume_role(
    RoleArn=role_arn,
    RoleSessionName='MyDev',
    DurationSeconds=3600,
    SerialNumber=mfa_id,
    TokenCode=mfa_token
)

print('\nYour credentials: ', role)

credentials = role['Credentials']
aws_access_key_id = credentials['AccessKeyId']
aws_secret_access_key = credentials['SecretAccessKey']
aws_session_token = credentials['SessionToken']

print('\nUsing your session credentials to authenticate to S3...')
region = input('Region name: ')

s3 = boto3.client(service_name="s3",
                  region_name=region,
                  aws_access_key_id=aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key,
                  aws_session_token=aws_session_token
                 )

response = s3.list_buckets()

print("S3 Response: ", response)

print('\n\nSuccessfully authenticated!')