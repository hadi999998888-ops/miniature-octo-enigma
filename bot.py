import asyncio, os, html, hashlib, logging
from pathlib import Path
from datetime import date, timedelta
import aiosqlite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Загружаем секреты именно из .env рядом с bot.py, независимо от папки запуска.
ENV_FILE = Path(__file__).resolve().with_name(".env")
if ENV_FILE.exists():
    # На Android/Linux ограничиваем чтение файла владельцем (если ОС поддерживает права).
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass
load_dotenv(dotenv_path=ENV_FILE, override=False)
TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB=Path("hestle_progress.db")
IMG=Path("Start.jpg")
dp=Dispatcher()
logging.basicConfig(level=logging.INFO)

MODULES={
"Старт и основы":["Что такое программа","Знакомство с Python","Первая команда print","Комментарии","Ошибки и отладка","Строки","Числа","Арифметика","Порядок выполнения"],
"Переменные и типы":["Переменные","Правила имён","Изменение значения","Тип str","Тип int","Тип float","Тип bool","Проверка типа type","Преобразование типов"],
"Ввод и строки":["Ввод input","Преобразование ввода","f-строки","Длина строки len","Объединение строк","Методы строк","Срезы строк","Проверка in","Форматирование чисел"],
"Условия":["Операторы сравнения","Условие if","Ветка else","Ветка elif","Логический and","Логический or","Логический not","Вложенные условия","Тернарное выражение"],
"Циклы":["Цикл for","Функция range","Цикл while","Счётчик","Оператор break","Оператор continue","Вложенные циклы","enumerate","zip"],
"Коллекции":["Списки","Индексы списка","Метод append","Удаление элементов","Сортировка","Кортежи","Множества","Словари","Методы словаря"],
"Функции":["Создание функций def","Параметры","Возврат return","Значения по умолчанию","Именованные аргументы","Область видимости","Импорт модулей","from import","Докстроки"],
"Файлы и ошибки":["Открытие файлов","Чтение read","Запись write","Добавление в файл","try и except","finally","raise","Пути pathlib","Формат JSON"],
"ООП":["Что такое класс","Создание объекта","Метод __init__","Атрибут self","Методы класса","Наследование","Переопределение","Инкапсуляция","dataclass"],
"Продвинутый Python":["List comprehension","Генераторы","lambda","map","filter","Аннотации типов","Контекстные менеджеры","Регулярные выражения","Тестирование assert"],
"Инструменты":["Терминал","Установка пакетов pip","Виртуальное окружение","Git","Коммиты","Структура проекта","Переменные окружения","Логирование","requirements.txt"],
"Проекты":["Калькулятор","Проверка пароля","Игра угадай число","Список покупок","Счётчик слов","Книга контактов","Заметки в файл","HTTP-запросы","Финальный проект"]
}
LESSONS=[]
for module, titles in MODULES.items():
    for title in titles:
        # Small, beginner-friendly learning unit with one exact, safe-to-check code task.
        example="print('Привет, Python!')"
        if module=="Переменные и типы": example="user_name = 'Alex'\nlevel = 1\nprint(user_name, level)"
        elif module=="Ввод и строки": example="name = input('Как тебя зовут? ')\nprint(f'Привет, {name}!')"
        elif module=="Условия": example="age = 18\nif age >= 18:\n    print('Доступ разрешён')\nelse:\n    print('Пока рано')"
        elif module=="Циклы": example="for number in range(3):\n    print(number)"
        elif module=="Коллекции": example="languages = ['Python', 'Java']\nlanguages.append('Go')\nprint(languages)"
        elif module=="Функции": example="def greet(name):\n    return f'Привет, {name}'\nprint(greet('Alex'))"
        elif module=="Файлы и ошибки": example="try:\n    number = int('12')\nexcept ValueError:\n    print('Нужно число')"
        elif module=="ООП": example="class User:\n    def __init__(self, name):\n        self.name = name\nuser = User('Alex')"
        elif module=="Продвинутый Python": example="squares = [n * n for n in range(5)]\nprint(squares)"
        elif module=="Инструменты": example="python -m pip install aiogram"
        elif module=="Проекты": example="def main():\n    print('Мой первый проект')\n\nif __name__ == '__main__':\n    main()"
        expected=f"print('{title}')"
        body=(f"<b>{html.escape(title)}</b> — тема раздела «{html.escape(module)}».\n\n"
              f"Разбирай тему по шагам: сначала пойми назначение конструкции, затем посмотри пример, "
              f"запусти его и измени значения. Не старайся просто запомнить строку — объясни себе, "
              f"что делает каждая часть кода.\n\n"
              f"<b>Главная привычка:</b> проверяй результат маленькими экспериментами. "
              f"Если появилась ошибка, прочитай её и найди строку, где возникла проблема.")
        LESSONS.append({"module":module,"title":title,"body":body,"example":example,"task":f"Напиши код, который выводит на экран название темы: {title}","expected":expected,"hint":"Используй print() и заключи текст в кавычки."})

