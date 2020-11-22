import json


class Route53Request:
    def __init__(self, action, domainName, zoneType='public', recordSetName=None, recordSetValue=None,
                 recordSetType=None, ttl=300):
        self.action = action
        self.domainName = domainName.lower()
        self.zoneType = zoneType
        self.recordSetName = recordSetName
        self.recordSetValue = recordSetValue
        self.recordSetType = recordSetType
        self.ttl = ttl

        self.split_multiple_record_values()

        if self.recordSetType == 'TXT':
            self.add_quotes_to_txt_values()

    def set_zoneType(self, zoneType):
        self.zoneType = zoneType

    def set_recordSetName(self, recordSetName):
        self.recordSetName = recordSetName

    def set_recordSetValue(self, recordSetValue):
        self.recordSetValue = recordSetValue

    def set_recordSetType(self, recordSetType):
        self.recordSetType = recordSetType

    def is_valid_action(self):
        if self.action not in ['UPSERT', 'DELETE']:
            return False
        return True

    def is_valid_record_type(self):
        if self.recordSetType not in ['MX', 'PTR', 'A', 'CNAME', 'SRV', 'TXT', 'NS', 'AAAA']:
            return False
        return True

    def split_multiple_record_values(self):
        record_set_values = self.recordSetValue.replace(' ', '').split(',')

        if len(record_set_values) > 1:
            self.recordSetValue = record_set_values
        else:
            self.recordSetValue = record_set_values[0]

    def add_quotes_to_txt_values(self):
        new_record_set_values = []

        for val in self.recordSetValue:
            new_record_set_values.append("\"" + val + "\"")

        self.recordSetValue = new_record_set_values

    def generate_change_recordSet_json(self):
        request_json = {
            'Action': self.action,
            'ResourceRecordSet': {
                'Name': self.recordSetName,
                'Type': self.recordSetType,
                'TTL': self.ttl,
                'ResourceRecords': [
                    {
                        'Value': self.recordSetValue
                    }
                ]
            }
        }

        return request_json
