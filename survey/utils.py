def __make_p_tag(origin: str) -> str:
    style = (
        'font-size:1.1rem; '
        'line-height:1.6; '
        'word-break:keep-all; '
        'text-align:center; '
        'padding:0 1rem;'
    )
    return f'<p style="{style}"><strong>{origin}</strong></p>'


def stress_result(scores: tuple) -> str:
    total = sum(scores)
    if total >= 16:
        return __make_p_tag(
            "심호흡을 한 후 잠깐 걸어 볼까요^^<br>"
            "그럼 이제 마음이 차분해지는 음악을 들어보세요♪<br>"
            "좋아하는 음악이면 됩니다.❤️️"
        )
    if total >= 10:
        return __make_p_tag("오늘 힘드셨군요.<br>잠시 앉아 심호흡을 해보세요.❤️️")
    if total >= 6:
        return __make_p_tag("하던 일을 멈추고 후~<br>심호흡을 해보세요.️❤️")
    return __make_p_tag("스트레스 점수가 낮습니다.<br>잘하셨어요.☺<br>짝짝짝 지금처럼 편안하게 지내세요.❤️")


def __check_score(scores: tuple, std: int) -> bool:
    return sum(scores) >= std


def pbras_result(scores: tuple) -> str:
    mon1 = (scores[0], scores[1], scores[6])
    mon2 = (scores[2], scores[3], scores[7])
    mon3 = (scores[4], scores[5])
    mon4 = (scores[8], scores[9])

    if __check_score(mon1, 3):
        return __make_p_tag("침상에서 안정을 취한 후, 증상이 계속되면 산과 진료를 받는 것을 추천합니다!")
    if __check_score(mon1, 2):
        return __make_p_tag("침상에 누워 안정을 취하세요.❤️")
    if __check_score(mon2, 3):
        return __make_p_tag("침대에 누워 안정을 취하세요.❤️")
    if __check_score(mon2, 2):
        return __make_p_tag("앉아서 물을 한잔 마시세요.❤️")
    if __check_score(mon3, 3):
        return __make_p_tag("틈틈이 앉아 물을 마시세요.❤️")
    if __check_score(mon4, 3):
        return __make_p_tag("물을 자주 마시고 심호흡을 해보세요.❤️")
    if __check_score(mon4, 2):
        return __make_p_tag("편안함을 주는 음악을 들으세요.❤️")
    return __make_p_tag("네 좋아요. 지금처럼 지내시면 됩니다.❤️")
