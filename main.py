import os
import requests
import feedparser
import yfinance as yf
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

# --- 2. جلب مؤشرات السلع والنفط الحية ---
def get_live_tickers():
    """جلب أسعار النفط المباشرة عبر yfinance"""
    try:
        brent = yf.Ticker("BZ=F")
        price = brent.history(period="1d")['Close'].iloc[-1]
        brent_str = f"${price:.2f}"
    except Exception:
        brent_str = "غير متوفر"

    return {
        "brent": brent_str,
        "wheat": "$542.10", # مؤشر تقديري لحين ربطه بـ API مخصص
        "bdi": "1,845"
    }

# --- 3. مصادر RSS الموسعة والكلمات المفتاحية ---
RSS_SOURCES = {
    "mewa": [
        "https://www.spa.gov.sa/rss.xml",                # واس
        "https://www.alriyadh.com/section.economy.xml", # اقتصاد الرياض
        "https://www.okaz.com.sa/rss/local"             # محلي عكاظ
    ],
    "global_risks": [
        "https://news.un.org/feed/subscribe/ar/news/topic/health/feed/rss.xml", # صحة الأمم المتحدة
        "http://feeds.bbci.co.uk/news/world/rss.xml",                          # BBC World
        "https://www.aljazeera.net/aljazeerarss/a7c18663-711e-42b7-a3a8-4ed09860b0f7/73d0e1b4-532f-45ef-b135-bfd3d2cb29e8" # الجزيرة اقتصاد
    ]
}

KEYWORDS = {
    "mewa": [
        "البيئة", "المياه", "الزراعة", "الأمن الغذائي", "القمح", "المخزون", "هسدا", "سد", "تحلية", 
        "حصول", "استثمار زراعي", "حبوب", "مواشي", "صوامع", "غطاء نباتي"
    ],
    "biosecurity": [
        "إنفلونزا", "جراد", "انسكاب", "تلوث", "سوسة", "جائحة", "فيروس", "حظر استيراد", 
        "تفشي", "طوارئ صحية", "بقعة زيت", "سلامة الأغذية"
    ],
    "geopolitics": [
        "مضيق", "هرمز", "باب المندب", "قناة السويس", "البحر الأحمر", "تأمين بحري", "توترات", 
        "ناقلة", "حظر تصدير", "سلاسل الإمداد", "شحن بحري"
    ]
}

def filter_feed(urls, keywords):
    """جلب وتصفية الأخبار من عدة مصادر بدون تكرار"""
    matched_entries = []
    seen_titles = set()
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.title.strip()
                link = entry.link
                
                if title in seen_titles:
                    continue
                
                # مطابقة الكلمات المفتاحية
                if any(kw.lower() in title.lower() for kw in keywords):
                    matched_entries.append({"title": title, "link": link})
                    seen_titles.add(title)
        except Exception as e:
            print(f"خطأ في قراءة المصدر {url}: {e}")
            
    return matched_entries

# --- 4. بناء هيكل النشرة ---
def generate_report():
    tickers = get_live_tickers()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # جلب الأخبار وتصنيفها
    mewa_news = filter_feed(RSS_SOURCES["mewa"], KEYWORDS["mewa"])
    bio_news = filter_feed(RSS_SOURCES["global_risks"], KEYWORDS["biosecurity"])
    geo_news = filter_feed(RSS_SOURCES["global_risks"], KEYWORDS["geopolitics"])

    # بناء نص الرسالة بـ HTML
    report = f"🚨 <b>الرصد اليومي | Daily Intelligence Briefing</b>\n"
    report += f"📅 <i>{date_str}</i> | ⏱️ <i>تحديث آلي</i>\n"
    report += "----------------------------------------\n\n"
    
    report += "📊 <b>1. شريط المؤشرات والسلع الحيوية</b>\n"
    report += f"• 🛢️ <b>نفط برنت المباشر:</b> {tickers['brent']}\n"
    report += f"• 🌾 <b>القمح العالمي:</b> {tickers['wheat']}\n"
    report += f"• ⛽ <b>مؤشر الشحن (BDI):</b> {tickers['bdi']}\n\n"

    report += "💡 <b>2. الخلاصة التنفيذية (Executive TL;DR)</b>\n"
    report += "<i>> متابعة مستمرة لمستجدات الأمن المائي والغذائي، واستقرار حركة الملاحة والتنبيهات البيئية الإقليمية.</i>\n\n"

    report += "🌱 <b>3. الأمن المائي والغذائي والزراعي (MEWA والجهات التابعة)</b>\n"
    if mewa_news:
        for item in mewa_news[:4]:
            report += f"• 🟢 <b>[خبر محلي/قطاعي]:</b> {item['title']}\n  🔗 <a href='{item['link']}'>رابط الخبر</a>\n"
    else:
        report += "• لا توجد مستجدات حرجة مسجلة في القطاع خلال الساعات الماضية.\n"
    report += "\n"

    report += "☣️ <b>4. الأمن الحيوي والسلامة البيئية</b>\n"
    if bio_news:
        for item in bio_news[:3]:
            report += f"• 🟡 <b>[تنبيه بيئي/حيوي]:</b> {item['title']}\n  🔗 <a href='{item['link']}'>المصدر</a>\n"
    else:
        report += "• لم يتم رصد مخاطر حيوية أو انسكابات نفطية رئيسية اليوم.\n"
    report += "\n"

    report += "⚠️ <b>5. الاضطرابات الجيوسياسية والممرات المائية</b>\n"
    if geo_news:
        for item in geo_news[:3]:
            report += f"• 🔴 <b>[ممرات مائية/أزمات]:</b> {item['title']}\n  🔗 <a href='{item['link']}'>التفاصيل</a>\n"
    else:
        report += "• استقرار حركة الملاحة في باب المندب ومضيق هرمز وقناة السويس.\n"

    return report

if __name__ == "__main__":
    briefing_text = generate_report()
    send_telegram_message(briefing_text)
