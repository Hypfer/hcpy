import json
import re

from HCSocket import now


def decamelcase(str):
    split = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', str)
    return f"{split[0]} {' '.join(split[1:]).lower()}".strip()


HA_DISCOVERY_PREFIX = "homeassistant"


def publish_ha_discovery(device, client, mqtt_topic):
    print(f"{now()} Publishing HA discovery for {device}")

    device_ident = device["host"]
    device_name = device["name"]
    device_description = device.get("description", {})

    version_parts = filter(
        lambda d : d is not None,
        [
            device_description.get("version"),
            device_description.get("revision")
        ]
    )

    device_info = {
        "identifiers": [device_ident],
        "name": device_name,
        "manufacturer": device_description.get("brand"),
        "model": device_description.get("model"),
        "sw_version": ".".join(version_parts)
    }

    for feature in device["features"].values():
        name_parts = feature["name"].split(".")
        name = name_parts[-1]
        feature_type = name_parts[-2]
        access = feature.get("access", "none")
        available = feature.get("available", False)

        if (feature_type == "Setting" and available and (access == "read" or access == "readWrite")) or \
            feature_type == "Event" or \
            feature_type == "Option":

            component_type = "binary_sensor" if feature_type == "Event" else "sensor" # TODO use more appropriate types

            discovery_topic = f"{HA_DISCOVERY_PREFIX}/{component_type}/hcpy/{device_ident}_{name}/config"
            # print(discovery_topic, state_topic)

            discovery_payload = {
                "name": decamelcase(name),
                "device": device_info,
                "state_topic": f"{mqtt_topic}/state",
                # "availability_topic": f"{mqtt_topic}/LWT",
                "value_template": "{{value_json." + name + "}}",
                "object_id": f"{device_ident}_{name}",
                "unique_id": f"{device_ident}_{name}",
            }

            if component_type == "binary_sensor":
                discovery_payload["payload_on"] = "On"
                discovery_payload["payload_off"] = "Off"

            print(discovery_topic)
            # print(discovery_payload)

            client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)
