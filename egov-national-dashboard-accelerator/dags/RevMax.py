from airflow import DAG
from hooks.elastic_hook import ElasticHook
from airflow.hooks.base import BaseHook
from airflow.operators.python_operator import PythonOperator
from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta, timezone
from datetime import date
from pytz import timezone
from pydruid.client import *
import logging
import pandas as pd
import numpy as np
import json
import logging
import os
import csv
import requests
from pytz import timezone



default_args = {
'owner': 'airflow',
'depends_on_past': False,
'retries': 3,
'retry_delay': timedelta(seconds=10),
'start_date': datetime(2017, 1, 24)
}

dag = DAG('rev_max', default_args=default_args, schedule_interval=None)
druid_url = "https://druid-qa.ifix.org.in/druid/indexer/v1/task"

def elastic_dump_pt(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query = """
    {{
    "size": 1000,
    "_source": ["Data.propertyId","data.superBuiltUpArea","Data.channel", "Data.tenantId", "Data.ward.name", 
    "Data.ward.code","Data.source", "Data.propertyType", "Data.accountId", "Data.noOfFloors", "Data.@timestamp", 
    "Data.ownershipCategory", "Data.acknowldgementNumber", "Data.usageCategory", "Data.status"],
    "query": {{
        "bool": {{
        "must_not": [
            {{
            "term": {{
                "Data.tenantId.keyword": "pb.testing"
            }}
            }}
        ],
        "must": [
            {{
                "range": {{
                    "Data.@timestamp": {{
                    "gte": {0},
                    "lte": {1},
                    "format": "epoch_millis"
                }}
              }}
            }}
        ]
        }}
    }},
    "sort": [
        {{
        "Data.@timestamp": {{
            "order": "desc"
        }}
        }}
    ]
    }}"""

    resp = hook.search('property-services/_search', json.loads(query.format(start,end)))
    logging.info(resp['hits']['hits'])
    with open("property_service.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))
    return resp['hits']['hits']

def elastic_dump_tl(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query = """
    {{
    "size": 1000,
    "_source": [
    "Data.ward.name",
    "Data.ward.code",
    "Data.tradelicense"
    ],
    "query": {{
        "bool": {{
        "must_not": [
            {{
            "term": {{
                "Data.tradelicense.tenantId.keyword": "pb.testing"
            }}
            }}
        ],
        "must": [
            {{
                "range": {{
                    "Data.tradelicense.@timestamp": {{
                    "gte": {0},
                    "lte": {1},
                    "format": "epoch_millis"
                }}
              }}
            }}
        ]
        }}
    }},
    "sort": [
        {{
        "Data.tradelicense.@timestamp": {{
            "order": "desc"
        }}
        }}
    ]
    }}
    """
    resp = hook.search('tlindex-v1-enriched/_search', json.loads(query.format(start,end)))
    logging.info(resp['hits']['hits'])
    with open("trade_license.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))
    return resp['hits']['hits']
    
def elastic_dump_ws(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query="""
    {{
        "size": 1000,
        "_source": [
                "Data.applicationType",
                "Data.applicationNo",
                "Data.oldConnectionNo",
                "Data.proposedPipeSize",
                "Data.pipeSize",
                "Data.channel",
                "Data.channel",
                "Data.propertyUsageType",
                "Data.ward.name",
                "Data.ward.code",
                "Data.connectionType",
                "Data.applicationStatus",
                "Data.roadCuttingArea",
                "Data.rainWaterHarvesting",
                "Data.id",
                "Data.dateEffectiveFrom",
                "Data.propertyId",
                "Data.connectionNo",
                "Data.plumberInfo",
                "Data.proposedTaps",
                "Data.noOfTaps",
                "Data.waterSource",
                "Data.connectionCategory",
                "Data.connectionHolders",
                "Data.roadCuttingInfo",
                "Data.roadType",
                "Data.@timestamp",
                "data.meterId",
                "Data.tenantId",
                "Data.status"
            ],
        "query": {{
          "bool" :{{
            "must": [
            {{
            "range": {{
                "Data.@timestamp": {{
                "gte": {0},
                "lte": {1},
                "format": "epoch_millis"
                }}
            }}
            }}
          ]
            }}
            }},
        "sort": [
        {{
        "Data.@timestamp": {{
            "order": "desc"
        }}
        }}
    ]
    }}
    """
    resp = hook.search('water-services-enriched/_search', json.loads(query.format(start,end)))
    logging.info(resp['hits']['hits'])
    with open("water_service.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))
    return resp['hits']['hits']

def elastic_dump_collection_pt(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query="""
    {{
    "size": 1000,
    "_source":["dataObject.paymentMode","dataObject.transactionNumber","dataObject.tenantId",
    "dataObject.paymentDetails.businessService","dataObject.paymentDetails.totalDue","dataObject.paymentDetails.receiptType",
    "dataObject.paymentDetails.receiptDate","dataObject.paymentDetails.bill.consumerCode","dataObject.paymentDetails.bill.billNumber",
    "dataObject.paymentDetails.bill.status","dataObject.paymentDetails.bill.billDate","dataObject.paymentDetails.bill.billDetails.fromPeriod",
    "dataObject.paymentDetails.bill.billDetails.toPeriod","dataObject.paymentDetails.bill.billDetails.demandId","dataObject.paymentDetails.bill.billDetails.billId", 
    "dataObject.paymentDetails.bill.billDetails.id", "dataObject.paymentDetails.bill.billNumber", 
    "dataObject.paymentDetails.totalAmountPaid","dataObject.paymentDetails.receiptNumber","dataObject.payer.name",
    "dataObject.payer.id","dataObject.paymentStatus","domainObject.ward.code","domainObject.ward.name","domainObject.propertyId",
    "domainObject.usageCategory","domainObject.tradeLicense","domainObject.propertyUsageType"],
    "query": {{
        "bool": {{
        "must_not": [
            {{
            "term": {{
                "Data.tenantId.keyword": "pb.testing"
            }}
            }}
        ],
        "must": [
            {{
            "term": {{
                "dataObject.paymentDetails.businessService.keyword": "PT"
            }}
            }},
            {{
                "range": {{
                    "dataObject.paymentDetails.receiptDate": {{
                    "gte": {0},
                    "lte": {1},
                    "format": "epoch_millis"
                }}
              }}
            }}
        ]
        }}
    }},
    "sort": [
        {{
        "dataObject.paymentDetails.receiptDate": {{
            "order": "desc"
        }}
        }}
    ] 
    }}
    """
    resp = hook.search('dss-collection_v2/_search', json.loads(query.format(start,end))) 
    logging.info(resp['hits']['hits'])
    with open("dss_collection_pt.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))
    return resp['hits']['hits']

def elastic_dump_collection_tl(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query="""
    {{
    "size": 1000,
    "_source":["dataObject.paymentMode","dataObject.transactionNumber","dataObject.tenantId",
    "dataObject.paymentDetails.businessService","dataObject.paymentDetails.totalDue","dataObject.paymentDetails.receiptType",
    "dataObject.paymentDetails.receiptDate","dataObject.paymentDetails.bill.consumerCode","dataObject.paymentDetails.bill.billNumber",
    "dataObject.paymentDetails.bill.status","dataObject.paymentDetails.bill.billDate","dataObject.paymentDetails.bill.billDetails.fromPeriod",
    "dataObject.paymentDetails.bill.billDetails.toPeriod","dataObject.paymentDetails.bill.billDetails.demandId","dataObject.paymentDetails.bill.billDetails.billId", 
    "dataObject.paymentDetails.bill.billDetails.id", "dataObject.paymentDetails.bill.billNumber", 
    "dataObject.paymentDetails.totalAmountPaid","dataObject.paymentDetails.receiptNumber","dataObject.payer.name",
    "dataObject.payer.id","dataObject.paymentStatus","domainObject.ward.code","domainObject.ward.name","domainObject.propertyId",
    "domainObject.usageCategory","domainObject.tradeLicense","domainObject.propertyUsageType"],
    "query": {{
        "bool": {{
        "must_not": [
            {{
            "term": {{
                "Data.tenantId.keyword": "pb.testing"
            }}
            }}
        ],
        "must": [
            {{
            "term": {{
                "dataObject.paymentDetails.businessService.keyword": "TL"
            }}
            }},
            {{
                "range": {{
                    "dataObject.paymentDetails.receiptDate": {{
                    "gte": {0},
                    "lte": {1},
                    "format": "epoch_millis"
                }}
              }}
            }}
        ]
        }}
    }},
    "sort": [
        {{
        "dataObject.paymentDetails.receiptDate": {{
            "order": "desc"
        }}
        }}
    ] 
    }}
    """
    resp = hook.search('dss-collection_v2/_search',json.loads(query.format(start,end))) 
    logging.info(resp['hits']['hits'])
    with open("dss_collection_tl.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))
    return resp['hits']['hits']

def elastic_dump_collection_ws(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query="""
    {{
    "size": 1000,
    "_source":["dataObject.paymentMode","dataObject.transactionNumber","dataObject.tenantId",
    "dataObject.paymentDetails.businessService","dataObject.paymentDetails.totalDue","dataObject.paymentDetails.receiptType",
    "dataObject.paymentDetails.receiptDate","dataObject.paymentDetails.bill.consumerCode","dataObject.paymentDetails.bill.billNumber",
    "dataObject.paymentDetails.bill.status","dataObject.paymentDetails.bill.billDate","dataObject.paymentDetails.bill.billDetails.fromPeriod",
    "dataObject.paymentDetails.bill.billDetails.toPeriod","dataObject.paymentDetails.bill.billDetails.demandId","dataObject.paymentDetails.bill.billDetails.billId", 
    "dataObject.paymentDetails.bill.billDetails.id", "dataObject.paymentDetails.bill.billNumber", 
    "dataObject.paymentDetails.totalAmountPaid","dataObject.paymentDetails.receiptNumber","dataObject.payer.name",
    "dataObject.payer.id","dataObject.paymentStatus","domainObject.ward.code","domainObject.ward.name","domainObject.propertyId",
    "domainObject.usageCategory","domainObject.tradeLicense","domainObject.propertyUsageType"],
    "query": {{
        "bool": {{
        "must_not": [
            {{
            "term": {{
                "Data.tenantId.keyword": "pb.testing"
            }}
            }}
        ],
       "must": [
        {{
          "terms": {{
            "dataObject.paymentDetails.businessService.keyword": [
              "WS",
              "WS.ONE_TIME_FEE",
              "SW.ONE_TIME_FEE",
              "SW"
            ]
          }}
        }},
        {{
                "range": {{
                   "dataObject.paymentDetails.receiptDate": {{
                    "gte": {0},
                    "lte": {1},
                    "format": "epoch_millis"
                }}
              }}
        }}
   ]
        }}
    }},
    "sort": [
        {{
        "dataObject.paymentDetails.receiptDate": {{
            "order": "desc"
        }}
        }}
    ] 
    }}
    """
    resp = hook.search('dss-collection_v2/_search', json.loads(query.format(start,end))) 
    logging.info(resp['hits']['hits'])
    with open("dss_collection_ws.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))
    return resp['hits']['hits']

def elastic_dump_meter(start,end):
    hook = ElasticHook('GET', 'es_conn')
    query="""
    {{
        "size": 1000,
        "query": {{
            "bool": {{
            "must": [
                {{
                "range": {{
                    "Data.currentReadingDate": {{
                    "gte": {0},
                    "lte": {1},
                    "format": "epoch_millis"
                    }}
                }}
                }}
            ]
            }}
         }},
        "sort": [
        {{
        "Data.currentReadingDate": {{
            "order": "desc"
        }}
        }}
    ]
    }}
    """
    resp = hook.search('meter-services/_search', json.loads(query.format(start,end)))
    logging.info(resp['hits']['hits'])
    with open("meter_service.json", "w") as outfile:
        outfile.write(json.dumps(resp['hits']['hits']))

    return resp['hits']['hits']

def collect_data(**kwargs):
    date = kwargs['dag_run'].conf.get('start')
    enddate = kwargs['dag_run'].conf.get('end')
    localtz = timezone('Asia/Kolkata')
    dt_aware = localtz.localize(datetime.strptime(date, "%d-%m-%Y"))
    start = int(dt_aware.timestamp() * 1000)
    dt_aware = localtz.localize(datetime.strptime(enddate, "%d-%m-%Y"))
    end = int(dt_aware.timestamp()*1000) + (24 * 60 * 60 * 1000) - 1000
    logging.info(start)
    logging.info(end)
    elastic_dump_pt(start,end)
    elastic_dump_tl(start,end)
    elastic_dump_ws(start,end)
    #elastic_dump_meter() - not in punjab prod
    elastic_dump_collection_pt(start,end)
    elastic_dump_collection_tl(start,end)
    elastic_dump_collection_ws(start,end)
    return 'done collecting data'

def join_data():
    logging.info("in join")
    f= open('property_service.json',"r")
    property_service_json = json.loads(f.read())
    f.close()

    f= open('trade_license.json',"r")
    trade_license_json = json.loads(f.read())
    f.close()

    f= open('water_service.json',"r")
    water_service_json = json.loads(f.read())
    f.close()

    f= open('dss_collection_pt.json',"r")
    dss_collection_pt_json = json.loads(f.read())
    f.close()

    f= open('dss_collection_tl.json',"r")
    dss_collection_tl_json = json.loads(f.read())
    f.close()
  
    f= open('dss_collection_ws.json',"r")
    dss_collection_ws_json = json.loads(f.read())
    f.close()
   
    # f= open('meter_service.json',"r")
    # meter_service_json = json.loads(f.read())
    # f.close()
  
    #property_service.csv
    df = get_dataframe_after_flattening(property_service_json)
    convert_dataframe_to_csv(dataframe=df,file_name="property_service")
    # water_service csv
    df = get_dataframe_after_flattening(water_service_json)
    convert_dataframe_to_csv(dataframe=df,file_name="water_service")
    # trade service csv
    df = get_dataframe_after_flattening(trade_license_json)
    convert_dataframe_to_csv(dataframe=df,file_name="trade_license")
    # meter_service csv
    # df = get_dataframe_after_flattening(meter_service_json)
    # convert_dataframe_to_csv(dataframe=df,file_name="meter_service")
    # dss_collection pt csv
    df = get_dataframe_after_flattening(dss_collection_pt_json)
    convert_dataframe_to_csv(dataframe=df,file_name="dss_collection_pt")
     # dss_collection tl csv
    df = get_dataframe_after_flattening(dss_collection_tl_json)
    convert_dataframe_to_csv(dataframe=df,file_name="dss_collection_tl")
    # dss_collection ws csv
    df = get_dataframe_after_flattening(dss_collection_ws_json)
    convert_dataframe_to_csv(dataframe=df,file_name="dss_collection_ws")


    property_service_after_flattening = get_dataframe_after_flattening(property_service_json)

    water_service_after_flattening = get_dataframe_after_flattening(water_service_json)

    dss_collection_pt_after_flattening = get_dataframe_after_flattening(dss_collection_pt_json)

    dss_collection_tl_after_flattening = get_dataframe_after_flattening(dss_collection_tl_json)

    dss_collection_ws_after_flattening = get_dataframe_after_flattening(dss_collection_ws_json)

    # meter_services_after_flattening = get_dataframe_after_flattening(meter_service_json)

    trade_licence_after_flattening = get_dataframe_after_flattening(trade_license_json)

    #join water and meter
    #water_and_meter_services(water_services=water_service_after_flattening,meter_services=meter_services_after_flattening)
    #join trade and property
    trade_and_property_services(trade_services=trade_licence_after_flattening,property_services=property_service_after_flattening)
    #join water and property
    property_and_water_services(water_services=water_service_after_flattening,property_services=property_service_after_flattening)
    #join water and collection
    dss_collection_and_water(water_services=water_service_after_flattening,dss_collection=dss_collection_ws_after_flattening)
    #join property and collection
    dss_collection_and_property(property_services=property_service_after_flattening,dss_collection=dss_collection_pt_after_flattening)
    #join trade and collection
    dss_collection_and_trade(trade_services=trade_licence_after_flattening,dss_collection=dss_collection_tl_after_flattening)
    #join water and property for rule3
    rule3(property_services=property_service_after_flattening,water_services=water_service_after_flattening)

def upload_property_service():
    data = ""
    f= open("property_service.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()

    payload =  """{{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "test2",
        "timestampSpec": {{
            "column": "!!!_no_such_column_!!!",
            "missingValue": "2010-01-01T00:00:00Z"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "additionaldetails",
            "billexpirytime",
            "businessservice",
            "consumercode",
            "consumertype",
            "createdby",
            {{
                "type": "long",
                "name": "createdtime"
            }},
            "fixedbillexpirydate",
            "id",
            "ispaymentcompleted",
            "lastmodifiedby",
            {{
                "type": "long",
                "name": "lastmodifiedtime"
            }},
            {{
                "type": "long",
                "name": "minimumamountpayable"
            }},
            "payer",
            "status",
            {{
                "type": "long",
                "name": "taxperiodfrom"
            }},
            {{
                "type": "long",
                "name": "taxperiodto"
            }},
            "tenantid"
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}"""
    q=payload.format(data)
    header = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_trade_license():
    data = ""
    f= open("trade_license.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()

    payload =  """{{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "test2",
        "timestampSpec": {{
            "column": "!!!_no_such_column_!!!",
            "missingValue": "2010-01-01T00:00:00Z"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "additionaldetails",
            "billexpirytime",
            "businessservice",
            "consumercode",
            "consumertype",
            "createdby",
            {{
                "type": "long",
                "name": "createdtime"
            }},
            "fixedbillexpirydate",
            "id",
            "ispaymentcompleted",
            "lastmodifiedby",
            {{
                "type": "long",
                "name": "lastmodifiedtime"
            }},
            {{
                "type": "long",
                "name": "minimumamountpayable"
            }},
            "payer",
            "status",
            {{
                "type": "long",
                "name": "taxperiodfrom"
            }},
            {{
                "type": "long",
                "name": "taxperiodto"
            }},
            "tenantid"
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}"""
    q=payload.format(data)
    header = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_water_service():
    data = ""
    f= open("water_service.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()

    payload =  """{{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "test2",
        "timestampSpec": {{
            "column": "!!!_no_such_column_!!!",
            "missingValue": "2010-01-01T00:00:00Z"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "additionaldetails",
            "billexpirytime",
            "businessservice",
            "consumercode",
            "consumertype",
            "createdby",
            {{
                "type": "long",
                "name": "createdtime"
            }},
            "fixedbillexpirydate",
            "id",
            "ispaymentcompleted",
            "lastmodifiedby",
            {{
                "type": "long",
                "name": "lastmodifiedtime"
            }},
            {{
                "type": "long",
                "name": "minimumamountpayable"
            }},
            "payer",
            "status",
            {{
                "type": "long",
                "name": "taxperiodfrom"
            }},
            {{
                "type": "long",
                "name": "taxperiodto"
            }},
            "tenantid"
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}"""
    q=payload.format(data)
    header = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_water_and_property():
    data = ""
    f= open("water_and_property.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()

    payload =  """{{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "test2",
        "timestampSpec": {{
            "column": "!!!_no_such_column_!!!",
            "missingValue": "2010-01-01T00:00:00Z"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "additionaldetails",
            "billexpirytime",
            "businessservice",
            "consumercode",
            "consumertype",
            "createdby",
            {{
                "type": "long",
                "name": "createdtime"
            }},
            "fixedbillexpirydate",
            "id",
            "ispaymentcompleted",
            "lastmodifiedby",
            {{
                "type": "long",
                "name": "lastmodifiedtime"
            }},
            {{
                "type": "long",
                "name": "minimumamountpayable"
            }},
            "payer",
            "status",
            {{
                "type": "long",
                "name": "taxperiodfrom"
            }},
            {{
                "type": "long",
                "name": "taxperiodto"
            }},
            "tenantid"
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}"""
    q=payload.format(data)
    header = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_trade_and_property():
    data = ""
    f= open("trade_and_property.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()

    payload =  """{{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "test2",
        "timestampSpec": {{
            "column": "!!!_no_such_column_!!!",
            "missingValue": "2010-01-01T00:00:00Z"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "additionaldetails",
            "billexpirytime",
            "businessservice",
            "consumercode",
            "consumertype",
            "createdby",
            {{
                "type": "long",
                "name": "createdtime"
            }},
            "fixedbillexpirydate",
            "id",
            "ispaymentcompleted",
            "lastmodifiedby",
            {{
                "type": "long",
                "name": "lastmodifiedtime"
            }},
            {{
                "type": "long",
                "name": "minimumamountpayable"
            }},
            "payer",
            "status",
            {{
                "type": "long",
                "name": "taxperiodfrom"
            }},
            {{
                "type": "long",
                "name": "taxperiodto"
            }},
            "tenantid"
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}"""
    q=payload.format(data)
    header = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_rule_3():
    data = ""
    f= open("rule_3.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()

    payload =  """
    {{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "rule_3",
        "timestampSpec": {{
            "column": "_source.Data.@timestamp",
            "format": "iso"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "_id",
            "_index",
            "_score",
            "_source.Data.accountId",
            "_source.Data.acknowldgementNumber",
            "_source.Data.channel",
            {{
                "type": "long",
                "name": "_source.Data.noOfFloors"
            }},
            "_source.Data.ownershipCategory",
            "_source.Data.propertyId",
            "_source.Data.propertyType",
            "_source.Data.source",
            "_source.Data.status",
            "_source.Data.tenantId",
            "_source.Data.usageCategory",
            "_source.Data.ward.code",
            "_source.Data.ward.name",
            "_type",
            {{
                "type": "long",
                "name": "sort.0"
            }}
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}
    """
    q=payload.format(data)
    logging.info(q)
    header = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_dss_service():
    data = ""
    header = {
    'Content-Type': 'application/json'
    }
    payload =  """{{
    "type": "index_parallel",
    "spec": {{
        "ioConfig": {{
        "type": "index_parallel",
        "inputSource": {{
            "type": "inline",
            "data": "{0}"
        }},
        "inputFormat": {{
            "type": "csv",
            "findColumnsFromHeader": true
        }}
        }},
        "tuningConfig": {{
        "type": "index_parallel",
        "partitionsSpec": {{
            "type": "dynamic"
        }}
        }},
        "dataSchema": {{
        "dataSource": "test2",
        "timestampSpec": {{
            "column": "!!!_no_such_column_!!!",
            "missingValue": "2010-01-01T00:00:00Z"
        }},
        "dimensionsSpec": {{
            "dimensions": [
            "additionaldetails",
            "billexpirytime",
            "businessservice",
            "consumercode",
            "consumertype",
            "createdby",
            {{
                "type": "long",
                "name": "createdtime"
            }},
            "fixedbillexpirydate",
            "id",
            "ispaymentcompleted",
            "lastmodifiedby",
            {{
                "type": "long",
                "name": "lastmodifiedtime"
            }},
            {{
                "type": "long",
                "name": "minimumamountpayable"
            }},
            "payer",
            "status",
            {{
                "type": "long",
                "name": "taxperiodfrom"
            }},
            {{
                "type": "long",
                "name": "taxperiodto"
            }},
            "tenantid"
            ]
        }},
        "granularitySpec": {{
            "queryGranularity": "none",
            "rollup": false,
            "segmentGranularity": "day"
        }}
        }}
    }}
    }}"""
   

    f= open("dss_collection_ws.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()
    q=payload.format(data)
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

    data = ""
    f= open("dss_collection_pt.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()
    q=payload.format(data)
    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

    data=""
    f= open("dss_collection_tl.csv","r")
    spamreader = csv.reader(f, delimiter=',', quotechar='"')
    for row in spamreader:
        data+=', '.join(row)
        data+='\\n'
    f.close()
    q=payload.format(data)

    response = requests.request("POST", druid_url, headers=header, data=q)
    logging.info(response.text)

def upload_data():
    logging.info("Upload data to Druid")
    # upload_property_service()
    # upload_trade_license()
    # upload_water_service()
    #upload_water_and_meter()
    #upload_meter_service()
    #upload_demand()
    # upload_water_and_property()
    # upload_trade_and_property() 
    upload_rule_3()   
    #upload_dss_service()


    #url = "https://druid-qa.ifix.org.in/druid/indexer/v1/task"
    # data = ""
    # f= open("property_service.csv","r")
    # spamreader = csv.reader(f, delimiter=',', quotechar='"')
    # for row in spamreader:
    #     data+=', '.join(row)
    #     data+='\\n'
    # f.close()

    # payload =  """{{
    # "type": "index_parallel",
    # "spec": {{
    #     "ioConfig": {{
    #     "type": "index_parallel",
    #     "inputSource": {{
    #         "type": "inline",
    #         "data": "{0}"
    #     }},
    #     "inputFormat": {{
    #         "type": "csv",
    #         "findColumnsFromHeader": true
    #     }}
    #     }},
    #     "tuningConfig": {{
    #     "type": "index_parallel",
    #     "partitionsSpec": {{
    #         "type": "dynamic"
    #     }}
    #     }},
    #     "dataSchema": {{
    #     "dataSource": "test2",
    #     "timestampSpec": {{
    #         "column": "!!!_no_such_column_!!!",
    #         "missingValue": "2010-01-01T00:00:00Z"
    #     }},
    #     "dimensionsSpec": {{
    #         "dimensions": [
    #         "additionaldetails",
    #         "billexpirytime",
    #         "businessservice",
    #         "consumercode",
    #         "consumertype",
    #         "createdby",
    #         {{
    #             "type": "long",
    #             "name": "createdtime"
    #         }},
    #         "fixedbillexpirydate",
    #         "id",
    #         "ispaymentcompleted",
    #         "lastmodifiedby",
    #         {{
    #             "type": "long",
    #             "name": "lastmodifiedtime"
    #         }},
    #         {{
    #             "type": "long",
    #             "name": "minimumamountpayable"
    #         }},
    #         "payer",
    #         "status",
    #         {{
    #             "type": "long",
    #             "name": "taxperiodfrom"
    #         }},
    #         {{
    #             "type": "long",
    #             "name": "taxperiodto"
    #         }},
    #         "tenantid"
    #         ]
    #     }},
    #     "granularitySpec": {{
    #         "queryGranularity": "none",
    #         "rollup": false,
    #         "segmentGranularity": "day"
    #     }}
    #     }}
    # }}
    # }}"""


def replace_empty_objects_with_null_value(df):
    df_columns = df.columns.tolist()
    for cols in df_columns:
        try:
            unique_values = df[cols].unique().tolist()
            if (len(unique_values) == 1) and (
                unique_values == "{}" or unique_values == "[]"
            ):
                df[cols] = np.NaN
        except Exception as e:
            df[cols] = np.NaN
    return df

def convert_dataframe_to_csv(dataframe, file_name):
    dataframe.to_csv(
       f"""{file_name}.csv""", index=False
    )
    logging.info("absolute path {0}".format(os.path.abspath(f"""{file_name}.csv"""))) 

    
    logging.info(dataframe)

def get_dataframe_after_flattening(json_data):
    logging.info(json_data)  
    df = [flatten_json(d) for d in json_data]  
    df = pd.DataFrame(df)
    df = replace_empty_objects_with_null_value(df)
    return df

def flatten_json(y):
    out = {}
    def flatten(x, name =''):
        if type(x) is dict:            
            for a in x:
                flatten(x[a], name + a + '.')
        elif type(x) is list:          
            i = 0        
            for a in x:                
                flatten(a, name + str(i) + '.')
                i += 1
        else:
            out[name[:-1]] = x
  
    flatten(y)
    return out

# def water_and_meter_services(water_services, meter_services):
#     water_and_meter = water_services.merge(
#         meter_services,
#         how="inner",
#         left_on="_source.Data.connectionNo",
#         right_on="_source.Data.connectionNo",
#         suffixes=("_water", "_meter"),
#     )
#     convert_dataframe_to_csv(dataframe=water_and_meter, file_name="water_and_meter")

def property_and_water_services(water_services, property_services):
    water_and_property = water_services.merge(
        property_services,
        how="inner",
        left_on="_source.Data.propertyId",
        right_on="_source.Data.propertyId",
        suffixes=("_water", "_property"),
    )
    convert_dataframe_to_csv(dataframe=water_and_property, file_name="water_and_property"
    )

def trade_and_property_services(trade_services, property_services):
    trade_and_property = trade_services.merge(
        property_services,
        how="inner",
        left_on="_source.Data.tradelicense.propertyId",
        right_on="_source.Data.propertyId",
        suffixes=("_trade", "_property"),
    )
    convert_dataframe_to_csv(dataframe=trade_and_property, file_name="trade_and_property"
    )

def dss_collection_and_water(dss_collection,water_services):
    collection_and_water = dss_collection.merge(
        water_services,
        how="inner",
        left_on="_source.dataObject.paymentDetails.bill.consumerCode",
        right_on="_source.Data.applicationNo",
        suffixes=("_trade", "_property"),
    )
    convert_dataframe_to_csv(dataframe=collection_and_water, file_name="collection_and_water"
    )

def dss_collection_and_property(dss_collection,property_services):
    collection_and_property = dss_collection.merge(
        property_services,
        how="inner",
        left_on="_source.dataObject.paymentDetails.bill.consumerCode",
        right_on="_source.Data.propertyId",
        suffixes=("_trade", "_property"),
    )
    convert_dataframe_to_csv(
        dataframe=collection_and_property, file_name="collection_and_property"
    )

def dss_collection_and_trade(trade_services, dss_collection):
    collection_and_trade = dss_collection.merge(
        trade_services,
        how="inner",
        left_on="_source.dataObject.paymentDetails.bill.consumerCode",
        right_on="_source.Data.tradelicense.applicationNumber",
        suffixes=("_trade", "_property"),
    )
    convert_dataframe_to_csv(
        dataframe=collection_and_trade, file_name="collection_and_trade"
    )

def rule3(property_services, water_services):
    water_and_property = water_services.merge(
        property_services,
        how="inner",
        left_on="_source.Data.propertyId",
        right_on="_source.Data.propertyId",
        suffixes=("_water", "_property"),
    )

    water_and_property = water_and_property["_source.Data.propertyId"]

    query = f"""(`_source.Data.propertyType`.str.upper() != 'VACANT')"""

    property_services = property_services.query(query)

    property_services = property_services[
        (~(property_services["_source.Data.propertyId"].isin(water_and_property)))
    ]
    convert_dataframe_to_csv(dataframe=property_services, file_name="rule_3")

flattendata = PythonOperator(
task_id='flatten_data',
python_callable=collect_data,
provide_context=True,
dag=dag)

joindata = PythonOperator(
task_id='join_data',
python_callable=join_data,
provide_context=True,
dag=dag)

uploaddata = PythonOperator(
task_id='upload_data',
python_callable=upload_data,
provide_context=True,
dag=dag)


flattendata >> joindata >> uploaddata
