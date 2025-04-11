import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import io
import base64
from fpdf import FPDF
import random
import pandas as pd

# Veritabanı ayarları
Base = declarative_base()
engine = create_engine('sqlite:///fithole_clone.db')
Session = sessionmaker(bind=engine)
session = Session()

# Tablolar
class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    customer = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    cabinets = relationship("Cabinet", back_populates="project")

class Cabinet(Base):
    __tablename__ = 'cabinets'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    cabinet_type = Column(String)
    width = Column(Float)
    height = Column(Float)
    depth = Column(Float)
    material = Column(String)
    project = relationship("Project", back_populates="cabinets")
    parts = relationship("Part", back_populates="cabinet")

class Part(Base):
    __tablename__ = 'parts'
    id = Column(Integer, primary_key=True)
    cabinet_id = Column(Integer, ForeignKey('cabinets.id'))
    name = Column(String)
    width = Column(Float)
    height = Column(Float)
    quantity = Column(Integer)
    unit_price = Column(Float)  # Birim fiyat
    stock = Column(Integer)     # Stok durumu
    cabinet = relationship("Cabinet", back_populates="parts")

# Veritabanı oluştur
Base.metadata.create_all(engine)

# Streamlit arayüz
st.title("Fithole Klonu - Üretim Yönetimi")

# Menü
menu = st.sidebar.radio("Menü", ["Proje Oluştur", "Kabin Ekle", "Kabin Listesi", "Fiyatlandırma ve Stok", "Raporlar"])

# Yeni Proje Oluştur
if menu == "Proje Oluştur":
    with st.form("project_form"):
        st.subheader("Yeni Proje Oluştur")
        name = st.text_input("Proje Adı")
        customer = st.text_input("Müşteri Adı")
        submitted = st.form_submit_button("Projeyi Kaydet")
        if submitted and name and customer:
            new_project = Project(name=name, customer=customer)
            session.add(new_project)
            session.commit()
            st.success(f"Proje oluşturuldu: {name}")

# Kabin Ekleme
if menu == "Kabin Ekle":
    st.subheader("Projelere Kabin Ekle")
    projects = session.query(Project).all()
    project_options = {f"{p.name} - {p.customer}": p.id for p in projects}
    if projects:
        selected_project_label = st.selectbox("Proje Seç", list(project_options.keys()))
        selected_project_id = project_options[selected_project_label]
        with st.form("cabinet_form"):
            cabinet_type = st.selectbox("Kabin Türü", ["Mutfak", "Portmanto", "Banyo", "TV Ünitesi"])
            width = st.number_input("Genişlik (mm)", min_value=100.0)
            height = st.number_input("Yükseklik (mm)", min_value=100.0)
            depth = st.number_input("Derinlik (mm)", min_value=100.0)
            material = st.selectbox("Malzeme", ["Sunta", "MDF", "Lake", "Laminat"])
            submit_cabinet = st.form_submit_button("Kabin Ekle")
            if submit_cabinet:
                new_cabinet = Cabinet(
                    project_id=selected_project_id,
                    cabinet_type=cabinet_type,
                    width=width,
                    height=height,
                    depth=depth,
                    material=material
                )
                session.add(new_cabinet)
                session.commit()
                st.success("Kabin başarıyla eklendi.")
    else:
        st.info("Lütfen önce bir proje oluşturun.")

# Fiyatlandırma ve Stok Yönetimi
if menu == "Fiyatlandırma ve Stok":
    st.subheader("Fiyat ve Stok Yönetimi")
    cabinets = session.query(Cabinet).all()
    if cabinets:
        selected_cabinet = st.selectbox("Kabin Seç", [f"{c.id} - {c.cabinet_type}" for c in cabinets])
        selected_cabinet_id = int(selected_cabinet.split(" - ")[0])
        parts = session.query(Part).filter_by(cabinet_id=selected_cabinet_id).all()
        for part in parts:
            st.write(f"**Parça Adı:** {part.name}")
            st.write(f"Genişlik: {part.width} mm, Yükseklik: {part.height} mm")
            st.write(f"Stok: {part.stock} adet")
            st.write(f"Birim Fiyat: {part.unit_price} TL")
            st.write(f"Toplam Maliyet: {part.quantity * part.unit_price} TL")
    else:
        st.info("Lütfen önce bir kabin ekleyin.")

# Raporlama
if menu == "Raporlar":
    st.subheader("Üretim Raporları")
    reports = []
    cabinets = session.query(Cabinet).all()
    if cabinets:
        for cab in cabinets:
            parts = session.query(Part).filter_by(cabinet_id=cab.id).all()
            total_cost = 0
            for part in parts:
                total_cost += part.quantity * part.unit_price
            reports.append({
                "Kabin Türü": cab.cabinet_type,
                "Toplam Parça Maliyeti": total_cost
            })
        df = pd.DataFrame(reports)
        st.dataframe(df)
    else:
        st.info("Henüz eklenmiş bir kabin yok.")
