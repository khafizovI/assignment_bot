import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from tortoise import Tortoise, run_async
from tortoise.fields import BigIntField, BooleanField, CharField, IntField, TextField
from tortoise.models import Model
from aiogram.dispatcher.filters import Text

# --- Configuration ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Bot and Dispatcher ---
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# --- Database Model ---
class Applicant(Model):
    id = IntField(pk=True)
    user_id = BigIntField(unique=True)
    username = CharField(max_length=255, null=True)
    full_name = CharField(max_length=255, null=True)
    language = CharField(max_length=3, default='en')
    age = IntField(null=True)
    gender = CharField(max_length=10, null=True)
    additional_benefits = TextField(null=True)
    quick_and_responsible = BooleanField(null=True)
    status = CharField(max_length=20, default="pending")

    def __str__(self):
        return f"Applicant {self.full_name} ({self.user_id})"


# --- FSM States ---
class ApplicationForm(StatesGroup):
    select_lang = State()
    main_menu = State()
    name = State()
    age = State()
    gender = State()
    additional_benefits = State()
    quick_and_responsible = State()


# --- Texts for multi-language support ---
texts = {
    'welcome': {
        'en': "🇬🇧 Welcome! Please select your language.",
        'ru': "🇷🇺 Добро пожаловать! Пожалуйста, выберите ваш язык.",
        'uz': "🇺🇿 Xush kelibsiz! Iltimos, tilingizni tanlang."
    },
    'select_language': {
        'en': "🇬🇧 Please select your language.",
        'ru': "🇷🇺 Пожалуйста, выберите ваш язык.",
        'uz': "🇺🇿 Iltimos, tilingizni tanlang."
    },
    'ask_name': {
        'en': "👤 What is your full name?",
        'ru': "👤 Как вас зовут (полное имя)?",
        'uz': "👤 To'liq ismingiz nima?"
    },
    'invalid_name': {
        'en': "❌ Invalid name. Please enter your full name.",
        'ru': "❌ Неверное имя. Пожалуйста, введите ваше полное имя.",
        'uz': "❌ Noto'g'ri ism. Iltimos, to'liq ismingizni kiriting."
    },
    'ask_age': {
        'en': "🎂 How old are you?",
        'ru': "🎂 Сколько вам лет?",
        'uz': "🎂 Yoshingiz nechada?"
    },
    'invalid_age': {
        'en': "❌ Invalid age. Please enter a number.",
        'ru': "❌ Неверный возраст. Пожалуйста, введите число.",
        'uz': "❌ Noto'g'ri yosh. Iltimos, raqam kiriting."
    },
    'ask_gender': {
        'en': "🚻 What is your gender?",
        'ru': "🚻 Ваш пол?",
        'uz': "🚻 Jinsingiz nima?"
    },
    'genders': {
        'en': ['👨 Male', '👩 Female'],
        'ru': ['👨 Мужской', '👩 Женский'],
        'uz': ['👨 Erkak', '👩 Ayol']
    },
    'invalid_gender': {
        'en': "❌ Invalid gender. Please select one of the options.",
        'ru': "❌ Неверный пол. Пожалуйста, выберите один из вариантов.",
        'uz': "❌ Noto'g'ri jins. Iltimos, variantlardan birini tanlang."
    },
    'ask_responsibility': {
        'en': "🏃‍♂️ Are you quick and responsible?",
        'ru': "🏃‍♂️ Вы быстрый и ответственный?",
        'uz': "Siz tez va mas'uliyatlimisiz?"
    },
    'yes_no': {
        'en': ['✅ Yes', '❌ No'],
        'ru': ['✅ Да', '❌ Нет'],
        'uz': ['✅ Ha', '❌ Yo\'q']
    },
    'invalid_responsibility': {
        'en': "❌ Invalid answer. Please select one of the options.",
        'ru': "❌ Неверный ответ. Пожалуйста, выберите один из вариантов.",
        'uz': "❌ Noto'g'ri javob. Iltimos, variantlardan birini tanlang."
    },
    'additional_benefits': {
        'en': "Do you have any other additional benefits? Please describe them.",
        'ru': "У вас есть какие-либо другие дополнительные льготы? Пожалуйста, опишите их.",
        'uz': "Boshqa qo'shimcha imtiyozlaringiz bormi? Iltimos, ularni tasvirlab bering."
    },
    'yes': {
        'en': "Yes",
        'ru': "Да",
        'uz': "Ha"
    },
    'no': {
        'en': "No",
        'ru': "Нет",
        'uz': "Yo'q"
    },
    'application_submitted': {
        'en': "✅ Your application has been submitted successfully! We will contact you soon.",
        'ru': "✅ Ваша заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.",
        'uz': "✅ Arizangiz muvaffaqiyatli yuborildi! Tez orada siz bilan bog'lanamiz."
    },
    'requirements_not_met': {
        'en': "❌ Unfortunately, you do not meet the requirements for this position.",
        'ru': "❌ К сожалению, вы не соответствуете требованиям для этой должности.",
        'uz': "❌ Afsuski, siz bu lavozim uchun talablarga javob bermaysiz."
    },
    'admin_notification': {
        'en': (
            f"📝 New Job Application:\n\n"
            f"👤 Name: {{name}}\n"
            f"🎂 Age: {{age}}\n"
            f"🚻 Gender: {{gender}}\n"
            f"🏃‍♂️ Quick & Responsible: {{responsible}}"
        ),
        'ru': (
            f"📝 Новая заявка на работу:\n\n"
            f"👤 Имя: {{name}}\n"
            f"🎂 Возраст: {{age}}\n"
            f"🚻 Пол: {{gender}}\n"
            f"🏃‍♂️ Быстрый и ответственный: {{responsible}}"
        ),
        'uz': (
            f"📝 Yangi ish arizasi:\n\n"
            f"👤 Ism: {{name}}\n"
            f"🎂 Yosh: {{age}}\n"
            f"🚻 Jins: {{gender}}\n"
            f"🏃‍♂️ Tezkor va mas'uliyatli: {{responsible}}"
        )
    },
    'admin_notification_rejected': {
        'en': (
            f"🚫 New Job Application (Rejected):\n\n"
            f"👤 Name: {{name}}\n"
            f"🎂 Age: {{age}}\n"
            f"🚻 Gender: {{gender}}\n"
            f"🏃‍♂️ Quick & Responsible: {{responsible}}"
        ),
        'ru': (
            f"🚫 Новая заявка на работу (Отклонена):\n\n"
            f"👤 Имя: {{name}}\n"
            f"🎂 Возраст: {{age}}\n"
            f"🚻 Пол: {{gender}}\n"
            f"🏃‍♂️ Быстрый и ответственный: {{responsible}}"
        ),
        'uz': (
            f"🚫 Yangi ish arizasi (Rad etilgan):\n\n"
            f"👤 Ism: {{name}}\n"
            f"🎂 Yosh: {{age}}\n"
            f"🚻 Jins: {{gender}}\n"
            f"🏃‍♂️ Tezkor va mas'uliyatli: {{responsible}}"
        )
    },
    'accepted_message': {
        'en': "✅ Congratulations! Your application has been accepted.",
        'ru': "✅ Поздравляем! Ваша заявка принята.",
        'uz': "✅ Tabriklaymiz! Sizning arizangiz qabul qilindi."
    },
    'rejected_message': {
        'en': "❌ We regret to inform you that your application has been rejected.",
        'ru': "❌ С сожалением сообщаем, что ваша заявка отклонена.",
        'uz': "❌ Afsuski, sizning arizangiz rad etildi."
    },
    'main_menu_prompt': {
        'en': '🏠 Please choose an option:',
        'ru': '🏠 Пожалуйста, выберите опцию:',
        'uz': '🏠 Iltimos, variantni tanlang:',
    },
    'main_menu_buttons': {
        'en': ['📝 Apply for a job', '📞 Contact us', '🌐 Language'],
        'ru': ['📝 Подать заявку', '📞 Связаться с нами', '🌐 Язык'],
        'uz': ['📝 Ishga ariza berish', '📞 Biz bilan bog\'lanish', '🌐 Til'],
    },
    'contact_us_message': {
        'en': '📞 You can contact us at: +998901234567',
        'ru': '📞 Вы можете связаться с нами по номеру: +998901234567',
        'uz': '📞 Biz bilan ushbu raqam orqali bog\'lanishingiz mumkin: +998901234567',
    },
    'ask_name': {
        'en': "👤 What is your full name?",
        'ru': "👤 Как вас зовут (полное имя)?",
        'uz': "👤 To'liq ismingiz nima?"
    }
}


