import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict
import re

class PiguAPIError(Exception):
    """Exception personnalisée pour les erreurs de l'API Pigu"""
    pass

class PiguClient:
    def __init__(self, username: str, password: str, seller_id: str):
        """Initialise le client avec les identifiants"""
        self.username = username
        self.password = password
        self.seller_id = seller_id
        self.token = None

    def _login(self) -> str:
        """Authentifie le client auprès de l'API"""
        headers = {"Content-Type": "application/json"}
        body = {"username": self.username, "password": self.password}

        try:
            response = requests.post(
                "https://pmpapi.pigugroup.eu/v3/login",
                headers=headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()

            token = response.json().get("token")
            if not token:
                raise PiguAPIError("Token d'authentification manquant")
            return token

        except requests.RequestException as e:
            raise PiguAPIError(f"Erreur d'authentification : {str(e)}")

    def fetch_offers(self) -> List[Dict]:
        """Récupère les offres du vendeur"""
        if not self.token:
            self.token = self._login()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Pigu-mp {self.token}"
        }

        params = {"amount_from": "1", "page_size": 100}
        url = f"https://pmpapi.pigugroup.eu/v3/sellers/{self.seller_id}/offers"
        offers_data = []

        st.write("🔄 Récupération des offres en cours...")
        progress_bar = st.progress(0)

        page_count = 0
        max_pages = 100

        while True:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                offers_batch = data.get("offers", [])
                offers_data.extend(offers_batch)

                page_count += 1
                progress = min(page_count / max_pages, 1.0)
                progress_bar.progress(progress)

                next_url = data.get("meta", {}).get("next")
                if not next_url:
                    break

                url = next_url
                # st.write(f"✨ Progression : {len(offers_data)} offres traitées")

            except requests.RequestException as e:
                raise PiguAPIError(f"Erreur de récupération des offres : {str(e)}")

        st.write(f"\n✅ Récupération terminée ! {len(offers_data)} offres trouvées.")
        progress_bar.progress(1.0)
        return offers_data

def main():
    """Fonction principale de l'application"""
    st.title("Extraction des Offres PHH")
    st.sidebar.header("Paramètres de Connexion")

    seller_id = st.sidebar.text_input("Identifiant Vendeur", value="")
    username = st.sidebar.text_input("Nom d'utilisateur", value="")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if st.sidebar.button("Extraire les Offres"):
        try:
            client = PiguClient(username, password, seller_id)
            offers = client.fetch_offers()
            df = pd.json_normalize(offers)

            st.write("\n📋 Aperçu des offres récupérées :")
            st.dataframe(df)  # L'icône de téléchargement CSV est automatiquement incluse

        except PiguAPIError as e:
            st.error(f"Erreur : {str(e)}")

if __name__ == "__main__":
    main()
