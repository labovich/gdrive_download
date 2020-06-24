#!/usr/bin/env python3

import argparse
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class Drive:
    def __init__(self, credentials_path=None):
        self.credentials_path = credentials_path if credentials_path else 'credentials.json'
        self.credentials = service_account.Credentials.from_service_account_file(self.credentials_path, scopes=SCOPES)
        self.service = build('drive', 'v3', credentials=self.credentials)

    def download(self, obj, path):
        file_path = os.path.join(path, obj['name'])

        if not os.path.isfile(file_path):
            request = self.service.files().get_media(fileId=obj['id'])
            with open(file_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print("Download {} {}%".format(obj['name'], int(status.progress() * 100)))
        else:
            print(f"File {obj['name']} alredy exist.")

    def folder(self, folder_id, parent_path, next_page_token=None):
        kwargs = {
            'fields': "nextPageToken, files(id, name, mimeType)",
            'q': f"'{folder_id}' in parents",
            'pageSize': 20
        }

        if next_page_token is not None:
            kwargs['pageToken'] = next_page_token

        results = self.service.files().list(**kwargs).execute()

        for obj in results.get('files', []):
            if obj['mimeType'] == 'application/vnd.google-apps.folder':
                path = os.path.join(parent_path, obj['name'])
                if not os.path.isdir(path):
                    os.mkdir(path)
                self.folder(obj['id'], path)
            else:
                self.download(obj, parent_path)

        next_pt = results.get('nextPageToken')
        if next_pt:
            self.folder(folder_id, parent_path, next_pt)


def get_parser():
    parser = argparse.ArgumentParser(description="Google drive downloader")
    parser.add_argument('-d', action='store', dest='out_dir', default=os.getcwd())
    parser.add_argument('-c', action='store', dest='credentials_path', default='credentials.json')
    parser.add_argument('file_id', action='store')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    drive = Drive(args.credentials_path)
    drive.folder(args.file_id, args.out_dir)
    print('Done!')