# --- Keyboards ---
def get_language_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("English"), types.KeyboardButton("Русский"), types.KeyboardButton("O'zbekcha"))
    return keyboard

def get_main_menu_keyboard(lang='en'):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = texts['main_menu_buttons'][lang]
    keyboard.row(buttons[0])
    keyboard.row(buttons[1], buttons[2])
    return keyboard

def get_gender_keyboard(lang='en'):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    gender_buttons = texts['genders'][lang]
    keyboard.add(types.KeyboardButton(gender_buttons[0]), types.KeyboardButton(gender_buttons[1]))
    return keyboard

def get_yes_no_keyboard(lang='en'):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    yes_no_buttons = texts['yes_no'][lang]
    keyboard.add(types.KeyboardButton(yes_no_buttons[0]), types.KeyboardButton(yes_no_buttons[1]))
    return keyboard

def get_admin_keyboard(user_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Accept", callback_data=f"admin_accept_{user_id}"),
        InlineKeyboardButton("Reject", callback_data=f"admin_reject_{user_id}")
    )
    return keyboard


# --- Bot Handlers ---
@dp.message_handler(commands=['start'], state='*')
async def start_handler(message: types.Message):
    applicant, created = await Applicant.get_or_create(user_id=message.from_user.id)

    # Update username if it has changed or was not set
    if applicant.username != message.from_user.username:
        applicant.username = message.from_user.username
        await applicant.save()

    if not created and applicant.language:
        await ApplicationForm.main_menu.set()
        await message.answer(texts['main_menu_prompt'][applicant.language],
                             reply_markup=get_main_menu_keyboard(applicant.language))
    else:
        await ApplicationForm.select_lang.set()
        await message.answer(texts['select_language']['en'], reply_markup=get_language_keyboard())


