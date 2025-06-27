import base64
from datetime import datetime, timezone
import json
from huami.configs.errors import ERRORS
from huami.configs.payloads import PAYLOADS
from huami.configs.urls import URLS
from urllib import parse
import uuid
import random

import requests


def _assemble_url(name: str, *args, **kwargs) -> str:
    """url 문자열 내에 특정 데이터 주입

    Args:
        name (str): url과 매핑되는 이름

    Returns:
        str: 조합된 url
    """    
    return URLS[name].format(*args, **kwargs)


def _assemble_payload(name: str, **kwargs) -> dict:
    """파라미터에 특정 데이터 주입

    Args:
        name (str): 파라미터와 매핑되는 이름

    Returns:
        dict: 조합된 파라미터
    """    
    return {**PAYLOADS[name].copy(), **kwargs}


def _validate_redirect_url_parameters(redirect_url_parameters: dict) -> None:
    """AccessToken 발급 시 검증절차
    AccessToken 발급 요청 시 받은 redirect_url의 파라미터에
    에러가 존재하는지 확인
    Args:
        redirect_url_parameters (dict): redirect url의 파라미터들을 담은 딕셔너리

    Raises:
        ValueError: 잘못된 이메일이나 비밀번호
        ValueError: accessToken의 부재
    """    
    if "error" in redirect_url_parameters:
        raise ValueError(
            f"Wrong E-mail or Password."
            f"Error: {redirect_url_parameters['error']}"
        )

    if "access" not in redirect_url_parameters:
        raise ValueError("No 'access' parameter in login url.")


def _validate_login_result(login_result: dict) -> None:
    """Login 수행 시 검증절차

    Args:
        login_result (dict): 로그인 결과를 담은 딕셔너리

    Raises:
        ValueError: 에러 코드가 존재하는 경우
        ValueError: 토큰정보가 존재하지 않는 경우
        ValueError: appToken이 존재하지 않는 경우
        ValueError: loginToken이 존재하지 않는 경우
        ValueError: user_id가 존재하지 않는 경우
    """    
    if "error_code" in login_result:
        error_message = ERRORS.get(login_result["error_code"])
        raise ValueError(f"Login error. Error: {error_message}")

    if "token_info" not in login_result:
        raise ValueError("No 'token_info' parameter in login data.")

    token_info = login_result["token_info"]
    if "app_token" not in token_info:
        raise ValueError("No 'app_token' parameter in login data.")

    if "login_token" not in token_info:
        raise ValueError("No 'login_token' parameter in login data.")

    if "user_id" not in token_info:
        raise ValueError("No 'user_id' parameter in login data.")


