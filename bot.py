import urllib.request
import urllib.parse
import json
import time

TOKEN = '8853754694:AAGDF04uDAzLW4t3I4e0TZi4m-JJBZI38w8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

CHANNEL_ID = "@Lada_cross7"
ADMIN_ID = 8673898827  

START_FILE_ID = "AgACAgIAAxkBAAIHBGqCeYL6t9TMIl9Ddz9SS9PIgbXOAAIjIGsb5YoQSIgNwmma5BpKAQADAgADeAADPQQ"
LOC_FILE_ID = "AgACAgIAAxkBAAIG02qCckSGuZBl6q3eG778d3hmycdNAAIZIGsb5YoQSA72CsJ4pW6kAQADAgADeAADPQQ"

MAPS_URL = "https://maps.google.com/?q=40.5243730,70.9442190"

user_states = {}
admin_reply_tracker = {}
all_users = set()

def send_api(method, data):
    try:
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(URL + method, data=data_encoded)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Xatolik ({method}): {e}")

def send_json_api(method, data):
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            URL + method, 
            data=json_data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res
    except Exception as e:
        print(f"JSON Xatolik ({method}): {e}")
        return {"ok": False}

print("Bot ishga tushdi (Media qo'llab-quvvatlash bilan)...")
last_update_id = None

