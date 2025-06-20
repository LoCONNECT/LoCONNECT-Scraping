from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def crawl_and_save_menu(url: str, filename: str = "menu.txt"):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(2)

        menu_elements = driver.find_elements(By.CSS_SELECTOR, ".menu ul li")

        lines = []
        for item in menu_elements:
            name = item.find_element(By.CLASS_NAME, "tit").text.strip()
            try:
                price = item.find_element(By.CLASS_NAME, "price").text.strip()
            except:
                price = "가격 정보 없음"
            lines.append(f"{name} - {price}")

        # 파일로 저장
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"메뉴 정보를 '{filename}'로 저장했습니다!")

    except Exception as e:
        print(f"에러 발생: {e}")

    finally:
        driver.quit()

# 실행 예시
if __name__ == "__main__":
    test_url = "https://www.diningcode.com/profile.php?rid=ebfGaEjvwLJG"
    crawl_and_save_menu(test_url, "menu.txt")
