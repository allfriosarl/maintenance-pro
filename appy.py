import streamlit as st
from supabase import create_client
import qrcode
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import base64

# 1. Connexion à Supabase
url = "https://rayuufirgcbaxwhsxluv.supabase.co"
key = "VOTRE_CLE_ANON_ICI"
supabase = create_client(url, key)

st.set_page_config(page_title="ReparApp Mobile", layout="centered")

st.title("🛠️ Gestion de Réparation")

# Choix du technicien
tech_name = st.selectbox("Qui êtes-vous ?", ["Amine", "Karim"])

# --- PILIER 1 : IDENTIFICATION ---
st.subheader("1. Identification de la machine")
qr_input = st.text_input("Scannez ou saisissez l'ID QR")

if qr_input:
    # On cherche si la machine existe déjà
    res = supabase.table("machines").select("*").eq("id_qr", qr_input).execute()
    
    if len(res.data) == 0:
        st.warning("⚠️ Machine inconnue. Création d'une nouvelle fiche...")
        modele = st.text_input("Modèle de l'appareil")
        client = st.text_input("Nom du client")
        if st.button("Enregistrer & Imprimer QR"):
            supabase.table("machines").insert({"id_qr": qr_input, "modele": modele, "client_nom": client}).execute()
            st.success("Machine enregistrée !")
            # Génération visuelle du QR pour test
            qr_img = qrcode.make(qr_input)
            st.image(qr_img.get_image(), caption="Collez ce code sur la machine", width=150)
    else:
        machine = res.data[0]
        st.success(f"✅ Machine reconnue : {machine['modele']} - Client : {machine['client_nom']}")

        # --- PILIER 2 & 3 : STOCK & INTERVENTION ---
        st.subheader("2. Détails de la réparation")
        panne = st.text_area("Description du problème")
        
        # Récupération du stock du technicien
        stock_res = supabase.table("stocks").select("nom_piece").eq("technicien_nom", tech_name).execute()
        liste_pieces = [item['nom_piece'] for item in stock_res.data]
        piece_choisie = st.selectbox("Pièce utilisée", liste_pieces)
        prix = st.number_input("Prix total (€)", min_value=0)

        # --- PILIER 5 : SIGNATURE ---
        st.subheader("3. Signature Client")
        canvas_result = st_canvas(
            stroke_width=3, stroke_color="#000", background_color="#eee",
            height=150, update_streamlit=True, key="canvas"
        )

        if st.button("Finaliser l'intervention"):
            # Déduction du stock
            supabase.rpc('deduire_stock', {'p_piece': piece_choisie, 'p_tech': tech_name}).execute()
            
            # Enregistrement intervention
            supabase.table("interventions").insert({
                "machine_id": qr_input,
                "technicien_nom": tech_name,
                "panne_constatee": panne,
                "piece_utilisee": piece_choisie,
                "prix_total": prix
            }).execute()
            
            st.balloons()
            st.success("Intervention validée et stock mis à jour !")