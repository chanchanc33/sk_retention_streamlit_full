
# sk-retention-streamlit

**무료(Streamlit Community Cloud)**로 HR 리텐션 대시보드를 배포하는 템플릿입니다.  
CSV 업로드/필터/차트/KPI/우선순위/리텐션 패키지/보고서 다운로드까지 포함했고, **SK 브랜드 컬러 & SK 그룹 로고**를 적용했습니다.

<p align="left">
  <img src="assets/sk_group_logo.png" alt="SK Group Logo" width="160" />
</p>

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
# http://localhost:8501
```

## 무료 배포 (Streamlit Community Cloud)
1) 이 레포를 GitHub에 푸시  
2) https://share.streamlit.io → **Create app**  
3) 레포/브랜치 선택 → **Main file**: `app.py` → **Deploy**

## 프로젝트 구조
```
.
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml        # SK 컬러 테마
└── assets/
    └── sk_group_logo.png  # SK 그룹 로고(플레이스홀더)
```

> ⚠️ **로고 저작권**: 현재 이미지는 플레이스홀더입니다. 실제 배포시 **공식 SK 그룹 로고** 이미지로 교체하세요.
> - 파일 경로는 동일하게 `assets/sk_group_logo.png`를 유지하면 됩니다.

## 커스터마이징
- 색/테마: `.streamlit/config.toml` (전역 테마), `app.py`의 `DEFAULT_THEME` (그래프 색)
- 리텐션 패키지/ROI 로직: `gen_pkg`, `calc_roi` 함수
- 우선순위 정렬: 위험도 → 인재등급 → 연봉 (하단 정렬 구문)

---
Made with ❤️
