import copy, sys
from pathlib import Path
sys.path.insert(0, '/home/user/auto-stock')
from PIL import Image, ImageDraw
from screendaily.post import load_post, load_config
from screendaily.cards import render_cover, font
ROOT = Path('/home/user/auto-stock')
c = load_config()
H = {
 "2026-11-16_1900": [("A 경고·공감", "월요일 밤엔\n머리 쓰는 거\n금지", "뇌 끄고 보기"),
                     ("B 숫자·결과", "틀어두기만 해도\n월요병 잊는\n예능 4편", "월요일 밤 생존템ㅠ")],
 "2026-11-17_1900": [("A 숫자·결과", "2화부터\n멈출 수 없는\n스릴러 4편", "출근 어떡해ㅠ"),
                     ("B 경고", "내일 출근이면\n1화도\n틀지 마세요", "진짜 못 멈춤")],
 "2026-11-18_1900": [("A 결과 먼저", "엔딩 크레딧 올라가도\n못 일어난\n드라마 3편", "휴지 꼭 챙기세요"),
                     ("B 경고", "지하철에서\n절대 보지 마세요", "눈물 주의")],
 "2026-11-19_1900": [("A 경고", "밤 12시 넘으면\n틀지 마세요", "불 켜고 보세요"),
                     ("B 숫자·결과", "불 켜고 봐도\n무서운\n한국 호러 4편", "혼자 보기 금지")],
 "2026-11-20_1900": [("A 숫자·결과", "토요일에 시작해\n일요일에 끝나는\n시리즈 4편", "주말 순삭 보장"),
                     ("B 상황 공감", "주말 약속 없으면\n이거 보세요", "이틀이면 끝")],
 "2026-11-22_2100": [("A 정체 숨기기", "대기업 사표 내고\n오디션에 나간 남자,\n누굴까요?", "맞혀보세요!"),
                     ("B 결과 먼저", "이 악역 배우,\n원래 회사원이었어요", "누군지 맞혀보세요")],
 "2026-11-23_1900": [("A 결과 먼저", "보다가 혼자\n소리 지른\n로맨스 4편", "광대 승천 주의"),
                     ("B 경고", "광대 아파도\n책임 못 집니다", "설렘 과다")],
 "2026-11-24_1900": [("A 통념 깨기", "자막 싫어도\n1화만 버티세요", "1화만 보면 끝"),
                     ("B 숫자", "자막 5분이면\n적응 끝나는\n시리즈 3편", "금방 적응돼요")],
 "2026-11-25_1900": [("A 경고", "새벽 2시에\n틀면 안 되는\n영화 4편", "잠 다 깸"),
                     ("B 결과 먼저", "끝날 때까지\n폰 못 본\n영화 4편", "새벽 2시 각")],
 "2026-11-26_1900": [("A 경고", "배고플 때\n절대 보지 마세요", "야식 주의ㅠ"),
                     ("B 결과 먼저", "보다가 결국\n야식 시킨\n3편", "배달앱 켜는 중")],
 "2026-11-27_1900": [("A 숫자·결과", "생각 끄고\n2시간 순삭\n액션 영화 4편", "스트레스 순삭"),
                     ("B 상황 공감", "스트레스 받은 날엔\n이거 틀어요", "팝콘 준비")],
}
W = 360
for slot, alts in H.items():
    post = load_post(ROOT/'queue'/slot, c)
    ims = [("지금", render_cover(post, c))]
    for name, t, b in alts:
        p = copy.copy(post); p.title = t; p.bubble = b
        ims.append((name, render_cover(p, c)))
    h = int(ims[0][1].height * W / ims[0][1].width)
    s = Image.new('RGB', (W*3 + 40, h + 60), 'white'); d = ImageDraw.Draw(s)
    for i, (name, im) in enumerate(ims):
        x = i*(W+20); d.text((x+8, 12), name, font=font('NanumSquareEB.ttf', 32), fill='black')
        s.paste(im.resize((W, h)), (x, 60))
    s.save(ROOT/'drafts'/'hooks'/f'{slot}.jpg', quality=88)
    print(slot)
