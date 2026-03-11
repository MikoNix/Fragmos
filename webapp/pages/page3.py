import random
from time import time
import streamlit as st
import os


from pages.modules import util_sidebar
util_sidebar()

"# ТУТ нечего нет (пока что) "
random_image = random.randint(1, 2)
image_path = os.path.abspath(f'static/media/{random_image}.gif')
st.image(image_path, use_container_width=False) 