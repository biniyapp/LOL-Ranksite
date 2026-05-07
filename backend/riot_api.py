import requests
import urllib.parse
from fastapi import HTTPException

# ⚠️ 최신 API 키를 사용해 주세요
API_KEY = "RGAPI-8899f5c9-c4b0-4c08-96f5-7c71db02b670"

def get_summoner_lp(nickname: str, tag: str):
    encoded_nickname = urllib.parse.quote(nickname)
    encoded_tag = urllib.parse.quote(tag)
    
    headers = {
        "X-Riot-Token": API_KEY,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.4 Safari/605.1.15",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }

    try:
        # 1단계: PUUID 조회 (Asia 서버)
        print(f"--- 1단계: PUUID 조회 ({nickname}#{tag}) ---")
        account_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_nickname}/{encoded_tag}"
        response = requests.get(account_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ 1단계 실패: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Account API Error")
        
        puuid = response.json().get("puuid")
        print(f"✅ PUUID 획득 완료: {puuid}")

        # 2단계: PUUID로 바로 랭크 정보 조회 (KR 서버)
        print(f"--- 2단계: 랭크 데이터 조회 (KR) ---")
        league_url = f"https://kr.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        response = requests.get(league_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ 2단계 실패: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail="League API Error")
        
        league_entries = response.json()
        print(f"✅ 데이터 수신 완료: {league_entries}")

        for entry in league_entries:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                lp = entry.get("leaguePoints", 0)
                tier = entry.get("tier", "UNKNOWN")
                rank = entry.get("rank", "")
                print(f"🏆 결과: {tier} {rank} - {lp}LP")
                return lp
                
        print("ℹ️ 솔로 랭크 데이터가 없습니다.")
        return 0

    except Exception as e:
        print(f"💥 최종 에러: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
