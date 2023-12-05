# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import urllib.request
from datetime import datetime

from restapi.models import *
from restapi.serializers import *

import pickle
import boto3

from constants import FILE_READER_TIMEOUT

class MetricsCollector:
    def __init__(self):
        pass

    def getMetricsDataFromS3(self):
        """fetches from external source"""
        client = boto3.client('s3')
        response = client.list_objects_v2(
            Bucket='s3_metrics_bucket_us-east-1',
        )
        contents = response["Contents"]
        metrics = []
        for key in contents:
            metric_object = boto3.get_object(Bucket=key, Key=key)
            metrics.append(metric_object)
        return metrics

    def transformMetrics(self, metrics):
        """transforms to a suitable structure"""
        for metric in metrics:
            aggregated = (metric["USA"] + metric["India"])/metrics["Total"]
            metric['aggregated'] = aggregated
        return metrics

    def writeMetricsDataToFile(self, metrics):
        """exports transformed data locally"""
        metrics_file = open("metrics.txt", "w+")
        metrics_file.write(metrics)

    def writeMetricsDataToS3(self, metrics):
        """exports transformed data externally"""
        boto3.put_object(
            Body=metrics,
            Bucket='transformed_metrics_bucket_q3',
            Key='transformed_metrics'
        )


class SignalsCollector:
    def __init__(self):
        pass

    def fetchSignalsData(self, ):
        """fetches from an external source"""
        signals = []
        signal_streams = ["https://new_signal_stream.com/latest", "https://signal_stream.com/latest"]
        for stream in signal_streams:
            data = UtilityService.reader(stream, FILE_READER_TIMEOUT)
            data = data.decode('utf-8')
            signals.extend(data.split("\n"))
        return signals

    def processSignal(self, signals):
        """transforms to a suitable structures"""
        list(map(lambda x: (x**2)**(1./3.), signals))

    def saveSignalsToPickle(self, signals):
        """exports transformed data locally"""
        storage = open("signaldump", "rb")
        pickle.dump(signals, storage)

    def saveSignalsToS3(self, signals):
        """exports transformed data externally"""
        boto3.put_object(
            Body=signals,
            Bucket='process_signal_bucket_us-east-1',
            Key='transformed_metrics'
        )

class LogsCollector:
    def __init__(self):
        pass

    def loopedReader(urls, num_threads):
        """
            Read multiple files through HTTP
        """
        result = []
        for url in urls:
            data = UtilityService.reader(url, FILE_READER_TIMEOUT)
            data = data.decode('utf-8')
            result.extend(data.split("\n"))
        result = sorted(result, key=lambda elem:elem[1])
        return result
    
    def sortByTimeStamp(logs):
        data = []
        for log in logs:
            data.append(log.split(" "))
        data = sorted(data, key=lambda elem: elem[1])
        return data

    def responseFormat(raw_data):
        response = []
        for timestamp, data in raw_data.items():
            entry = {'timestamp': timestamp}
            logs = []
            data = {k: data[k] for k in sorted(data.keys())}
            for exception, count in data.items():
                logs.append({'exception': exception, 'count': count})
            entry['logs'] = logs
            response.append(entry)
        return response

    def aggregate(cleaned_logs):
        data = {}
        for log in cleaned_logs:
            [key, text] = log
            value = data.get(key, {})
            value[text] = value.get(text, 0)+1
            data[key] = value
        return data

    def transform(logs):
        result = []
        for log in logs:
            [_, timestamp, text] = log
            text = text.rstrip()
            timestamp = datetime.utcfromtimestamp(int(int(timestamp)/1000))
            hours, minutes = timestamp.hour, timestamp.minute
            key = ''

            if minutes >= 45:
                if hours == 23:
                    key = "{:02d}:45-00:00".format(hours)
                else:
                    key = "{:02d}:45-{:02d}:00".format(hours, hours+1)
            elif minutes >= 30:
                key = "{:02d}:30-{:02d}:45".format(hours, hours)
            elif minutes >= 15:
                key = "{:02d}:15-{:02d}:30".format(hours, hours)
            else:
                key = "{:02d}:00-{:02d}:15".format(hours, hours)

            result.append([key, text])
            print(key)

        return result
class UtilityService:
    
    @staticmethod
    def reader(url, timeout):
        with urllib.request.urlopen(url, timeout=timeout) as conn:
            return conn.read()

    @staticmethod
    def getBalancesFromDues(dues):
        dues = [(k, v) for k, v in sorted(dues.items(), key=lambda item: item[1])]
        start = 0
        end = len(dues) - 1
        balances = []
        while start < end:
            amount = min(abs(dues[start][1]), abs(dues[end][1]))
            user_balance = {
                "from_user": dues[start][0].id,
                "to_user": dues[end][0].id,
                "amount": amount
            }
            balances.append(user_balance)
            dues[start] = (dues[start][0], dues[start][1] + amount)
            dues[end] = (dues[end][0], dues[end][1] - amount)
            if dues[start][1] == 0:
                start += 1
            else:
                end -= 1
        return balances