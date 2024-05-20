import telebot
from telebot.types import Message
from PyPDF2 import PdfWriter, PdfReader, PageObject
from io import BytesIO
from PIL import Image
import redis

bot = telebot.TeleBot('7066817221:AAEohmbOMljanOQ9U35Pj4Vkl0b08S-eb5g')

r = redis.Redis(decode_responses=True)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    text = "Привет, отправь мне фото, а затем команду /done, и я склею их в pdf файл. /clear чтобы очистить отправленные фото"
    bot.send_message(message.chat.id, text)

@bot.message_handler(content_types=['photo'])
def photo_conversion(message : Message):    
    photo = message.photo[-1]

    key = f"{message.from_user.id}_files"
    r.lpush(key, photo.file_id)

@bot.message_handler(commands=['done'])
def send_pdf(message):
    output_pdf = PdfWriter()

    key = f"{message.from_user.id}_files"
    files_ids = r.lrange(key, 0, -1)

    if len(files_ids) == 0:
        bot.send_message(message.chat.id, "Сначала отправь фото")
        return

    bot.send_message(message.chat.id, "Начинаю формировать твой пдф.")

    for id in reversed(files_ids):
        file = bot.get_file(id)
        file_bytes = bot.download_file(file.file_path)
        
        img = Image.open(BytesIO(file_bytes))
        img_temp = BytesIO()
        img.save(img_temp, format="PDF")

        pdf_image = PdfReader(img_temp)
        
        output_pdf.add_page(pdf_image.pages[0])
    

    virtual_file = BytesIO()
    output_pdf.write(virtual_file)
    virtual_file.seek(0)

    bot.send_document(message.chat.id, virtual_file.getvalue(), visible_file_name="результат.pdf", caption="Ваш pdf файл")

    r.delete(key)


@bot.message_handler(commands=["clear"])
def clear_images(message):
    key = f"{message.from_user.id}_files"
    r.delete(key)

    bot.send_message(message.chat.id, "Список изображений очищен")


bot.polling(none_stop=True, interval=0)