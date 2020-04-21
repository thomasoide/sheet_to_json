import gspread, os.path, boto3, json, tempfile, requests
from datetime import datetime
from dateutil.parser import parse
from itertools import islice
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Pull .env variables for script use
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET', '')
SHEET_ID = os.environ.get('SHEET_ID', '')
KEYFILE = os.environ.get('JSON_KEY', '')

def switch(i):
    """
    Switch function to parse spaces out of categorical variables
    "key" is the input value and "value" is the value returned to the json object
    If you want the values as is from the Google sheet, disregard this function
    """
    switcher = {
        "key": "value"
    }
    return switcher.get(i, "")


def sheet_to_json(obj, filename):
    """
    The gspread package returns Google Sheet data as a 2D array. i.e.
    [
        [1,2]
        [3,4]
    ]
    To access the value 1 -- array[0][0]. This function eliminates the need to loop through each row.
    Access data by the column index. For example if you wanted to get the value from the first column, the code would be var = row[0]
    Reassign the variables you need in obj_props, which is what is written into the json file.
    """

    sheet_json = []
    for row in islice(obj, 1, None):
        name = row[0]
        city = row[2]
        thank = row[3]
        message = row[4]
        publish = row[5]

        """
        if you need rows ignored, add to this conditional. For example, a check for a null value in row[1] would look like this

        if not row or not row[1]
        """
        if not row:
            continue
        else:
            obj_props = {
                "name": name,
                "city": city,
                "thank": thank,
                "message": message,
                "publish": publish
            }
            sheet_json.append(obj_props)

    with open(filename, 'w') as f:
        json.dump(sheet_json, f)

    return

# hook up gspread credentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(KEYFILE, scope)
gc = gspread.authorize(credentials)

# open sheet
sheet = gc.open_by_key(SHEET_ID).get_worksheet(0)
sheet_array = sheet.get_all_values()

"""
Set file name. i.e. data/____.json. This is the file where the script writes JSON to.
"""
sheet_to_json(sheet_array, './data/wishes.json')

# push json to s3. if file does not need to go to s3, comment the following lines out.
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

"""
Assign variable path to s3_path variable, as well as the output variable with the file name.
"""
s3_path = 'assets/features/thomas/'
output = s3_path + 'wishes.json'

s3.upload_file('./data/wishes.json', AWS_S3_BUCKET, output)
