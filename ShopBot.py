import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile


# Установка уровня логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot_token = "Ваш токен телеграмм бота"
chat_id= Ваш id телеграмм
bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Определение состояний
class FeedbackStates(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_coupon = State()
    waiting_for_phone = State()

# Обработчик команды "/start"
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ["🌟 Бонус за отзыв", "💬 Задать вопрос", "🎁 Акционные товары", "🌐 Наши ресурсы"]
    keyboard_markup.add(*(types.KeyboardButton(text) for text in buttons))

    text = "👋 Здравствуйте! Спасибо, что обратились в службу поддержки.\n\n" \
           "Выберите, пожалуйста, один из вариантов.\n\n" \
           "Если у вас пропало меню выбора ответа, нажмите справа на значок клавиатуры рядом со значком микрофона."

    await message.answer(text, reply_markup=keyboard_markup)

# Обработчик кнопки "🌟 Бонус за отзыв"
@dp.message_handler(lambda message: message.text == "🌟 Бонус за отзыв")
async def review_bonus_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "Ортопедические подушки", 
        "Женская одежда", 
        "🔙 Вернуться в главное меню"
    ]
    keyboard_markup.add(*(types.KeyboardButton(text) for text in buttons))

    text = "🌟 Выберите категорию товара, за который вы хотите получить бонус за отзыв."

    await message.answer(text, reply_markup=keyboard_markup)

# Обработка нажатия на кнопку "Я оставил отзыв"
@dp.message_handler(lambda message: message.text == "Я оставил(-а) отзыв")
async def feedback(message: types.Message):
    # Отправка сообщения с инструкцией и просьбой о скриншоте
    await message.answer_photo(
        photo="https://postimg.cc/xXLFr503",
        caption="📸 Сделайте скриншот оставленного отзыва и отправьте его сюда (Отправляйте, пожалуйста, только скриншот, без текста)."
    )

    # Переход в состояние ожидания скриншота
    await FeedbackStates.waiting_for_screenshot.set()


# Обработка получения скриншота от пользователя
@dp.message_handler(state=FeedbackStates.waiting_for_screenshot, content_types=types.ContentType.PHOTO)
async def process_screenshot(message: types.Message, state: FSMContext):
    # Сохранение полученного фото
    photo_id = message.photo[-1].file_id

    # Отправка сообщения с просьбой о фото купона
    await bot.send_message(
        chat_id=message.chat.id,
        text="📸 Пришлите, пожалуйста, фото Вашего купона сюда (Отправляйте, пожалуйста, только фотографию, без текста)."
    )

    # Сохранение идентификатора фото в состоянии
    await state.update_data(screenshot=photo_id)

    # Переход в состояние ожидания фото купона
    await FeedbackStates.waiting_for_coupon.set()


# Обработка получения фото купона от пользователя
@dp.message_handler(state=FeedbackStates.waiting_for_coupon, content_types=types.ContentType.PHOTO)
async def process_coupon(message: types.Message, state: FSMContext):
    # Получение данных из состояния
    data = await state.get_data()
    screenshot_id = data.get('screenshot')
    coupon_id = message.photo[-1].file_id

    # Получение фото из сохраненных идентификаторов
    screenshot = await bot.download_file_by_id(screenshot_id)
    coupon = await bot.download_file_by_id(coupon_id)

    # Отправка сообщения с просьбой о номере телефона
    await bot.send_message(
        chat_id=message.chat.id,
        text="📞 Последний шаг. Напишите Ваш номер телефона, мы пополним его на сумму купона.\n"
             "Формат номера +7 ХХХ ХХХ ХХ ХХ"
    )

    # Сохранение идентификатора фото купона в состоянии
    await state.update_data(coupon=coupon_id)

    # Переход в состояние ожидания номера телефона
    await FeedbackStates.waiting_for_phone.set()


