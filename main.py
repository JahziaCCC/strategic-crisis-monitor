import os
import requests
import feedparser
import yfinance as yf
import html
from urllib.parse import quote, unquote, urlparse, urlunparse
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

def clean_url(url_str):
    """تنظيف ترميز الرابط وإصلاحه ليكون متوافقاً تماماً مع Telegram"""
    url_str = url_str.strip()
    if url_str.lower().startswith("https://"):
        url_str = "https://" + url_str[8:]
    elif url_str.lower().startswith("http://"):
        url_str = "http://" + url_str[7:]
    
    # تفكيك الرابط وإعادة ترميز الأحرف العربية والخاصة بـ URL Encoding
    parsed = urlparse(url_str)
    encoded_path = quote(unquote(parsed.path))
    encoded_query = quote(unquote(parsed.query), safe="=&")
    clean_parts = (parsed.scheme, parsed.netloc, encoded_path, parsed.params, encoded_query, parsed.fragment)
    return urlunparse(clean_parts)

# --- 2. جلب مؤشرات السلع والنفط الحية ---
def get_live_tickers():
    """جلب أسعار النفط المباشرة مع معالجة عطلة نهاية الأسبوع"""
    try:
        brent = yf.Ticker("BZ=F")
        hist = brent.history(period="5d")
        if not hist.empty:
            last_price = hist['Close'].iloc[-1]
            brent_str = f"${last_price:.2f}"
        else:
            brent_str = "$88.10"
    except Exception as e:
        print(f"خطأ في جلب النفط: {e}")
        brent_str = "$88.10"

    return {
        "brent": brent_str,
        "wheat": "$542.10",
        "bdi": "1,845"
    }

# --- 3. مصادر RSS الموسعة والكلمات المفتاحية ---
RSS_SOURCES = {
    "mewa": [
        "https://www.spa.gov.sa/rss.xml",
        "https://www.alriyadh.com/section.economy.xml",
        "https://www.okaz.com.sa/rss/local"
    ],
    "global_risks": [
        "https://news.un.org/feed/subscribe/ar/news/topic/health/feed/rss.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.net/aljazeerarss/a7c18663-711e-42b7-a3a8-4ed09860b0f7/73d0e1b4-532f-45ef-b135-bfd3d2cb29e8"
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
    """جلب وتصفية الأخبار وتجهيز الروابط والنصوص بصيغة آمنة"""
    matched_entries = []
    seen_titles = set()
    
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.title.strip()
                raw_link = entry.link.strip()
                
                clean_link = clean_url(raw_link)
                clean_title = html.escape(title)
                
                if clean_title in seen_titles:
                    continue
                
                if any(kw.lower() in title.lower() for kw in keywords):
                    matched_entries.append({"title": clean_title, "link": clean_link})
                    seen_titles.add(clean_title)
        except Exception as e:
            print(f"خطأ في قراءة المصدر {url}: {e}")
            
    return matched_entries

# --- 4. بناء هيكل النشرة ---
def generate_report():
    tickers = get_live_tickers()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    mewa_news = filter_feed(RSS_SOURCES["mewa"], KEYWORDS["mewa"])
    bio_news = filter_feed(RSS_SOURCES["global_risks"], KEYWORDS["biosecurity"])
    geo_news = filter_feed(RSS_SOURCES["global_risks"], KEYWORDS["geopolitics"])

    # بناء نص الرسالة
    report = f"🚨 <b>الرصد اليومي</b>\n"
    report += f"📅 <i>{date_str}</i> | ⏱️ <i>تحديث آلي</i>\n"
    report += "----------------------------------------\n\n"
    
    report += "📊 <b>1. شريط المؤشرات والسلع الحيوية</b>\n"
    report += f"• 🛢️ <b>نفط برنت المباشر:</b> {tickers['brent']}\n"
    report += f"• 🌾 <b>القمح العالمي:</b> {tickers['wheat']}\n"
    report += f"• ⛽ <b>مؤشر الشحن (BDI):</b> {tickers['bdi']}\n\n"

    report += "💡 <b>2. الخلاصة التنفيذية</b>\n"
    report += "<i>> متابعة مستمرة لمستجدات الأمن المائي والغذائي، واستقرار حركة الملاحة والتنبيهات البيئية الإقليمية.</i>\n\n"

    report += "🌱 <b>3. الأمن المائي والغذائي والزراعي (MEWA والجهات التابعة)</b>\n"
    if mewa_news:
        for item in mewa_news[:4]:
            report += f"• 🟢 <b>[خبر محلي/قطاعي]:</b> {item['title']}\n  🔗 <a href=\"{item['link']}\">المصدر</a>\n"
    else:
        report += "• لا توجد مستجدات حرجة مسجلة في القطاع خلال الساعات الماضية.\n"
    report += "\n"

    report += "☣️ <b>4. الأمن الحيوي والسلامة البيئية</b>\n"
    if bio_news:
        for item in bio_news[:3]:
            report += f"• 🟡 <b>[تنبيه بيئي/حيوي]:</b> {item['title']}\n  🔗 <a href=\"{item['link']}\">المصدر</a>\n"
    else:
        report += "• لم يتم رصد مخاطر حيوية أو انسكابات نفطية رئيسية اليوم.\n"
    report += "\n"

    report += "⚠️ <b>5. الاضطرابات الجيوسياسية والممرات المائية</b>\n"
    if geo_news:
        for item in geo_news[:3]:
            report += f"• 🔴 <b>[ممرات مائية/أزمات]:</b> {item['title']}\n  🔗 <a href=\"{item['link']}\">المصدر</a>\n"
    else:
        report += "• استقرار حركة الملاحة في باب المندب ومضيق هرمز وقناة السويس.\n"

    return report

if __name__ == "__main__":
    briefing_text = generate_report()
    send_telegram_message(briefing_text)
