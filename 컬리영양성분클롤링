import os
import time
import requests
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------
# 1. 팝업 닫기 (방해 요소 제거)
# ---------------------------------------------------------
def close_popup(driver):
    try:
        close_btns = driver.find_elements(By.XPATH, "//button[contains(text(), '닫기')]")
        for btn in close_btns:
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.5)
    except:
        pass

# ---------------------------------------------------------
# 2. '검색어'로 상품 검색 후 정확한 상품 클릭
# ---------------------------------------------------------
def search_and_click_product(driver, keyword):
    # URL 파라미터 sword 사용
    encoded_keyword = quote(keyword)
    search_url = f"https://www.kurly.com/search?sword={encoded_keyword}&page=1"
    
    print(f"▶ '{keyword}' 검색 페이지로 이동: {search_url}")
    driver.get(search_url)
    time.sleep(3) 
    
    close_popup(driver) 

    try:
        # 상품 링크 요소들 가져오기
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/goods/']")))
        
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/goods/']")
        
        target_url = None
        print(f"▶ 검색 결과 {len(links)}개 분석 중...")

        # 검색어의 핵심 단어만 추출 
        core_keyword = keyword.split()[0]
        if key_word_clean := keyword.replace("[", "").replace("]", "").split(" ")[0]:
             core_keyword = key_word_clean

        for link in links:
            try:
                # 상품명 텍스트가 안 보일 경우를 대비해 innerHTML 등도 고려할 수 있으나,
                # 보통 링크 안의 텍스트나 img alt를 확인
                product_name = link.text.strip()
                
                # 텍스트가 없으면(이미지 배너 등) 건너뜀
                if not product_name: 
                    continue
                
                # 사용자가 입력한 키워드가 상품명에 포함되어 있는지 확인
                # 정확도를 높이기 위해 in 검사
                if core_keyword in product_name or keyword in product_name:
                    print(f"  [성공] 일치하는 상품 발견! -> {product_name.splitlines()[0]}")
                    target_url = link.get_attribute("href")
                    break
            except:
                continue
        
        # 반복문이 끝났는데 못 찾았으면, 리스트의 첫 번째 상품(배너 제외)을 선택
        if not target_url and len(links) > 0:
             print(" 정확한 이름 일치를 못 찾아 첫 번째 상품을 선택합니다.")
             target_url = links[0].get_attribute("href")

        return target_url

    except Exception as e:
        print(f" 검색 도중 에러 발생: {e}")
        return None

# ---------------------------------------------------------
# 3. 상세 페이지 이미지 수집 (★핵심 수정 부분★)
# ---------------------------------------------------------
def get_images(driver, url):
    print(f"▶ 상세 페이지 이동 중: {url}")
    driver.get(url)
    time.sleep(3)
    
    close_popup(driver)

    # 스크롤 다운 (이미지 로딩 유도)
    print("▶ 이미지 로딩을 위해 스크롤을 내립니다...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # 너무 빨리 내리면 로딩 안될 수 있으니 천천히 3번 정도 나눠서 내리기
    for i in range(1, 4):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/4});")
        time.sleep(1)
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    image_list = []
    
    selectors = [
        "img.ktx_yjgr948",            # 최신 템플릿 
        "img.css-1d3w5wq",            # 일반 템플릿
        "#goods-description img",     # 구버전 템플릿
        ".goods_view_infomation img", # 또 다른 버전
        ".ktx_1qwdml40 img"           # 최상위 컨테이너 기반 탐색
    ]

    found_imgs = []
    # 여러 선택자 중 하나라도 걸리면 그것을 사용
    for selector in selectors:
        found_imgs = driver.find_elements(By.CSS_SELECTOR, selector)
        if len(found_imgs) > 0:
            print(f"  -> '{selector}' 선택자로 {len(found_imgs)}장 발견!")
            break
    
    for img in found_imgs:
        src = img.get_attribute("src")
        # src가 있고, http로 시작하는 유효한 이미지인지 확인
        if src and src.startswith("http"):
            image_list.append(src)
            
    return list(dict.fromkeys(image_list)) # 중복 제거

# ---------------------------------------------------------
# 4. 이미지 다운로드
# ---------------------------------------------------------
def download_images(image_urls, keyword):
    if not image_urls:
        print("저장할 이미지가 없습니다.")
        return

    # 폴더명에서 특수문자 제거 (윈도우 폴더 생성 오류 방지)
    safe_keyword = "".join([c for c in keyword if c.isalnum() or c in (' ', '_')]).strip()
    folder_name = f"kurly_{safe_keyword}"
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    print(f"▶ '{folder_name}' 폴더에 저장 시작")
    headers = {"User-Agent": "Mozilla/5.0"}

    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                ext = url.split('.')[-1].split('?')[0]
                if len(ext) > 4 or len(ext) < 3: ext = "jpg"
                
                filename = f"{folder_name}/img_{i+1}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"  [저장] {filename}")
        except:
            pass

# ---------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------
if __name__ == "__main__":
    user_input = input("검색할 상품명을 입력하세요 : ")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        target_url = search_and_click_product(driver, user_input)
        
        if target_url:
            images = get_images(driver, target_url)
            
            if images:
                download_images(images, user_input)
                print("\n 모든 작업 완료")
            else:
                print("\n 상세 페이지에서 이미지를 찾지 못했습니다")
        else:
            print("\n 상품을 찾지 못해 작업을 종료합니다")

    finally:
        driver.quit()
