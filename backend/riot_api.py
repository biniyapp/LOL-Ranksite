import os
import requests
import urllib.parse
from fastapi import HTTPException
import concurrent.futures
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키를 가져옵니다.
API_KEY = os.getenv("RIOT_API_KEY")

if not API_KEY:
    print("⚠️ 경고: RIOT_API_KEY 환경 변수가 설정되지 않았습니다.")

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
                return lp, tier, rank
                
        print("ℹ️ 솔로 랭크 데이터가 없습니다.")
        return 0, "UNKNOWN", ""

    except Exception as e:
        print(f"💥 최종 에러: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

def fetch_riot_id(summoner_id, headers):
    """소환사 ID로 Riot ID(닉네임#태그)를 가져오는 헬퍼 함수"""
    try:
        # 1. Summoner ID -> PUUID
        sum_url = f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
        sum_resp = requests.get(sum_url, headers=headers)
        if sum_resp.status_code != 200:
            return "Unknown", "KR1"
        puuid = sum_resp.json().get("puuid")

        # 2. PUUID -> Riot ID
        acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
        acc_resp = requests.get(acc_url, headers=headers)
        if acc_resp.status_code != 200:
            return "Unknown", "KR1"
        data = acc_resp.json()
        return data.get("gameName", "Unknown"), data.get("tagLine", "KR1")
    except:
        return "Unknown", "KR1"

def get_global_top_50():
    headers = {
        "X-Riot-Token": API_KEY,
        "Accept-Language": "ko-KR,ko;q=0.9"
    }
    
    try:
        # 1. 챌린저 리그 정보 조회
        url = "https://kr.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Global League API Error")
        
        data = response.json()
        entries = data.get("entries", [])
        
        # 2. LP 순으로 정렬 후 상위 50명 추출
        sorted_entries = sorted(entries, key=lambda x: x.get("leaguePoints", 0), reverse=True)[:50]
        
        # 3. 각 소환사의 실제 닉네임과 태그를 병렬로 가져오기 (성능 향상)
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # summonerId 리스트 추출
            summoner_ids = [entry.get("summonerId") for entry in sorted_entries]
            # 병렬 호출
            future_to_id = {executor.submit(fetch_riot_id, sid, headers): sid for sid in summoner_ids}
            
            id_to_riotinfo = {}
            for future in concurrent.futures.as_completed(future_to_id):
                sid = future_to_id[future]
                try:
                    name, tag = future.result()
                    id_to_riotinfo[sid] = (name, tag)
                except:
                    id_to_riotinfo[sid] = ("Unknown", "KR1")

        # 4. 최종 결과 조립
        for i, entry in enumerate(sorted_entries):
            sid = entry.get("summonerId")
            nickname, tag = id_to_riotinfo.get(sid, ("Unknown", "KR1"))
            
            results.append({
                "id": i,
                "nickname": nickname,
                "tag": tag,
                "score": entry.get("leaguePoints", 0),
                "max_score": entry.get("leaguePoints", 0),
                "tier": "CHALLENGER",
                "rank": ""
            })
            
        return results
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
