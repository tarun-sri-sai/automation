#!/usr/bin/env bash

echo "Usage: $0 --hostname <fqdn> --domain <domain> --dns <dns_ip>"

log() { echo "[INFO] $1"; }

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --hostname) HOSTNAME="$2"; shift ;;
        --domain) DOMAIN="$2"; shift ;;
        --dns) DNS_IP="$2"; shift ;;
        *) echo "[ERROR] Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$HOSTNAME" || -z "$DOMAIN" || -z "$DNS_IP" ]]; then exit 1; fi

log "Setting hostname"
hostnamectl set-hostname "$HOSTNAME"

log "Installing packages"
dnf install -y realmd oddjob oddjob-mkhomedir sssd adcli krb5-workstation

log "Configuring DNS"
nmcli con mod eth0 ipv4.dns "$DNS_IP"

log "Discovering domain"
realm discover "$DOMAIN"

log "Updating crypto policies"
update-crypto-policies --set DEFAULT:AD-SUPPORT

log "Setup complete. Reboot now before running join_ad.sh."
