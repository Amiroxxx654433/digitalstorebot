import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

API_TOKEN = '7620831538:AAHDF4rvhKK1sLkhUF_2xlmoYy1r0tQxIPs'
ADMIN_IDS = [5231298684]  # أضف معرفات الأدمن هنا

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# === ملفات المنتجات والكوبونات ===
PRODUCTS_FILE = 'products.json'
COUPONS_FILE = 'coupons.json'
ORDERS_FILE = 'orders.json'

# === الحالات ===
class AddProduct(StatesGroup):
    name = State()
    price = State()

class AddCoupon(StatesGroup):
    code = State()
    discount = State()

# === وظائف المساعدة ===
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# === /start ===
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('قائمة المنتجات'))
    if msg.from_user.id in ADMIN_IDS:
        kb.add(KeyboardButton('لوحة التحكم'))
    await msg.answer('مرحبًا بك في متجر المنتجات الرقمية.', reply_markup=kb)

# === قائمة المنتجات ===
@dp.message_handler(lambda m: m.text == 'قائمة المنتجات')
async def show_products(msg: types.Message):
    products = load_data(PRODUCTS_FILE)
    if not products:
        await msg.answer("لا توجد منتجات حالياً.")
        return
    for pid, p in products.items():
        btn = InlineKeyboardMarkup().add(InlineKeyboardButton("شراء", callback_data=f'buy_{pid}'))
        await msg.answer(f"{p['name']}\nالسعر: {p['price']} USDT", reply_markup=btn)

# === شراء منتج ===
@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def buy_product(callback: types.CallbackQuery):
    pid = callback.data.split('_')[1]
    products = load_data(PRODUCTS_FILE)
    if pid not in products:
        await callback.message.edit_text("المنتج غير موجود.")
        return
    order = {
        'user_id': callback.from_user.id,
        'product_id': pid,
        'status': 'pending'
    }
    orders = load_data(ORDERS_FILE)
    orders[str(len(orders)+1)] = order
    save_data(ORDERS_FILE, orders)
    await callback.message.edit_text("تم إنشاء الطلب. سيتم التواصل معك لتسليم المنتج.")
    for admin in ADMIN_IDS:
        await bot.send_message(admin, f"طلب جديد من @{callback.from_user.username} لمنتج: {products[pid]['name']}")

# === لوحة التحكم ===
@dp.message_handler(lambda m: m.text == 'لوحة التحكم')
async def admin_panel(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("إضافة منتج", "إضافة كوبون")
    kb.add("عرض الطلبات", "رجوع")
    await msg.answer("أهلاً بك في لوحة التحكم.", reply_markup=kb)

# === إضافة منتج ===
@dp.message_handler(lambda m: m.text == 'إضافة منتج')
async def add_product(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer("أدخل اسم المنتج:")
    await AddProduct.name.set()

@dp.message_handler(state=AddProduct.name)
async def set_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("أدخل سعر المنتج:")
    await AddProduct.price.set()

@dp.message_handler(state=AddProduct.price)
async def set_price(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    price = msg.text
    products = load_data(PRODUCTS_FILE)
    pid = str(len(products)+1)
    products[pid] = {'name': name, 'price': price}
    save_data(PRODUCTS_FILE, products)
    await msg.answer(f"تم إضافة المنتج: {name} بسعر {price}.")
    await state.finish()

# === إضافة كوبون ===
@dp.message_handler(lambda m: m.text == 'إضافة كوبون')
async def add_coupon(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer("أدخل رمز الكوبون:")
    await AddCoupon.code.set()

@dp.message_handler(state=AddCoupon.code)
async def set_coupon_code(msg: types.Message, state: FSMContext):
    await state.update_data(code=msg.text)
    await msg.answer("أدخل نسبة الخصم (مثال: 20):")
    await AddCoupon.discount.set()

@dp.message_handler(state=AddCoupon.discount)
async def set_coupon_discount(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data['code']
    discount = msg.text
    coupons = load_data(COUPONS_FILE)
    coupons[code] = discount
    save_data(COUPONS_FILE, coupons)
    await msg.answer(f"تم إضافة الكوبون: {code} بنسبة خصم {discount}%")
    await state.finish()

# === عرض الطلبات ===
@dp.message_handler(lambda m: m.text == 'عرض الطلبات')
async def show_orders(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    orders = load_data(ORDERS_FILE)
    if not orders:
        await msg.answer("لا توجد طلبات.")
        return
    products = load_data(PRODUCTS_FILE)
    for oid, order in orders.items():
        user = order['user_id']
        product = products[order['product_id']]['name']
        status = order['status']
        await msg.answer(f"طلب #{oid}\nالمنتج: {product}\nالمستخدم: {user}\nالحالة: {status}")

# === رجوع ===
@dp.message_handler(lambda m: m.text == 'رجوع')
async def back(msg: types.Message):
    await start(msg)

# === تشغيل البوت ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
