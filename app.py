from flask import Flask, request, render_template_string
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

API_KEY = "VJBAMA1G8WINZMQWU4BA9N157IUC2J2PMT"
TIERS = {
    2: 1, 4: 2, 8: 3, 16: 4, 32: 5,
    64: 6, 128: 7, 256: 8, 512: 9, 1024: 10,
    2048: 11, 4096: 12, 8192: 13, 16384: 14, 32768: 15,
    65536: 16, 131072: 17, 262144: 18, 524288: 19, 1048576: 20
}

def fetch_usdt_volume(address):
    url = f"https://api.bscscan.com/api?module=account&action=tokentx&address={address}&startblock=1&endblock=99999999&sort=desc&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    total = 0
    if data.get("status") == "1":
        utc = pytz.UTC
        now = datetime.now(utc)
        today0 = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=utc)
        start_ts = int(today0.timestamp())
        end_ts = start_ts + 86400

        for tx in data["result"]:
            if tx.get("tokenSymbol") != "BSC-USD":
                continue
            ts = int(tx["timeStamp"])
            if not (start_ts <= ts < end_ts):
                continue
            amount = float(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
            total += amount

    return round(total, 2)


def get_alpha_point(amount):
    point = 0
    next_tier = None
    for threshold, p in TIERS.items():
        if amount >= threshold:
            point = p
        else:
            next_tier = (threshold, p)
            break
    return point, next_tier

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>USDT 거래량 조회</title>
    <style>
        body { font-family: Arial; padding: 30px; }
        input { padding: 6px; width: 400px; }
        button { padding: 6px 12px; }
        p { font-size: 16px; }
        .highlight { background-color: #ffe6e6; font-weight: bold; color: red; }
        .next { margin-top: 20px; color: blue; font-weight: bold; }
        table { border-collapse: collapse; margin-top: 30px; }
        th, td { border: 1px solid #ccc; padding: 8px 12px; }
        th { background-color: #f2f2f2; }

        .progress-container {
            width: 100%;
            background-color: #eee;
            border-radius: 10px;
            margin-top: 10px;
            height: 24px;
            overflow: hidden;
            box-shadow: inset 0 0 5px #ccc;
        }

        .progress-bar {
            height: 100%;
            text-align: center;
            line-height: 24px;
            color: white;
            font-weight: bold;
            background-color: #4caf50;
        }
    </style>
</head>
<body>
    <h2>🪙 adggong.com 제공 BSC 지갑의 USDT 거래량 (UTC 오전 0시 기준 24시간)</h2>
    <form method="GET">
        지갑 주소: <input type="text" name="address" required value="{{ address or '' }}">
        <button type="submit">조회</button>
    </form>

    {% if total is not none %}
        <p><strong>총 USDT 거래량:</strong> ${{ "{:,.2f}".format(total) }}<strong>  현재 포인트:</strong> <span class="highlight">{{ point }}점</span></p>
        {% if next_tier %}
            {% set needed = next_tier[0] - total %}
            {% set percent = ((total - current_amt) / (next_tier[0] - current_amt)) * 100 %}
            {% set percent = 0 if percent < 0 else (100 if percent > 100 else percent) %}

            <p class="next">🎯 다음 포인트({{ next_tier[1] }}점)까지 남은 거래액: ${{ "{:,.2f}".format(needed) }} 
            (스왑 USDT: ${{ "{:,.2f}".format(needed / 2) }})</p>

            <div class="progress-container">
                <div class="progress-bar" style="width: {{ "{:.1f}".format(percent) }}%;">
                    {{ "{:.1f}".format(percent) }}%
                </div>
            </div>
        {% else %}
            <p class="next">🎉 최대 포인트(20점)에 도달했습니다!</p>
        {% endif %}

        <h3>📊 포인트</h3>
        <table>
            <tr>
                <th>누적액</th><th>포인트</th>
                <th style="padding-left: 40px;">누적액</th><th>포인트</th>
            </tr>
            {% set keys = tiers.keys() | list %}
            {% set mid = (tiers | length + 1) // 2 %}
            {% for i in range(mid) %}
                {% set left_amt = keys[i] %}
                {% set right_index = i + mid %}
                <tr>
                    <td {% if tiers[left_amt] == point %}class="highlight"{% endif %}>${{ "{:,}".format(left_amt) }}</td>
                    <td {% if tiers[left_amt] == point %}class="highlight"{% endif %}>{{ tiers[left_amt] }}점</td>

                    {% if right_index < tiers | length %}
                        {% set right_amt = keys[right_index] %}
                        <td {% if tiers[right_amt] == point %}class="highlight"{% endif %} style="padding-left: 40px;">${{ "{:,}".format(right_amt) }}</td>
                        <td {% if tiers[right_amt] == point %}class="highlight"{% endif %}>{{ tiers[right_amt] }}점</td>
                    {% else %}
                        <td></td><td></td>
                    {% endif %}
                </tr>
            {% endfor %}
        </table>


    {% elif address %}
        <p style="color:red;">해당 기간 동안 USDT 거래가 없습니다.</p>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    address = request.args.get("address", "").strip()
    total = None
    point = 0
    next_tier = None
    current_amt = 0
    if address:
        total = fetch_usdt_volume(address)
        point, next_tier = get_alpha_point(total)
        for amt, p in TIERS.items():
            if p == point:
                current_amt = amt
                break
    return render_template_string(
        HTML,
        address=address,
        total=total,
        point=point,
        next_tier=next_tier,
        tiers=TIERS,
        current_amt=current_amt
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
