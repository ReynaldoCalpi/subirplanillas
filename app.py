import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# 1. Carga de credenciales (asegúrate de tener tu archivo config.yaml listo)
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 2. Inicialización del autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 3. Interfaz de Login
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    st.sidebar.success(f'Bienvenido, {name}')
    authenticator.logout('Cerrar sesión', 'sidebar')
    
    st.title("Bienvenido a [Nombre de tu Firma]")
    st.write("Selecciona una opción en el menú lateral.")
    
elif authentication_status == False:
    st.error('Usuario o contraseña incorrectos')
elif authentication_status == None:
    st.warning('Por favor, ingresa tus credenciales')