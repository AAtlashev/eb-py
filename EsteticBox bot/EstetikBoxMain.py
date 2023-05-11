import asyncio
import logging
import pendulum
import random
import ast
import psycopg2
import json 
import gspread

from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, PAYMENTS_PROVIDER_TOKEN, IMAGE_URL, WEB_APP, PHOTO_MES, NUMBER_OF_TIPS, GO_TABLE_KEY, INFO_PHOTO_MES
from aiogram.types import ReplyKeyboardMarkup , KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from messages import MESSAGES
from keyboards import keyboard1 , keyboard2, keyboard3 , keyboard4
from utils import TestStates

connection = psycopg2.connect(user= "postgres",password = "123", host = "localhost",database = "esteticbox")

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO)
            
loop = asyncio.get_event_loop()
bot = Bot(BOT_TOKEN, parse_mode=types.ParseMode.MARKDOWN)
dp = Dispatcher(bot, loop=loop)

gc = gspread.service_account(filename='estetic-bot-3d83063cbdc3.json')
sh = gc.open("estetic-box-bot")
worksheet = sh.sheet1

POST_SHIPPING_OPTION = types.ShippingOption(
    id='post_russia',
    title='Почта России'
).add(types.LabeledPrice('Доставка Почтой России', 6000))

SDEK_SHIPPING_OPTION = types.ShippingOption(
    id='sdek',
    title='СДЭК'
).add(types.LabeledPrice('Доставка СДЭК', 10000))

@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
   name = message.from_user.first_name
   await message.answer('Привет, ' + name + '!' +'\nМеня зовут Юлия Шишкина, и я твой проводник в мир красоты и здоровой кожи!' + '\nДля заказа Estetic box нажми кнопку ниже.', 
   reply_markup=ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton(text="Сделайте заказ", 
   web_app=WebAppInfo(url= WEB_APP))))
   await bot.send_photo(message.chat.id, photo= PHOTO_MES ,caption = MESSAGES['help'] ,parse_mode= types.ParseMode.HTML)
   
@dp.message_handler(commands= "121980")
async def process_terms_command(message: types.Message):
    await message.answer(MESSAGES['adm'],reply_markup= keyboard3)

@dp.message_handler(content_types = "web_app_data")
async def answer(webAppMes):
    webapp = webAppMes.web_app_data.data
    res_dict=ast.literal_eval(webapp) 
    dictes = dict(res_dict)
    text = ''
    textbd = ''
    a = json.dumps(dictes)
    cursor = connection.cursor()
    cursor.execute('SELECT userid FROM public.user where userid = '+ str(webAppMes.chat.id))
    Chek = cursor.fetchone()
    connection.commit()

    for key, value in dictes.items():
        text += (f'{key} - {value//100} RUB') + "\n"
        textbd += (f'{key}') + ", "

    cursor = connection.cursor()
    cursor.execute("INSERT INTO public.\"orders\"(id, userid, web_app_data, web_app_data_str) VALUES ((SELECT MAX(id) + 1 FROM public.\"orders\"),'" + str(webAppMes.chat.id) + "', '"+ a + "', '"+ textbd +"')")
    connection.commit()

    if Chek != None:
        summ = sum(dictes.values())
        summm = summ //100
        await bot.send_message(webAppMes.chat.id, "Прекрасный выбор! " + "\nПроверь свой заказ:" "\n\n" + text + "\nОбщая сумма заказа -  " + str(summm)+" RUB" + "\n\nЗаказ правильный?", reply_markup= keyboard2)
    else:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO public.\"user\"(userid, \"first_name\", \"last_name\", \"username\",\"date\") VALUES ('" + str(webAppMes.chat.id) + "', '"+ str(webAppMes.chat.first_name) +"','"+ str(webAppMes.chat.last_name) +"','"+ str(webAppMes.chat.username) +"','" + str(webAppMes.date) +"')")
        connection.commit()

        summ = sum(dictes.values())
        summm = summ //100
        await bot.send_message(webAppMes.chat.id, "Прекрасный выбор! " + "\nПроверь свой заказ:" "\n\n" + text + "\nОбщая сумма заказа -  " + str(summm)+" RUB" + "\n\nЗаказ правильный?", reply_markup= keyboard2)

@dp.callback_query_handler(lambda call: call.data == "yes")
async def yes(message):
    await bot.delete_message(message.from_user.id, message.message.message_id)
    return await info(message)

