import boto3, botocore, json, os, requests
import csv
import s3fs
import time
import Route53Request

route53 = boto3.client("route53")
s3 = boto3.resource("s3")

def read_csv_input(bucket, key):
    csv_file = s3.get_object(Bucket=bucket, Key=key)
    csv_data = csv_file['Body'].read().split(b'\n')
    csv_data_dict = csv.DictReader(csv_data)

    return list(csv_data_dict)


def get_hosted_zone_id(domain_name, zone_type):
    response_zones = route53.list_hosted_zones_by_name(
        DNSName=domain_name,
        MaxItems="5"
    )

    error = None
    zone_id = None

    for zone in response_zones['HostedZones']:
        zone_name = zone['Name']
        response_zone_type = 'private' if zone['Config']['PrivateZone'] is True else 'public'

        if domain_name + '.' == zone_name and zone_type == response_zone_type:
            if zone_id is not None:
                error = 'Multiple hosted zones with the same name {0} were found'.format(domain_name)
                break

            zone_id = i['Id'].partition("hostedzone/")[2]

    if zone_id is None and error is None:
        error = 'The hosted zone {0} does not exist'.format(domain_name)

    time.sleep(0.5)

    return zone_id, error


def upsert(zone_id, action_requests):
    action_json = []
    msg = None
    error = None

    for action_request in action_requests:
        action_json.append(action_request.generate_change_recordSet_json())

    try:
        upsert_response = route53.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': action_json
            }
        )

        msg = upsert_response['ChangeInfo']['Id']

        time.sleep(1)

    except Exception as e:
        time.sleep(0.5)
        error = 'Upsert failed with error: ', upsert_response

    return msg, error


def process_upserts(upsert_list):
    for domain_name in upsert_list.keys():
        action_requests = upsert_list[domain_name]

        zone_id, zone_id_error = get_hosted_zone_id(domain_name, domain_name[0].zoneType)

        msg, upsert_error = upsert(zone_id)



def handler(event, context):
    try:
        data_file = event['file_name']

        bucket = data_file['bucket']['name']
        key = data_file['object']['key']

        csv_data = read_csv_input(bucket, key)
        upsert_list = {}
        delete_list = []
        error = None

        for i, row in enumerate(csv_data):
            request_info = Route53Request(row['dns_request_option'],
                                          domainName=row['domain_name'],
                                          recordSetName=row['record_name'],
                                          recordSetValue=row['value'],
                                          recordSetType=row['record_type']
                                          )

            if request_info.is_valid_action() == False:
                error = ("Invalid request action", i+1)
                break

            if request_info.is_valid_record_type() == False:
                error = ("Record type is not recognised", i+1)
                break

            if request_info.action == 'UPSERT':
                if request_info.domainName not in upsert_list.keys():
                    upsert_list[request_info.domainName] = [request_info]
                else:
                    upsert_list[request_info.domainName].append(request_info)
            else:
                delete_list.append(request_info)

        if error is not None:
            APIresponse = {
                "number": event['number'],
                "state": "Validation Error",
                "request_number": error[1],
                "message": error[0]
            }

            return APIresponse

        # Process Upserts
        error = process_upserts(upsert_list)

        # Process Deletes


        # Get Zone ID before performing action





    except Exception as e:
        print(e) ## or raise to get more enhanced details
        APIresponse = {
            "number": event['number'],
            "state": "Error"
        }

    return APIresponse