PRACTICE=[
("Что выводит print(4 + 3)?",["7","43","ошибка"],"7","Оператор + складывает числа."),
("Какой тип хранит текст?",["str","int","bool"],"str","str — строковый тип."),
("С какого индекса начинается список?",["0","1","-1"],"0","Первый элемент имеет индекс 0."),
("Что означает == ?",["Сравнение","Присваивание","Умножение"],"Сравнение","Один знак = присваивает, два == сравнивают."),
("Как объявить функцию?",["def","func","make"],"def","Функции объявляют через def."),
("Как добавить элемент в конец списка?",["append()","push()","add_end()"],"append()","У списка есть метод append()."),
("Как завершить цикл?",["break","stop","close"],"break","break завершает ближайший цикл."),
("Как получить ввод пользователя?",["input()","print()","type()"],"input()","input() ждёт пользовательский ввод.")
]
LEVELS=[(0,"Новичок"),(100,"Ученик"),(250,"Практик"),(500,"Разработчик"),(900,"Профи"),(1500,"Мастер кода"),(2500,"Легенда")]
BADGES=[("first","Первый шаг","Заверши 1 урок",1),("five","Вошёл во вкус","Заверши 5 уроков",5),("ten","Уверенный старт","Заверши 10 уроков",10),("25","Упорство","Заверши 25 уроков",25),("half","Половина пути","Заверши 54 урока",54),("all","Курс пройден","Заверши 108 уроков",108)]

def menu():
    return ReplyKeyboardMarkup(keyboard=[
      [KeyboardButton(text="📚 Уроки"),KeyboardButton(text="🧪 Практика")],
      [KeyboardButton(text="🔁 Повторение"),KeyboardButton(text="📅 Задание дня")],
      [KeyboardButton(text="🏆 Достижения"),KeyboardButton(text="📊 Прогресс")],
      [KeyboardButton(text="❓ Помощь"),KeyboardButton(text="⭐ О боте")]],resize_keyboard=True)

