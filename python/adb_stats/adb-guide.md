# ADB Guide

## Connecting via Wifi

1. Ensure both the PC and Android device are connected to the same Wifi network.
1. Ensure `adb` is installed and is on PATH.
1. Ensure Wifi debugging is enabled on the Android device.
1. Run the below command to make `adb` listen on port `5555`:

   ```powershell
   adb tcpip 5555
   ```

1. Run the below command to pair the Android device via pairing code:

   ```powershell
   adb pair <IP>:<port>     # These details will be shown in the pairing dialog on the Android device
   ```

1. Run the below command to connect to the Android device:

   ```powershell
   adb connect <IP>:<port>  # The port will not be the same as the one used to pair, it is common for all pairing methods
   ```

1. Run the below command to disconnect the Android device:

   ```powershell
   adb disconnect           # This will disconnect everything
   ```
