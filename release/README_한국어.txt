키드 이카루스: 신화와 괴물 (GB) 한글 패치 v1.0f (최종판)
제작: arqhive

대상: Kid Icarus - Of Myths and Monsters (USA, Europe).gb
원본 크기: 131,072바이트
원본 SHA-256: 92c1fbf422abb8f09ca7fdbb563d1284108cc042e60e1222422986d9a59f9d97
결과 SHA-256: 2e80a37f0d7314ad33159da04a985826c92e60ca9c9b21f7bc6d733da31b2455

[적용]
1. ZIP을 폴더째 풉니다.
2. IPS 패처로 KidIcarus_KO_v1.0f.ips를 수정하지 않은 원본 영문 ROM에 적용합니다.
   Python 3.11 이상이 있다면 다음 명령으로도 적용할 수 있습니다.
   python apply_patch.py "원본.gb"
3. 원본과 같은 폴더에 Kid Icarus - Korean Full (Galmuri).gb가 생깁니다.
   출력 이름은 --output "결과.gb"로 지정할 수 있습니다.
4. 에뮬레이터에서 결과 ROM을 새로 실행합니다.

동봉 Python 패처는 원본·패치·결과 해시를 검사하며 원본을 덮어쓰지 않습니다.
이전 한글판 위에 덧씌우지 마세요. 타이틀·오프닝을 포함한 통합 패치입니다.
기존 한글판의 세이브 스테이트는 사용하지 않는 것을 권장합니다.

[적용 범위]
타이틀, 부제, 오프닝, 메뉴, 대사 39개, 상태창, 결과 화면, 저장 질문,
남은 기회, 시작 안내, 일시 정지, 게임 오버, 최종 엔딩 문구.
Nintendo 상표와 저작권 표기는 유지했습니다.

[검증]
mGBA에서 처음부터 엔딩까지 플레이하며 확인했습니다.

[라이선스]
도구·번역문·문서는 MIT, Galmuri 글꼴은 SIL OFL 1.1입니다.
LICENSE, OFL.txt, RELEASE_NOTES.md를 함께 읽어 주세요.
비공식 팬 패치입니다. 게임 ROM은 포함하지 않으며, 적용한 ROM은 배포하지 마세요.
