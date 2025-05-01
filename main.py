import json import os from aiogram import Bot, Dispatcher, executor, types from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton from aiogram.dispatcher.filters import Command from aiogram.contrib.fsm_storage.memory import MemoryStorage from aiogram.dispatcher import FSMContext from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE" ADMIN_ID = 5231298684  # استبدل بالآيدي الخاص بك

bot = Bot(token=TOKEN) dp = Dispatcher(bot, storage=MemoryStorage())

PRODUCTS_FILE = "data/products.json" COUPONS_FILE = "data/coupons.json" ORDERS_FILE = "data/orders.json"

التأكد من وجود الملفات الأساسية

os.makedirs("data", exist_ok=True) for f in [PRODUCTS_FILE, COUPONS_FILE, ORDERS_FILE]: if not os.path.exists(f): with open(f, "w") as file: json.dump({}, file)

حالات FSM

class AddProductState(StatesGroup): name = State() price = State() content = State()

class AddCouponState(StatesGroup): code = State() discount = State()

لوحات

admin_kb = InlineKeyboardMarkup(row_width=2) admin_kb.add( InlineKeyboardButton("إضافة منتج", callback_data="add_product"), InlineKeyboardButton("إدارة المنتجات", callback_data="manage_products"), InlineKeyboardButton("إضافة كوبون", callback_data="add_coupon"), InlineKeyboardButton("إدارة الكوبونات", callback_data="manage_coupons") )

وظائف المساعدة

def load_data(file): with open(file, 'r') as f: return json.load(f)

def save_data(file, data): with open(file, 'w') as f: json.dump(data, f, ensure_ascii=False, indent=2)

أوامر أساسية

@dp.message_handler(commands=['start']) async def start_cmd(message: types.Message): if message.from_user.id == ADMIN_ID: await message.answer("مرحبًا بك في لوحة تحكم الأدمن", reply_markup=admin_kb) else: await message.answer("مرحبًا! يمكنك تصفح المنتجات هنا.")

إضافة منتج

@dp.callback_query_handler(lambda c: c.data == "add_product") async def add_product_start(callback: types.CallbackQuery): await callback.message.answer("أدخل اسم المنتج:") await AddProductState.name.set()

@dp.message_handler(state=AddProductState.name) async def add_product_name(message: types.Message, state: FSMContext): await state.update_data(name=message.text) await message.answer("أدخل السعر:") await AddProductState.next()

@dp.message_handler(state=AddProductState.price) async def add_product_price(message: types.Message, state: FSMContext): await state.update_data(price=message.text) await message.answer("أدخل محتوى المنتج أو التفاصيل:") await AddProductState.next()

@dp.message_handler(state=AddProductState.content) async def add_product_content(message: types.Message, state: FSMContext): data = await state.get_data() products = load_data(PRODUCTS_FILE) pid = str(len(products) + 1) products[pid] = { "name": data['name'], "price": data['price'], "content": message.text } save_data(PRODUCTS_FILE, products) await message.answer("تم إضافة المنتج بنجاح.") await state.finish()

عرض المنتجات

@dp.callback_query_handler(lambda c: c.data == "manage_products") async def manage_products(callback: types.CallbackQuery): products = load_data(PRODUCTS_FILE) if not products: await callback.message.answer("لا توجد منتجات.") return msg = "قائمة المنتجات:\n" for pid, p in products.items(): msg += f"ID: {pid} | {p['name']} - {p['price']}\n" await callback.message.answer(msg)

إضافة كوبون

@dp.callback_query_handler(lambda c: c.data == "add_coupon") async def add_coupon_start(callback: types.CallbackQuery): await callback.message.answer("أدخل رمز الكوبون:") await AddCouponState.code.set()

@dp.message_handler(state=AddCouponState.code) async def coupon_code_entered(message: types.Message, state: FSMContext): await state.update_data(code=message.text.upper()) await message.answer("أدخل نسبة الخصم (مثلاً 20 للخصم 20%):") await AddCouponState.next()

@dp.message_handler(state=AddCouponState.discount) async def coupon_discount_entered(message: types.Message, state: FSMContext): data = await state.get_data() coupons = load_data(COUPONS_FILE) coupons[data['code']] = int(message.text) save_data(COUPONS_FILE, coupons) await message.answer("تمت إضافة الكوبون بنجاح.") await state.finish()

إدارة الكوبونات

@dp.callback_query_handler(lambda c: c.data == "manage_coupons") async def manage_coupons(callback: types.CallbackQuery): coupons = load_data(COUPONS_FILE) if not coupons: await callback.message.answer("لا توجد كوبونات.") return msg = "قائمة الكوبونات:\n" for code, discount in coupons.items(): msg += f"{code} - {discount}% خصم\n" await callback.message.answer(msg)

if name == 'main': executor.start_polling(dp, skip_updates=True)