def lesson_kb(i):
    rows=[[InlineKeyboardButton(text="🧪 Практическое задание",callback_data=f"task:{i}")],
          [InlineKeyboardButton(text="✅ Отметить изученным",callback_data=f"done:{i}")]]
    if i>0: rows.append([InlineKeyboardButton(text="⬅️ Предыдущий",callback_data=f"lesson:{i-1}")])
    if i<len(LESSONS)-1: rows.append([InlineKeyboardButton(text="Следующий ➡️",callback_data=f"lesson:{i+1}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def list_kb(page=0):
    start=page*10
    rows=[[InlineKeyboardButton(text=f"{i+1}. {LESSONS[i]['title']}",callback_data=f"lesson:{i}")]
          for i in range(start,min(start+10,len(LESSONS)))]
    nav=[]
    if page: nav.append(InlineKeyboardButton(text="⬅️",callback_data=f"page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/11",callback_data="noop"))
    if start+10<len(LESSONS): nav.append(InlineKeyboardButton(text="➡️",callback_data=f"page:{page+1}"))
    rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def init_db():
    async with aiosqlite.connect(DB) as d:
        await d.execute("CREATE TABLE IF NOT EXISTS users(uid INTEGER PRIMARY KEY,name TEXT,xp INTEGER DEFAULT 0,streak INTEGER DEFAULT 0,last_daily TEXT)")
        await d.execute("CREATE TABLE IF NOT EXISTS progress(uid INTEGER,lesson INTEGER,review_due TEXT,stage INTEGER DEFAULT 0,PRIMARY KEY(uid,lesson))")
        await d.execute("CREATE TABLE IF NOT EXISTS stats(uid INTEGER PRIMARY KEY,correct INTEGER DEFAULT 0,total INTEGER DEFAULT 0,daily_done INTEGER DEFAULT 0)")
        await d.execute("CREATE TABLE IF NOT EXISTS badges(uid INTEGER,code TEXT,PRIMARY KEY(uid,code))")
        await d.execute("CREATE TABLE IF NOT EXISTS pending(uid INTEGER PRIMARY KEY,kind TEXT,item INTEGER)")
        await d.execute("CREATE TABLE IF NOT EXISTS daily(uid INTEGER,day TEXT,item INTEGER,done INTEGER DEFAULT 0,PRIMARY KEY(uid,day))")
        await d.commit()

async def ensure(uid,name=""):
    async with aiosqlite.connect(DB) as d:
        await d.execute("INSERT OR IGNORE INTO users(uid,name) VALUES(?,?)",(uid,name or ""))
        await d.execute("INSERT OR IGNORE INTO stats(uid) VALUES(?)",(uid,))
        await d.commit()

async def done_ids(uid):
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT lesson FROM progress WHERE uid=?",(uid,))
        return {r[0] for r in await c.fetchall()}

async def user_stats(uid):
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT xp,streak,last_daily FROM users WHERE uid=?",(uid,)); user=await c.fetchone()
        c=await d.execute("SELECT correct,total,daily_done FROM stats WHERE uid=?",(uid,)); stats=await c.fetchone()
    return user or (0,0,None), stats or (0,0,0)

async def mark_done(uid,i):
    intervals=[1,3,7,14,30]
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT stage FROM progress WHERE uid=? AND lesson=?",(uid,i)); row=await c.fetchone()
        if row is None:
            await d.execute("INSERT INTO progress(uid,lesson,review_due,stage) VALUES(?,?,?,0)",(uid,i,(date.today()+timedelta(days=1)).isoformat()))
            await d.execute("UPDATE users SET xp=xp+20 WHERE uid=?",(uid,)); fresh=True
        else:
            stage=min(row[0]+1,len(intervals)-1)
            due=(date.today()+timedelta(days=intervals[stage])).isoformat()
            await d.execute("UPDATE progress SET stage=?,review_due=? WHERE uid=? AND lesson=?",(stage,due,uid,i)); fresh=False
        await d.commit()
    return fresh

async def pending_set(uid,kind,item):
    async with aiosqlite.connect(DB) as d:
        await d.execute("INSERT INTO pending(uid,kind,item) VALUES(?,?,?) ON CONFLICT(uid) DO UPDATE SET kind=excluded.kind,item=excluded.item",(uid,kind,item)); await d.commit()

async def pending_take(uid):
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT kind,item FROM pending WHERE uid=?",(uid,)); r=await c.fetchone()
        if r: await d.execute("DELETE FROM pending WHERE uid=?",(uid,)); await d.commit()
        return r

def norm(s):
    return "\n".join(x.rstrip() for x in s.strip().replace("\r","").split("\n") if x.strip())

async def achievements(uid):
    completed=len(await done_ids(uid))
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT code FROM badges WHERE uid=?",(uid,)); have={x[0] for x in await c.fetchall()}
        new=[]
        for code,title,desc,goal in BADGES:
            if completed>=goal and code not in have:
                await d.execute("INSERT OR IGNORE INTO badges(uid,code) VALUES(?,?)",(uid,code)); new.append(title)
        await d.commit()
    return new

async def show_lesson(msg,uid,i):
    l=LESSONS[i]; completed=await done_ids(uid)
    status="✅ Изучен" if i in completed else "📝 Не завершён"
    await msg.answer(f"<b>Урок {i+1}/{len(LESSONS)} · {html.escape(l['title'])}</b>\n<i>{html.escape(l['module'])}</i>\n\n{l['body']}\n\n<b>Пример кода:</b>\n<pre>{html.escape(l['example'])}</pre>\n<b>Задание:</b> {html.escape(l['task'])}\n\n{status} · +20 XP за первое завершение",reply_markup=lesson_kb(i))

async def set_daily(msg,uid):
    today=date.today().isoformat()
    task=int(hashlib.sha256(today.encode()).hexdigest()[:8],16)%len(LESSONS)
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT item,done FROM daily WHERE uid=? AND day=?",(uid,today)); r=await c.fetchone()
        if not r:
            await d.execute("INSERT INTO daily(uid,day,item,done) VALUES(?,?,?,0)",(uid,today,task)); await d.commit(); r=(task,0)
    task,done=r
    if done:
        await msg.answer("📅 Сегодняшнее задание уже выполнено. Возвращайся завтра 💜"); return
    await pending_set(uid,"daily",task)
    l=LESSONS[task]
    await msg.answer(f"📅 <b>Задание дня</b>\n{html.escape(l['module'])} · {html.escape(l['title'])}\n\n{html.escape(l['task'])}\n\nОтправь решение кодом. Награда: +30 XP.")

@dp.message(CommandStart())
async def start(m):
    await ensure(m.from_user.id,m.from_user.first_name)
    text=("🚀 <b>Добро пожаловать в Hestle External!</b>\n\n"
          "Твой учебный бот по программированию с нуля.\n\n"
          "📚 108 уроков в 12 разделах\n🧪 Практика с проверкой решений\n🏆 Опыт, уровни и достижения\n📅 Ежедневные задания\n🔁 Повторение тем по расписанию\n\n"
          "<b>Учись. Практикуйся. Создавай.</b> 💜")
    if IMG.exists(): await m.answer_photo(FSInputFile(IMG),caption=text,reply_markup=menu())
    else: await m.answer(text+"\n⚠️ Start.jpg не найден рядом с bot.py.",reply_markup=menu())

@dp.message(Command("lessons"))
@dp.message(F.text=="📚 Уроки")
async def lessons(m):
    await ensure(m.from_user.id)
    done=await done_ids(m.from_user.id)
    await m.answer(f"📚 <b>Программа обучения</b>\n{len(MODULES)} разделов · {len(LESSONS)} уроков\nПройдено: {len(done)}/{len(LESSONS)}\n\nВыбери урок:",reply_markup=list_kb())

@dp.callback_query(F.data.startswith("page:"))
async def page(c):
    await c.message.edit_reply_markup(reply_markup=list_kb(int(c.data.split(":")[1]))); await c.answer()

@dp.callback_query(F.data=="noop")
async def noop(c): await c.answer()

@dp.callback_query(F.data.startswith("lesson:"))
async def lesson(c):
    i=int(c.data.split(":")[1])
    if 0<=i<len(LESSONS): await show_lesson(c.message,c.from_user.id,i)
    await c.answer()

@dp.callback_query(F.data.startswith("task:"))
async def task(c):
    i=int(c.data.split(":")[1]); await pending_set(c.from_user.id,"lesson",i)
    await c.message.answer(f"🧪 <b>Практика · {html.escape(LESSONS[i]['title'])}</b>\n\n{html.escape(LESSONS[i]['task'])}\n\nОтправь код одним сообщением. Подсказка: /hint")
    await c.answer()

@dp.callback_query(F.data.startswith("done:"))
async def done(c):
    i=int(c.data.split(":")[1]); fresh=await mark_done(c.from_user.id,i)
    await c.message.answer("✅ Урок завершён! +20 XP." if fresh else "🔁 Повторение отмечено. Следующая проверка запланирована.")
    awards=await achievements(c.from_user.id)
    if awards: await c.message.answer("🏆 <b>Новое достижение!</b>\n" + "\n".join("• "+html.escape(x) for x in awards))
    await c.answer("Готово")

@dp.message(Command("hint"))
async def hint(m):
    p=await pending_take(m.from_user.id)
    if not p: await m.answer("Сначала открой практическое задание."); return
    await pending_set(m.from_user.id,*p)
    await m.answer("💡 Используй print() и заключи текст в кавычки. Проверь скобки и написание команды.")

@dp.message(Command("practice"))
@dp.message(F.text=="🧪 Практика")
async def practice(m):
    await ensure(m.from_user.id)
    qid=(date.today().toordinal()+m.from_user.id)%len(PRACTICE)
    q,opts,correct,ex=PRACTICE[qid]
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=o,callback_data=f"quiz:{qid}:{i}")] for i,o in enumerate(opts)])
    await m.answer("🧪 <b>Вопрос дня</b>\n\n"+html.escape(q),reply_markup=kb)

