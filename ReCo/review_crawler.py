import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from tqdm import tqdm

def safe_click(driver, element):
    """네 가지 방식으로 클릭을 시도하여 성공하면 True를 반환한다."""
    try:
        element.click()
        return True
    except Exception:
        pass
    try:
        driver.execute_script("arguments[0].click()", element)
        return True
    except Exception:
        pass
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element).click().perform()
        return True
    except Exception:
        pass
    try:
        driver.execute_script(
            "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));",
            element
        )
        return True
    except Exception:
        pass
    return False

def extract_reviews_in_iframe(driver, wait):
    """
    iframe 컨텍스트 안에서 전체보기/더보기 처리 후,
    리뷰를 <li> 요소 기반으로 추출한다.
    """
    # 전체보기 버튼 클릭
    try:
        view_all = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'전체')]")))
        safe_click(driver, view_all)
        time.sleep(random.uniform(0.5, 1.5))
    except TimeoutException:
        pass

    # 더보기 버튼 반복 클릭
    while True:
        try:
            more_btn = driver.find_element(By.XPATH, "//*[contains(text(),'더보기')]")
            safe_click(driver, more_btn)
            time.sleep(random.uniform(0.5, 1.5))
        except Exception:
            break

    # 스크롤하여 모든 리뷰 로딩
    try:
        review_panel = driver.find_element(By.XPATH, "//div[@role='dialog' or contains(@class,'overflow-y-auto')]")
    except NoSuchElementException:
        review_panel = driver.find_element(By.TAG_NAME, "body")

    last_height = 0
    while True:
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", review_panel)
        time.sleep(0.5)
        new_height = driver.execute_script("return arguments[0].scrollTop", review_panel)
        if new_height == last_height:
            break
        last_height = new_height

    # <li> 요소 기준으로 후기 추출
    items = driver.find_elements(By.TAG_NAME, 'li')
    data = []
    for li in items:
        # 전체 텍스트를 줄 단위로 분할
        lines = [line.strip() for line in li.text.split('\n') if line.strip()]
        # 리뷰 항목은 작성자, 역할+날짜, 내용(그 외 줄) 구조를 갖는다
        if len(lines) >= 3:
            reviewer = lines[0]
            role_date = lines[1]
            content = ' '.join(lines[2:])
            # 역할과 날짜 분리 (예: "구매자 │ 2021-11-27")
            if '│' in role_date:
                role, date = [part.strip() for part in role_date.split('│')]
            else:
                # 구분자가 다른 경우 공백으로 분리
                parts = role_date.split()
                role = parts[0] if parts else ''
                date = parts[1] if len(parts) > 1 else ''
            data.append({
                'reviewer_id': reviewer,
                'review_role': role,
                'review_date': date,
                'review_content': content
            })
    return data