while True:
    try:
        url = URL + f'getUpdates?timeout=10&offset={last_update_id if last_update_id else 0}'
        response = urllib.request.urlopen(url, timeout=15).read().decode('utf-8')
        updates = json.loads(response)
        
        if updates and "result" in updates:
            for update in updates["result"]:
                last_update_id = update["update_id"] + 1

                # --- INLINE TUGMALAR ---
                if "callback_query" in update:
                    cb = update["callback_query"]
                    cb_id = cb["id"]
                    cb_data = cb.get("data", "")
                    cb_from_id = cb["from"]["id"]
                    user = cb["from"]
                    user_info = f"@{user.get('username')}" if user.get('username') else f"{user.get('first_name', '')} (ID: {cb_from_id})"

                    if cb_data.startswith("reply_user:"):
                        target_id = int(cb_data.split(":")[1])
                        user_states[cb_from_id] = f"replying_to_{target_id}"
                        send_api('sendMessage', {
                            'chat_id': cb_from_id,
                            'text': "✍️ Javobingizni (matn, rasm, video, fayl yoki ovozli xabar) yuboring:"
                        })
                        send_json_api('answerCallbackQuery', {'callback_query_id': cb_id})

                    elif cb_data.startswith("rate_"):
                        stars_count = cb_data.split("_")[1]
                        
                        send_json_api('answerCallbackQuery', {
                            'callback_query_id': cb_id,
                            'text': f"Rahmat! Siz {stars_count}⭐️ baho qo'ydingiz.",
                            'show_alert': True
                        })
                        
                        send_api('sendMessage', {
                            'chat_id': ADMIN_ID,
                            'text': f"🌟 YANGI BAHO!\n👤 Foydalanuvchi: {user_info}\n⭐️ Qo'yilgan baho: {stars_count}/10 yulduz"
                        })

                        send_json_api('editMessageText', {
                            'chat_id': cb_from_id,
                            'message_id': cb["message"]["message_id"],
                            'text': f"✅ Bahoingiz uchun rahmat! Siz {stars_count}⭐️ qo'ydingiz."
                        })

                    continue

                # --- XABARLAR (MATN, RASM, VIDEO, VA H.K.) ---
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "").strip()
                    user = msg.get("from", {})
                    user_info = f"@{user.get('username')}" if user.get('username') else f"{user.get('first_name', '')} (ID: {chat_id})"

                    keyboard = json.dumps({
                        'keyboard': [
                            [{'text': '📍 Locatsiya'}, {'text': '📍 Manzil'}],
                            [{'text': '🛍 Zakaz qilish'}, {'text': '🔍 Zapchast bor/yo\'qligini bilish'}],
                            [{'text': '🔥 Chegirmalar'}, {'text': '🚚 Yetkazib berish'}],
                            [{'text': '💳 To‘lov usullari'}, {'text': '❓ Ko‘p beriladigan savollar'}],
                            [{'text': '📞 Call manager'}, {'text': '📢 Kanal'}],
                            [{'text': '⭐️ Mijozlar fikrlari'}, {'text': '✍️ Shikoyat qilish'}],
                            [{'text': '📢 Kanalga reklama qo\'yish'}, {'text': 'ℹ️ Biz haqimizda'}],
                            [{'text': '⭐️ Baholash'}]
                        ],
                        'resize_keyboard': True
                    })

                    cancel_keyboard = json.dumps({
                        'keyboard': [[{'text': '❌ Bekor qilish'}]],
                        'resize_keyboard': True
                    })

                    current_state = user_states.get(chat_id, "")

                    if text == "❌ Bekor qilish":
                        user_states[chat_id] = None
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "❌ Amal bekor qilindi.", 'reply_markup': keyboard})
                        continue

                    # 1. JAVOB YOZISH REJIMI (ADMIN YOKI USER)
                    if current_state and str(current_state).startswith("replying_to_"):
                        target_chat_id = int(current_state.split("_")[-1])
                        reply_btn = json.dumps({
                            'inline_keyboard': [[{'text': '💬 Javob berish', 'callback_data': f'reply_user:{chat_id}'}]]
                        })

                        send_api('sendMessage', {'chat_id': target_chat_id, 'text': "💬 Sizga yangi xabar keldi:"})
                        res = send_json_api('copyMessage', {
                            'chat_id': target_chat_id,
                            'from_chat_id': chat_id,
                            'message_id': msg['message_id'],
                            'reply_markup': reply_btn
                        })

                        if res.get("ok"):
                            send_api('sendMessage', {'chat_id': chat_id, 'text': "✅ Xabaringiz yuborildi!", 'reply_markup': keyboard})
                        else:
                            send_api('sendMessage', {'chat_id': chat_id, 'text': "❌ Xatolik yuz berdi.", 'reply_markup': keyboard})

                        user_states[chat_id] = None
                        continue

                    # 2. ADMIN TELEGRAM 'REPLY' QILGANDA (RASM/VIDEO/MATN FARQI YO'Q)
                    if chat_id == ADMIN_ID and "reply_to_message" in msg:
                        replied_msg_id = msg["reply_to_message"]["message_id"]
                        if replied_msg_id in admin_reply_tracker:
                            target_chat_id = admin_reply_tracker[replied_msg_id]
                            reply_btn = json.dumps({
                                'inline_keyboard': [[{'text': '💬 Javob berish', 'callback_data': f'reply_user:{ADMIN_ID}'}]]
                            })

                            res = send_json_api('copyMessage', {
                                'chat_id': target_chat_id,
                                'from_chat_id': ADMIN_ID,
                                'message_id': msg['message_id'],
                                'reply_markup': reply_btn
                            })

                            if res.get("ok"):
                                send_api('sendMessage', {'chat_id': ADMIN_ID, 'text': "✅ Javobingiz foydalanuvchiga yetkazildi!"})
                            else:
                                send_api('sendMessage', {'chat_id': ADMIN_ID, 'text': "❌ Javob yetkazilmadi."})
                            continue

                    # 3. REKLAMA (HAR QANDAY MEDIA)
                    if current_state == "waiting_for_ad":
                        res = send_json_api('copyMessage', {
                            'chat_id': CHANNEL_ID,
                            'from_chat_id': chat_id,
                            'message_id': msg['message_id']
                        })
                        if res.get("ok"):
                            send_api('sendMessage', {'chat_id': chat_id, 'text': "✅ Reklama kanalga joylandi!", 'reply_markup': keyboard})
                        else:
                            send_api('sendMessage', {'chat_id': chat_id, 'text': "❌ Xatolik! Botni kanalga admin qiling.", 'reply_markup': keyboard})
                        user_states[chat_id] = None
                        continue

                    # 4. ZAPCHAST SO'RASH (RASM, VIDEO, OVOZ)
                    elif current_state == "waiting_for_part":
                        reply_btn = json.dumps({'inline_keyboard': [[{'text': '💬 Javob berish', 'callback_data': f'reply_user:{chat_id}'}]]})
                        send_api('sendMessage', {'chat_id': ADMIN_ID, 'text': f"❓ ZAPCHAST SO'ROVI!\n👤 Kimdan: {user_info}"})
                        
                        res = send_json_api('copyMessage', {
                            'chat_id': ADMIN_ID,
                            'from_chat_id': chat_id,
                            'message_id': msg['message_id'],
                            'reply_markup': reply_btn
                        })
                        if res.get("ok"):
                            admin_reply_tracker[res["result"]["message_id"]] = chat_id

                        send_api('sendMessage', {'chat_id': chat_id, 'text': "✅ So'rovingiz va yuborgan fayllaringiz qabul qilindi!", 'reply_markup': keyboard})
                        user_states[chat_id] = None
                        continue

                    # 5. ZAKAZ QILISH (RASM, VIDEO, OVOZ)
                    elif current_state == "waiting_for_order":
                        reply_btn = json.dumps({'inline_keyboard': [[{'text': '💬 Javob berish', 'callback_data': f'reply_user:{chat_id}'}]]})
                        send_api('sendMessage', {'chat_id': ADMIN_ID, 'text': f"📦 YANGI ZAKAZ!\n👤 Kimdan: {user_info}"})
                        
                        res = send_json_api('copyMessage', {
                            'chat_id': ADMIN_ID,
                            'from_chat_id': chat_id,
                            'message_id': msg['message_id'],
                            'reply_markup': reply_btn
                        })
                        if res.get("ok"):
                            admin_reply_tracker[res["result"]["message_id"]] = chat_id

                        send_api('sendMessage', {'chat_id': chat_id, 'text': "✅ Zakazingiz qabul qilindi!", 'reply_markup': keyboard})
                        user_states[chat_id] = None
                        continue

                    # 6. SHIKOYAT YUBORISH (HAR QANDAY MEDIA)
                    elif current_state == "waiting_for_complaint":
                        reply_btn = json.dumps({'inline_keyboard': [[{'text': '💬 Javob berish', 'callback_data': f'reply_user:{chat_id}'}]]})
                        send_api('sendMessage', {'chat_id': ADMIN_ID, 'text': f"⚠️ YANGI SHIKOYAT / TAKLIF!\n👤 Kimdan: {user_info}"})
                        
                        res = send_json_api('copyMessage', {
                            'chat_id': ADMIN_ID,
                            'from_chat_id': chat_id,
                            'message_id': msg['message_id'],
                            'reply_markup': reply_btn
                        })
                        if res.get("ok"):
                            admin_reply_tracker[res["result"]["message_id"]] = chat_id

                        send_api('sendMessage', {'chat_id': chat_id, 'text': "✅ Shikoyat / taklifingiz adminga yetkazildi!", 'reply_markup': keyboard})
                        user_states[chat_id] = None
                        continue

                    # --- MENYU TUGMALARI ---
                    if text == "/start":
                        is_new = chat_id not in all_users
                        all_users.add(chat_id)
                        
                        if chat_id != ADMIN_ID:
                            status_text = "yangi foydalanuvchi" if is_new else "qayta"
                            send_api('sendMessage', {
                                'chat_id': ADMIN_ID,
                                'text': f"🚀 {user_info} botga /start bosdi ({status_text}).\n👥 Obunachilar soni: {len(all_users)} ta"
                            })

                        start_msg = "Assalomu Alaykum! LADA CROSS botiga xush kelibsiz. Kerakli bo'limni tanlang:"
                        send_api('sendPhoto', {'chat_id': chat_id, 'photo': START_FILE_ID, 'caption': start_msg, 'reply_markup': keyboard})
                    
                    elif text == '📍 Locatsiya':
                        send_api('sendLocation', {'chat_id': chat_id, 'latitude': 40.5243730, 'longitude': 70.9442190})
                        loc_text = f"📍 Do'konimiz binosi va Xarita havolasi:\n{MAPS_URL}"
                        send_api('sendPhoto', {'chat_id': chat_id, 'photo': LOC_FILE_ID, 'caption': loc_text, 'reply_markup': keyboard})
                    
                    elif text == '📍 Manzil':
                        manzil_text = (
                            "📍 Do'kon manzili:\nQo'qon shahar, Kalvak svetofori.\n\n"
                            "🏢 Mo'ljal:\nKalvak choyxonasi ro'parasida.\n\n"
                            f"🗺 Xarita: {MAPS_URL}"
                        )
                        send_api('sendPhoto', {'chat_id': chat_id, 'photo': LOC_FILE_ID, 'caption': manzil_text, 'reply_markup': keyboard})

                    elif text == '📞 Call manager':
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "📞 Manager: SOLLIHONAKA\nTelefon: +998905077266", 'reply_markup': keyboard})
                    
                    elif text == 'ℹ️ Biz haqimizda':
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "ℹ️ LADA CROSS ZAPCHAST do'koni.\nBarcha turdagi Lada avtomashinalari ehtiyot qismlari arzon narxlarda sotiladi. Barcha zapchastlarimizga 100% kafolat beriladi!", 'reply_markup': keyboard})
                    
                    elif text == '📢 Kanal':
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "📢 Rasmiy telegram kanalimiz:\nhttps://t.me/Lada_cross7", 'reply_markup': keyboard})

                    elif text == "🔥 Chegirmalar":
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "🔥 Hozirgi kunda mavjud bo'lgan chegirmalar va aksiyalar haqida ma'lumot olish uchun rasmiy kanalimizni kuzatib boring:\nhttps://t.me/Lada_cross7", 'reply_markup': keyboard})

                    elif text == "🚚 Yetkazib berish":
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "🚚 Dastavka / Yetkazib berish xizmati bor!\nO'zbekiston bo'ylab pochta yoki taksi orqali tezkor yetkazib beramiz. Batafsil ma'lumot uchun menejer bilan bog'laning.", 'reply_markup': keyboard})

                    elif text == "💳 To‘lov usullari":
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "💳 To'lov turlari:\n• Naqd pul\n• Click / Payme (Karta orqali)\n• Joyida to'lov qilishingiz mumkin.", 'reply_markup': keyboard})

                    elif text == "❓ Ko‘p beriladigan savollar":
                        faq_text = (
                            "❓ **Ko'p beriladigan savollar:**\n\n"
                            "1. Zapchastlar originalmi?\n— Ha, barcha zapchastlarimiz sifatli va kafolatlangan.\n\n"
                            "2. Boshqa viloyatlarga dastavka bormi?\n— Ha, respublika bo'yicha yetkazib beramiz.\n\n"
                            "3. Do'kon ish vaqti qachon?\n— Har kuni 08:00 dan 19:00 gacha."
                        )
                        send_api('sendMessage', {'chat_id': chat_id, 'text': faq_text, 'reply_markup': keyboard})

                    elif text == "⭐️ Mijozlar fikrlari":
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "⭐️ Mijozlarimizning fikrlari va izohlarini kanalimizda ko'rishingiz mumkin:\nhttps://t.me/Lada_cross7", 'reply_markup': keyboard})

                    elif text == "✍️ Shikoyat qilish":
                        user_states[chat_id] = "waiting_for_complaint"
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "✍️ Shikoyat yoki taklifingizni yuboring (Matn, rasm, video yoki audio shaklida):", 'reply_markup': cancel_keyboard})

                    elif text == "📢 Kanalga reklama qo'yish":
                        user_states[chat_id] = "waiting_for_ad"
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "Reklama matni, rasm yoki videongizni yuboring:", 'reply_markup': cancel_keyboard})

                    elif text == "🔍 Zapchast bor/yo'qligini bilish":
                        user_states[chat_id] = "waiting_for_part"
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "Kerakli zapchast rasmi, nomi yoki videosini yuboring:", 'reply_markup': cancel_keyboard})

                    elif text == "🛍 Zakaz qilish":
                        user_states[chat_id] = "waiting_for_order"
                        send_api('sendMessage', {'chat_id': chat_id, 'text': "Zakaz qilmoqchi bo'lgan buyumingiz rasm/videosi yoki nomini yuboring:", 'reply_markup': cancel_keyboard})

                    elif text == "⭐️ Baholash":
                        rating_keyboard = json.dumps({
                            'inline_keyboard': [
                                [{'text': '1⭐️', 'callback_data': 'rate_1'}, {'text': '2⭐️', 'callback_data': 'rate_2'}, {'text': '3⭐️', 'callback_data': 'rate_3'}, {'text': '4⭐️', 'callback_data': 'rate_4'}, {'text': '5⭐️', 'callback_data': 'rate_5'}],
                                [{'text': '6⭐️', 'callback_data': 'rate_6'}, {'text': '7⭐️', 'callback_data': 'rate_7'}, {'text': '8⭐️', 'callback_data': 'rate_8'}, {'text': '9⭐️', 'callback_data': 'rate_9'}, {'text': '10⭐️', 'callback_data': 'rate_10'}]
                            ]
                        })
                        send_json_api('sendMessage', {
                            'chat_id': chat_id,
                            'text': "Xizmatimizni baholang (1 dan 10 gacha):",
                            'reply_markup': rating_keyboard
                        })

    except Exception as e:
        time.sleep(2)
        
    time.sleep(0.5)