@dp.callback_query(F.data.startswith("quiz:"))
async def quiz(c):
    _,qi,ci=c.data.split(":"); q,opts,correct,ex=PRACTICE[int(qi)]; ok=opts[int(ci)]==correct
    async with aiosqlite.connect(DB) as d:
        await d.execute("UPDATE stats SET total=total+1,correct=correct+? WHERE uid=?",(int(ok),c.from_user.id))
        if ok: await d.execute("UPDATE users SET xp=xp+10 WHERE uid=?",(c.from_user.id,))
        await d.commit()
    await c.message.edit_text(("✅ <b>Верно! +10 XP</b>" if ok else f"❌ <b>Правильный ответ:</b> {html.escape(correct)}")+f"\n\n💡 {html.escape(ex)}")
    await c.answer()

@dp.message(Command("daily"))
@dp.message(F.text=="📅 Задание дня")
async def daily(m):
    await ensure(m.from_user.id); await set_daily(m,m.from_user.id)

@dp.message(Command("repeat"))
@dp.message(F.text=="🔁 Повторение")
async def repeat(m):
    today=date.today().isoformat()
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT lesson FROM progress WHERE uid=? AND review_due<=? ORDER BY review_due LIMIT 10",(m.from_user.id,today)); rows=await c.fetchall()
    if not rows: await m.answer("🔁 Пока нет тем для повторения. После первого завершения урок появится здесь на следующий день."); return
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔁 "+LESSONS[r[0]]["title"],callback_data=f"lesson:{r[0]}")] for r in rows])
    await m.answer(f"🔁 <b>Пора повторить: {len(rows)} тем</b>",reply_markup=kb)