def main():
    input_csv = 'seller_new_data.csv'
    review_output_csv = 'seller_review_data.csv'
    
    # 배치 크기 설정
    BATCH_SIZE = 500
    
    # 전체 데이터 로드
    sellers_df = pd.read_csv(input_csv)
    total_sellers = len(sellers_df)
    
    print(f"총 {total_sellers}개 판매자 데이터 로드")
    print(f"배치 크기: {BATCH_SIZE}개씩 처리")
    
    # 전체 결과를 담을 리스트
    all_review_rows = []
    
    # 기존 데이터가 있으면 불러오기 (배치 1 결과)
    try:
        existing_df = pd.read_csv(f'temp_{review_output_csv}')
        all_review_rows = existing_df.to_dict('records')
        print(f"기존 데이터 로드: {len(all_review_rows)}개 리뷰")
    except FileNotFoundError:
        print("기존 데이터 없음 - 새로 시작")
    
    # 배치별로 처리 (배치 2부터 시작)
    START_BATCH = 52  # 시작할 배치 번호 (1부터 시작하려면 1로 변경)
    start_index = (START_BATCH - 1) * BATCH_SIZE
    
    for batch_start in range(start_index, total_sellers, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_sellers)
        batch_df = sellers_df.iloc[batch_start:batch_end]
        
        print(f"\n=== 배치 {batch_start//BATCH_SIZE + 1}: {batch_start+1}~{batch_end} 처리 중 ===")
        
        # 브라우저 초기화 (배치별로 새로 시작)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/125.0.0.0 Safari/537.36')
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        batch_review_rows = []

        for _, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc=f"Batch {batch_start//BATCH_SIZE + 1}"):
            seller_code = str(row['판매자코드']).strip()
            seller_name = row['판매자명']
            review_count = int(row['거래후기수'])

            # 리뷰 수가 0인 경우 건너뜀
            if review_count == 0:
                continue

            store_url = f"https://web.joongna.com/store/{seller_code}"

            # 스토어 페이지 접속
            driver.get(store_url)
            time.sleep(random.uniform(2.0, 4.0))

            # 리뷰 버튼 찾기 위한 XPath 후보
            review_xpaths = [
                "//dt[normalize-space()='거래후기']/parent::div",
                "//div[@class='relative cursor-pointer']/dt[normalize-space()='거래후기']/..",
                "//*[contains(text(),'거래후기')]/ancestor::div[contains(@class,'cursor-pointer')]",
                "//*[contains(text(),'거래후기')]"
            ]

            clicked = False
            for xpath in review_xpaths:
                try:
                    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    driver.execute_script("arguments[0].scrollIntoView();", elem)
                    time.sleep(random.uniform(0.2, 0.5))
                    if safe_click(driver, elem):
                        clicked = True
                        break
                except TimeoutException:
                    continue

            if not clicked:
                print(f"{seller_code}({seller_name}) 페이지에서 '거래후기' 버튼 클릭 실패")
                time.sleep(random.uniform(1.0, 2.0))
                continue

            time.sleep(random.uniform(0.5, 1.5))

            try:
                # 리뷰 iframe이 로드될 때까지 대기 후 전환
                wait.until(EC.frame_to_be_available_and_switch_to_it(
                    (By.CSS_SELECTOR, "iframe.w-full.h-full")
                ))

                # iframe 안에서 리뷰 추출
                reviews = extract_reviews_in_iframe(driver, wait)
                for r in reviews:
                    r['seller_code'] = seller_code
                    r['seller_name'] = seller_name
                    r['url'] = driver.current_url
                    batch_review_rows.append(r)

                # iframe에서 나와 원래 페이지로 돌아가기
                driver.switch_to.default_content()

            except TimeoutException:
                print(f"{seller_code}({seller_name}) 페이지에서 리뷰 iframe을 찾지 못했습니다.")
                driver.switch_to.default_content()
                continue

            # 판매자 간 무작위 대기
            time.sleep(random.uniform(1.0, 2.0))
        
        # 배치 처리 완료 후 브라우저 종료
        driver.quit()
        
        # 배치 결과를 전체 결과에 추가
        all_review_rows.extend(batch_review_rows)
        
        print(f"배치 {batch_start//BATCH_SIZE + 1} 완료: 리뷰 {len(batch_review_rows)}개 수집")
        
        # 중간 저장 (배치마다 백업)
        if all_review_rows:
            temp_review_df = pd.DataFrame(all_review_rows)
            temp_review_df.to_csv(f'temp_{review_output_csv}', index=False, encoding='utf-8-sig')
            
        print(f"중간 저장 완료 (총 누적: 리뷰 {len(all_review_rows)}개)")
    
    print(f"\n=== 전체 처리 완료 ===")
    
    # 최종 데이터 저장
    if all_review_rows:
        review_df = pd.DataFrame(all_review_rows)
        review_df.to_csv(review_output_csv, index=False, encoding='utf-8-sig')
        print(f"모든 리뷰 데이터가 {review_output_csv}에 저장되었습니다. (총 {len(all_review_rows)}개)")
    else:
        print("수집된 리뷰 데이터가 없습니다.")

if __name__ == "__main__":
    main()