AI SYSTEM PROMPT — Zona Controller

You are interacting with the Zona Controller project.
This software is a Python/Flask-based real-time UWB (Ultra-Wideband) localization controller, designed to receive, process, and visualize TDOA (Time Difference of Arrival) positioning data.

System Purpose

The Zona Controller:

receives TDOA measurement packets from UWB anchors via UDP,

computes or receives precomputed TAG positions,

maintains internal application state,

exposes a web interface (dashboard + map) to visualize TAG positions, anchors, and system status,

allows user authentication and configuration management.

Core Components

UDPServer: Listens for raw TDOA or UWB position data and updates internal shared State.

State model: Holds active TAG positions, anchor metadata, timestamps, and last-known system messages.

Flask Web App:

/ Dashboard: JSON state visualization (TAG tables, nodes, last message).

/map Map View: Canvas-based 2D position rendering.

/config Configuration UI.

HOCON Configuration (zona.conf):

network parameters (UDP/HTTP ports, sink host),

system/zone metadata,

anchors and tags,

cryptographic options,

user list with roles & permissions (diag / admin / root).

Input Data Model

Incoming UDP packets contain UWB anchor messages or TDOA snapshots.

TAG positions are either computed externally or derived from received TDOA data.

The system assumes multiple anchors in the environment and one or more TAGs.

Output / UI

Real-time TAG positions shown on a map.

Logs and raw last-known TDOA message.

Configurable via web GUI.

User Roles

diag: diagnostics only

admin: can edit system/network/tdoa config

root: full access (crypto, users, etc.)

High-Level Behavior

Start with run.py, which loads zona.conf, initializes Flask, and launches UDPServer.

The server updates global state continuously as packets arrive.

Web pages pull data through JSON API endpoints every 1–2 seconds.

What the AI Should Do

When assisting with this repository, the AI should:

Understand that this is a real-time positioning controller, not a simulation.

Treat anchors and tags as physical UWB devices with IDs and positions.

Respect the configuration structure defined in zona.conf.

Generate or modify code only within established module boundaries (zona_controller/).

Maintain compatibility with Flask, HOCON config, and the existing UDPServer infrastructure.

Avoid inventing non-existent features; rely on described and discovered modules.

What the AI Must Not Do

Must not assume cloud dependencies — everything runs locally.

Must not restructure the project unless explicitly requested.

Must not produce configuration that violates role-based access rules.

Must not assume how TDOA computation is done unless defined in the code (external or provided).

Key Goal

Provide reliable assistance in extending, debugging, documenting, or integrating the Zona Controller while preserving consistency with the existing architecture and real-time behavior.