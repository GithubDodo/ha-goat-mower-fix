# GOAT mower start fix (Ecovacs GOAT O1200) for Home Assistant

Home Assistant's Ecovacs integration can read the **Ecovacs GOAT O1200** robot mower and send it back to the dock,
but **Start, Pause and Resume do nothing**. The log shows:

```
No response received for command "clean_V2"
```

## Why

The integration uses the library [deebot-client](https://github.com/DeebotUniverse/client.py), which sends the
GOAT O1200 the *vacuum* command `clean_V2`. The mower firmware never answers that command.
It does accept the older command name `clean` with the newer, nested content:

```json
{"act": "start", "content": {"type": "auto"}}
```

(An empty `type` is rejected with error code 20003 "unknow type", so `auto` is always sent.)
This was verified on a real GOAT O1200: start, pause and dock all work.

## What this integration does

It swaps exactly this one command for the GOAT O1200 device classes `2i0fns` and `0jbd6s` when Home Assistant starts.
Nothing else changes; the built-in Ecovacs integration stays as it is. No account data, no network access, no configuration
besides one line.

The proper fix belongs into deebot-client and has been proposed there: [DeebotUniverse/client.py#1969](https://github.com/DeebotUniverse/client.py/pull/1969). **As soon as deebot-client contains it, this
integration is no longer needed**: it then only logs that the fix is not needed, and you can remove it.

## Installation

**HACS:** add this repository as a custom repository (category *Integration*), install "GOAT mower start fix", restart.
**Manual:** copy `custom_components/goat_mower_fix` into your `config/custom_components/` folder.

Then add one line to `configuration.yaml` and restart Home Assistant:

```yaml
goat_mower_fix:
```

The log then shows `GOAT mower fix active: class 2i0fns starts with 'clean'`.

## Other GOAT models

Other GOAT models (O800, O500, A1600, …) report the same symptom in
[home-assistant/core#168621](https://github.com/home-assistant/core/issues/168621). They use other device classes and were
**not tested**. If your model has the same problem, the same command may work for it. Please open an issue with your
device class (shown in the Ecovacs integration's diagnostics) and whether `clean` works for you.

## Kurz auf Deutsch

Der Ecovacs-Mähroboter GOAT O1200 lässt sich in Home Assistant andocken, aber nicht starten, weil die Bibliothek ihm den
Saugroboter-Befehl `clean_V2` schickt. Dieser Baustein tauscht ihn gegen `clean` aus (am echten Gerät getestet).
Installation wie oben, danach `goat_mower_fix:` in die `configuration.yaml` und neu starten.

## License

MIT, see [LICENSE](LICENSE). Not affiliated with Ecovacs or Home Assistant.
