
import argparse
from time import sleep
from selenium.webdriver.common.by import By

from browser_automation import BrowserManager, Node
from utils import Utility
from w_metamask import Setup as w_metamaskSetup, Auto as w_metamaskAuto

PROJECT_URL = "https://bytenova.ai/rewards"

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        self.w_metamask_setup = w_metamaskSetup(node, profile)
        
    def _run(self):
        self.w_metamask_setup._run()
        self.node.new_tab(f'{PROJECT_URL}?invite_code=Ljdm0oFIR', method="get")
        Utility.wait_time(10)

class Auto:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.password = profile.get('password')
        self.w_metamask_auto = w_metamaskAuto(node, profile)
    
    def check_connected(self):
        self.node.find(By.XPATH, '//title[contains(text(),"Quests")]')
        btns = self.node.find_all(By.TAG_NAME, 'button', timeout=5)
        if not btns:
            #Đã đăng nhập
            div_els = self.node.find_all(By.TAG_NAME, 'div')
            for div in div_els:
                if '0x' in div.text.lower():
                    self.node.log('Đã đăng nhập')
                    return True
            
        for btn in btns:
            if 'Connect Wallet'.lower() in btn.text.lower():
                self.node.log(f'Cần đăng nhập')
                return False

        self.node.snapshot('Không thể xác nhận trạng thái đăng nhập')

    def connect(self):
        self.node.find_and_click(By.XPATH, '//button[contains(text(),"Connect Wallet")]')
        self.node.find_and_click(By.XPATH, '//p[contains(text(),"MetaMask")]')
        self.w_metamask_auto.confirm('connect')
        self.w_metamask_auto.confirm('approve')
        self.w_metamask_auto.confirm('confirm')
        
        self.node.reload_tab()
        return self.check_connected()

    def check_in(self, el):
        self.node.scroll_to(el)
        self.node.click(el)
        self.node.find_and_click(By.XPATH, '//img[contains(@src, "arrow-black")]/..')
        return self.w_metamask_auto.confirm('confirm')

    def social_1_click(self, el):
        self.node.scroll_to(el)
        self.node.click(el)
        self.node.find_and_click(By.XPATH, '//img[contains(@src, "arrow-black")]/..')
        self.node.close_tab('https://x.com')
        return self.node.switch_tab(PROJECT_URL)

    def _run(self):
        completed=[]
        quests=['check-in', 'social']
        self.w_metamask_auto._run()
        self.node.new_tab(f'{PROJECT_URL}?invite_code=Ljdm0oFIR', method="get")
        if not self.check_connected():
            self.connect()
        
        while True:
            self.node.reload_tab()
            task=None
            tasks = self.node.find_all(By.XPATH, '//div[contains(text(),"Active")]/../..')
            if 'CHECK-IN'.lower() in quests:
                task = tasks[0]
            else:
                if len(tasks) > 1:
                    task = tasks[1]

            if task:
                if 'CHECK-IN'.lower() in quests and 'CHECK-IN'.lower() in task.text.lower():
                    quests.remove('check-in')
                    if self.check_in(task):
                        completed.append('CHECK-IN')
                        self.node.log('checked-in')
                elif 'Reply'.lower() in task.text.lower():
                    if self.social_1_click(task):
                        completed.append('Reply')
                elif 'Repost'.lower() in task.text.lower():
                    if self.social_1_click(task):
                        completed.append('Repost')
                elif 'Like'.lower() in task.text.lower():
                    if self.social_1_click(task):
                        completed.append('Like')
                elif 'Follow'.lower() in task.text.lower():
                    if self.social_1_click(task):
                        completed.append('Follow')
                else:
                    break
            if len(tasks) <= 1:
                break

        counts = {}
        for task in completed:
            if task in counts:
                counts[task] += 1
            else:
                counts[task] = 1
        self.node.snapshot(f'Hoàn thành: {counts}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help="Chạy ở chế độ tự động")
    parser.add_argument('--headless', action='store_true', help="Chạy trình duyệt ẩn")
    parser.add_argument('--disable-gpu', action='store_true', help="Tắt GPU")
    args = parser.parse_args()

    profiles = Utility.read_data('profile_name', 'password')
    if not profiles:
        print("Không có dữ liệu để chạy")
        exit()

    browser_manager = BrowserManager(AutoHandlerClass=Auto, SetupHandlerClass=Setup)
    browser_manager.config_extension('Meta-Wallet-*.crx')
    browser_manager.run_terminal(
        profiles=profiles,
        max_concurrent_profiles=4,
        block_media=True,
        auto=args.auto,
        headless=args.headless,
        disable_gpu=args.disable_gpu,
    )