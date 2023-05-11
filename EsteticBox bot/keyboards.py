from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

one = InlineKeyboardButton("Оплатить", pay = True) 
keyboard1 = InlineKeyboardMarkup(row_width=1).add(one)

yes = InlineKeyboardButton("Да", callback_data= "yes")
no = InlineKeyboardButton("Нет", callback_data= "no")
keyboard2 = InlineKeyboardMarkup().add(yes,no)

key1 = InlineKeyboardButton("Какая то кнопка",callback_data="func")
key2 = InlineKeyboardButton("И ещё какая то кнопка",callback_data="func1")
keyboard3 = InlineKeyboardMarkup().add(key1,key2)

design = InlineKeyboardButton("Оформить заказ",callback_data="des")
keyboard4 = InlineKeyboardMarkup().add(design)