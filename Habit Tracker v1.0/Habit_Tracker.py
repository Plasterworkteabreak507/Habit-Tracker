import sqlite3
import time
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass
import datetime
import sys

class DataBase:
    def __init__(self):
        self.name = "Tracker_For_Habits.db"
        self.SQLITE()
        self.init_achievements()
    
    def SQLITE(self):
        conn = sqlite3.connect(self.name)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           username TEXT UNIQUE NOT NULL,
           password_hash TEXT NOT NULL,
           salt TEXT NOT NULL,
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL,  
           habit_name TEXT NOT NULL, 
           description TEXT,
           period_type TEXT CHECK(period_type IN ('daily', 'weekly', 'monthly')),
           current_streak INTEGER DEFAULT 0,  
           best_streak INTEGER DEFAULT 0,
           target_count INTEGER DEFAULT 1,
           created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
           last_completed DATE,
           FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completion_date DATETIME NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'skipped', 'failed')),
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
            UNIQUE(habit_id, completion_date)
        )
        """)
    
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            streak_required INTEGER NOT NULL UNIQUE, 
            icon TEXT NOT NULL,
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
         """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          achievement_id INTEGER NOT NULL,
          unlocked_date DATETIME DEFAULT CURRENT_TIMESTAMP,
          habit_name TEXT,  
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
          UNIQUE(user_id, achievement_id)
        )
        """)

  
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_habit_id ON habits_logs(habit_id)")  
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_date ON habits_logs(completion_date)")

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_habit_date_status 
        ON habits_logs(habit_id, date(completion_date), status)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_habits_user_active_date 
        ON habits(user_id, last_completed)
        WHERE last_completed IS NOT NULL
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_achievements_streak 
        ON achievements(streak_required)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_achievements_composite 
        ON user_achievements(user_id, achievement_id)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_logs_date_status 
        ON habits_logs(date(completion_date), status)
        """)
    
        conn.commit()
        conn.close()

    def init_achievements(self):
      conn = sqlite3.connect(self.name)
      cursor = conn.cursor()
    
      try:
         cursor.execute("SELECT COUNT(*) FROM achievements")
         if cursor.fetchone()[0] == 0:
           print("Инициализация системы достижений...")
        
         achievements = [
            (7, "Первая неделя", "7 дней подряд", ),
            (10, "Десять дней", "10 дней подряд", ),
            (30, "Первый месяц", "30 дней подряд", ),
            (50, "Пятьдесят дней", "50 дней подряд", ),
            (100, "Сто дней", "100 дней подряд", ),
            (200, "Двести дней", "200 дней подряд",),
            (365, "Первый год", "365 дней подряд", ),
            (500, "Пятьсот дней", "500 дней подряд", ),
            (1000, "Тысяча дней", "1000 дней подряд", )
         ]

         for streak, name, desc,  in achievements:
            cursor.execute("""
            INSERT OR IGNORE INTO achievements (streak_required, name, description)
            VALUES (?, ?, ?)
            """, (streak, name, desc))
        
         conn.commit()
         print("Система достижений инициализирована!")
      except Exception as ia:
         print(f"Ошибка: {ia}")
      finally:
         conn.close()


