# google_sync.py — Google Sheets & Drive Sync
import os
import json
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
TOKEN_FILE = "token.pickle"
CREDENTIALS_FILE = "credentials.json"


def get_google_services():
    """OAuth लगइन गरेर Sheets + Drive service फर्काउने"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "credentials.json भेटिएन। Google Cloud Console बाट डाउनलोड गरेर प्रोजेक्ट फोल्डरमा राख्नुहोस्।"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive


# ============================================================
# 📊 SHEETS FUNCTIONS
# ============================================================
def create_spreadsheet(title: str) -> dict:
    """नयाँ Google Sheet बनाउने"""
    sheets, _ = get_google_services()
    body = {"properties": {"title": title}}
    result = sheets.spreadsheets().create(body=body, fields="spreadsheetId,spreadsheetUrl").execute()
    return {"id": result["spreadsheetId"], "url": result["spreadsheetUrl"]}


def write_dataframe_to_sheet(spreadsheet_id: str, df, sheet_name: str = "Sheet1"):
    """Pandas DataFrame लाई Sheet मा लेख्ने"""
    sheets, _ = get_google_services()

    # Sheet अवस्थित छ कि जाँच
    meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta["sheets"]]

    if sheet_name not in existing:
        sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}
        ).execute()

    # DataFrame → list of lists (header सहित)
    values = [df.columns.tolist()] + df.astype(str).values.tolist()

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

    return True


def read_sheet_as_dataframe(spreadsheet_id: str, sheet_name: str = "Sheet1"):
    """Sheet बाट DataFrame पढ्ने"""
    import pandas as pd
    sheets, _ = get_google_services()
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1:Z10000"
    ).execute()
    values = result.get("values", [])
    if not values:
        return pd.DataFrame()
    header = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=header)


# ============================================================
# ☁️ DRIVE FUNCTIONS
# ============================================================
def upload_file_to_drive(local_path: str, drive_folder_id: str = None) -> dict:
    """लोकल फाइल Drive मा अपलोड गर्ने"""
    _, drive = get_google_services()
    file_name = os.path.basename(local_path)
    media = MediaFileUpload(local_path, resumable=True)

    metadata = {"name": file_name}
    if drive_folder_id:
        metadata["parents"] = [drive_folder_id]

    file = drive.files().create(body=metadata, media_body=media, fields="id,name,webViewLink").execute()
    return {"id": file["id"], "name": file["name"], "url": file["webViewLink"]}


def list_drive_files(query: str = "", max_results: int = 20) -> list:
    """Drive मा फाइल खोज्ने"""
    _, drive = get_google_services()
    q = query or "trashed=false"
    results = drive.files().list(
        q=q, pageSize=max_results, fields="files(id,name,mimeType,webViewLink,size)"
    ).execute()
    return results.get("files", [])


def download_file_from_drive(file_id: str, save_path: str) -> str:
    """Drive बाट फाइल डाउनलोड गर्ने"""
    from googleapiclient.http import MediaIoBaseDownload
    import io
    _, drive = get_google_services()
    request = drive.files().get_media(fileId=file_id)
    fh = io.FileIO(save_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    return save_path