@dp.message(Command("progress"))
@dp.message(F.text=="📊 Прогресс")
async def progress(m):
    await ensure(m.from_user.id); completed=len(await done_ids(m.from_user.id)); (xp,streak,last),(correct,total,daily_done)=await user_stats(m.from_user.id)
    level=LEVELS[0]; nxt=None
    for n,x in enumerate(LEVELS):
        if xp>=x[0]: level=x; nxt=LEVELS[n+1] if n+1<len(LEVELS) else None
    pct=round(completed/len(LESSONS)*100); bar="🟪"*(pct//10)+"⬛"*(10-pct//10)
    extra=f"\nДо уровня «{nxt[1]}»: {nxt[0]-xp} XP" if nxt else "\nМаксимальный уровень!"
    await m.answer(f"📊 <b>Твой прогресс</b>\n\n{bar} <b>{pct}% курса</b>\nУроки: {completed}/{len(LESSONS)}\nОпыт: <b>{xp} XP</b>\nУровень: <b>{html.escape(level[1])}</b>{extra}\nТесты: {correct}/{total}\nЕжедневных заданий: {daily_done}\nСерия дней: {streak}")

@dp.message(Command("achievements"))
@dp.message(F.text=="🏆 Достижения")
async def badges(m):
    completed=len(await done_ids(m.from_user.id))
    async with aiosqlite.connect(DB) as d:
        c=await d.execute("SELECT code FROM badges WHERE uid=?",(m.from_user.id,)); earned={r[0] for r in await c.fetchall()}
    lines=[("🏅" if code in earned else "🔒")+f" <b>{title}</b> — {desc}" for code,title,desc,goal in BADGES]
    await m.answer("🏆 <b>Достижения</b>\n\n"+"\n".join(lines))

@dp.message(Command("help"))
@dp.message(F.text=="❓ Помощь")
async def help(m):
    await m.answer("❓ <b>Разделы Hestle External</b>\n\n📚 Уроки — 108 тем по Python.\n🧪 Практика — тесты с объяснениями.\n🔁 Повторение — темы по расписанию 1, 3, 7, 14 и 30 дней.\n📅 Задание дня — ежедневная задача.\n🏆 Достижения — награды за обучение.\n📊 Прогресс — XP, уровень и статистика.\n\nКоманды: /start /lessons /practice /repeat /daily /progress /achievements /hint /help")

@dp.message(Command("about"))
@dp.message(F.text=="⭐ О боте")
async def about(m):
    await m.answer("⭐ <b>Hestle External</b>\nУчебный Telegram-бот для самостоятельного изучения Python с нуля. 12 разделов, 108 уроков, практика, повторение, ежедневные задания, XP, уровни и достижения. Без ИИ и без обязательного администратора.")

@dp.message()
async def catch(m):
    if not m.text: await m.answer("Отправь код текстом."); return
    p=await pending_take(m.from_user.id)
    if not p: await m.answer("Выбери раздел в меню или нажми /help.",reply_markup=menu()); return
    kind,i=p; expected=LESSONS[i]["expected"]
    if norm(m.text)==norm(expected):
        if kind=="daily":
            today=date.today().isoformat()
            async with aiosqlite.connect(DB) as d:
                c=await d.execute("SELECT done FROM daily WHERE uid=? AND day=?",(m.from_user.id,today)); row=await c.fetchone()
                if row and not row[0]:
                    await d.execute("UPDATE daily SET done=1 WHERE uid=? AND day=?",(m.from_user.id,today))
                    await d.execute("UPDATE stats SET daily_done=daily_done+1 WHERE uid=?",(m.from_user.id,))
                    c=await d.execute("SELECT last_daily,streak FROM users WHERE uid=?",(m.from_user.id,)); last,streak=await c.fetchone()
                    yesterday=(date.today()-timedelta(days=1)).isoformat()
                    streak=streak+1 if last==yesterday else (streak if last==today else 1)
                    await d.execute("UPDATE users SET xp=xp+30,streak=?,last_daily=? WHERE uid=?",(streak,today,m.from_user.id))
                    await d.commit()
            await m.answer("🎉 <b>Задание дня выполнено! +30 XP</b>")
        else:
            fresh=await mark_done(m.from_user.id,i)
            await m.answer("✅ <b>Код принят!</b> "+("+20 XP за первое прохождение." if fresh else "Урок уже был пройден."))
        new=await achievements(m.from_user.id)
        if new: await m.answer("🏆 <b>Новое достижение!</b>\n"+"\n".join("• "+html.escape(x) for x in new))
    else:
        await pending_set(m.from_user.id,kind,i)
        await m.answer("🟨 <b>Пока не совпало с эталоном.</b> Проверь кавычки, скобки и написание. Можешь попросить подсказку: /hint\n\nПроверка сравнивает код с образцом и не запускает присланные программы.")

async def main():
    if not TOKEN or TOKEN in {"ВСТАВЬ_СЮДА_ТОКЕН", "YOUR_BOT_TOKEN_HERE"}:
        raise RuntimeError("Не задан BOT_TOKEN. Открой .env рядом с bot.py и вставь токен от @BotFather.")
    if ":" not in TOKEN or len(TOKEN) < 30:
        raise RuntimeError("BOT_TOKEN выглядит некорректно. Проверь токен от @BotFather.")
    await init_db()
    bot=Bot(TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logging.info("Hestle External ready: %s lessons",len(LESSONS))
    await dp.start_polling(bot)

if __name__=="__main__": asyncio.run(main())