# Обработка получения номера телефона от пользователя
@dp.message_handler(state=FeedbackStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    # Получение данных из состояния
    data = await state.get_data()
    screenshot_id = data.get('screenshot')
    coupon_id = data.get('coupon')

    # Отправка сообщения с информацией об отзыве и номером телефона
    await bot.send_message(
        chat_id,
        text=f"💌 Новый отзыв! \n\n От: {message.from_user.first_name} (@{message.from_user.username})\n\n"
             "📸 Скриншот отзыва:"
    )
    await bot.send_photo(chat_id, photo=screenshot_id)

    await bot.send_message(
        chat_id,
        text="\n🛒 Фото купона:"
    )
    await bot.send_photo(chat_id, photo=coupon_id)

    await bot.send_message(
        chat_id,
        text=f"\n📞 Номер телефона: {message.text}"
    )

    # Стилизация и отправка ответного сообщения пользователю
    await message.reply("Спасибо за отзыв! Ваш номер телефона принят. 🙌")

    # Очистка состояния
    await state.finish()

# Обработчики кнопок категорий товаров
@dp.message_handler(lambda message: message.text in ["Ортопедические подушки", "Женская одежда"])
async def category_selected_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "Я оставил(-а) отзыв",
        "🔙 Вернуться в главное меню"
    ]
    keyboard_markup.add(*buttons)

    text = "Чтобы получить бонус, сделайте несколько простых действий:\n\n" \
           "1. Откройте приложение Wildberries на телефоне.\n" \
           "2. Нажмите на иконку профиля в нижнем правом углу.\n" \
           "3. Выберете категорию «Покупки».\n" \
           "4. Выберите товар, на котором хотите оставить отзыв.\n" \
           "5. Найдите строчку «Отзывы», находится обычно под описанием товара.\n" \
           "6. Нажмите кнопку «Оставить отзыв».\n" \
           "7. Поставьте товару 5 звезд.\n" \
           "8. Напишите текстовый комментарий."

    await message.answer(text, reply_markup=keyboard_markup)

# Обработчик кнопки "🔙 Вернуться в главное меню"
@dp.message_handler(lambda message: message.text == "🔙 Вернуться в главное меню")
async def return_to_main_menu_handler(message: types.Message):
    await start_command(message)

# Обработчик кнопки "🎁 Акционные товары"
@dp.message_handler(lambda message: message.text == "🎁 Акционные товары")
async def action_goods_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["🔙 Вернуться в главное меню"]
    keyboard_markup.add(*buttons)

    text = "Каталог товаров можно посмотреть на странице:\n" \
           "[Отдел заботы](ваша ссылка)\n" \
           "А так же большие скидки в нашем магазине :\n"\
           "[Wildberries](ваша ссылка)\n\n" \
           "🌟 Только сегодня скидка 10% на все товары! 🎉"

    await message.answer(text, reply_markup=keyboard_markup, parse_mode=types.ParseMode.MARKDOWN)

# Обработчик кнопки "🌐 Наши ресурсы"
@dp.message_handler(lambda message: message.text == "🌐 Наши ресурсы")
async def our_resources_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["🔙 Вернуться в главное меню"]
    keyboard_markup.add(*buttons)

    text = "Спасибо за интерес, проявленный к нашему бренду! 🙌\n\n" \
           "Приобретайте наши товары на WB:\n\n" \
           "🛒 Наш каталог это подушки Ортопедические подушки\n" \
           "[Ортопедические подушки](ваша ссылка)\n\n" \
           "👚 Одежда женская\n" \
           "[Одежда женская](ваша ссылка)\n\n" \
           "Всегда рады вам! 😊"

    await message.answer(text, reply_markup=keyboard_markup, parse_mode=types.ParseMode.MARKDOWN)

# Обработчик всех текстовых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def process_text_message(message: types.Message):
    text = message.text
    if text == "💬 Задать вопрос":
        await ask_question_handler(message)
    elif text == "🔙 Вернуться в главное меню":
        await return_to_main_menu_handler(message)
    else:
        await forward_to_owner(message)

# Обработчик кнопки "💬 Задать вопрос"
async def ask_question_handler(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["🔙 Вернуться в главное меню"]
    keyboard_markup.add(*buttons)

    text = "📝 Расскажите, какой у Вас вопрос и мы быстро поможем решить вашу проблему."

    await message.answer(text, reply_markup=keyboard_markup)
    
    

# Обработчик кнопки "🔙 Вернуться в главное меню"
async def return_to_main_menu_handler(message: types.Message):
    await start_command(message)
    await forward_to_owner(message)
# Пересылка сообщения владельцу бота
async def forward_to_owner(message: types.Message):
    forwarded_message = await bot.send_message(
        chat_id,
        text=f"📬 Новый вопрос:\n\n<b>{message.text}</b>\n\nОт: {message.from_user.first_name} (@{message.from_user.username})",
        parse_mode=types.ParseMode.HTML
    )

# Запуск бота
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)