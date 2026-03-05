import time
import os
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------
# 1. 팝업 닫기
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
# 2. 상품 검색 및 이동
# ---------------------------------------------------------
def search_and_click_product(driver, keyword):
    encoded_keyword = quote(keyword)
    search_url = f"https://www.kurly.com/search?sword={encoded_keyword}&page=1"
    print(f"▶ '{keyword}' 검색 페이지로 이동: {search_url}")
    driver.get(search_url)
    time.sleep(3)
    close_popup(driver) 

    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/goods/']")))
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/goods/']")
        
        target_url = None
        core_keyword = keyword.split()[0]
        
        for link in links:
            try:
                product_name = link.text.strip()
                if not product_name: continue
                
                if core_keyword in product_name or keyword in product_name:
                    print(f"  [성공] 상품 발견! -> {product_name.splitlines()[0]}")
                    target_url = link.get_attribute("href")
                    break
            except: continue
        
        if not target_url and len(links) > 0:
            print("정확한 이름 일치를 못 찾아 첫 번째 상품을 선택합니다.")
            target_url = links[0].get_attribute("href")

        return target_url
    except Exception as e:
        print(f"❌ 검색 도중 에러 발생: {e}")
        return None

# ---------------------------------------------------------
# 3. 리뷰 데이터 수집
# ---------------------------------------------------------
def get_reviews(driver, url, max_pages=3):
    print(f"상세 페이지 이동 중: {url}")
    driver.get(url)
    time.sleep(3)
    close_popup(driver)

    try:
        review_section = driver.find_element(By.ID, "review")
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        time.sleep(1)
        driver.execute_script("window.scrollBy(0, -100);")
    except:
        print("⚠ 리뷰 섹션 ID(#review)를 찾을 수 없어 페이지 끝으로 이동합니다.")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    time.sleep(2)

    all_reviews = []
    
    for page in range(1, max_pages + 1):
        print(f" 리뷰 {page}페이지 수집 중...")
        articles = driver.find_elements(By.CSS_SELECTOR, "#review article")
        
        if not articles:
            print("  - 리뷰를 찾을 수 없습니다.")
            break

        for article in articles:
            try:
                try: user_id = article.find_element(By.CSS_SELECTOR, "span[class*='css-f3vz0n']").text
                except: user_id = "익명"

                try: product_option = article.find_element(By.TAG_NAME, "h3").text
                except: product_option = "-"

                try: content = article.find_element(By.TAG_NAME, "p").text
                except: content = "내용 없음"

                try: date_str = article.find_element(By.CSS_SELECTOR, "footer span").text
                except: date_str = "-"

                try: 
                    helpful_text = article.find_element(By.CSS_SELECTOR, "footer button span:nth-child(2)").text
                    helpful_count = helpful_text.replace("도움돼요", "").strip()
                except: helpful_count = "0"

                review_data = {
                    "작성자": user_id,
                    "구매옵션": product_option,
                    "내용": content,
                    "날짜": date_str,
                    "도움수": helpful_count
                }
                all_reviews.append(review_data)
            except:
                continue
        
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "#review button[aria-label='다음 페이지'], #review button.css-1orps7k")
            if next_btn.get_attribute("disabled"):
                print("  - 마지막 페이지입니다.")
                break
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
        except:
            break
            
    return all_reviews

# ---------------------------------------------------------
# 4. TXT 파일 저장 
# ---------------------------------------------------------
def save_to_txt(reviews, keyword):
    if not reviews:
        print("❌ 저장할 리뷰 데이터가 없습니다.")
        return

    # 파일명 생성
    safe_keyword = "".join([c for c in keyword if c.isalnum() or c in (' ', '_')]).strip()
    filename = f"kurly_reviews_{safe_keyword}.txt"

    # 파일 쓰기 
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"검색어: {keyword}\n")
            f.write(f"수집 날짜: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"총 리뷰 수: {len(reviews)}개\n")
            f.write("=" * 50 + "\n\n")

            for i, r in enumerate(reviews, 1):
                f.write(f"[Review {i}]\n")
                f.write(f"작성자  : {r['작성자']}\n")
                f.write(f"작성일  : {r['날짜']}\n")
                f.write(f"구매옵션: {r['구매옵션']}\n")
                f.write(f"도움수  : {r['도움수']}\n")
                f.write("-" * 20 + "\n")
                f.write(f"{r['내용']}\n")
                f.write("\n" + "=" * 50 + "\n\n")
        
        print(f"\n '{filename}' 파일에 저장이 완료되었습니다!")
        
    except Exception as e:
        print(f"\n 파일 저장 중 오류 발생: {e}")

# ---------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------
if __name__ == "__main__":
    user_input = input("검색할 상품명을 입력하세요: ")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    # 브라우저 꺼짐 방지 옵션
    chrome_options.add_experimental_option("detach", True)
    
    # chrome_options.add_experimental_option("detach", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        target_url = search_and_click_product(driver, user_input)
        
        if target_url:
            reviews = get_reviews(driver, target_url, max_pages=3)
            # TXT 저장 함수 호출
            save_to_txt(reviews, user_input)
        else:
            print("\n상품을 찾지 못해 작업을 종료합니다")

    finally:
        #
        driver.quit()
