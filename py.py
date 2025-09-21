import streamlit as st
import pandas as pd
import plotly.express as px
import io
import pyrebase
import datetime

firebaseConfig = {
  "apiKey": "AIzaSyDGep9N3G7podp7Uk61VrXodkUprBXNI04",
  "authDomain": "takipapp-957e7.firebaseapp.com",
  "databaseURL": "https://takipapp-957e7-default-rtdb.firebaseio.com",
  "projectId": "takipapp-957e7",
  "storageBucket": "takipapp-957e7.appspot.com",
  "messagingSenderId": "436837321759",
  "appId": "1:436837321759:web:a96a59929e301a6916592a",
  "measurementId": "G-PVC8VCLREM"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

if "user" not in st.session_state:
    st.session_state.user = None
if "menu" not in st.session_state:
    st.session_state.menu = "Giriş"
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Tarih","Kategori","Tip","Miktar","Hedef"])

menu = st.sidebar.selectbox("Menü", ["Giriş", "Kayıt Ol", "Dashboard", "Sohbet"], index=["Giriş","Kayıt Ol","Dashboard","Sohbet"].index(st.session_state.menu))

if menu == "Kayıt Ol":
    st.subheader("🔑 Kayıt Ol")
    email = st.text_input("Email")
    password = st.text_input("Şifre", type="password")
    if st.button("Kayıt Ol"):
        try:
            user = auth.create_user_with_email_and_password(email, password)
            st.success("✅ Kayıt başarılı! Giriş yapabilirsiniz.")
        except Exception as e:
            st.error(f"Hata: {e}")

elif menu == "Giriş":
    st.subheader("🔑 Giriş Yap")
    email = st.text_input("Email")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.session_state.username = user["email"].split("@")[0]
            st.success("✅ Giriş başarılı! Dashboard'a yönlendiriliyorsunuz...")
            st.session_state.menu = "Dashboard"
            st.rerun()
        except Exception as e:
            st.error(f"Hata: {e}")

elif menu == "Dashboard" and st.session_state.user:
    st.title("📊 Dashboard")
    st.sidebar.header("📥 Veri Girişi")

    kategori = st.sidebar.text_input("Kategori")
    tip = st.sidebar.selectbox("Tip", ["Süre (saat)", "Adet", "Net"])
    miktar = st.sidebar.number_input("Miktar", 0.0, step=0.5)
    hedef = st.sidebar.number_input("Hedef", 0.0, step=0.5)
    tarih = st.sidebar.date_input("Tarih", datetime.date.today())

    if st.sidebar.button("Ekle"):
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([{
            "Tarih": pd.to_datetime(tarih),
            "Kategori": kategori,
            "Tip": tip,
            "Miktar": float(miktar),
            "Hedef": float(hedef)
        }])], ignore_index=True)
        st.success("✅ Veri eklendi!")

    st.dataframe(st.session_state.data)

    if not st.session_state.data.empty:
        fig = px.line(st.session_state.data, x="Tarih", y="Miktar", color="Kategori",
                      markers=True, line_shape="spline")
        st.plotly_chart(fig, use_container_width=True)

elif menu == "Sohbet" and st.session_state.user:
    st.title("💬 Sohbet Alanı")

    msg = st.text_input("Mesajınız")
    if st.button("Gönder"):
        db.child("messages").push({
            "user": st.session_state.username,
            "msg": msg,
            "time": str(datetime.datetime.now())
        })
        st.success("📨 Mesaj gönderildi!")

    if st.button("📊 İstatistik Paylaş"):
        if not st.session_state.data.empty:
            toplam = round(st.session_state.data["Miktar"].sum(),2)
            ort = round(st.session_state.data["Miktar"].mean(),2)
            hedef = round(st.session_state.data["Hedef"].sum(),2)
            icerik = f"📈 İstatistiklerim → Toplam: {toplam}, Ortalama: {ort}, Hedef: {hedef}"
            db.child("messages").push({
                "user": st.session_state.username,
                "msg": icerik,
                "time": str(datetime.datetime.now())
            })
            st.success("📨 İstatistikler paylaşıldı!")

    file = st.file_uploader("Dosya Yükle", type=["png","jpg","mp4","pdf"])
    if file and st.button("Yükle"):
        path_on_cloud = f"uploads/{file.name}"
        storage.child(path_on_cloud).put(file, st.session_state.user['idToken'])
        st.success("✅ Dosya yüklendi!")

    st.subheader("📜 Mesajlar")
    messages = db.child("messages").get()
    if messages.each():
        for m in messages.each():
            st.write(f"**{m.val()['user']}**: {m.val()['msg']} ({m.val()['time']})")
