from PIL import Image
import pytesseract
import matplotlib.pyplot as plt
import pandas as pd
import re

# 웹훅
import requests

from google.oauth2 import service_account
from googleapiclient.discovery import build 
from googleapiclient.http import MediaIoBaseDownload
import io

from dotenv import load_dotenv
import os

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


# 1️ 서비스 계정 키 파일 경로
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


# 3️ 인증 및 서비스 객체 생성
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# 4️ 폴더 내 이미지 검색 (최신 1개)
results = drive_service.files().list(
    q=f"'{FOLDER_ID}' in parents and mimeType contains 'image/'",
    pageSize=1,
    orderBy="createdTime desc",
    fields="files(id, name)"
).execute()

items = results.get('files', [])
if not items:
    print("이미지 파일이 없습니다.")
else:
    file_id = items[0]['id']
    file_name = 'out.jpg'

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(file_name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    print(f" 최신 이미지 다운로드 완료: {file_name}")

names = [
    "권보민", "김아영", "김태연", "김현지", "원승현",
    "박준현", "박찬혁", "신은혜", "원승현", "유수상",
    "윤소정", "이나연", "이수진", "이지연", "정석영",
    "정재영", "정하영", "한상준", "홍원준"
]
discord_ids = {
    "권보민": "100000000000000001",
    "김아영": "100000000000000002",
    "김태연": "100000000000000003",
    "김현지": "100000000000000004",
    "김혜은": "1119595999590105129",
    "박준현": "1356053613243400292",
    "박찬혁": "482846122860347403",
    "신은혜": "777218848499695647",
    "원승현": "361811213379829770",
    "유수상": "100000000000000009",
    "윤소정": "1356050491032862752",
    "이나연": "793689538982969346",
    "이수진": "1298479579752828942",
    "이지연": "100000000000000013",
    "정석영": "289402609154916353",
    "정재영": "877438605918883871",
    "정하영": "1322826848178278434",
    "한상준": "593761341748150273",
    "홍원준": "860401449677750293"
}

# 이미지 열기
image = Image.open("out.jpg")

#(left, upper, right, lower)
areas = [
    (350, 1750, 700, 1870),
    (350, 2340, 700, 2460),
    (350, 2940, 700, 3060),
    (350, 3550, 700, 3670),
    (350, 4150, 700, 4270),
    (350, 4750, 700, 4870),
    (350, 5350, 700, 5470),
    (350, 5960, 700, 6080), 
    (350, 6560, 700, 6680), 
    (350, 7170, 700, 7290), 
    (350, 7770, 700, 7890), 
    (350, 8370, 700, 8490), 
    (350, 8975, 700, 9085), 
    (350, 9575, 700, 9695),  
    (350, 10180, 700, 10295), 
    (350, 10780, 700, 10900),
    (350, 11390, 700, 11510),
    (350, 11990, 700, 12110),
    (350, 12590, 700, 12710)
]

# OCR 수행
records = []
for idx, box in enumerate(areas):
    cropped = image.crop(box)
    ocr_text = pytesseract.image_to_string(cropped)

    # OUT 시간 패턴 확인 (숫자가 있으면 정상, 없으면 미퇴근)
    if re.search(r'\d{2}:\d{2}:\d{2}', ocr_text):
        status = '정상'
    else:
        status = '미퇴근'

    records.append({
        '이름': names[idx],
        '퇴근상태': status
    })

# 결과 출력
df = pd.DataFrame(records)
print(df.to_string(index=False))

# 미퇴근자 필터링
missed = df[df['퇴근상태'] == '미퇴근']['이름'].tolist()

# 미퇴근자 있을 경우에만 디스코드 알림
if missed:

    mention_text = "\n".join(
        [f"<@{discord_ids[name]}> 님, ❗**퇴실**❗ 꼭 찍어주세요!" for name in missed if name in discord_ids]
    )
    message = f" **미퇴근 인원 알림**\n{mention_text}"

    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})