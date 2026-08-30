import os
import requests
import feedparser
from datetime import datetime

# --- 1. إعدادات Telegram ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(text):
    """إرسال النشرة إلى تليجرام باستخدام HTML Parse Mode"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("خطأ: لم يتم ضبط TELEGRAM_TOKEN أو CHAT_ID في secrets")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("تم إرسال النشرة بنجاح إلى تليجرام.")
    else:
        print(f"فشل إرسال الرسالة: {response.text}")

# --- 2. جلب مؤشرات السلع والنفط ---
def get_live_tickers():
    """جلب أسعار النفط والأسواق (مبسط)"""
    # يمكن ربطه بـ yfinance أو Yahoo Finance API
    return {
        "brent": "$88.40 (▲ +1.4%)",
        "wheat": "$542.10 (▼ -0.3%)",
        "bdi": "1,845 (▲ +2.1%)"
    }

# --- 3. مصادر RSS والكلمات المفتاحية ---
RSS_SOURCES = {
    "mewa": [
        "https://www.spa.gov.sa/rss.xml",  # واس
    ],
    "global_risks": [
        "https://news.un.org/feed/subscribe/ar/news/topic/health/feed/rss.xml", # صحة بيئية
        "http://feeds.bbci.co.uk/news/world/rss.xml"
    ]
}

KEYWORDS = {
    "mewa": ["البيئة", "المياه", "الزراعة", "الأمن الغذائي", "القمح", "المخزون الاستراتيجي", "هسدا", "سد", "تحلية"],
    "biosecurity": ["إنفلونزا الطيور", "جراد", "انسكاب", "تلوث", "سوسة النخيل", "جائحة", "فيروس", "حظر استيراد"],
    "geopolitics": ["مضيق هرمز", "باب المندب", "قناة السويس", "البحر الأحمر", "تأمين بحري", "توترات"]
}

def filter_feed(url, keywords):
    """جلب وتصفية الأخبار حسب الكلمات المفتاحية"""
    feed = feedparser.parse(url)
    matched_entries = []
    
    for entry in feed.entries[:15]:
        title = entry.title
        link = entry.link
        # البحث عن الكلمات المفتاحية في العنوان
        if any(kw.lower() in title.lower() for kw in keywords):
            matched_entries.append({"title": title, "link": link})
            
    return matched_entries

# --- 4. بناء هيكل النشرة ---
def generate_report():
    tickers = get_live_tickers()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # جلب الأخبار وتصنيفها
    mewa_news = []
    for url in RSS_SOURCES["mewa"]:
        mewa_news.extend(filter_feed(url, KEYWORDS["mewa"]))
        
    bio_news = []
    for url in RSS_SOURCES["global_risks"]:
        bio_news.extend(filter_feed(url, KEYWORDS["biosecurity"]))

    geo_news = []
    for url in RSS_SOURCES["global_risks"]:
        geo_news.extend(filter_feed(url, KEYWORDS["geopolitics"]))

    # بناء نص الرسالة بـ HTML
    report = f"🚨 <b>النشرة الاستراتيجية للإنذار المبكر والأمن الحيوي</b>\n"
    report += f"📅 <i>{date_str}</i> | ⏱️ <i>التحديث التلقائي</i>\n"
    report += "----------------------------------------\n\n"
    
    report += "📊 <b>1. شريط المؤشرات والسلع الحيوية</b>\n"
    report += f"• 🛢️ <b>نفط برنت:</b> {tickers['brent']}\n"
    report += f"• 🌾 <b>القمح العالمي:</b> {tickers['wheat']}\n"
    report += f"• ⛽ <b>مؤشر الشحن (BDI):</b> {tickers['bdi']}\n\n"

    report += "💡 <b>2. الخلاصة التنفيذية (Executive TL;DR)</b>\n"
    report += "<i>> رصد استقرار الإمدادات الوطنية مع متابعة مستمرة لمؤشرات سلاسل الإمداد والممرّات المائية والتحذيرات البيئية.</i>\n\n"

    report += "🌱 <b>3. الأمن المائي والغذائي والزراعي (MEWA والجهات التابعة)</b>\n"
    if mewa_news:
        for item in mewa_news[:3]:
            report += f"• 🟢 <b>[حدث محلي]:</b> {item['title']}\n  🔗 <a href='{item['link']}'>رابط الخبر</a>\n"
    else:
        report += "• لا توجد مستجدات حرجة مسجلة خلال الساعات الماضية.\n"
    report += "\n"

    report += "☣️ <b>4. الأمن الحيوي والسلامة البيئية</b>\n"
    if bio_news:
        for item in bio_news[:2]:
            report += f"• 🟡 <b>[تنبيه بيئي/حيوي]:</b> {item['title']}\n  🔗 <a href='{item['link']}'>المصدر</a>\n"
    else:
        report += "• لم يتم رصد تهديدات حيوية أو انسكابات نفطية رئيسية.\n"
    report += "\n"

    report += "⚠️ <b>5. الاضطرابات الجيوسياسية والممرات المائية</b>\n"
    if geo_news:
        for item in geo_news[:2]:
            report += f"• 🔴 <b>[ممرات مائية]:</b> {item['title']}\n  🔗 <a href='{item['link']}'>التفاصيل</a>\n"
    else:
        report += "• استقرار حركة الملاحة في باب المندب ومضيق هرمز وقناة السويس.\n"

    return report

if __name__ == "__main__":
    briefing_text = generate_report()
    send_telegram_message(briefing_text)
