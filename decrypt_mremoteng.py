import sys
import os
import base64
import hashlib
import logging
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from Crypto.Cipher import AES
from pathlib import Path
from lib.logging_util import setup_logger


def init_logger():
    script_file_path = Path(__file__)
    work_dir = script_file_path.parent
    script_name = script_file_path.stem

    setup_logger(work_dir / "logs" / f"{script_name}.log")
    logging.getLogger()


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
    init_logger()

    parser = ArgumentParser(description="decrypt mremoteng confCons.xml")
    parser.add_argument("file", help="path to mremoteng confCons.xml")
    args = parser.parse_args()

    try:
        file_path = Path(args.file)
        if not file_path.exists():
            logging.critical(f"error: file '{file_path}' not found")
            sys.exit(1)

        tree = process_xml_file(file_path)

        output_path = f"{file_path.stem}_decrypted{file_path.suffix}"
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        logging.info(f"decrypted file saved to: {output_path}")
    except Exception as e:
        logging.critical(f"error processing file: {e}", exc_info=True)


if __name__ == "__main__":
    main()
