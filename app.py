
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import io
import uuid

# =========================================================
# 1. CẤU HÌNH TRANG
# =========================================================
st.set_page_config(
    page_title="MR BÌNH | Milk Tea POS",
    page_icon="🧋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. CSS - GIAO DIỆN RỰC RỠ
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}
.stApp {
    background: linear-gradient(135deg, #fff0f5 0%, #fff8e7 48%, #f1eaff 100%);
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}
.hero {
    background: linear-gradient(120deg, #ff4d8d, #9b5de5, #ff914d);
    padding: 30px 24px;
    border-radius: 24px;
    color: white;
    text-align: center;
    box-shadow: 0 10px 30px #c75b8b33;
    margin-bottom: 22px;
}
.hero h1 {
    font-size: 42px;
    font-weight: 900;
    margin: 0;
}
.hero p {
    font-size: 17px;
    margin: 8px 0 0;
}
.section-title {
    color: #8529a6;
    font-weight: 900;
    font-size: 23px;
    padding-bottom: 8px;
}
.metric-card {
    background: white;
    padding: 18px;
    border-radius: 18px;
    border-left: 6px solid #ff4d8d;
    box-shadow: 0 5px 18px #70205012;
    margin-bottom: 10px;
}
.metric-label {
    color: #777;
    font-size: 14px;
    font-weight: 700;
}
.metric-value {
    color: #8b35b5;
    font-size: 25px;
    font-weight: 900;
}
.menu-card {
    background: white;
    padding: 15px;
    border-radius: 16px;
    border: 1px solid #f5d9ed;
    margin-bottom: 10px;
}
div.stButton > button {
    border-radius: 12px;
    font-weight: 800;
    border: none;
    transition: 0.2s;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #ff4d8d, #a855f7);
    color: white;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px #9b5de533;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffe0ed, #f0e5ff);
}
div[data-testid="stDataFrame"] {
    border-radius: 14px;
}
div[data-testid="stMetric"] {
    background: white;
    border-radius: 15px;
    padding: 14px;
    border: 1px solid #f3d9ed;
}
hr {
    border-color: #edc7e6;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. MENU VÀ BẢNG GIÁ
# =========================================================
MENU_TEA = {
    "Trà Sữa Truyền Thống": 30000,
    "Trà Sữa Trân Châu Đường Đen": 35000,
    "Trà Sữa Thái Xanh": 32000,
    "Trà Sữa Ô Long": 35000,
    "Trà Sữa Matcha": 38000,
    "Trà Sữa Dâu Tây": 35000,
    "Trà Đào Cam Sả": 35000,
    "Trà Dâu Tằm": 32000,
}

SIZE_OPTIONS = {
    "S": 0,
    "M": 5000,
    "L": 10000
}

TOPPING_OPTIONS = {
    "Trân châu đen": 5000,
    "Trân châu trắng": 7000,
    "Thạch trái cây": 5000,
    "Pudding trứng": 8000,
    "Kem Cheese": 10000
}

SUGAR_LEVELS = ["100%", "70%", "50%", "30%", "0%"]
ICE_LEVELS = ["100%", "70%", "50%", "30%", "0%"]

# =========================================================
# 4. KHỞI TẠO DỮ LIỆU PHIÊN
# =========================================================
if "cart" not in st.session_state:
    st.session_state.cart = []

if "history" not in st.session_state:
    st.session_state.history = []

if "paid_invoice" not in st.session_state:
    st.session_state.paid_invoice = None

if "order_counter" not in st.session_state:
    st.session_state.order_counter = 0

def money(value):
    return f"{int(value):,} đ"

def reset_payment():
    st.session_state.paid_invoice = None

# =========================================================
# 5. HÀM TẠO HÓA ĐƠN TXT
# =========================================================
def create_invoice_text(invoice):
    lines = [
        "=" * 45,
        "MR BINH MILK TEA".center(45),
        "HOA DON BAN HANG".center(45),
        "=" * 45,
        f"Ma don: {invoice['order_id']}",
        f"Thoi gian: {invoice['time']}",
        f"Khach hang: {invoice['customer']}",
        "-" * 45,
    ]

    for i, item in enumerate(invoice["cart"], start=1):
        lines.append(f"{i}. {item['Tên món']} - Size {item['Size']}")
        lines.append(f"   Duong: {item['Đường']} | Da: {item['Đá']}")
        lines.append(f"   Topping: {item['Topping']}")
        lines.append(
            f"   {item['Số lượng']} x {money(item['Đơn giá'])}"
            f" = {money(item['Thành tiền'])}"
        )

    lines += [
        "-" * 45,
        f"Tong tien: {money(invoice['total'])}",
        f"Giam gia: {invoice['discount']}%",
        f"Khach can tra: {money(invoice['final'])}",
        f"Khach dua: {money(invoice['cash'])}",
        f"Tien thua: {money(invoice['change'])}",
        "=" * 45,
        "Cam on quy khach!".center(45),
        "Hen gap lai!".center(45),
    ]
    return "\n".join(lines)

# =========================================================
# 6. HEADER
# =========================================================
logo_path = Path("TRASUA.jpg")

if logo_path.exists():
    st.image(str(logo_path), use_container_width=True)

st.markdown("""
<div class="hero">
    <h1>🧋 MR BÌNH MILK TEA 🌈</h1>
    <p>Thêm topping - Thêm niềm vui - Năng lượng mỗi ngày!</p>
    <p>✨ ORDER • PAYMENT • SALES MANAGEMENT ✨</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 7. SIDEBAR - MENU THAM KHẢO
# =========================================================
with st.sidebar:
    st.markdown("## 🍓 MENU NHÀ MR BÌNH")
    st.caption("Bảng giá tham khảo - đơn vị VNĐ")

    for name, price in MENU_TEA.items():
        st.markdown(
            f"<div class='menu-card'>"
            f"<b>🧋 {name}</b><br>"
            f"<span style='color:#ed4085;font-weight:900'>"
            f"{money(price)}</span></div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 📏 Phụ thu size")
    for size, price in SIZE_OPTIONS.items():
        st.write(f"Size {size}: +{money(price)}")

    st.markdown("### 🍮 Giá topping")
    for topping, price in TOPPING_OPTIONS.items():
        st.write(f"{topping}: {money(price)}")

    st.markdown("---")
    st.caption("MR BÌNH MILK TEA • POS DEMO")

# =========================================================
# 8. THỐNG KÊ DOANH THU
# =========================================================
paid_orders = st.session_state.history
revenue = sum(o["final"] for o in paid_orders)
order_count = len(paid_orders)
cups_sold = sum(
    item["Số lượng"]
    for order in paid_orders
    for item in order["cart"]
)

m1, m2, m3 = st.columns(3)

with m1:
    st.metric("💰 Doanh thu phiên", money(revenue))

with m2:
    st.metric("🧾 Đơn đã thanh toán", order_count)

with m3:
    st.metric("🥤 Số ly đã bán", cups_sold)

st.markdown("---")

# =========================================================
# 9. GIAO DIỆN BÁN HÀNG
# =========================================================
col_left, col_right = st.columns([1, 1.1], gap="large")

with col_left:
    st.markdown(
        '<div class="section-title">📝 TẠO ĐƠN HÀNG</div>',
        unsafe_allow_html=True
    )

    customer_name = st.text_input(
        "👤 Tên khách hàng",
        placeholder="Nhập tên hoặc để trống nếu khách vãng lai",
        key="customer_name"
    )

    st.markdown("#### 🧋 Chọn món yêu thích")

    selected_tea = st.selectbox(
        "Loại đồ uống",
        list(MENU_TEA.keys())
    )

    quantity = st.number_input(
        "Số lượng ly",
        min_value=1,
        max_value=100,
        value=1,
        step=1
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        selected_size = st.selectbox("📏 Size", list(SIZE_OPTIONS.keys()))

    with c2:
        selected_sugar = st.selectbox("🍯 Đường", SUGAR_LEVELS)

    with c3:
        selected_ice = st.selectbox("🧊 Đá", ICE_LEVELS)

    selected_toppings = st.multiselect(
        "🍮 Topping (có thể chọn nhiều)",
        list(TOPPING_OPTIONS.keys())
    )

    base_price = MENU_TEA[selected_tea]
    size_price = SIZE_OPTIONS[selected_size]
    topping_price = sum(
        TOPPING_OPTIONS[t] for t in selected_toppings
    )

    unit_price = base_price + size_price + topping_price
    item_total = unit_price * quantity

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">GIÁ MỖI LY</div>
        <div class="metric-value">{money(unit_price)}</div>
        <div>📦 Thành tiền: <b>{money(item_total)}</b></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "➕ THÊM VÀO GIỎ HÀNG",
        type="primary",
        use_container_width=True
    ):
        item = {
            "id": uuid.uuid4().hex[:8],
            "Tên món": selected_tea,
            "Size": selected_size,
            "Đường": selected_sugar,
            "Đá": selected_ice,
            "Topping": ", ".join(selected_toppings)
                        if selected_toppings else "Không",
            "Đơn giá": unit_price,
            "Số lượng": int(quantity),
            "Thành tiền": item_total,
        }

        st.session_state.cart.append(item)
        reset_payment()
        st.toast("Đã thêm món vào giỏ hàng! 🎉")
        st.rerun()

with col_right:
    st.markdown(
        '<div class="section-title">🛒 GIỎ HÀNG CỦA BẠN</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.cart:
        st.info("🧋 Chưa có món nào. Hãy chọn món ở bên trái nhé!")
    else:
        cart = st.session_state.cart

        df_cart = pd.DataFrame(cart)

        st.dataframe(
            df_cart[
                ["Tên món", "Size", "Topping",
                 "Số lượng", "Đơn giá", "Thành tiền"]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Đơn giá": st.column_config.NumberColumn(
                    "Đơn giá", format="%d đ"
                ),
                "Thành tiền": st.column_config.NumberColumn(
                    "Thành tiền", format="%d đ"
                ),
            }
        )

        st.markdown("#### 🗑️ Điều chỉnh giỏ hàng")

        for item in list(st.session_state.cart):
            a, b = st.columns([4, 1])

            with a:
                st.write(
                    f"**{item['Tên món']}** · Size {item['Size']} "
                    f"· SL: {item['Số lượng']}"
                )

            with b:
                if st.button(
                    "❌",
                    key=f"delete_{item['id']}",
                    help="Xóa món này"
                ):
                    st.session_state.cart = [
                        x for x in st.session_state.cart
                        if x["id"] != item["id"]
                    ]
                    reset_payment()
                    st.rerun()

        if st.button("🧹 XÓA TOÀN BỘ GIỎ HÀNG"):
            st.session_state.cart = []
            reset_payment()
            st.rerun()

        st.markdown("---")

        total_price = sum(
            item["Thành tiền"] for item in st.session_state.cart
        )

        discount = st.number_input(
            "🎁 Giảm giá (%)",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
            key="discount"
        )

        final_price = round(total_price * (100 - discount) / 100)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">TỔNG TIỀN MÓN</div>
            <div class="metric-value">{money(total_price)}</div>
            <div>🎁 Giảm giá: {discount}%</div>
            <hr>
            <div class="metric-label">KHÁCH CẦN THANH TOÁN</div>
            <div class="metric-value" style="color:#ff4081">
                {money(final_price)}
            </div>
        </div>
        """, unsafe_allow_html=True)

        cash_received = st.number_input(
            "💵 Tiền khách đưa (VNĐ)",
            min_value=0,
            value=0,
            step=10000,
            key="cash_received"
        )

        change = int(cash_received - final_price)

        if cash_received < final_price:
            st.warning(
                f"Còn thiếu {money(final_price - cash_received)}"
            )
        else:
            st.success(f"💸 Tiền thừa: {money(change)}")

        if st.button(
            "💳 XÁC NHẬN THANH TOÁN",
            type="primary",
            use_container_width=True
        ):
            if cash_received < final_price:
                st.error("Tiền khách đưa chưa đủ để thanh toán!")
            else:
                st.session_state.order_counter += 1

                invoice = {
                    "order_id": (
                        f"MRB{datetime.now().strftime('%Y%m%d')}-"
                        f"{st.session_state.order_counter:04d}"
                    ),
                    "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "customer": customer_name.strip()
                                or "Khách vãng lai",
                    "cart": [dict(item)
                             for item in st.session_state.cart],
                    "total": int(total_price),
                    "discount": int(discount),
                    "final": int(final_price),
                    "cash": int(cash_received),
                    "change": int(change),
                }

                st.session_state.paid_invoice = invoice
                st.session_state.history.append(invoice)
                st.balloons()
                st.rerun()

# =========================================================
# 10. HÓA ĐƠN SAU THANH TOÁN
# =========================================================
invoice = st.session_state.paid_invoice

if invoice:
    st.markdown("---")
    st.markdown(
        '<div class="section-title">🎉 THANH TOÁN THÀNH CÔNG</div>',
        unsafe_allow_html=True
    )

    st.success(f"Đơn hàng {invoice['order_id']} đã được ghi nhận.")

    with st.container(border=True):
        st.markdown(
            "<h2 style='text-align:center;color:#e83e8c'>"
            "🧋 MR BÌNH MILK TEA</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center'>"
            "HÓA ĐƠN THANH TOÁN</p>",
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:
            st.write(f"**Mã đơn:** {invoice['order_id']}")
            st.write(f"**Khách hàng:** {invoice['customer']}")

        with c2:
            st.write(f"**Thời gian:** {invoice['time']}")
            st.write(f"**Trạng thái:** Đã thanh toán")

        st.dataframe(
            pd.DataFrame(invoice["cart"])[
                ["Tên món", "Size", "Đường", "Đá",
                 "Topping", "Số lượng", "Đơn giá", "Thành tiền"]
            ],
            use_container_width=True,
            hide_index=True
        )

        x, y = st.columns(2)

        with x:
            st.write(f"Tiền món: **{money(invoice['total'])}**")
            st.write(f"Giảm giá: **{invoice['discount']}%**")
            st.write(f"Khách đưa: **{money(invoice['cash'])}**")

        with y:
            st.markdown(
                f"<h3 style='color:#ed4085'>"
                f"THANH TOÁN: {money(invoice['final'])}</h3>",
                unsafe_allow_html=True
            )
            st.write(f"Tiền thừa: **{money(invoice['change'])}**")

        st.markdown(
            "<p style='text-align:center;color:#8b35b5'>"
            "💖 Cảm ơn quý khách và hẹn gặp lại! 💖</p>",
            unsafe_allow_html=True
        )

    invoice_text = create_invoice_text(invoice)

    dl1, dl2 = st.columns(2)

    with dl1:
        st.download_button(
            "📥 TẢI HÓA ĐƠN TXT",
            data=invoice_text,
            file_name=f"{invoice['order_id']}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with dl2:
        order_csv = pd.DataFrame(invoice["cart"]).drop(
            columns=["id"], errors="ignore"
        ).to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "📊 TẢI CHI TIẾT MÓN CSV",
            data=order_csv,
            file_name=f"{invoice['order_id']}_chitiet.csv",
            mime="text/csv",
            use_container_width=True
        )

    if st.button(
        "🔄 BẮT ĐẦU ĐƠN HÀNG MỚI",
        type="primary",
        use_container_width=True
    ):
        st.session_state.cart = []
        st.session_state.paid_invoice = None
        st.session_state["customer_name"] = ""
        st.session_state["cash_received"] = 0
        st.session_state["discount"] = 0
        st.rerun()

# =========================================================
# 11. LỊCH SỬ BÁN HÀNG
# =========================================================
st.markdown("---")
st.markdown(
    '<div class="section-title">📈 LỊCH SỬ BÁN HÀNG</div>',
    unsafe_allow_html=True
)

if st.session_state.history:
    history_rows = []

    for order in st.session_state.history:
        history_rows.append({
            "Mã đơn": order["order_id"],
            "Thời gian": order["time"],
            "Khách hàng": order["customer"],
            "Số ly": sum(i["Số lượng"] for i in order["cart"]),
            "Tổng tiền": order["total"],
            "Giảm giá (%)": order["discount"],
            "Thanh toán": order["final"],
        })

    df_history = pd.DataFrame(history_rows)

    st.dataframe(
        df_history,
        use_container_width=True,
        hide_index=True
    )

    history_csv = df_history.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "📥 XUẤT BÁO CÁO DOANH THU CSV",
        data=history_csv,
        file_name=f"BaoCao_MRBINH_{datetime.now():%Y%m%d_%H%M%S}.csv",
        mime="text/csv"
    )

else:
    st.info("📊 Chưa có đơn hàng thanh toán trong phiên này.")

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#a05aa5'>"
    "🧋 MR BÌNH MILK TEA · Made with 💗 and Streamlit"
    "</div>",
    unsafe_allow_html=True
)
