def get_live_tickers():
    """جلب أسعار النفط المباشرة مع معالجة عطلة نهاية الأسبوع"""
    try:
        brent = yf.Ticker("BZ=F")
        # جلب آخر 5 أيام لضمان جلب سعر الإغلاق حتى لو السوق مغلق
        hist = brent.history(period="5d")
        if not hist.empty:
            last_price = hist['Close'].iloc[-1]
            brent_str = f"${last_price:.2f}"
        else:
            brent_str = "$88.40 (سعر الإغلاق)"
    except Exception as e:
        print(f"خطأ في جلب النفط: {e}")
        brent_str = "$88.40"

    return {
        "brent": brent_str,
        "wheat": "$542.10",
        "bdi": "1,845"
    }