class BaseProgramm:
    def __init__(self):
        self.db = DataBase()
        self.name = "Tracker For Habits"
        self.company = "With Open Crypto"
        self.version = "v1.0"
        self.current_user = None
        self.username = None

    def main(self):
        print("Привет! Я Tracker For Habits - Умный Трейкер за привычками")
        while True:
            print("1 - ВХОД В АККАУНТ")
            print("2 - РЕГИСТРАЦИЯ")
            print("3 - ВЫХОД")
            choice = input("Введите (1-3): ").strip()
            if choice == "1":
                self.login()
            elif choice == "2":
                self.registr()
            elif choice == "3":
                sys.exit(1)
            else:
                print("Ваш ответ не понятен. Попробуйте снова")


    @staticmethod
    def password_hash(password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        return base64.b64encode(kdf.derive(password.encode())).decode()
    

    def registr(self):
        print("РЕГИСТРАЦИЯ")
        while True:
          username = input("Введите имя пользователю: ").strip()
          if len(username) < 0:
              print("Имя пользователя не должно быть пустым")
              continue
          if len(username) < 3:
              print("Имя слишком маленькое")
              continue
          
          conn = sqlite3.connect(self.db.name)
          cursor = conn.cursor()

          cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
          if cursor.fetchone():
              print("Имя уже занято")
              continue
          while True:
              password = getpass.getpass("Введите мастер-пароль: ").strip()
              if len(password) < 6:
                  print("Пароль слишком мал")
                  continue
              confirm = getpass.getpass("Подтвердите мастер-пароль: ").strip()
              if password != confirm:
                  print("Пароли не совпадают")
                  continue
              break
          
          break

        salt = secrets.token_bytes(16)
        password_hash = self.password_hash(password, salt)
        

        try:
            cursor.execute("""
            INSERT INTO users (username, password_hash, salt)
            VALUES (?, ?, ?)
            """, (username, password_hash, base64.b64encode(salt).decode()))

            conn.commit()
            self.current_user = cursor.lastrowid
            self.username = username
            print(f"\nУспешная регистрация!Добро пожаловать {username}")
            print("ВАЖНОЕ УВЕДОМЛЕНИЕ: Запомните свой мастер-пароль. Потеряв его вы не сможете войти в аккаунт!")

            print("Перехожу...")
            time.sleep(0.5)
            self.show_menu()
            return True
        except Exception as reg:
            print(f"Произошла ошибка: {reg}")
            return False
        finally:
            conn.close()

    def login(self):
        conn = sqlite3.connect(self.db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()

        if user_count == 0:
            print("В системе нет зарегистрированных пользователей!\nСначала зарегистрируйтесь!")
            time.sleep(1.5)
            return False
        while True:
            username = input("Введите имя пользователя: ").strip()
            if not username:
                print("Имя не должно быть пустым")
                continue

            password = getpass.getpass("Введите мастер-пароль: " ).strip()
            if not password:
                print("Пароль не должен быть пустым!")
                continue

            conn = sqlite3.connect(self.db.name)
            cursor = conn.cursor()

            try:
               cursor.execute("SELECT id, password_hash, salt FROM users WHERE username = ?", (username,))
               user_data = cursor.fetchone()
               if not user_data:
                 print("Пользовтаель не найден!")
                 continue
               
               user_id, stored_hash, salt_b64 = user_data
               salt = base64.b64decode(salt_b64)
               password_hash = self.password_hash(password, salt)
               if password_hash != stored_hash:
                   print("Пароль неверный!")
                   conn.close()
                   continue
               
               self.current_user = user_id
               self.username = username
               print(f"Успешный вход!\nДобро пожаловать {username}")
               self.show_menu()
               return True
            
            except Exception as log:
                print(F"Произошла ошибка: {log}")
                return False
            finally:
                conn.close()


    def show_menu(self):
        print("Меню функций:")
        while True:
            print("1 - Создание привычки")
            print("2 - Просмотр привычки")
            print("3 - Пометка выполнение привычки")
            print("4 - Просмотр наград")
            print("5 - Выход в меню аутенфикации")
            print("6 - Быстрый выход")

            choice = input("Введите (1-6): ").strip()
            if choice == "1":
                self.create_habits()
            elif choice == "2":
                self.watch_habits()
            elif choice == "3":
                self.streak_habits()
            elif choice == "4":
                self.watch_achiements()
            elif choice == "5":
                self.main()
            elif choice == "6":
                import sys
                sys.exit(0)
            else:
                print("Ответ не понятен. Попробуйте снова!")
                continue   



    def create_habits(self):
        print("Создание привычки") 
        conn = sqlite3.connect(self.db.name)
        cursor = conn.cursor()


    
        try:
               name = input("Введите имя привычки: ").strip()                                                                                                                                                                                                                                                                                                                                                                                                              
               if not name:
                  print("Имя не должно быть пустым")
                  return False
           
               description = input("Введите описание (необязательно): ").strip() or "-"
           
               period_type = input("Введите тип периода (daily, weekly, monthly): ").strip().lower()
               if period_type not in ("daily", "weekly", "monthly"):
                  print("Введите daily, weekly или monthly")
                  return False
           
               target_count = int(input("Введите сколько раз надо выполнить: ").strip() or 1)

               cursor.execute("""
               INSERT INTO habits (user_id, habit_name, description, period_type, target_count)     
               VALUES (?, ?, ?, ?, ?)       
               """, (self.current_user, name, description, period_type, target_count))

               conn.commit()

               print("Данные успешно сохранены!")
               print("Результаты:")
               print(f"Имя привычки: {name}")
               print(f"Описание привычки: {description}")
               print(f"Тип пероида: {period_type}")
               print(f"Целевое количество: {target_count}")
               time.sleep(3)
               return True

        except Exception as ch:
               print(f"Произошла ошибка: {ch}")
        finally:
               conn.close()


    def watch_habits(self):
        print("Просмотр привычек")

        try:
            conn = sqlite3.connect(self.db.name)
            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, habit_name, description, period_type, 
                 target_count, current_streak, last_completed
            FROM habits 
            WHERE user_id = ?
            ORDER BY 
              CASE WHEN last_completed IS NULL THEN 1 ELSE 0 END,
              current_streak DESC,
              created_date DESC
            """, (self.current_user,))

            habits = cursor.fetchall()
            conn.close()

            if not habits:
                print("У вас нет привычек! Сначала их создайте")
                return
            
            print("\nВаши привычки:")
            for habit in habits:
                self.habits_show(habit)

            time.sleep(3)
            return habits
            

        except Exception as wh:
            print(f"Произошла ошибка: {wh}")
            return []
        finally:
            conn.close()

    def habits_show(self, habit):
        habit_id, name, desc, period, target, streak, last_date = habit 

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        today_status = "Не выполнено"
        if last_date:
           last_date_str = last_date.split()[0] if isinstance(last_date, str) else str(last_date)
           if last_date_str == today:
               today_status = "Выполнено"
    
        print(f"\nID: {habit_id}")
        print(f"Название: {name}")
    
        if desc:
           print(f"Описание: {desc}")
     
        print(f"Тип: {period}")
        print(f"Цель: {target} раз")
        print(f"Текущая серия: {streak} дней")
    
        if last_date:
           last_date_formatted = last_date[:10] if isinstance(last_date, str) else str(last_date)
           print(f"Последнее выполнение: {last_date_formatted}")


    def achivements(self):
        conn = sqlite3.connect(self.db.name)
        cursor = conn.cursor()

        achievements = [
            (7, "Первая неделя", "7 дней подряд"),
            (10, "Десять дней", "10 дней подряд"),
            (30, "Первый месяц", "30 дней подряд"),
            (50, "Пятьдесят дней", "50 дней подряд"),
            (100, "Сто дней", "100 дней подряд"),
            (200, "Двести дней", "200 дней подряд"),
            (365, "Первый год", "365 дней подряд"),
            (500, "Пятьсот дней", "500 дней подряд"),
            (1000, "Тысяча дней", "1000 дней подряд")
        ]

        for streak, name, desc in achievements:
          cursor.execute("""
          INSERT INTO achievements (streak_required, name, description)
          VALUES (?, ?, ?)
          """, (streak, name, desc))


        conn.close()

    def check_or_award_achiviements(self, habit_id, current_streak, habit_name):
        conn = sqlite3.connect(self.db.name)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT a.id, a.name, a.description, a.streak_required
        FROM achievements a
        WHERE a.streak_required <= ?
        AND a.id NOT IN (
           SELECT ua.achievement_id 
           FROM user_achievements ua 
           WHERE ua.user_id = ?
        )
        ORDER BY a.streak_required DESC
        """, (current_streak, self.current_user))
    
        new_achievements = cursor.fetchall()
    
        unlocked = []
        for ach_id, name, desc, required in new_achievements:
          cursor.execute("""
          INSERT INTO user_achievements (user_id, achievement_id, habit_name)
          VALUES (?, ?, ?)
          """, (self.current_user, ach_id, habit_name))
        
          unlocked.append({
            'name': name,
            'desc': desc,
            'required': required,
            'current': current_streak
          })
    
        conn.commit()
        conn.close()
    
   
        if unlocked:
           self.show_new_achievements(unlocked)
    
        return unlocked
    
    def show_new_achievements(self, achievements):
        print("Получено новое достижение!")
        for ach in achievements:
           print(f"\nДостижение: {ach['name']}")
           print(f"Условие: {ach['required']}+ дней")
           print(f"Ваш результат: {ach['current']} дней")
           print(f"Описание: {ach['desc']}")
           if ach.get('habit_name'):
              print(f"Получено за привычку: {ach['habit_name']}")


    def watch_achiements(self):
         conn = sqlite3.connect(self.db.name)
         cursor = conn.cursor()
    
         cursor.execute("""
         SELECT 
           a.name,
           a.description,
           a.streak_required,
           ua.unlocked_date,
           ua.habit_name
         FROM user_achievements ua
         JOIN achievements a ON ua.achievement_id = a.id
         WHERE ua.user_id = ?
         ORDER BY a.streak_required
         """, (self.current_user,))
    
         unlocked = cursor.fetchall()
    
    
         cursor.execute("""
         SELECT 
           name,
           description,
           streak_required
         FROM achievements
         ORDER BY streak_required
         """)
    
         all_achievements = cursor.fetchall()
         conn.close()

         print("Ваши достижения:")
         if unlocked:
           print("\nПолученные достижения")
           for name, desc, required, date_str, habit_name in unlocked:
            date_formatted = date_str[:10] if date_str else "Неизвестно"
            print(f"\n{name}")
            print(f"Требовалось: {required} дней")
            print(f"Получено: {date_formatted}")
            if habit_name:
                print(f"За привычку: {habit_name}")
            print(f"Описание: {desc}")
         else:
            print("\nУ вас пока нет достижений")

         time.sleep(3)


    def streak_habits(self):
        habits = self.watch_habits()
        if not habits:
          return
    
        try:
            habit_id = input("\nВведите ID привычки для отметки: ").strip()
            if not habit_id.isdigit():
               print("Ошибка: введите число")
               return
        
            habit_id = int(habit_id)
        
        
            conn = sqlite3.connect(self.db.name)
            cursor = conn.cursor()
        
            cursor.execute("""
            SELECT habit_name, current_streak FROM habits 
            WHERE id = ? AND user_id = ?
            """, (habit_id, self.current_user))
        
            habit_data = cursor.fetchone()
            if not habit_data:
               print("Ошибка: привычка не найдена или нет доступа")
               conn.close()
               return
        
            habit_name, current_streak = habit_data
        
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            SELECT 1 FROM habits_logs 
            WHERE habit_id = ? AND date(completion_date) = date(?)
            """, (habit_id, today))
        
            if cursor.fetchone():
               print("Эта привычка уже отмечена сегодня!")
               conn.close()
               return
        
  
            notes = input("Заметки (необязательно): ").strip() or None
        
            cursor.execute("""
            INSERT INTO habits_logs (habit_id, completion_date, notes, status)
            VALUES (?, ?, ?, 'completed')
            """, (habit_id, today, notes))

            new_streak = current_streak + 1
            cursor.execute("""
            UPDATE habits 
            SET current_streak = ?, 
               last_completed = date(?),
               best_streak = CASE WHEN ? > best_streak THEN ? ELSE best_streak END
            WHERE id = ?
            """, (new_streak, today, new_streak, new_streak, habit_id))
        
            conn.commit()
            conn.close()
        
            print(f"\nПривычка '{habit_name}' отмечена как выполненная!")
            print(f"Новый стрик: {new_streak} дней")
        
            time.sleep(3)
            self.check_or_award_achiviements(habit_id, new_streak, habit_name)
        
        except Exception as SH:
           print(f"Ошибка при отметке привычки: {SH}")


if __name__ == "__main__":
    try:
        time.sleep(1)
        app = BaseProgramm()
        app.main()

    except Exception as main:
        print(f"Произошла ошибка: {main}")
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("Программа приостанолвена пользователем")
    finally:
        print("Tracker For Habits завершает работу! До свидания!")


        

        

           


        
               