class HuamiAmazfit:
    """Huami 계정 연동 클래스
    """    
    def __init__(self, email: str, password: str) -> None:
        """생성자

        Args:
            email (str): Huami 계정 이메일
            password (str): Huami 계정 비밀번호
        """        
        self.email: str = email
        self.password: str = password
        self.access_token: str = ""
        self.country_code: str | None = None

        self.app_token: str | None = None
        self.login_token: str | None = None
        self.user_id: str | None = None

        self.r = str(uuid.uuid4())
        self.device_id: str = "02:00:00:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )

    def _set_country_code(self, redirect_url_parameters: dict) -> None:
        """country code setter 메서드
        accessToken 발급 과정 중 country Code를 저장
        Args:
            redirect_url_parameters (dict): redirect url의 파라미터들을 담은 딕셔너리
        """        
        if "country_code" not in redirect_url_parameters:
            region = redirect_url_parameters['region'][0]
            self.country_code = region[0:2].upper()
            return

        self.country_code = redirect_url_parameters['country_code']

    def _set_access_token(self, redirect_url_parameters: dict) -> None:
        """access token setter 메서드
        assessToken 발급 후 저장
        Args:
            redirect_url_parameters (dict): redirect url의 파라미터들을 담은 딕셔너리
        """        
        self.access_token = redirect_url_parameters["access"][0]

    def _profile_process(self, profile_data: dict) -> dict:
        """Profile 요청을 통해 받은 데이터를 생년월, 키(m), 무게(kg)로 나누어 반환

        Args:
            profile_data (dict): response.json() 그대로

        Returns:
            dict: {'birth': 'yyyy-mm', height: 'x.xx', weight: 'xx.x'}
        """
        return {
            'birth': profile_data['birthday'],
            'height': profile_data['height']/100,
            'weight': profile_data['weight']
        }
    
    def profile(self, process=True):
        """Huami 서버로 profile 정보를 요청
        
        Args:
            process (bool): 데이터 가공 여부, 기본 True. (False인 경우 받은 그대로 반환)
        
        Returns:
            dict: 결과를 Json dict으로 전달
        """        
        response = requests.get(
            url=_assemble_url(name='profile',
                              user_id=parse.quote(self.user_id)),
            headers={'apptoken': self.app_token,}
        )
        response.raise_for_status()
        if process:
            return self._profile_process(response.json())
        return response.json()
    
    def _band_data_process(self, band_data:dict) -> dict:
        """band data 요청을 통해 받은 데이터를 날짜별 심박수, 수면 질, 걸음 수로 나누어 반환

        Args:
            band_data (dict): response.json() 그대로

        Returns:
            dict: {'yyyy-mm-dd': {
                'heart': [], 'sleeps': [], 'steps: []
            }, ...} 포맷 딕셔너리
        """        
        result = {}
        for data in band_data["data"]:
            complex_data = base64.b64decode(data['data'])
            heart_data = base64.b64decode(data['data_hr'])
            integers = [byte for byte in complex_data]
            result[data['date_time']] = {
                'heart': [heart_data[i] % 255 for i in range(0, len(heart_data))],
                'sleeps': [integers[i] for i in range(0, len(integers), 3)],
                'steps': [integers[i] for i in range(2, len(integers), 3)]
            }
        return result

    def band_data(self, from_date: str, to_date: str, process:bool = True):
        """Huami 서버로 band data 정보를 요청
        분당 수면 점수, 심박수 등
        Args:
            from_date (str): 'yyyy-mm-dd' 타입의 문자열
            to_date (str): 'yyyy-mm-dd' 타입의 문자열
            process (bool): 데이터 가공 여부, 기본 True. (False인 경우 받은 그대로 반환)

        Returns:
            dict: 결과를 Json dict으로 전달
        """        
        response = requests.get(
            url=_assemble_url(name='band_data'),
            params=_assemble_payload(name='band_data',
                                     userid=self.user_id,
                                     from_date=from_date,
                                     to_date=to_date),
            headers={'apptoken':self.app_token}
        )
        response.raise_for_status()
        if process:
            return self._band_data_process(response.json())
        return response.json()

    def _time_for_stress(self, date: str) -> str:
        """문자열 시간을 timestamp로 변환

        Args:
            date (str): 'yyyy-mm-dd' 타입의 문자열

        Returns:
            str: '1690803229711' 13자리 타임스탬프 형식의 문자열
        """        
        return str(int(datetime.strptime(date + " 00:00:00.001", "%Y-%m-%d %H:%M:%S.%f").timestamp() * 1000))

    def _timestamp_to_datetime(self, timestamp: str) -> datetime:
        """13자리 타임스탬프 형식의 문자열을 datetime으로 변환

        Args:
            timestamp (str): '1690803229711' 13자리 타임스탬프 형식의 문자열

        Returns:
            datetime: 현재 위치에 맞는 시간대가 적용된 datetime
        """        
        return datetime.utcfromtimestamp(float(timestamp)/1000).replace(tzinfo=timezone.utc).astimezone()

    def _stress_data_process(self, stress_data: dict) -> dict:
        """stress 요청을 통해 받은 데이터를 날짜별 스트레스로 변환

        Args:
            stress_data (dict): response.json() 그대로

        Returns:
            dict: {'yyyy-mm-dd': [0, 0, 4, ...], ...} 포맷 딕셔너리
        """        
        result = {}
        for data in stress_data["items"]:
            date = self._timestamp_to_datetime(data['timestamp']).strftime('%Y-%m-%d')
            result[date] = [0 for _ in range(1440)]
            for obj in json.loads(data['data']):
                time = self._timestamp_to_datetime(obj['time'])
                result[date][time.hour * 60 + time.minute] = obj['value']
        return result
    
    def stress(self, from_date: str, to_date: str, process: bool = True):
        """Huami 서버로 stress 정보를 요청

        Args:
            from_date (str): 'yyyy-mm-dd' 타입의 문자열
            to_date (str): 'yyyy-mm-dd' 타입의 문자열
            process (bool): 데이터 가공 여부, 기본 True. (False인 경우 받은 그대로 반환)

        Returns:
            dict: 결과를 Json dict으로 전달
        """        
        params = _assemble_payload(name='stress')
        params['from']=self._time_for_stress(from_date)
        params['to']=self._time_for_stress(to_date)
        response = requests.get(
            url=_assemble_url(name='stress',
                              user_id=self.user_id),
            params=params,
            headers={'apptoken':self.app_token}
        )
        response.raise_for_status()
        if process:
            return self._stress_data_process(response.json())
        return response.json()
    
    def _time_for_blood(self, date: str) -> str:
        """문자열 시간을 blood 요청에 맞게 변환

        Args:
            date (str): 'yyyy-mm-dd' 타입의 문자열

        Returns:
            str: 'yyyy-mm-ddThh:mm:ss' 형식의 문자열 ex) '2019-01-01T00:00:00'
        """        
        return date+"T00:00:00"
    
    def _blood_data_process(self, blood_data: dict) -> dict:
        """blood 요청을 통해 받은 데이터를 날짜별 산소포화도로 변환

        Args:
            blood_data (dict): response.json() 그대로

        Returns:
            dict: {'yyyy-mm-dd': [0, 0, 4, ...], ...} 포맷 딕셔너리
        """        
        result = {}
        for data in blood_data["items"]:
            datetime = self._timestamp_to_datetime(data['timestamp'])
            date = datetime.strftime('%Y-%m-%d')
            if date not in result:
                result[date] = [0 for _ in range(1440)]
            result[date][datetime.hour * 60 + datetime.minute] = json.loads(data['extra'])['spo2']
        return result

    def blood_oxygen(self, from_date: str, to_date:str, process=True):
        """Huami 서버로 혈중산소포화도 정보를 요청

        Args:
            from_date (str): 'yyyy-mm-dd' 타입의 문자열
            to_date (str): 'yyyy-mm-dd' 타입의 문자열
            process (bool): 데이터 가공 여부, 기본 True. (False인 경우 받은 그대로 반환)

        Returns:
            dict: 결과를 Json dict으로 전달
        """        
        params = _assemble_payload(name='blood_oxygen')
        params['from']=self._time_for_blood(from_date)
        params['to']=self._time_for_blood(to_date)
        response = requests.get(
            url=_assemble_url(name='blood_oxygen',
                              user_id=self.user_id),
            params=params,
            headers={'apptoken':self.app_token}
        )
        response.raise_for_status()
        if process:
            return self._blood_data_process(response.json())
        return response.json()

    def access(self) -> None:
        """Huami 서버로 accessToken 요청
        accessToken과 country code를 설정
        """        
        response = requests.post(
            url=_assemble_url(name='tokens_amazfit', user_email=parse.quote(self.email)),
            data=_assemble_payload(name='tokens_amazfit', password=self.password),
            allow_redirects=False
        )
        response.raise_for_status()

        redirect_url_parameters: dict = parse.parse_qs(
            # 'Location' parameter contains url with login status
            parse.urlparse(response.headers.get('Location')).query
        )
        _validate_redirect_url_parameters(redirect_url_parameters)

        self._set_country_code(redirect_url_parameters)
        self._set_access_token(redirect_url_parameters)

    def login(self) -> None:
        """Huami 서버로 Login 요청
        AccessToken 설정이 완료되어야 가능
        Login시 login token과 app token, user id 설정
        """        
        response = requests.post(
            url=_assemble_url(name='login_amazfit'),
            data=_assemble_payload(name='login_amazfit',
                                   country_code=self.country_code,
                                   device_id=self.device_id,
                                   code=self.access_token),
            allow_redirects=False
        )
        response.raise_for_status()
        login_result = response.json()
        _validate_login_result(login_result)

        self.user_id = login_result['token_info']["user_id"]
        self.login_token = login_result['token_info']["login_token"]
        self.app_token = login_result['token_info']["app_token"]

    def logout(self) -> None:
        """Huami 서버로 Logout 요청
        Logout 요청하지 않을 경우 
        스마트폰 앱으로 로그인 되어 있는 유저가 로그아웃 됨
        """        
        requests.post(
            url=_assemble_url(name='logout'),
            data=_assemble_payload(name='logout', login_token=self.login_token)
        )
        
    def devices(self) -> json:
        """디바이스 정보들을 모두 요청

        Returns:
            json: 디바이스 상태, 시리얼번호, 마지막 동기화 시간 등
        """
        return requests.get(
            url=_assemble_url(name='devices', user_id=self.user_id),
            params=_assemble_payload(name='devices'),
            headers={'apptoken': self.app_token}
        ).json()
        
    @staticmethod
    def is_valid(email: str, password: str) -> None:
        """Huami 계정이 유효한지 검증

        Args:
            email (str): Huami 계정 이메일
            password (str): Huami 계정 비밀번호

        Raises:
            value_error: AccessCode를 발급받을 수 없을 때 에러 발생
                            이메일이나 비밀번호가 잘못 되었을 경우
        """        
        account = HuamiAmazfit(email, password)
        try:
            account.access()
        except ValueError as value_error:
            raise value_error