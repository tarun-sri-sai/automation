from lib.azure_cert import convert_pfx_to_pri_key


def get_credential(client_id, tenant_id, certificate_file, thumbprint,
                   certificate_password):
    private_key = convert_pfx_to_pri_key(certificate_file, certificate_password)

    return {
        "tenant": tenant_id,
        "client_id": client_id,
        "thumbprint": thumbprint,
        "private_key": private_key,
    }
