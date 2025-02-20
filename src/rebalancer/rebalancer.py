import math
import os
import pickle
import base64
from email.mime.text import MIMEText

# Google / GMail dependencies
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Local modules
from src.modules.calc_bucket_allocation import BucketAllocator
from src.modules.get_metrics import MetricsCollector

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('config/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def send_email(subject, body, to_email):
    service = get_gmail_service()
    message = MIMEText(body)
    message['to'] = to_email
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw_message}
    sent_message = service.users().messages().send(userId='me', body=message_body).execute()
    print("Email sent, message id:", sent_message.get('id'))
    return sent_message

"""
Rebalancer Class - Skeleton Implementation with Email Notification

NOTE:
This class is a simplified skeleton for demonstration.
It does not execute actual blockchain transactions.
It fetches pool metrics and computes bucket ranges via BucketAllocator,
then uses both the narrow and wide bucket ranges to decide if a rebalance is needed.
In production, you would also implement logic to fire on-chain transactions.
"""

class Rebalancer:
    def __init__(self, api_key, subgraph_id, pool_id, notification_email):
        self.api_key = api_key
        self.subgraph_id = subgraph_id
        self.pool_id = pool_id
        self.notification_email = notification_email
        # Active bucket stores the last-used narrow bucket range.
        self.active_bucket = None

    def check_rebalance(self):
        # Get all current metrics and bucket info
        bucket_info = BucketAllocator.get_current_bucket_allocation(
            self.api_key, self.subgraph_id, self.pool_id,
            volatility_threshold=0.01,
            narrow_pct=0.001,  # ±0.1%
            wide_pct=0.002     # ±0.2%
        )
        current_tick = bucket_info["current_tick"]
        narrow_bucket = bucket_info["allocation"]["narrow_bucket"]
        wide_bucket = bucket_info["allocation"]["wide_bucket"]

        # First-time liquidity provision: set active bucket to the narrow bucket.
        if self.active_bucket is None:
            self.active_bucket = narrow_bucket
            msg = (f"No active bucket. New position would be created with narrow bucket: {narrow_bucket}\n"
                   f"Wide bucket: {wide_bucket}\nDetails: {bucket_info}")
            print(msg)
            send_email("Rebalance Alert: Create Position", msg, self.notification_email)
            return {"rebalance_needed": True, "action": "create_position", "details": bucket_info}

        # If current tick is within the active narrow bucket, no rebalance is needed.
        if narrow_bucket[0] <= current_tick <= narrow_bucket[1]:
            msg = f"No rebalance needed. Current tick {current_tick} is within narrow bucket {narrow_bucket}."
            print(msg)
            return {"rebalance_needed": False, "action": None, "details": bucket_info}

        # If current tick is outside the wide bucket, it's an urgent alert.
        if current_tick < wide_bucket[0] or current_tick > wide_bucket[1]:
            msg = (f"URGENT: Current tick {current_tick} is outside the wide bucket {wide_bucket}.\n"
                   f"Details: {bucket_info}")
            print(msg)
            send_email("Rebalance Alert: Urgent Rebalance Needed", msg, self.notification_email)
            return {"rebalance_needed": True, "action": "urgent_rebalance", "details": bucket_info}

        # If current tick is within the wide bucket but outside the narrow bucket, it's a moderate alert.
        msg = (f"Warning: Current tick {current_tick} is outside the narrow bucket {narrow_bucket} "
               f"but within the wide bucket {wide_bucket}.\nDetails: {bucket_info}")
        print(msg)
        send_email("Rebalance Alert: Moderate Rebalance Recommended", msg, self.notification_email)
        return {"rebalance_needed": True, "action": "moderate_rebalance", "details": bucket_info}

if __name__ == "__main__":
    API_KEY = "6bfcf592f7ffd72bce3c7e77bad7f5e5"
    SUBGRAPH_ID = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    POOL_ID = "0xd340b57aacdd10f96fc1cf10e15921936f41e29c"
    NOTIFICATION_EMAIL = "kshitijchakravarty@gmail.com"

    rebalancer = Rebalancer(API_KEY, SUBGRAPH_ID, POOL_ID, NOTIFICATION_EMAIL)
    result = rebalancer.check_rebalance()
    print("Rebalance check result:")
    print(result)
