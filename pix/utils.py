import qrcode
from io import BytesIO
import base64


def generate_pix_qr_code(pix_key, amount=None):
    qr_data = f"PIX:{pix_key}"
    if amount:
        qr_data += f":AMOUNT:{amount}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer.getvalue()


def generate_pix_qr_code_base64(pix_key, amount=None):
    qr_bytes = generate_pix_qr_code(pix_key, amount)
    return base64.b64encode(qr_bytes).decode('utf-8')


def read_pix_qr_code(image_path):
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image

        img = Image.open(image_path)
        decoded_objects = decode(img)

        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
        return None
    except Exception as e:
        return None
