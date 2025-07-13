import qrcode

# Dirección IP local del servidor Flask (la de tu laptop)
ip_local = "192.168.1.25"
url = f"http://{ip_local}:5000/visitante"

# Generar el código QR
qr = qrcode.make(url)

# Guardarlo como imagen
qr.save("qr_visitante.png")

print(f"Código QR generado para: {url}")

