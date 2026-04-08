![eon_infrastructure_diagram](https://github.com/user-attachments/assets/f0da3470-78f6-4a81-8b17-b4e88904b3d5)# 🚀 EON: EV Charging Platform Backend

> **전기차 사용자를 위한 실시간 충전소 정보 및 보조금 데이터 제공 API**
>
> 이 서비스는 고성능 공간 데이터 처리와 효율적인 외부 API 통합을 통해 사용자에게 가장 빠른 경로의 충전 인프라 정보를 제공합니다.
> 성남시 주최 프로젝트의 일환으로 개발되었으며, **실시간 데이터 정합성**과 **시스템 확장성**을 핵심 가치로 설계되었습니다.

---

## 📌 목차

1. [인프라 구성도](#-인프라-구성도)
2. [데이터 흐름도](#-데이터-흐름도--cache-first)
3. [핵심 아키텍처](#️-핵심-아키텍처--성능-전략)
4. [기술 스택](#-기술-스택)
5. [데이터베이스 스키마](#-데이터베이스-스키마)
6. [API 명세](#-api-명세)
7. [시작하기](#-시작하기)
8. [보안 및 관리자 설정](#-보안--관리자-설정)
9. [프로젝트 구조](#-프로젝트-구조)

---

## 🗺 인프라 구성도

전체 시스템은 **Render.com 위의 Docker 컨테이너 4개**로 구성됩니다.
외부 클라이언트의 요청은 Nginx를 통해 FastAPI로 전달되며, Redis와 PostgreSQL이 데이터 계층을 담당하고, KEPCO API · Nominatim이 외부 데이터 소스 역할을 합니다.

![Uplo<svg width="100%" viewBox="0 0 680 620" role="img" xmlns="http://www.w3.org/2000/svg">
  <title style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">EON EV Charging Platform — 인프라 구성도</title>
  <desc style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">클라이언트부터 외부 API까지의 인프라 전체 구성 및 데이터 흐름</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  <mask id="imagine-text-gaps-j48hyp" maskUnits="userSpaceOnUse"><rect x="0" y="0" width="680" height="620" fill="white"/><rect x="-11.942777633666992" y="93.72218322753906" width="59.88555908203125" height="19.11115264892578" fill="black" rx="2"/><rect x="-6.755697727203369" y="225.72218322753906" width="49.51139831542969" height="19.11115264892578" fill="black" rx="2"/><rect x="-17.129859924316406" y="345.72216796875" width="70.25971984863281" height="19.11115264892578" fill="black" rx="2"/><rect x="-1.568617343902588" y="475.72216796875" width="39.137237548828125" height="19.11115264892578" fill="black" rx="2"/><rect x="-7.368112564086914" y="565.72216796875" width="50.736228942871094" height="19.11115264892578" fill="black" rx="2"/><rect x="42" y="157.72218322753906" width="127.72341918945312" height="19.11115264892578" fill="black" rx="2"/><rect x="135.32284545898438" y="67.02774810791016" width="59.35430908203125" height="21.944494247436523" fill="black" rx="2"/><rect x="107.84535217285156" y="86.44441986083984" width="114.30931854248047" height="19.11115264892578" fill="black" rx="2"/><rect x="484.348876953125" y="67.02774810791016" width="61.30223083496094" height="21.944494247436523" fill="black" rx="2"/><rect x="464.21295166015625" y="86.44441986083984" width="101.57404327392578" height="19.23445415496826" fill="black" rx="2"/><rect x="316.2403869628906" y="199.0277557373047" width="47.51920700073242" height="21.944494247436523" fill="black" rx="2"/><rect x="275.70294189453125" y="220.4444122314453" width="128.59407806396484" height="19.156490325927734" fill="black" rx="2"/><rect x="157.1934051513672" y="319.0277404785156" width="125.61316680908203" height="21.944494247436523" fill="black" rx="2"/><rect x="157.06796264648438" y="338.4444274902344" width="125.8640365600586" height="19.156490325927734" fill="black" rx="2"/><rect x="433.4586486816406" y="319.0277404785156" width="53.08258819580078" height="21.944494247436523" fill="black" rx="2"/><rect x="409.06536865234375" y="338.4444274902344" width="101.86917877197266" height="19.11115264892578" fill="black" rx="2"/><rect x="197.41355895996094" y="449.0277404785156" width="45.17284393310547" height="21.944494247436523" fill="black" rx="2"/><rect x="161.69427490234375" y="468.44439697265625" width="116.61141204833984" height="19.11112403869629" fill="black" rx="2"/><rect x="382.89385986328125" y="449.0277404785156" width="154.2122039794922" height="21.944494247436523" fill="black" rx="2"/><rect x="391.82183837890625" y="468.44439697265625" width="136.35626220703125" height="19.11112403869629" fill="black" rx="2"/><rect x="168.36968994140625" y="562.0277709960938" width="83.2606201171875" height="21.944494247436523" fill="black" rx="2"/><rect x="153.4872589111328" y="581.4444580078125" width="113.02545928955078" height="19.11115264892578" fill="black" rx="2"/><rect x="429.4617004394531" y="562.0277709960938" width="81.07659149169922" height="21.944494247436523" fill="black" rx="2"/><rect x="420.297607421875" y="581.4444580078125" width="99.4047622680664" height="19.23445415496826" fill="black" rx="2"/><rect x="154.72732543945312" y="390.7221984863281" width="44.27267074584961" height="19.11115264892578" fill="black" rx="2"/><rect x="365.9999694824219" y="387.72216796875" width="55.23711013793945" height="19.23445415496826" fill="black" rx="2"/><rect x="80.46778869628906" y="450.7221984863281" width="38.53220176696777" height="19.156490325927734" fill="black" rx="2"/></mask></defs>

  <!-- ── 영역 레이블 (왼쪽 세로) ──────────────────────────── -->
  <text x="18" y="108" text-anchor="middle" transform="rotate(-90,18,108)" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">클라이언트</text>
  <text x="18" y="240" text-anchor="middle" transform="rotate(-90,18,240)" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">인그레스</text>
  <text x="18" y="360" text-anchor="middle" transform="rotate(-90,18,360)" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">애플리케이션</text>
  <text x="18" y="490" text-anchor="middle" transform="rotate(-90,18,490)" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">데이터</text>
  <text x="18" y="580" text-anchor="middle" transform="rotate(-90,18,580)" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:auto">외부 API</text>

  <!-- 구분선 -->
  <line x1="34" y1="150" x2="648" y2="150" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="4 4" style="fill:rgb(0, 0, 0);stroke:rgba(222, 220, 209, 0.15);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-dasharray:4px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="34" y1="290" x2="648" y2="290" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="4 4" style="fill:rgb(0, 0, 0);stroke:rgba(222, 220, 209, 0.15);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-dasharray:4px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="34" y1="420" x2="648" y2="420" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="4 4" style="fill:rgb(0, 0, 0);stroke:rgba(222, 220, 209, 0.15);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-dasharray:4px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="34" y1="540" x2="648" y2="540" stroke="var(--color-border-tertiary)" stroke-width="0.5" stroke-dasharray="4 4" style="fill:rgb(0, 0, 0);stroke:rgba(222, 220, 209, 0.15);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-dasharray:4px, 4px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- ── Render.com 컨테이너 박스 ──────────────────────────── -->
  <rect x="38" y="155" width="606" height="382" rx="12" fill="none" stroke="var(--color-border-secondary)" stroke-width="1" stroke-dasharray="6 3" style="fill:none;stroke:rgba(222, 220, 209, 0.3);color:rgb(255, 255, 255);stroke-width:1px;stroke-dasharray:6px, 3px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <text x="46" y="172" fill="var(--color-text-tertiary)" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:start;dominant-baseline:auto">Render.com (Docker)</text>

  <!-- ── 클라이언트 ──────────────────────────── -->
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="100" y="60" width="130" height="44" rx="8" stroke-width="0.5" style="fill:rgb(68, 68, 65);stroke:rgb(180, 178, 169);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="165" y="78" text-anchor="middle" dominant-baseline="central" style="fill:rgb(211, 209, 199);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">모바일 앱</text>
    <text x="165" y="96" text-anchor="middle" dominant-baseline="central" style="fill:rgb(180, 178, 169);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">프론트엔드 클라이언트</text>
  </g>
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="450" y="60" width="130" height="44" rx="8" stroke-width="0.5" style="fill:rgb(68, 68, 65);stroke:rgb(180, 178, 169);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="515" y="78" text-anchor="middle" dominant-baseline="central" style="fill:rgb(211, 209, 199);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">관리자 UI</text>
    <text x="515" y="96" text-anchor="middle" dominant-baseline="central" style="fill:rgb(180, 178, 169);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Swagger / Admin</text>
  </g>

  <!-- ── 인그레스 : Nginx ──────────────────────────── -->
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="240" y="190" width="200" height="56" rx="8" stroke-width="0.5" style="fill:rgb(8, 80, 65);stroke:rgb(93, 202, 165);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="340" y="210" text-anchor="middle" dominant-baseline="central" style="fill:rgb(159, 225, 203);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">Nginx</text>
    <text x="340" y="230" text-anchor="middle" dominant-baseline="central" style="fill:rgb(93, 202, 165);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Reverse Proxy / :8080</text>
  </g>

  <!-- ── 애플리케이션: FastAPI + Locust ──────────────────────────── -->
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="120" y="310" width="200" height="56" rx="8" stroke-width="0.5" style="fill:rgb(60, 52, 137);stroke:rgb(175, 169, 236);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="220" y="330" text-anchor="middle" dominant-baseline="central" style="fill:rgb(206, 203, 246);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">FastAPI (Uvicorn)</text>
    <text x="220" y="348" text-anchor="middle" dominant-baseline="central" style="fill:rgb(175, 169, 236);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Gunicorn + async I/O</text>
  </g>
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="360" y="310" width="200" height="56" rx="8" stroke-width="0.5" style="fill:rgb(68, 68, 65);stroke:rgb(180, 178, 169);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="460" y="330" text-anchor="middle" dominant-baseline="central" style="fill:rgb(211, 209, 199);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">Locust</text>
    <text x="460" y="348" text-anchor="middle" dominant-baseline="central" style="fill:rgb(180, 178, 169);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">부하 테스트 / :8089</text>
  </g>

  <!-- ── 데이터: Redis + PostgreSQL ──────────────────────────── -->
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="120" y="440" width="200" height="56" rx="8" stroke-width="0.5" style="fill:rgb(99, 56, 6);stroke:rgb(239, 159, 39);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="220" y="460" text-anchor="middle" dominant-baseline="central" style="fill:rgb(250, 199, 117);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">Redis</text>
    <text x="220" y="478" text-anchor="middle" dominant-baseline="central" style="fill:rgb(239, 159, 39);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">L1/L2/L3 캐시 / :6379</text>
  </g>
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="360" y="440" width="200" height="56" rx="8" stroke-width="0.5" style="fill:rgb(12, 68, 124);stroke:rgb(133, 183, 235);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="460" y="460" text-anchor="middle" dominant-baseline="central" style="fill:rgb(181, 212, 244);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">PostgreSQL + PostGIS</text>
    <text x="460" y="478" text-anchor="middle" dominant-baseline="central" style="fill:rgb(133, 183, 235);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">공간 인덱스 / stations DB</text>
  </g>

  <!-- ── 외부 API ──────────────────────────── -->
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="120" y="555" width="180" height="44" rx="8" stroke-width="0.5" style="fill:rgb(113, 43, 19);stroke:rgb(240, 153, 123);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="210" y="573" text-anchor="middle" dominant-baseline="central" style="fill:rgb(245, 196, 179);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">KEPCO API</text>
    <text x="210" y="591" text-anchor="middle" dominant-baseline="central" style="fill:rgb(240, 153, 123);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">충전소 / 충전기 데이터</text>
  </g>
  <g style="fill:rgb(0, 0, 0);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto">
    <rect x="380" y="555" width="180" height="44" rx="8" stroke-width="0.5" style="fill:rgb(113, 43, 19);stroke:rgb(240, 153, 123);color:rgb(255, 255, 255);stroke-width:0.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
    <text x="470" y="573" text-anchor="middle" dominant-baseline="central" style="fill:rgb(245, 196, 179);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:14px;font-weight:500;text-anchor:middle;dominant-baseline:central">Nominatim</text>
    <text x="470" y="591" text-anchor="middle" dominant-baseline="central" style="fill:rgb(240, 153, 123);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:middle;dominant-baseline:central">Geocoding / 폴백</text>
  </g>

  <!-- ── 화살표 ──────────────────────────── -->
  <!-- 클라이언트 → Nginx -->
  <line x1="165" y1="104" x2="300" y2="190" marker-end="url(#arrow)" mask="url(#imagine-text-gaps-j48hyp)" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <line x1="515" y1="104" x2="400" y2="190" marker-end="url(#arrow)" mask="url(#imagine-text-gaps-j48hyp)" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- Nginx → FastAPI -->
  <line x1="290" y1="246" x2="240" y2="310" marker-end="url(#arrow)" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- FastAPI ↔ Redis -->
  <line x1="220" y1="366" x2="220" y2="440" marker-end="url(#arrow)" stroke="#BA7517" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <text x="195" y="405" text-anchor="end" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:end;dominant-baseline:auto">Cache</text>

  <!-- FastAPI ↔ PostgreSQL -->
  <line x1="320" y1="352" x2="360" y2="440" marker-end="url(#arrow)" stroke="#185FA5" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <text x="370" y="402" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:start;dominant-baseline:auto">asyncpg</text>

  <!-- FastAPI → KEPCO -->
  <line x1="180" y1="366" x2="180" y2="555" marker-end="url(#arrow)" stroke="#993C1D" stroke-dasharray="4 2" mask="url(#imagine-text-gaps-j48hyp)" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-dasharray:4px, 2px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
  <text x="115" y="465" text-anchor="end" style="fill:rgb(194, 192, 182);stroke:none;color:rgb(255, 255, 255);stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:12px;font-weight:400;text-anchor:end;dominant-baseline:auto">httpx</text>

  <!-- FastAPI → Nominatim -->
  <line x1="260" y1="366" x2="420" y2="555" marker-end="url(#arrow)" stroke="#993C1D" stroke-dasharray="4 2" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-dasharray:4px, 2px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- Redis → KEPCO (캐시 미스 시 폴백) -->
  <line x1="200" y1="496" x2="160" y2="555" marker-end="url(#arrow)" stroke="#BA7517" stroke-dasharray="3 3" stroke-width="0.8" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-dasharray:3px, 3px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>

  <!-- Locust → Nginx (부하테스트) -->
  <line x1="400" y1="338" x2="390" y2="246" marker-end="url(#arrow)" stroke="var(--color-border-secondary)" stroke-dasharray="4 2" style="fill:none;stroke:rgb(156, 154, 146);color:rgb(255, 255, 255);stroke-width:1.5px;stroke-dasharray:4px, 2px;stroke-linecap:butt;stroke-linejoin:miter;opacity:1;font-family:&quot;Anthropic Sans&quot;, -apple-system, &quot;system-ui&quot;, &quot;Segoe UI&quot;, sans-serif;font-size:16px;font-weight:400;text-anchor:start;dominant-baseline:auto"/>
</svg>ading eon_infrastructure_diagram.svg…]()


> **Docker Compose 서비스:** `redis` · `api` · `nginx` · `locust`
> **프로덕션 실행 명령:** `gunicorn -k uvicorn.workers.UvicornWorker app.main:app`

---

## 🔄 데이터 흐름도 — Cache-First

충전소 조회 요청(`GET /api/v1/stations`)이 처리되는 전체 경로입니다.
Redis 캐시를 우선 확인하여 응답하고, 미스 시에만 DB 조회 → 외부 API 호출 순으로 진행합니다.

```
클라이언트
    │  x-api-key 헤더 포함
    ▼
  Nginx  ──── 인증 헤더 검증
    │
    ▼
FastAPI Router
    │  좌표 파싱 / 정규화 (CACHE_COORD_ROUND_DECIMALS)
    ▼
Redis 캐시 조회 (L1, TTL 5분)
    │
    ├── [Hit] ─────────────────────────────► 즉시 응답 반환 ✅
    │
    └── [Miss]
          │
          ▼
    PostgreSQL / PostGIS
    ST_DWithin 반경 검색
          │
          ├── 정적 정보(이름·위치) → Redis L2에 캐시 (24h)
          │
          └── 실시간 충전기 상태 필요?
                │
                ▼
          KEPCO API  (httpx 비동기)
          └── Nominatim 폴백 (Geocoding 실패 시)
                │
                ▼
          결과 조합 → Redis L1 갱신 → 클라이언트 응답 ✅
```

---

## 🏗️ 핵심 아키텍처 & 성능 전략

단순한 CRUD API를 넘어, 대량의 외부 API 데이터를 효율적으로 서빙하기 위해 다음과 같은 백엔드 최적화 전략을 채택했습니다.

### 1. Multi-Tier Caching (Redis)

외부 API(KEPCO)의 응답 지연 및 Rate Limit 문제를 극복하기 위해 **3단계 캐싱**을 구현했습니다.

| 계층 | 대상 데이터 | TTL | 목적 |
| :---: | :--- | :---: | :--- |
| **L1** Short-term | 좌표 기반 검색 결과 | 5분 | 반복 요청 응답 최적화 |
| **L2** Persistent | 충전소 위치·이름 등 정적 정보 | 24시간 | 인프라 데이터 보존 |
| **L3** Detail | 실시간 충전기 상태 정보 | 30분 | 데이터 신선도 유지 |

> **결과:** API 평균 응답 속도 **70% 이상 개선** 및 외부 API Rate Limit 회피를 통한 시스템 안정성 확보.

---

### 2. Spatial Data Optimization (PostGIS)

수만 개의 충전소 데이터를 단순 위경도 비교가 아닌 **PostGIS 공간 인덱스**를 통해 처리합니다.

- `ST_DWithin`을 활용한 인덱스 기반 반경 검색으로 대량 데이터셋에서도 **O(1)에 가까운 검색 성능** 확보
- 좌표 정규화(Bucket) 및 반올림 전략(`CACHE_COORD_ROUND_DECIMALS`)을 통해 **캐시 히트율 극대화**

---

### 3. Fault-Tolerant Data Pipeline

외부 API 장애 시에도 서비스 연속성을 보장하는 방어적 로직을 구축했습니다.

- **Geocoding Fallback:** Nominatim 실패 시 지역 단위 폴백으로 서비스 중단 없이 위치 검색 유지
- **Async I/O:** `httpx`와 `asyncpg`를 이용한 완전 비동기 처리로 동시성 요청 처리 능력 향상
- **api_logs 테이블:** 모든 외부 API 통신 이력 기록으로 장애 추적성(Traceability) 확보

---

## 🛠 기술 스택

| 분류 | 기술 | 선택 이유 |
| :--- | :--- | :--- |
| **Framework** | FastAPI | 고성능 비동기 처리 및 자동화된 API 명세(Swagger) 활용 |
| **Database** | PostgreSQL + PostGIS | 공간 데이터(Geometry) 엔진을 통한 고정밀 위치 검색 |
| **Cache** | Redis 7 (Alpine) | 다층 캐시 구조 구현 및 시스템 성능 메트릭 추적 |
| **ORM / Migration** | SQLAlchemy 2.0 / Alembic | Async 환경 최적화 및 안정적인 스키마 버전 관리 |
| **Auth** | JWT / X-API-Key | 프론트엔드 통신 보안 및 사용자 인증의 이중화 |
| **Infra** | Docker / Render.com | 컨테이너화를 통한 환경 일관성 및 CI/CD 자동화 |
| **Load Test** | Locust 2.20 | 실제 트래픽 패턴 기반 부하 시뮬레이션 |
| **Proxy** | Nginx (Alpine) | Reverse Proxy / Admin Basic Auth / htpasswd 보호 |

---

## 📊 데이터베이스 스키마

시스템의 핵심은 **정적 데이터(Station)**와 **동적 데이터(Charger 상태)**의 분리 및 효율적 연동입니다.

```
stations (1) ──── (N) chargers
    │
    └── PostGIS Geometry 컬럼 (ST_DWithin 공간 인덱스)

subsidies ──── 국가·지자체 보조금 데이터 (ILIKE 패턴 매칭)
api_logs  ──── 외부 API 통신 이력 및 응답 상태 기록
```

| 테이블 | 역할 | 핵심 기술 |
| :--- | :--- | :--- |
| `stations` | 충전소 위치·이름 등 정적 정보 | PostGIS `Geometry` 컬럼, 공간 인덱스 |
| `chargers` | 실시간 충전기 상태 및 충전 타입 | `stations`와 1:N 관계 |
| `subsidies` | 전국 단위 전기차 보조금 데이터 | `ILIKE` 패턴 매칭 고속 조회 |
| `api_logs` | 외부 API 통신 및 응답 상태 기록 | 장애 추적성(Traceability) 확보 |

---

## 🔌 API 명세

| Endpoint | Method | Auth | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/stations` | `GET` | X-API-Key | 좌표 + 반경 기반 주변 충전소 검색 (Cache-First) |
| `/api/v1/station/{id}/chargers` | `GET` | X-API-Key | 실시간 충전기 가동 상태 및 상세 스펙 조회 |
| `/subsidy` | `GET` | X-API-Key | 제조사 / 모델별 국고 및 지방비 보조금 검색 |
| `/api/v1/auth/token` | `POST` | None | 사용자 인증 및 JWT 발급 |

---

## 🚀 시작하기

### 사전 요구사항

- Python 3.12+ / Poetry
- Docker & Docker Compose (PostgreSQL + PostGIS, Redis 환경 구성용)

### 로컬 실행

**1. 의존성 설치**

```bash
poetry install
```

**2. 환경 변수 설정**

```bash
cp .env.template .env
# .env 파일에서 DATABASE_URL, REDIS_HOST, EXTERNAL_STATION_API_KEY 등 입력
```

**3. 인프라 실행 (Redis + API + Nginx + Locust)**

```bash
docker-compose up -d
```

**4. DB 마이그레이션 및 초기 데이터 적재**

```bash
poetry run alembic upgrade head
poetry run python app/db/init_db.py
```

**5. 개발 서버 실행 (로컬 단독 실행 시)**

```bash
poetry run uvicorn app.main:app --reload
```

서버가 실행되면 `http://localhost:8000/docs` 에서 Swagger UI를 확인할 수 있습니다.

---

## 🛡 보안 & 관리자 설정

| 설정 | 방식 | 설명 |
| :--- | :--- | :--- |
| **Admin Mode** | `ADMIN_MODE=true` 환경변수 | HTTP Basic Auth로 보호된 Swagger UI 및 Redis 모니터링 엔드포인트 활성화 |
| **Admin 인증** | `ADMIN_CREDENTIALS` + `nginx/.htpasswd` | Nginx 레벨에서 Basic Auth 적용 |
| **API Security** | `x-api-key` 헤더 (`FRONTEND_API_KEYS`) | 허가된 프론트엔드 서비스와의 통신만 허용 |
| **User Auth** | JWT Bearer Token | `/api/v1/auth/token` 발급 후 인증 필요 엔드포인트에 사용 |

---

## 📂 프로젝트 구조

```
Eon-BackEnd-Server/
├── app/
│   ├── api/              # 라우터 및 의존성 정의 (Dependency Injection)
│   ├── core/             # 환경 설정 (Pydantic Settings)
│   ├── db/               # 비동기 엔진 및 리포지토리 패턴 (asyncpg)
│   ├── services/         # 지오코딩 및 보조금 조회 비즈니스 로직
│   └── models.py         # SQLAlchemy ORM 모델
├── alembic/              # DB 마이그레이션 히스토리
├── nginx/
│   ├── conf.d/           # Nginx 설정
│   └── .htpasswd         # Admin Basic Auth 파일
├── scripts/              # 데이터 동기화 및 운영 스크립트
├── locustfile.py         # 부하 테스트 시나리오
├── Dockerfile            # Python 3.12-slim 기반 이미지 빌드
├── docker-compose.yml    # redis / api / nginx / locust 4-서비스 구성
├── render.yaml           # Render.com 배포 정의
└── .env.template         # 환경 변수 템플릿
```
