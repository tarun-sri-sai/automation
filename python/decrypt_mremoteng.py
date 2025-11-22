import sys
import os
import base64
import hashlib
import xml.etree.ElementTree as ET
from traceback import print_exc
from Crypto.Cipher import AES


def decrypt_password(encrypted_password, encryption_key="mR3m"):
    if not encrypted_password:
        return ""

    try:
        encrypted_data = base64.b64decode(encrypted_password)

        salt = encrypted_data[:16]
        associated_data = encrypted_data[:16]
        nonce = encrypted_data[16:32]
        ciphertext = encrypted_data[32:-16]
        tag = encrypted_data[-16:]

        key = hashlib.pbkdf2_hmac(
            "sha1", 
            encryption_key.encode(), 
            salt, 
            1000, 
            dklen=32
        )

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        cipher.update(associated_data)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        return plaintext.decode("utf-8")
    except Exception:
        print_exc()
        return "[DECRYPTION FAILED]"


def process_xml_file(input_path):
    tree = ET.parse(input_path)
    root = tree.getroot()

    for node in root.findall(".//Node"):
        if "Password" in node.attrib:
            encrypted_password = node.attrib["Password"]
            if encrypted_password:
                decrypted_password = decrypt_password(encrypted_password)
                node.attrib["Password"] = decrypted_password

    return tree


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_mremoteng_xml>")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"Error: File '{input_path}' not found")
        sys.exit(1)

    base_path, ext = os.path.splitext(input_path)
    output_path = f"{os.path.basename(base_path)}_decrypted{ext}"

    try:
        tree = process_xml_file(input_path)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"Decrypted file saved to: {output_path}")
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