@dp.callback_query_handler(lambda call: call.data == "no")
async def no(call):
    await bot.delete_message(call.message.from_user.id, call.message.message_id)
    await bot.send_message(call.message.from_user.id,"Ничего страшного!" + "\nТолько без паники!" + "\nПросто нажмите ещё раз на кнопку ниже", reply_markup=ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton(text="Сделайте заказ", 
    web_app=WebAppInfo(url= WEB_APP))))
    cursor = connection.cursor()
    cursor.execute("DELETE FROM public.orders WHERE userid = "+ str(call.message.chat.id) +" and id = (SELECT MAX(id) FROM public.orders);")
    connection.commit()

@dp.callback_query_handler(lambda call: call.data == "des")
async def des(message):
    await bot.delete_message(message.from_user.id, message.message.message_id)
    return await pay2(message)

@dp.message_handler(state=TestStates.TEST_STATE_2)
async def info(message):
   await bot.send_photo(message.from_user.id, photo= INFO_PHOTO_MES ,caption = MESSAGES['info'] ,parse_mode= types.ParseMode.HTML, reply_markup = keyboard4)


@dp.message_handler(state=TestStates.TEST_STATE_1)
async def pay2(message):
    await bot.send_message(message.from_user.id, MESSAGES['pay'])
    tomorrow = pendulum.now('Europe/Moscow').format('HH:mm')
    random_id = ' '.join([str(random.randint(0, 999)).zfill(3) for _ in range(2)])
    x = []
    cursor = connection.cursor()
    cursor.execute("WITH timeorder as  (SELECT web_app_data, userid, id from public.orders where userid = '" + str(message.from_user.id) + "') SELECT web_app_data FROM timeorder where id = (SELECT MAX(id) FROM timeorder)")
    prise = cursor.fetchone()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO public.\"orders_number\"(id, userid, order_number) VALUES ((SELECT MAX(id) +1 FROM public.orders_number), '" + str(message.from_user.id) + "', '"+ str(random_id) +"');")
    cursor = connection.cursor()
    
    c = json.loads((prise[0]))
    for key, value in c.items():
        x.append(types.LabeledPrice(str(key) ,  int(value)))
    
    await bot.send_invoice(
        message.from_user.id, 
        title ='Заказ №' + random_id +' от ' + tomorrow + '.' ,
        description = 'Ваш заказ.' ,
        payload='some-invoice-payload-for-our-internal-use',
        provider_token=PAYMENTS_PROVIDER_TOKEN, 
        max_tip_amount = 20000,
        suggested_tip_amounts = NUMBER_OF_TIPS,
        currency='RUB',
        prices = x,
        photo_url= IMAGE_URL,
        photo_height= 450,
        photo_width=450,
        photo_size = 450,
        need_name= True,
        need_email= True,
        need_phone_number= True,
        is_flexible=True,
        #need_shipping_address= True,
        start_parameter='time-machine-example',
        reply_markup = keyboard1)

@dp.shipping_query_handler(lambda query: True)
async def process_shipping_query(shipping_query: types.ShippingQuery):
    shipping_options = [POST_SHIPPING_OPTION,SDEK_SHIPPING_OPTION] 

    await bot.answer_shipping_query(
        shipping_query.id,
        ok=True,
        shipping_options=shipping_options
    )

