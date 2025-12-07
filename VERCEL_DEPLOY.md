# Vercel 배포 가이드

이 가이드는 Elliot Fitting 프로젝트를 Vercel에 배포하는 방법을 설명합니다.

## 사전 요구사항

1. GitHub 계정
2. Vercel 계정 (https://vercel.com 에서 무료로 가입 가능)
3. 프로젝트가 GitHub 저장소에 푸시되어 있어야 함

## 배포 단계

### 1. GitHub에 코드 푸시

먼저 모든 변경사항을 GitHub에 푸시합니다:

```bash
git add .
git commit -m "Add Flask web interface and Vercel configuration"
git push origin main
```

### 2. Vercel에 프로젝트 연결

1. [Vercel 대시보드](https://vercel.com/dashboard)에 로그인
2. "Add New..." → "Project" 클릭
3. "Import Git Repository" 선택
4. GitHub 저장소 선택 (jinwoo7park/Eliot-model)
5. "Import" 클릭

### 3. 프로젝트 설정

Vercel이 자동으로 프로젝트를 감지합니다:

- **Framework Preset**: Other (또는 Python)
- **Root Directory**: `./` (기본값)
- **Build Command**: (비워둠 - Vercel이 자동으로 처리)
- **Output Directory**: (비워둠)
- **Install Command**: `pip install -r requirements.txt`

### 4. 환경 변수 설정 (필요한 경우)

현재는 특별한 환경 변수가 필요하지 않지만, 필요시 "Environment Variables" 섹션에서 추가할 수 있습니다.

### 5. 배포 실행

"Deploy" 버튼을 클릭하여 배포를 시작합니다.

### 6. 배포 확인

배포가 완료되면:
- Vercel이 자동으로 URL을 생성합니다 (예: `your-project.vercel.app`)
- 배포 로그를 확인하여 오류가 없는지 확인합니다
- 생성된 URL로 접속하여 웹 애플리케이션이 정상 작동하는지 테스트합니다

## 문제 해결

### Python 버전 문제

만약 Python 버전 관련 오류가 발생하면, `vercel.json`의 `PYTHON_VERSION`을 조정하거나 `runtime.txt` 파일을 생성할 수 있습니다:

```
python-3.9.18
```

### 의존성 설치 오류

`requirements.txt`에 모든 필요한 패키지가 포함되어 있는지 확인하세요. 특히:
- numpy
- scipy
- matplotlib
- flask
- werkzeug

### 메모리 제한

Vercel의 무료 플랜은 메모리 제한이 있습니다. 큰 데이터 파일을 처리할 때 문제가 발생할 수 있습니다. 이 경우:
- 파일 크기 제한을 확인하세요 (현재 16MB로 설정됨)
- 더 큰 파일이 필요하면 Vercel Pro 플랜을 고려하세요

## 자동 배포 설정

GitHub 저장소와 연결하면:
- `main` 브랜치에 푸시할 때마다 자동으로 배포됩니다
- Pull Request를 생성하면 Preview 배포가 생성됩니다

## 로컬 테스트

배포 전에 로컬에서 테스트하려면:

```bash
pip install -r requirements.txt
python app.py
```

그 다음 브라우저에서 `http://localhost:5000`으로 접속하여 테스트할 수 있습니다.

## 추가 리소스

- [Vercel Python 문서](https://vercel.com/docs/runtimes/python)
- [Flask 문서](https://flask.palletsprojects.com/)
- [프로젝트 GitHub 저장소](https://github.com/jinwoo7park/Eliot-model)

