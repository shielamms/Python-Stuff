import boto3
import csv
import time
import codecs
from Route53Request import Route53Request
from RequestException import RequestException

route53 = boto3.client("route53")
s3 = boto3.client("s3")


def read_csv_input(bucket, key):
    try:
        csv_file = s3.get_object(Bucket=bucket, Key=key)
        csv_data = csv_file['Body'].read().split(b'\n')
        csv_data_dict = csv.DictReader(codecs.iterdecode(csv_data, 'utf-8-sig'))

        return csv_data_dict
    except:
        raise RequestException(message='Failed to read CSV file from S3', error_data=key)


def get_hosted_zone_id(domain_name, zone_type):
    response_zones = None
    zone_id = None

    try:
        response_zones = route53.list_hosted_zones_by_name(
            DNSName=domain_name,
            MaxItems="2"
        )

        time.sleep(0.5)
    except:
        raise RequestException(message='Could not perform list operation from Route 53', error_data=domain_name)

    for zone in response_zones['HostedZones']:
        zone_name = zone['Name']
        response_zone_type = 'private' if zone['Config']['PrivateZone'] is True else 'public'

        if domain_name + '.' == zone_name and zone_type == response_zone_type:
            if zone_id is not None:
                raise RequestException(message='Multiple hosted zones with the same name were found',
                                       error_data=domain_name)

            zone_id = zone['Id'].partition("hostedzone/")[2]

    if zone_id is None and error is None:
        raise RequestException('The hosted zone {0} does not exist'.format(domain_name))

    return zone_id


def commit_changes(zone_id, action_requests):
    action_json = []
    msg = None

    for action_request in action_requests:
        action_json.append(action_request.generate_change_recordSet_json())

    try:
        response = route53.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': action_json
            }
        )

        time.sleep(1)

        msg = response['ChangeInfo']['Id']

    except Exception as e:
        raise RequestException(message="Could not commit changes to Route 53. Invalid JSON request", error_data=zone_id)

    return msg


def process_changes(changes_dict):
    for domain_name in changes_dict.keys():
        action_requests = changes_dict[domain_name]

        zone_id = get_hosted_zone_id(domain_name, action_requests[0].zoneType)

        msg = commit_changes(zone_id, action_requests)

    return msg


def handler(event, context):
    try:
        data_file = event['file_name']

        bucket = data_file['bucket']['name']
        key = data_file['object']['key']

        csv_data = read_csv_input(bucket, key)

        changes_dict = {}
        error = None

        for i, row in enumerate(csv_data):
            request_info = Route53Request(row['action'],
                                          domainName=row['domain_name'],
                                          recordSetName=row['record_name'],
                                          recordSetValue=row['value'],
                                          recordSetType=row['record_type']
                                          )

            if request_info.is_valid_action() == False:
                raise RequestException(message='Invalid request action', index=i + 1, error_data=request_info.action)

            if request_info.is_valid_record_type() == False:
                raise RequestException(message='Record type is not recognised', index=i + 1,
                                       error_data=request_info.recordSetType)

            if request_info.domainName not in changes_dict.keys():
                changes_dict[request_info.domainName] = [request_info]
            else:
                changes_dict[request_info.domainName].append(request_info)

        # Process Changes
        msg = process_changes(changes_dict)

        APIresponse = {
            "number": event['number'],
            "state": "Successfully committed changes to Route53",
            "message": msg,
        }

        return APIresponse

    except RequestException as req_exc:
        print(req_exc)

        APIresponse = {
            "number": event['number'],
            "state": "Error",
            "message": req_exc.get_msg_data()
        }

        return APIresponse