@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=['successful_payment'])
async def process_successful_payment(message):
    cursor = connection.cursor()
    cursor.execute("WITH timeorder2 as  (SELECT web_app_data, userid, id ,web_app_data_str from public.orders where userid = '" + str(message.from_user.id) + "' ) SELECT web_app_data_str FROM timeorder2 where id = (SELECT MAX(id) FROM timeorder2)")
    webinfo = cursor.fetchone()
    web = list(webinfo)
    we = web[0]
    cursor = connection.cursor()
    cursor.execute("WITH timeorder3 as  (SELECT order_number, userid, id from public.orders_number where userid = '" + str(message.from_user.id) + "' ) SELECT order_number FROM timeorder3 where id = (SELECT MAX(id) FROM timeorder3)")
    order_number = cursor.fetchone()
    i = list(order_number)
    ornum = i[0]

    sum = message.successful_payment.total_amount // 100
        
    if message.successful_payment.shipping_option_id == 'sdek':
        ship = 'СДЕК'
    else:
        ship = 'Почта России'
    
    cursor = connection.cursor()
    cursor.execute("INSERT INTO public.\"paid_orders_are\"(id, userid, \"name\", \"order_number\", \"wep_app_data_str\" , \"phone_number\", \"email\", \"country_code\", \"region\", \"city\", \"street_line1\", \"street_line2\", \"post_code\", \"total_amount\", \"shipping_option_id\", \"telegram_payment_charge_id\", \"provider_payment_charge_id\", \"currency\") VALUES ((SELECT MAX(id) +1  FROM public.\"paid_orders_are\"), '"+ str(message.from_user.id) +"','"+ str(message.successful_payment.order_info.name) +"','" + str(ornum) + "','" + str(we) + "',  '"+ str(message.successful_payment.order_info.phone_number) +"', '" + str(message.successful_payment.order_info.email) + "', '" + str(message.successful_payment.order_info.shipping_address.country_code) + "', '" + str(message.successful_payment.order_info.shipping_address.state) + "', '" + str(message.successful_payment.order_info.shipping_address.city) + "', '" + str(message.successful_payment.order_info.shipping_address.street_line1) + "', '" + str(message.successful_payment.order_info.shipping_address.street_line2) + "', '" + str(message.successful_payment.order_info.shipping_address.post_code) + "', '" + str(sum) + "', '"+ ship +"', '"+ str(message.successful_payment.telegram_payment_charge_id) +"', '"+ str(message.successful_payment.provider_payment_charge_id) +"', '"+ str(message.successful_payment.currency) +"');")
    connection.commit()
    
    worksheet.append_row([str(message.from_user.id), str(message.successful_payment.order_info.name), str(ornum), str(we), str(message.successful_payment.order_info.phone_number), str(message.successful_payment.order_info.email), str(message.successful_payment.order_info.shipping_address.country_code), str(message.successful_payment.order_info.shipping_address.state), str(message.successful_payment.order_info.shipping_address.city), str(message.successful_payment.order_info.shipping_address.street_line1), str(message.successful_payment.order_info.shipping_address.street_line2), str(message.successful_payment.order_info.shipping_address.post_code), str(sum), ship, str(message.successful_payment.telegram_payment_charge_id), str(message.successful_payment.provider_payment_charge_id),str(message.successful_payment.currency)])
    await bot.send_message(message.from_user.id,MESSAGES['fin'] )
    await bot.send_message(382478851,'Поступил новый заказ: №' + str(ornum) + '\n\nИмя клиента: ' + str(message.successful_payment.order_info.name) + '\nЗаказ: ' + str(we) + '\nНомер телефона: ' + str(message.successful_payment.order_info.phone_number) + '\nEmail: ' + str(message.successful_payment.order_info.email) + '\nКод страны: ' + str(message.successful_payment.order_info.shipping_address.country_code) + '\nОбласть(штат): ' + str(message.successful_payment.order_info.shipping_address.state) + '\nГород: ' + str(message.successful_payment.order_info.shipping_address.city) + '\nАдрес 1: ' + str(message.successful_payment.order_info.shipping_address.street_line1) + '\nАдрес2: ' + str(message.successful_payment.order_info.shipping_address.street_line2) + '\nПочтовый индекс: ' + str(message.successful_payment.order_info.shipping_address.post_code) + '\nСумма заказа: '+ str(sum) +' RUB' +'\nСпособ Доставки: '+ ship + '\nТокен оплаты Telegram: ' + str(message.successful_payment.telegram_payment_charge_id) + '\nТокен оплаты провайдера: ' + str(message.successful_payment.provider_payment_charge_id) +'\nВалюта: '+ str(message.successful_payment.currency) + '')
    
@dp.message_handler(content_types= "text")
async def process_terms_command(message: types.Message):
    name = message.from_user.first_name
    await message.reply('Привет, ' + name + '!' +'\nМеня зовут Юлия Шишкина, и я твой проводник в мир красоты и здоровой кожи!' + '\nДля заказа Estetic box нажми кнопку ниже.', 
    reply_markup=ReplyKeyboardMarkup(resize_keyboard = True).add(KeyboardButton(text="Сделайте заказ", 
    web_app=WebAppInfo(url= WEB_APP))), reply=False)
    await bot.send_photo(message.chat.id, photo= PHOTO_MES, caption = MESSAGES['help'] ,parse_mode= types.ParseMode.HTML)

if __name__ == "__main__":
   executor.start_polling(dp, loop=loop)