@dp.message_handler(state=ApplicationForm.select_lang)
async def process_language_select(message: types.Message, state: FSMContext):
    lang = 'en'  # Default language
    if message.text == "🇷🇺 Русский":
        lang = 'ru'
    elif message.text == "🇺🇿 O'zbekcha":
        lang = 'uz'

    # Save language to database and state
    applicant, created = await Applicant.get_or_create(
        user_id=message.from_user.id,
        defaults={'language': lang, 'username': message.from_user.username}
    )
    if not created:
        applicant.language = lang
        await applicant.save()

    await state.update_data(language=lang, username=message.from_user.username)
    await ApplicationForm.main_menu.set()
    await message.answer(texts['main_menu_prompt'][lang], reply_markup=get_main_menu_keyboard(lang))


@dp.message_handler(state=ApplicationForm.main_menu)
async def process_main_menu(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        lang = data.get('language', 'en')

    buttons = texts['main_menu_buttons'][lang]
    if message.text == buttons[0]:  # Apply for a job
        await ApplicationForm.name.set()
        await message.answer(texts['ask_name'][lang], reply_markup=types.ReplyKeyboardRemove())
    elif message.text == buttons[1]:  # Contact us
        await message.answer(texts['contact_us_message'][lang])
    elif message.text == buttons[2]:  # Change language
        await ApplicationForm.select_lang.set()
        await message.answer(texts['select_language'][lang], reply_markup=get_language_keyboard())
    else:
        await message.answer(texts['main_menu_prompt'][lang], reply_markup=get_main_menu_keyboard(lang))


@dp.message_handler(state=ApplicationForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        lang = data.get('language', 'en')
    await ApplicationForm.next()
    await message.answer(texts['ask_age'][lang])


@dp.message_handler(lambda message: not message.text.isdigit(), state=ApplicationForm.age)
async def process_age_invalid(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        lang = data.get('language', 'en')
    return await message.answer(texts['invalid_age'][lang])


@dp.message_handler(lambda message: message.text.isdigit(), state=ApplicationForm.age)
async def process_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = int(message.text)
        lang = data.get('language', 'en')
    await ApplicationForm.next()
    await message.answer(texts['ask_gender'][lang], reply_markup=get_gender_keyboard(lang))


@dp.message_handler(state=ApplicationForm.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text
        lang = data.get('language', 'en')

    applicant, created = await Applicant.get_or_create(user_id=message.from_user.id)
    applicant.gender = message.text
    await applicant.save()

    await ApplicationForm.additional_benefits.set()
    await message.reply(texts['additional_benefits'][lang], reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=ApplicationForm.additional_benefits)
async def process_additional_benefits(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        lang = data.get('language', 'en')
        data['additional_benefits'] = message.text

    applicant, created = await Applicant.get_or_create(user_id=message.from_user.id)
    applicant.additional_benefits = message.text
    await applicant.save()

    await ApplicationForm.quick_and_responsible.set()
    await message.reply(texts['ask_responsibility'][lang], reply_markup=get_yes_no_keyboard(lang))


@dp.message_handler(lambda message: message.text in texts['yes_no']['en'] + texts['yes_no']['ru'] + texts['yes_no']['uz'],
                    state=ApplicationForm.quick_and_responsible)
async def process_responsibility(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        lang = data.get('language', 'en')
        is_quick_and_responsible = message.text == texts['yes_no'][lang][0]
        data['quick_and_responsible'] = is_quick_and_responsible

        # Retrieve the applicant to get the username
        applicant, _ = await Applicant.get_or_create(user_id=message.from_user.id)

        # Save applicant data
        await Applicant.filter(user_id=message.from_user.id).update(
            full_name=data['name'],
            age=data['age'],
            gender=data['gender'],
            additional_benefits=data['additional_benefits'],
            quick_and_responsible=is_quick_and_responsible,
            status='pending'  # All applications are pending admin review
        )

        # Notify admin
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            try:
                applicant_info = (
                    f"New application:\n"
                    f"Username: @{applicant.username or applicant.username}\n"
                    f"Full Name: {applicant.full_name}\n"
                    f"Age: {applicant.age}\n"
                    f"Gender: {applicant.gender}\n"
                    f"Additional Benefits: {applicant.additional_benefits}\n"
                    f"Quick and Responsible: {'Yes' if applicant.quick_and_responsible else 'No'}"
                )
                await bot.send_message(admin_id, applicant_info, reply_markup=get_admin_keyboard(applicant.user_id))
            except Exception as e:
                logging.error(f"Failed to send message to admin: {e}")

        # Thank user and finish
        await message.reply(texts['application_submitted'][lang], reply_markup=types.ReplyKeyboardRemove())
        await state.finish()


# --- Admin Callback Handlers ---
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('admin:'))
async def process_admin_callback(callback_query: types.CallbackQuery):
    action, user_id_str = callback_query.data.split(':', 2)[1:]
    user_id = int(user_id_str)

    applicant = await Applicant.get(user_id=user_id)
    if not applicant:
        await callback_query.answer("Applicant not found.")
        return

    lang = applicant.language

    if action == "accept":
        applicant.status = "approved"
        await applicant.save()
        await bot.send_message(user_id, texts['accepted_message'][lang])
        await callback_query.answer("Application accepted.")
    elif action == "reject":
        applicant.status = "rejected"
        await applicant.save()
        await bot.send_message(user_id, texts['rejected_message'][lang])
        await callback_query.answer("Applicant rejected.")

    # Return user to the main menu
    state = dp.current_state(user=user_id)
    await state.set_state(ApplicationForm.main_menu)
    await bot.send_message(user_id, texts['main_menu_prompt'][lang], reply_markup=get_main_menu_keyboard(lang))

    # Remove the inline keyboard from the admin message
    await callback_query.message.edit_reply_markup(reply_markup=None)


# --- Database and Bot Initialization ---
async def init_db():
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['__main__']}
    )
    await Tortoise.generate_schemas()


async def on_startup(dp):
    await init_db()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
