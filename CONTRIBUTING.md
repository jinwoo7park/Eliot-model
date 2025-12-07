# 기여 가이드

이 프로젝트에 기여해주셔서 감사합니다!

## 개발 환경 설정

1. 저장소 클론
```bash
git clone https://github.com/yourusername/elliot-fitting.git
cd elliot-fitting
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
pip install -e .
```

## 코드 스타일

- PEP 8 스타일 가이드를 따릅니다
- 함수와 클래스에는 docstring을 작성합니다
- 변수명은 명확하게 작성합니다

## Pull Request 프로세스

1. 새로운 브랜치 생성 (`git checkout -b feature/amazing-feature`)
2. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
3. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
4. Pull Request 생성

## 이슈 리포트

버그를 발견하거나 기능 제안이 있으시면 이슈를 생성해주세요.


