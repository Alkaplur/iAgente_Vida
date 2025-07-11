# 🎨 Cómo Añadir tu Logo a iAgente_Vida

## 📋 Pasos para añadir tu logo:

### **Opción 1: Usar GitHub (Recomendada)**

1. **Subir logo al repositorio:**
   ```
   assets/
   └── logo.png    # Tu logo aquí
   ```

2. **Obtener URL del logo:**
   ```
   https://raw.githubusercontent.com/tu-usuario/iAgente_Vida/main/assets/logo.png
   ```

3. **Actualizar streamlit_app.py línea 68:**
   ```python
   st.image("https://raw.githubusercontent.com/tu-usuario/iAgente_Vida/main/assets/logo.png", width=150)
   ```

### **Opción 2: Usar Imgur (Gratis)**

1. **Ir a [imgur.com](https://imgur.com)**
2. **Subir tu logo**
3. **Copiar "Direct link"**
4. **Reemplazar en streamlit_app.py línea 68**

### **Opción 3: Usar Cloudinary (Profesional)**

1. **Crear cuenta en [cloudinary.com](https://cloudinary.com)**
2. **Subir logo**
3. **Copiar URL pública**
4. **Usar en streamlit_app.py**

## 🎯 Especificaciones del Logo:

### **Tamaño recomendado:**
- **Ancho:** 300-600px
- **Alto:** 100-200px
- **Formato:** PNG (fondo transparente) o SVG

### **Estilo sugerido:**
- **Colores:** Azul (#0066cc) y gris (#666) para consistencia
- **Fondo:** Transparente
- **Estilo:** Profesional, clean, legible

## 🔄 Actualización Rápida:

**Reemplaza la línea 68 en `streamlit_app.py`:**

```python
# ANTES:
st.image("https://i.imgur.com/placeholder.png", width=150)

# DESPUÉS:
st.image("TU_URL_DEL_LOGO_AQUÍ", width=150)
```

## 📱 Ejemplos de URLs válidas:

```
# GitHub:
https://raw.githubusercontent.com/tu-usuario/iAgente_Vida/main/assets/logo.png

# Imgur:
https://i.imgur.com/AbC123.png

# Cloudinary:
https://res.cloudinary.com/tu-cloud/image/upload/v123/logo.png
```

## 🎨 Logo Temporal:

Mientras preparas tu logo, puedes usar estos emojis:
```python
st.markdown("🤖💼🛡️", unsafe_allow_html=True)  # Robot + Maletín + Escudo
```

---

**¡Una vez tengas el logo listo, solo cambia una línea y estará visible en toda la aplicación!** 🚀