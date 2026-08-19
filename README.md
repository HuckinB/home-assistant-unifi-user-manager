# UniFi User Manager for Home Assistant

A custom Home Assistant integration for monitoring and managing UniFi users from Home Assistant.

> The Home Assistant integration domain remains `unifi_protect_access` for compatibility with existing v0.2.x/v0.3.0 config entries and entity history.

## Features

- Represents each UniFi user as a Home Assistant device.
- Account active switch (`ACTIVE` / `DEACTIVATED`).
- Account status sensor.
- Protect-linked diagnostic sensor.
- Console-level active/deactivated user counts.
- Manual refresh button.
- Configurable polling interval (15–300 seconds, 30 seconds by default).
- Select which users are exposed to Home Assistant.
- Automatically discovers newly-added users.
- Reauthentication and reconfiguration flows.
- Redacted diagnostics.
- Immediate refresh after activate/deactivate actions.

## API behaviour

Read operations use the official UniFi Protect Integration API where available.

Account activation/deactivation uses the local UniFi Users service endpoint observed from the UniFi web interface:

- `PUT /proxy/users/api/v2/user/{id}/active?isULP=1`
- `PUT /proxy/users/api/v2/user/{id}/deactivate?isULP=1`

Other write operations should only be added after their exact UniFi endpoint and payload have been verified.

## Install with HACS

1. Create/publish this repository on GitHub.
2. In Home Assistant open **HACS**.
3. Open the menu and choose **Custom repositories**.
4. Add:
   `https://github.com/HuckinB/home-assistant-unifi-user-manager`
5. Select **Integration** as the repository type.
6. Install **UniFi User Manager**.
7. Restart Home Assistant.
8. Go to **Settings → Devices & services → Add integration** and search for **UniFi User Manager**.

## Manual installation

Copy:

`custom_components/unifi_protect_access`

to:

`/config/custom_components/unifi_protect_access`

Then restart Home Assistant.

## Upgrading from v0.2.x/v0.3.0

The integration keeps the existing `unifi_protect_access` domain, so existing config entries should be retained. Replace the files or install the repository through HACS and restart Home Assistant.

## Security

Do not commit UniFi usernames, passwords, API keys, session cookies, CSRF tokens, or diagnostics containing secrets to this repository. Credentials are stored in the Home Assistant config entry and are not part of the repository.
