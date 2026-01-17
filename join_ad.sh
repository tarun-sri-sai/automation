#!/usr/bin/env bash

echo "Usage: $0 --domain <domain> --user <domain_user>"

log() { echo "[INFO] $1"; }

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --domain) DOMAIN="$2"; shift ;;
        --user) DOMAIN_USER="$2"; shift ;;
        *) echo "[ERROR] Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$DOMAIN" || -z "$DOMAIN_USER" ]]; then exit 1; fi

log "Joining domain"
realm join -v "$DOMAIN" -U "$DOMAIN_USER"

log "Validating user"
getent passwd "${DOMAIN_USER}@${DOMAIN}"

SSSD_CONF="/etc/sssd/sssd.conf"

log "Updating sssd.conf"
sed -i "s/^default_domain_suffix.*/default_domain_suffix = $DOMAIN/" "$SSSD_CONF"
sed -i "s|^fallback_homedir.*|fallback_homedir = /home/%u|" "$SSSD_CONF"

log "Restarting sssd"
systemctl restart sssd

log "Validating user after restart"
getent passwd "${DOMAIN_USER}@${DOMAIN}"

log "Join complete."
