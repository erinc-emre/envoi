# envoi
A Distributed Chat Application

# How to run

## Configure your settings

Update your IP Address and mask in calculate_broadcast.py

Use it to find your broadcast address.

Update it in config.json - BROADCAST_IP

## For Server Application
```bash
python3 server.py --unicast-port <your-port>
```

## For Client Application
```bash
python3 client.py
```

# Requirements

Your network should support UDP Multicast and Broadcast. If not then you can use multicast/braodcast tunneling tools like socat.
