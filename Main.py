import requests
import re
import json
import time
from recap_token import RecaptchaSolver

class TicketBooking:
    def __init__(self, user_data_file, recaptcha_token):
        self.s = requests.Session()
        self.recaptcha_token = recaptcha_token
        self.load_user_data(user_data_file)
        self.possible_seat_locations = self.determine_seat_locations()
        self.teams = self.initialize_teams()
        self.notified_matches = set()

    def load_user_data(self, user_data_file):
        with open(user_data_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
            self.username = lines[0]
            self.password = lines[1]
            self.search_word = lines[2]
            self.seats = lines[3]
            self.category = lines[4]

    def determine_seat_locations(self):
        if "درج" in self.category and "ول" in self.category:
            return ["Cat 1", "Cat1"]
        elif "درج" in self.category and "اني" in self.category:
            return ["Cat 2", "Cat2"]
        elif "تالت" in self.category or "ثالث" in self.category:
            return ["Cat 3", "Cat3"]
        elif "مقصو" in self.category:
            return ["VIP"]
        elif "علو" in self.category:
            return ["Upper"]
        elif "سفل" in self.category:
            return ["Lower"]
        else:
            return []

    def initialize_teams(self):
        return {
            'سماع': {'team_name': 'الاسماعيلى', 'eng_team': 'ISMAILY SC', 'categoryName': 'ISMAILY', 'teamid': '182'},
            'زمالك': {'team_name': 'الزمالك', 'eng_team': 'Zamalek SC', 'categoryName': 'Zamalek', 'teamid': '79'},
            'هل': {'team_name': 'الأهلى', 'eng_team': 'Al Ahly FC', 'categoryName': 'Ahly', 'teamid': '77'},
            'مصر': {'team_name': 'النادي المصري للألعاب الرياضية', 'eng_team': 'Al-Masry SC', 'categoryName': 'Al-Masry'}
        }

    def find_team_info(self):
        for key in self.teams:
            if key in self.search_word:
                team_info = self.teams[key]
                self.team_name = team_info['team_name']
                self.eng_team = team_info['eng_team']
                self.category_name = team_info['categoryName']
                self.team_id = team_info['teamid']
                return

    def get_headers(self):
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://tazkarti.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }

    def login(self):
        headers = self.get_headers()
        headers.update({'Content-Type': 'application/json'})
        json_data = {
            'Username': self.username,
            'Password': self.password,
            'recaptchaResponse': self.recaptcha_token,
        }
        r = self.s.post('https://tazkarti.com/home/Login', headers=headers, json=json_data).text
        if 'access_token' not in r:
            print("فشل تسجيل الدخول!")
            return False
        return True

    def check_matches_and_notify(self):
        try:
            res = self.s.get('https://tazkarti.com/data/matches-list-json.json', headers=self.get_headers()).text
            matches = json.loads(res)
            for match in matches:
                if (match["teamName1"] == self.eng_team or match["teamName2"] == self.eng_team) and match.get('matchStatus') == 1:
                    match_id = match["matchId"]
                    match_key = f"{match['teamName1']} vs {match['teamName2']}"
                    if match_key in self.notified_matches:
                        continue  # تم الإبلاغ عنه سابقاً

                    r1 = self.s.get(f'https://tazkarti.com/data/TicketPrice-AvailableSeats-{match_id}.json', headers=self.get_headers()).text
                    r1_data = json.loads(r1)

                    available_tickets = []
                    for category in r1_data['data']:
                        if category['categoryName'].strip().lower() == self.category_name.strip().lower():
                            available_tickets.append(category)
                        else:
                            for loc in self.possible_seat_locations:
                                if loc.lower() in category['categoryName'].strip().lower() and int(self.team_id) == category['teamId']:
                                    available_tickets.append(category)

                    if available_tickets:
                        message = f"🎟️ المباراة بين: {match['teamName1']} و {match['teamName2']}\n"
                        message += "التذاكر المتاحة الآن:\n"
                        for ticket in available_tickets:
                            message += f"فئة: {ticket['categoryName']} - {ticket['availableSeats']} مقعد بسعر {ticket['price']} جنيه.\n"
                        print(message)
                        self.send_telegram_notification(message)
                        self.notified_matches.add(match_key)
        except Exception as e:
            print(f"⚠️ خطأ أثناء الفحص: {e}")

    def send_telegram_notification(self, message):
        telegram_token = '7914202337:AAH7_T9TNFoMa3X8SfyvzmGFjah3lMhhPAA'
        chat_id = '6589167323'
        url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
        payload = {'chat_id': chat_id, 'text': message}
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print("✅ تم إرسال التنبيه عبر Telegram.")
            else:
                print("❌ فشل إرسال التنبيه عبر Telegram.")
        except Exception as e:
            print(f"❌ فشل إرسال التنبيه عبر Telegram: {e}")

if __name__ == '__main__':
    solver = RecaptchaSolver('https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LeypS8dAAAAAGWYer3FgEpGtmlBWBhsnGF0tCGZ&co=aHR0cHM6Ly90YXprYXJ0aS5jb206NDQz&hl=en&v=9pvHvq7kSOTqqZusUzJ6ewaF&size=invisible&cb=376av9ky8egv')
    token = solver.get_token()
    booking = TicketBooking(r'C:\Users\mohamed\Documents\Auto-Booking-Tazkarti-Ticket-main\data.txt', token)

    booking.find_team_info()

    if booking.login():
        last_keep_alive = time.time()
        while True:
            booking.check_matches_and_notify()

            # رسالة كل ساعة تطمنك إن السكربت شغال
            if time.time() - last_keep_alive >= 3600:
                try:
                    booking.send_telegram_notification("✅ مازال السكربت يعمل ويقوم بالفحص كل 30 ثانية بدون مشاكل.")
                    print("✅ تم إرسال رسالة تأكيد بأن السكربت شغال.")
                except Exception as e:
                    print(f"❌ فشل إرسال رسالة الاطمئنان: {e}")
                last_keep_alive = time.time()

            time.sleep(30)



