# 🔔 HR NEWS EVERY MORNING

자동으로 매일 아침 HR 관련 뉴스를 수집하고 요약하여 이메일로 받아보세요.

## 🎯 개요

이 프로젝트는 GitHub Actions를 활용하여 매일 정해진 시간(한국 시간 오전 9시)에 자동으로 실행되는 HR 뉴스 수집 및 요약 봇입니다.

- **뉴스 수집**: Naver News API를 통해 HR 관련 뉴스 검색
- **AI 처리**: OpenAI GPT를 활용하여 뉴스 자동 요약
- **이메일 발송**: 처리된 내용을 매일 아침 자동으로 메일 배송

## 🚀 시작하기

### 필수 요구사항

- Python 3.9+
- Naver API 인증 정보 (Client ID, Client Secret)
- OpenAI API 키
- Gmail 계정 (또는 SMTP 지원 이메일)

### 로컬 설정

```bash
# 1. 저장소 클론
git clone https://github.com/dkdud7171/HRNEWS_EVERY_MORNING.git
cd HRNEWS_EVERY_MORNING

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cat > .env << EOF
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
OPENAI_API_KEY=your_openai_api_key
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_email_app_password
EMAIL_RECEIVER=recipient@example.com
EOF

# 5. 로컬에서 테스트
python hr_agent.py
```

### GitHub Secrets 설정

GitHub 저장소의 Settings > Secrets에 다음 정보를 추가하세요:

- `NAVER_CLIENT_ID`: Naver 개발자 센터에서 발급받은 ID
- `NAVER_CLIENT_SECRET`: Naver 개발자 센터에서 발급받은 Secret
- `OPENAI_API_KEY`: OpenAI에서 발급받은 API 키
- `EMAIL_SENDER`: 발신자 이메일 주소
- `EMAIL_PASSWORD`: Gmail 앱 비밀번호 (Gmail 계정의 경우)
- `EMAIL_RECEIVER`: 수신자 이메일 주소

## 📋 파일 구조

```
.
├── .github/
│   └── workflows/
│       └── daily_hr_report.yml    # GitHub Actions 워크플로우
├── hr_agent.py                     # 메인 에이전트 스크립트
├── requirements.txt                # Python 의존성
├── .gitignore                      # Git 무시 파일
└── README.md                       # 이 파일
```

## 🔧 환경변수 설명

| 변수명 | 설명 |
|--------|------|
| `NAVER_CLIENT_ID` | Naver API 클라이언트 ID |
| `NAVER_CLIENT_SECRET` | Naver API 클라이언트 시크릿 |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `EMAIL_SENDER` | 이메일 발신자 (Gmail 주소) |
| `EMAIL_PASSWORD` | Gmail 앱 비밀번호 |
| `EMAIL_RECEIVER` | 이메일 수신자 |

## 📅 일정

- **실행 시간**: 매일 UTC 00:00 (한국 시간 오전 9시)
- **스케줄 설정**: `.github/workflows/daily_hr_report.yml`의 cron 표현식으로 변경 가능

## 🔐 보안

- **절대로** 시크릿 정보를 저장소에 커밋하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어 있습니다
- GitHub Secrets를 통해 민감한 정보를 관리하세요

## 📝 로그

GitHub Actions 워크플로우 실행 로그는 저장소의 **Actions** 탭에서 확인할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 개선 사항은 이슈로 등록해주세요.

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.