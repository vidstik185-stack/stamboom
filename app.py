from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
import os
import datetime
import re
import uuid
from collections import defaultdict
import json
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = 'zet-hier-een-sterke-geheime-sleutel'  # Nodig voor sessies

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Login - Stamboom Feenstra</title>
    <link href='https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap' rel='stylesheet'>
    <style>
        body { background: #e0e7ef; font-family: 'Roboto', Arial, sans-serif; }
        .login-container {
            max-width: 340px; margin: 120px auto; background: #fff; border-radius: 12px;
            box-shadow: 0 4px 32px rgba(37,99,235,0.13); padding: 32px 28px 28px 28px; text-align: center;
        }
        h2 { color: #2563eb; margin-bottom: 24px; }
        input[type='password'] {
            width: 100%; padding: 10px; border-radius: 6px; border: 1.5px solid #b0b8c1;
            font-size: 1.1rem; margin-bottom: 18px; transition: border 0.2s;
        }
        input[type='password']:focus { border: 2px solid #2563eb; outline: none; }
        button {
            background: linear-gradient(90deg, #2563eb 60%, #1d4ed8 100%);
            color: #fff; border: none; border-radius: 6px; padding: 10px 22px; font-size: 1rem; font-weight: 700;
            cursor: pointer; box-shadow: 0 2px 8px rgba(37,99,235,0.08); transition: background 0.2s, transform 0.15s;
        }
        button:hover { background: linear-gradient(90deg, #1d4ed8 60%, #2563eb 100%); transform: translateY(-2px) scale(1.04); }
        .msg { color: #d32f2f; margin-bottom: 10px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Stamboom Feenstra</h2>
        {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
        <form method="post">
            <input type="password" name="password" placeholder="Wachtwoord" autofocus required>
            <button type="submit">Inloggen</button>
        </form>
    </div>
</body>
</html>
"""

HTML_PAGE = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <title>Stamboom Feenstra</title>
    <link rel="icon" type="x-icon" href="/favicon.ico">
    <link href='https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap' rel='stylesheet'>
    <link href="https://fonts.googleapis.com/css?family=Press+Start+2P" rel="stylesheet">
        <style>
            /* Centraal uitlijnen van de knoppen/timer rij */
            .center-row {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 24px;
                margin: 20px 0;
                width: 100%;
            }
            @media (max-width: 700px) {
                .center-row { flex-direction: column; gap: 10px; }
            }
            /* Stijl voor de select-lijst in het modal kind-koppel-menu */
            #modal-add-child-select {
                border-radius: 7px;
                border: 1.5px solid #b0b8c1;
                background: #f8fbff;
                font-size: 1.08rem;
                color: #1a237e;
                padding: 7px 10px;
                box-shadow: 0 2px 10px rgba(37,99,235,0.07);
                margin-bottom: 0;
                transition: border 0.2s, box-shadow 0.2s;
                outline: none;
                min-height: 44px;
                max-height: 180px;
            }
            #modal-add-child-select:focus {
                border: 2px solid #2563eb;
                box-shadow: 0 0 0 2px #2563eb33;
                background: #eaf2ff;
            }
            #modal-add-child-select option {
                padding: 6px 10px;
                border-radius: 5px;
                font-size: 1.05rem;
                transition: background 0.15s, color 0.15s;
            }
            #modal-add-child-select option:hover, #modal-add-child-select option:checked {
                background: #dbeafe;
                color: #2563eb;
            }
            .retro-title {
                font-family: 'Press Start 2P', cursive;
                font-size: 2.2rem;
                color: #fff;
                background: #2b52ff;
                padding: 18px 0 18px 0;
                border-radius: 12px 12px 0 0;
                margin-bottom: 32px;
                text-align: center;
                letter-spacing: 2px;
                text-shadow: -1px 1px 8px rgba(255,255,255,0.6), 1px -1px 8px rgba(255,255,235,0.7), 0px 0 1px rgba(251,0,231,0.8), 0 0px 3px rgba(0,233,235,0.8), 0px 0 3px rgba(0,242,14,0.8), 0 0px 3px rgba(244,45,0,0.8), 0px 0 3px rgba(59,0,226,0.8);
                animation: rgbText 2s steps(9) 0s infinite alternate;
            }
            @keyframes rgbText {
                0% {
                    text-shadow: -1px 1px 8px rgba(255,255,255,0.6), 1px -1px 8px rgba(255,255,235,0.7), 0px 0 1px rgba(251,0,231,0.8), 0 0px 3px rgba(0,233,235,0.8), 0px 0 3px rgba(0,242,14,0.8), 0 0px 3px rgba(244,45,0,0.8), 0px 0 3px rgba(59,0,226,0.8);
                }
                45% {
                    text-shadow: -1px 1px 8px rgba(255,255,255,0.6), 1px -1px 8px rgba(255,255,235,0.7), 5px 0 1px rgba(251,0,231,0.8), 0 5px 1px rgba(0,233,235,0.8), -5px 0 1px rgba(0,242,14,0.8), 0 -5px 1px rgba(244,45,0,0.8), 5px 0 1px rgba(59,0,226,0.8);
                }
                50% {
                    text-shadow: -1px 1px 8px rgba(255,255,255,0.6), 1px -1px 8px rgba(255,255,235,0.7), -5px 0 1px rgba(251,0,231,0.8), 0 -5px 1px rgba(0,233,235,0.8), 5px 0 1px rgba(0,242,14,0.8), 0 5px 1px rgba(244,45,0,0.8), -5px 0 1px rgba(59,0,226,0.8);
                }
                100% {
                    text-shadow: -1px 1px 8px rgba(255,255,255,0.6), 1px -1px 8px rgba(255,255,235,0.7), 5px 0 1px rgba(251,0,231,0.8), 0 -5px 1px rgba(0,233,235,0.8), -5px 0 1px rgba(0,242,14,0.8), 0 5px 1px rgba(244,45,0,0.8), -5px 0 1px rgba(59,0,226,0.8);
                }
            }
        </style>
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <link href="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css" rel="stylesheet" />
        <style>
                html { height:100%; }
                body { margin:0; font-family: 'Roboto', Arial, sans-serif; height:100%; }
                        .bg {
                            animation:slide 10s ease-in-out infinite alternate;
                            background-image: linear-gradient(-60deg, #6c3 50%, #09f 50%);
                            bottom:0;
                            left:-50%;
                            opacity:.5;
                            position:fixed;
                            right:-50%;
                            top:0;
                            z-index:-1;
                        }
                        .bg2 {
                            animation-direction:alternate-reverse;
                            animation-duration:14s;
                        }
                        .bg3 {
                            animation-duration:18s;
                        }
                .content {
                    background-color:rgba(255,255,255,.8);
                    border-radius:.25em;
                    box-shadow:0 0 .25em rgba(0,0,0,.25);
                    box-sizing:border-box;
                    left:50%;
                    padding:0;
                    position:fixed;
                    text-align:center;
                    top:50%;
                    transform:translate(-50%, -50%);
                    max-width: 1100px;
                    width: 100vw;
                    min-width: 320px;
                }
                .container { margin: 0; background: none; border-radius: 12px; box-shadow: none; padding: 32px 40px 40px 40px; }
                h1 { text-align: center; color: #2a3b4c; margin-bottom: 32px; font-size: 2.4rem; font-weight: 700; letter-spacing: 1px; font-family:monospace; }
                #network { width: 100%; height: 500px; border: 1px solid #e3eaf2; border-radius: 8px; background: #fafbfc; margin-bottom: 32px; }
                form { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; justify-content: center; }
                form input, form select { padding: 8px; border-radius: 4px; border: 1px solid #b0b8c1; font-size: 1rem; }
            .btn-main {
                background: linear-gradient(90deg, #2563eb 60%, #1d4ed8 100%);
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
                font-size: 1rem;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(37,99,235,0.08);
                transition: background 0.2s, transform 0.15s, box-shadow 0.2s;
                position:relative;
                overflow:hidden;
                outline: none;
            }
            .btn-main:hover, .btn-main:focus {
                background: linear-gradient(90deg, #1d4ed8 60%, #2563eb 100%);
                transform: translateY(-2px) scale(1.04);
                box-shadow: 0 6px 18px rgba(37,99,235,0.13);
            }
            .btn-main:active {
                background: linear-gradient(90deg, #1d4ed8 60%, #2563eb 100%);
                transform: scale(0.98);
                box-shadow: 0 1px 4px rgba(37,99,235,0.10);
            }
                form button { background: #2563eb; color: #fff; border: none; border-radius: 4px; padding: 8px 18px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
                form button:hover { background: #1d4ed8; }
                .msg { text-align: center; color: #2563eb; margin-bottom: 16px; font-weight: 700; }
            /* Algemene animatieklassen */
            .fade-in {
                animation: fadeIn 0.6s cubic-bezier(0.4,0,0.2,1);
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .scale-in {
                animation: scaleIn 0.4s cubic-bezier(0.4,0,0.2,1);
            }
            @keyframes scaleIn {
                from { opacity: 0; transform: scale(0.85); }
                to { opacity: 1; transform: scale(1); }
            }
            #edit-modal {
                display:none;
                position:fixed;
                top:0; left:0; width:100vw; height:100vh;
                background:rgba(0,0,0,0.25);
                align-items:center; justify-content:center;
                z-index:1000;
                transition: background 0.3s;
            }
            #edit-modal.show {
                display:flex;
                animation: fadeIn 0.3s;
            }
            #edit-modal .modal-content {
                background:#fff;
                border-radius:16px;
                padding:32px 40px;
                box-shadow:0 8px 40px rgba(0,0,0,0.18);
                min-width:320px;
                max-width:95vw;
                animation: scaleIn 0.4s cubic-bezier(0.4,0,0.2,1);
                position:relative;
            }
            #edit-modal label { display:block; margin-top:14px; font-weight:500; color:#1a237e; }
            #edit-modal input {
                width:100%; margin-top:4px; padding:8px; border-radius:5px; border:1px solid #b0b8c1; font-size:1rem;
                transition: border 0.2s;
            }
            #edit-modal input:focus {
                border:1.5px solid #2563eb;
                outline:none;
            }
            #edit-modal button {
                margin-top:16px;
                background: linear-gradient(90deg, #2563eb 60%, #1d4ed8 100%);
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
                font-size: 1rem;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(37,99,235,0.08);
                transition: background 0.2s, transform 0.15s, box-shadow 0.2s;
                position:relative;
                overflow:hidden;
                outline: none;
            }
            #edit-modal button:hover, #edit-modal button:focus {
                background: linear-gradient(90deg, #1d4ed8 60%, #2563eb 100%);
                transform: translateY(-2px) scale(1.04);
                box-shadow: 0 6px 18px rgba(37,99,235,0.13);
            }
            #edit-modal button:active {
                background: linear-gradient(90deg, #1d4ed8 60%, #2563eb 100%);
                transform: scale(0.98);
                box-shadow: 0 1px 4px rgba(37,99,235,0.10);
            }
            #edit-modal hr {
                border: none;
                border-top: 1.5px solid #e3eaf2;
                margin: 18px 0 12px 0;
            }
                @media (max-width: 700px) { .content { padding: 10px; } h1 { font-size: 1.3rem; } }
                @keyframes slide {
                    0% { transform:translateX(-25%); }
                    100% { transform:translateX(25%); }
                }
        </style>
</head>
<body>
        <div class="bg"></div>
        <div class="bg bg2"></div>
        <div class="bg bg3"></div>
        <div class="content">
            <div class="container">
    <div class="retro-title">Feenstra Stamboom</div>
        <div style="text-align:center;margin-bottom:20px;">
            <label for="gen-select"><b>Kies generatie:</b></label>
            <select id="gen-select" style="margin-left:10px;"></select>
        </div>
        <div id="shortcuts" style="text-align:center;margin-bottom:20px;"></div>
        <div id="network"></div>
        <div class="msg" id="msg"></div>
        <form id="add-person-form">
            <input type="text" id="naam" placeholder="Naam" required>
            <input type="date" id="geboortedatum" placeholder="Geboortedatum">
            <input type="date" id="overlijdensdatum" placeholder="Overlijdensdatum">
            <input type="text" id="bijzonderheden" placeholder="Bijzonderheden">
            <button type="submit" class="btn-main">Voeg Persoon Toe</button>
        </form>
        <form id="link-child-form" style="display:none;">
            <select id="ouder-select"></select>
            <select id="kind-select"></select>
            <button type="submit">Koppel Kind aan Ouder</button>
        </form>
        <form id="unlink-child-form" style="display:none;margin-top:10px;">
            <select id="ouder-unlink-select"></select>
            <select id="kind-unlink-select"></select>
            <button type="submit">Verwijder Kind van Ouder</button>
        </form>
        <div class="center-row">
            <button id="force-save" class="btn-main">Nu opslaan</button>
            <span id="timer" style="font-size:1.2rem;color:#d97706;font-weight:bold; min-width:70px; text-align:center;">05:00</span>
            <button id="reset-view" class="btn-main">Reset weergave</button>
        </div>
            </div>
        </div>
        <div id="edit-modal">
            <div class="modal-content scale-in">
                <h3>Bewerk Persoon</h3>
                <h3 style="margin-top:0; color:#2563eb; font-family:'Roboto',sans-serif; font-size:1.5rem; letter-spacing:1px;">Bewerk Persoon</h3>
                <form id="edit-person-form">
                <form id="edit-person-form" autocomplete="off">
                    <input type="hidden" id="edit-id">
                    <label>Naam<input type="text" id="edit-naam" required></label>
                    <label>Geboortedatum<input type="date" id="edit-geboortedatum"></label>
                    <label>Overlijdensdatum<input type="date" id="edit-overlijdensdatum"></label>
                    <label>Bijzonderheden<input type="text" id="edit-bijzonderheden"></label>
                    <button type="submit">Opslaan</button>
                    <button type="button" onclick="closeEditModal()">Annuleer</button>
                </form>
                <hr>
                        <div style="margin-bottom:8px;">
                            <label style="display:block; margin-bottom:4px;">Voeg bestaand kind toe:</label>
                            <div style="display:flex; gap:8px; align-items:flex-end;">
                                <div style="display:flex; flex-direction:column; flex:2 1 220px; min-width:120px;">
                                    <input type="text" id="modal-add-child-search" placeholder="Zoek op naam..." style="margin-bottom:4px;" autocomplete="off">
                                    <select id="modal-add-child-select" size="6" style="width:100%; min-width:100px;"></select>
                                </div>
                                <button id="modal-add-child-btn" style="flex:0 0 auto; height:40px;">Koppel</button>
                            </div>
                        </div>
                <div style="margin-top:10px;">
                    <label>Verwijder kind:<br>
                        <select id="modal-remove-child-select"></select>
                        <button id="modal-remove-child-btn">Ontkoppel</button>
                    </label>
                </div>
                <hr>
                <div style="margin-top:10px;">
                    <label>Voeg nieuw kind toe:<br>
                        <input type="text" id="modal-new-child-name" placeholder="Naam nieuw kind" style="margin-bottom:4px;">
                        <button id="modal-new-child-btn">Voeg nieuw kind toe</button>
                    </label>
                </div>
            </div>
        </div>
    <script>
    // Sla posities automatisch op vóór herladen/sluiten
    window.onbeforeunload = function() {
        if (window.network) {
            const positions = window.network.getPositions();
            navigator.sendBeacon('/api/save_positions', JSON.stringify({ positions }));
        }
    };
    let personen = [];
    let network;
    // Genereer generatiestructuur (klassiek: root = gen 1, kinderen = gen 2, ...)
    function getGeneraties() {
        // Bouw ouder->kind en kind->ouder relaties
        const idMap = {};
        personen.forEach(p => { idMap[p.id] = p; });
        // Maak kind->ouders map
        const childToParents = {};
        personen.forEach(p => {
            (p.kinderen_ids||[]).forEach(kidId => {
                if (!childToParents[kidId]) childToParents[kidId] = [];
                childToParents[kidId].push(p.id);
            });
        });
        // Recursieve functie om generatie te bepalen
        const genMap = {};
        function getGen(id) {
            if (genMap[id] !== undefined) return genMap[id];
            const ouders = childToParents[id] || [];
            if (ouders.length === 0) {
                genMap[id] = 1;
                return 1;
            }
            // Alleen als er een ouder is die zelf een generatie heeft
            const parentGens = ouders.map(getGen).filter(g => g !== undefined);
            if (parentGens.length === 0) {
                // Geen ouder met generatie, dus niet in een generatie
                genMap[id] = undefined;
                return undefined;
            }
            const gen = 1 + Math.max(...parentGens);
            genMap[id] = gen;
            return gen;
        }
        let maxGen = 1;
        personen.forEach(p => {
            const g = getGen(p.id);
            if (g !== undefined && g > maxGen) maxGen = g;
        });
        // Maak lijst van generaties
        let gens = [];
        for (let g = 1; g <= maxGen; g++) {
            const genPersonen = personen.filter(p => {
                if (genMap[p.id] !== g) return false;
                // Alleen tonen als persoon minstens één ouder of één kind heeft
                const heeftOuder = (childToParents[p.id] && childToParents[p.id].length > 0);
                const heeftKind = (p.kinderen_ids && p.kinderen_ids.length > 0);
                return heeftOuder || heeftKind;
            });
            if (genPersonen.length > 0) {
                gens.push({
                    nummer: g,
                    personen: genPersonen
                });
            }
        }
        return gens;
    }
    function renderGenMenu() {
        const genSel = document.getElementById('gen-select');
        const gens = getGeneraties();
        genSel.innerHTML = '';
        gens.forEach(gen => {
            const opt = document.createElement('option');
            opt.value = gen.nummer;
            opt.textContent = 'Gen ' + gen.nummer;
            genSel.appendChild(opt);
        });
    }
    function renderShortcuts() {
        const shortcutsDiv = document.getElementById('shortcuts');
        shortcutsDiv.innerHTML = '';
        const gen = document.getElementById('gen-select') ? document.getElementById('gen-select').value : '1';
        const gens = getGeneraties();
        const genObj = gens.find(g => String(g.nummer) === String(gen));
        let html = '';
        if (genObj) {
            html += `<b>Gen ${genObj.nummer}:</b> `;
            genObj.personen.forEach(p => {
                html += `<button class="shortcut-btn" data-id="${p.id}">${p.naam||'Onbekend'}</button> `;
            });
        }
        shortcutsDiv.innerHTML = html;
        // Event listeners
        Array.from(document.getElementsByClassName('shortcut-btn')).forEach(btn => {
            btn.onclick = function() {
                const nodeId = this.getAttribute('data-id');
                if (network && nodeId) {
                    network.focus(nodeId, {scale:1.5, animation:true});
                }
            };
        });
    }
    function fetchTreeAndRender() {
        fetch('/api/tree').then(r => r.json()).then(data => {
            console.log('Ontvangen personen met posities:', data.map(p => ({naam: p.naam, id: p.id, x: p.x, y: p.y})));
            personen = data;
            renderNetwork(data);
            fillSelects(data);
            renderGenMenu();
            renderShortcuts();
            // Herteken shortcuts bij wisselen van generatie
            const genSel = document.getElementById('gen-select');
            if (genSel) {
                genSel.onchange = renderShortcuts;
            }
        });
    }
    function renderNetwork(data) {
        const nodes = data.map(p => {
            let node = {
                id: p.id,
                label: p.naam || 'Onbekend',
                shape: 'box',
                color: { background: '#d0e8ff', border: '#a3cfff', highlight: { background: '#b3dbff', border: '#2563eb' } },
                widthConstraint: { minimum: 200 },
                heightConstraint: { minimum: 90 },
                font: {
                    size: 32,
                    face: 'Arial Black, Arial, Roboto, sans-serif',
                    color: '#000',
                    bold: true,
                    weight: 900,
                    vadjust: 0,
                    strokeWidth: 0,
                    strokeColor: '#fff',
                    background: 'none',
                    multi: false,
                    align: 'center',
                    sizeConstraint: { min: 32, max: 32 },
                    // Extra leesbaarheid: subtiele glow
                    shadow: true,
                    shadowColor: '#fff',
                    shadowSize: 4
                },
                margin: 28
            };
            if (typeof p.x === 'number' && typeof p.y === 'number') {
                node.x = p.x;
                node.y = p.y;
            }
            return node;
        });
        // Detecteer of er posities zijn
        const anyPositions = data.some(p => typeof p.x === 'number' && typeof p.y === 'number');
        let edges = [];
        data.forEach(p => {
            (p.kinderen_ids||[]).forEach(kid => {
                edges.push({
                    from: p.id,
                    to: kid,
                    arrows: { to: { enabled: true, scaleFactor: 1.2, type: 'arrow' } },
                    color: { color: '#1a237e', highlight: '#0d1333', inherit: false },
                    width: 2.5,
                    smooth: false
                });
            });
        });
        const container = document.getElementById('network');
        network = new vis.Network(container, { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, {
            layout: anyPositions ? {} : { hierarchical: { enabled: true, direction: 'UD', sortMethod: 'directed' } },
            nodes: {
                font: {
                    size: 32,
                    face: 'Arial Black, Arial, Roboto, sans-serif',
                    color: '#000',
                    bold: true,
                    weight: 900,
                    vadjust: 0,
                    strokeWidth: 0,
                    strokeColor: '#fff',
                    background: 'none',
                    multi: false,
                    align: 'center',
                    sizeConstraint: { min: 32, max: 32 },
                    shadow: true,
                    shadowColor: '#fff',
                    shadowSize: 4
                },
                borderWidth: 2,
                margin: 28,
                widthConstraint: { minimum: 200 },
                heightConstraint: { minimum: 90 },
                scaling: { label: false, customScalingFunction: function(min,max,total,value){return 1;} }
            },
            edges: { smooth: false, arrows: { to: { enabled: true, scaleFactor: 1.2, type: 'arrow' } }, color: { color: '#1a237e', highlight: '#0d1333', inherit: false }, width: 2.5 },
            physics: !anyPositions ? false : { enabled: false }
        });
        // Sla positie op na slepen
        network.on('dragEnd', function(params) {
            if(params.nodes && params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const pos = network.getPositions([nodeId])[nodeId];
                fetch('/api/save_position', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: nodeId, x: pos.x, y: pos.y })
                });
            }
        });
        network.on('doubleClick', function(params) {
          if(params.nodes.length > 0) {
            const id = params.nodes[0];
            const persoon = personen.find(p => p.id === id);
            if(persoon) openEditModal(persoon);
          }
        });
    }
    function fillSelects(data) {
        const ouderSel = document.getElementById('ouder-select');
        const kindSel = document.getElementById('kind-select');
        const ouderUnlinkSel = document.getElementById('ouder-unlink-select');
        const kindUnlinkSel = document.getElementById('kind-unlink-select');
        ouderSel.innerHTML = '';
        kindSel.innerHTML = '';
        ouderUnlinkSel.innerHTML = '';
        kindUnlinkSel.innerHTML = '';
        data.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id; opt.textContent = p.naam || 'Onbekend';
            ouderSel.appendChild(opt.cloneNode(true));
            kindSel.appendChild(opt.cloneNode(true));
            ouderUnlinkSel.appendChild(opt.cloneNode(true));
        });
        // Vul kindUnlinkSel met kinderen van geselecteerde ouder
        ouderUnlinkSel.onchange = function() {
            const ouderId = ouderUnlinkSel.value;
            kindUnlinkSel.innerHTML = '';
            const ouder = data.find(p => p.id === ouderId);
            if (ouder && ouder.kinderen_ids) {
                ouder.kinderen_ids.forEach(kidId => {
                    const kind = data.find(p => p.id === kidId);
                    if (kind) {
                        const opt = document.createElement('option');
                        opt.value = kind.id; opt.textContent = kind.naam || 'Onbekend';
                        kindUnlinkSel.appendChild(opt);
                    }
                });
            }
        };
        ouderUnlinkSel.dispatchEvent(new Event('change'));
    }
    // Unlink child form
    document.getElementById('unlink-child-form').onsubmit = function(e) {
        e.preventDefault();
        const ouder_id = document.getElementById('ouder-unlink-select').value;
        const kind_id = document.getElementById('kind-unlink-select').value;
        if (!ouder_id || !kind_id) { document.getElementById('msg').textContent = 'Selecteer ouder en kind!'; return; }
        fetch('/api/unlink_child', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ouder_id, kind_id })
        }).then(r => r.json()).then(res => {
            document.getElementById('msg').textContent = 'Kind verwijderd van ouder!';
            fetchTreeAndRender();
            setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
        });
    };
    // Timer en autosave
    let timerInterval;
    let timeLeft = 300; // 5 minuten in seconden
    function updateTimerDisplay() {
        const min = String(Math.floor(timeLeft/60)).padStart(2,'0');
        const sec = String(timeLeft%60).padStart(2,'0');
        document.getElementById('timer').textContent = `${min}:${sec}`;
    }
    function startTimer() {
        clearInterval(timerInterval);
        timeLeft = 300;
        updateTimerDisplay();
        timerInterval = setInterval(() => {
            timeLeft--;
            updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                autoSave();
            }
        }, 1000);
    }
    // Sla viewport op vóór autosave
    function saveViewportAndAutoSave() {
        if (!network) { autoSave(); return; }
        const scale = network.getScale();
        const center = network.getViewPosition();
        fetch('/api/save_viewport', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ zoom: scale, center })
        }).then(() => {
            autoSave();
        });
    }
    function autoSave() {
        // Sla altijd eerst alle node-posities op
        if (network) {
            const positions = network.getPositions();
            fetch('/api/save_positions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ positions })
            }).then(() => {
                fetch('/api/autosave', {method:'POST'}).then(()=>{
                    document.getElementById('msg').textContent = 'Automatisch opgeslagen!';
                    setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                    startTimer();
                });
            });
        } else {
            fetch('/api/autosave', {method:'POST'}).then(()=>{
                document.getElementById('msg').textContent = 'Automatisch opgeslagen!';
                setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                startTimer();
            });
        }
    }
    document.getElementById('force-save').onclick = function() { saveViewportAndAutoSave(); };
    // Vervang autosave in timer
    function startTimer() {
        clearInterval(timerInterval);
        timeLeft = 300;
        updateTimerDisplay();
        timerInterval = setInterval(() => {
            timeLeft--;
            updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                saveViewportAndAutoSave();
            }
        }, 1000);
    }
    startTimer();
    document.getElementById('add-person-form').onsubmit = function(e) {
        e.preventDefault();
        const naam = document.getElementById('naam').value;
        const geboortedatum = document.getElementById('geboortedatum').value;
        const overlijdensdatum = document.getElementById('overlijdensdatum').value;
        const bijzonderheden = document.getElementById('bijzonderheden').value;
        fetch('/api/add_person', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ naam, geboortedatum, overlijdensdatum, bijzonderheden })
        }).then(r => r.json()).then(res => {
            document.getElementById('msg').textContent = 'Persoon toegevoegd!';
            fetchTreeAndRender();
            this.reset();
            setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
        });
    };
    document.getElementById('link-child-form').onsubmit = function(e) {
        e.preventDefault();
        const ouder_id = document.getElementById('ouder-select').value;
        const kind_id = document.getElementById('kind-select').value;
        if (ouder_id === kind_id) { document.getElementById('msg').textContent = 'Ouder en kind mogen niet hetzelfde zijn!'; return; }
        fetch('/api/link_child', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ouder_id, kind_id })
        }).then(r => r.json()).then(res => {
            // Zoek ouder en kind in personenlijst
            const ouder = personen.find(p => p.id === ouder_id);
            const kind = personen.find(p => p.id === kind_id);
            if (ouder && kind) {
                const spacing_y = 200;
                const new_x = ouder.x || 0;
                const new_y = (ouder.y || 0) + spacing_y;
                // Verplaats kind direct onder ouder
                fetch('/api/save_position', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: kind.id, x: new_x, y: new_y })
                }).then(() => {
                    document.getElementById('msg').textContent = 'Kind gekoppeld aan ouder!';
                    fetchTreeAndRender();
                    setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                });
            } else {
                document.getElementById('msg').textContent = 'Kind gekoppeld aan ouder!';
                fetchTreeAndRender();
                setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
            }
        });
    };
            function openEditModal(persoon) {
                document.getElementById('edit-id').value = persoon.id;
                document.getElementById('edit-naam').value = persoon.naam || '';
                document.getElementById('edit-geboortedatum').value = persoon.geboortedatum || '';
                document.getElementById('edit-overlijdensdatum').value = persoon.overlijdensdatum || '';
                document.getElementById('edit-bijzonderheden').value = persoon.bijzonderheden || '';
                // Zoekfunctie en dropdown vullen
                const addSel = document.getElementById('modal-add-child-select');
                const addSearch = document.getElementById('modal-add-child-search');
                        function filterAndShowOptions(filter) {
                            addSel.innerHTML = '';
                            let personenLijst = personen.filter(p => p.id !== persoon.id && !(persoon.kinderen_ids||[]).includes(p.id));
                            if (filter && filter.trim() !== '') {
                                const lower = filter.trim().toLowerCase();
                                personenLijst = personenLijst.filter(p => (p.naam||'').toLowerCase().includes(lower));
                            }
                            personenLijst.forEach(p => {
                                const opt = document.createElement('option');
                                opt.value = p.id; opt.textContent = p.naam || 'Onbekend';
                                addSel.appendChild(opt);
                            });
                        }
                        addSearch.value = '';
                        addSearch.oninput = function() {
                            filterAndShowOptions(addSearch.value);
                        };
                        // Initieel tonen: alle personen behalve jezelf en je kinderen
                        filterAndShowOptions('');
                // Vul kind verwijderen dropdown (alle huidige kinderen)
                const remSel = document.getElementById('modal-remove-child-select');
                remSel.innerHTML = '';
                (persoon.kinderen_ids||[]).forEach(kidId => {
                    const kind = personen.find(p => p.id === kidId);
                    if (kind) {
                        const opt = document.createElement('option');
                        opt.value = kind.id; opt.textContent = kind.naam || 'Onbekend';
                        remSel.appendChild(opt);
                    }
                });
                const modal = document.getElementById('edit-modal');
                modal.style.display = 'flex';
                setTimeout(()=>{ modal.classList.add('show'); }, 10);
                // Voeg event listeners toe voor koppelen/ontkoppelen/nieuw kind
                document.getElementById('modal-add-child-btn').onclick = function(e) {
                    e.preventDefault();
                    const kind_id = addSel.value;
                    if (!kind_id) return;
                    fetch('/api/link_child', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ouder_id: persoon.id, kind_id })
                    }).then(r => r.json()).then(res => {
                        // Zoek ouder en kind in personenlijst
                        const ouder = personen.find(p => p.id === persoon.id);
                        const kind = personen.find(p => p.id === kind_id);
                        if (ouder && kind) {
                            const spacing_y = 200;
                            const new_x = ouder.x || 0;
                            const new_y = (ouder.y || 0) + spacing_y;
                            // Verplaats kind direct onder ouder
                            fetch('/api/save_position', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ id: kind.id, x: new_x, y: new_y })
                            }).then(() => {
                                document.getElementById('msg').textContent = 'Kind gekoppeld!';
                                closeEditModal();
                                fetchTreeAndRender();
                                setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                            });
                        } else {
                            document.getElementById('msg').textContent = 'Kind gekoppeld!';
                            closeEditModal();
                            fetchTreeAndRender();
                            setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                        }
                    });
                };
                document.getElementById('modal-remove-child-btn').onclick = function(e) {
                    e.preventDefault();
                    const kind_id = remSel.value;
                    if (!kind_id) return;
                    fetch('/api/unlink_child', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ouder_id: persoon.id, kind_id })
                    }).then(r => r.json()).then(res => {
                        document.getElementById('msg').textContent = 'Kind ontkoppeld!';
                        closeEditModal();
                        fetchTreeAndRender();
                        setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                    });
                };
                document.getElementById('modal-new-child-btn').onclick = function(e) {
                    e.preventDefault();
                    const naam = document.getElementById('modal-new-child-name').value.trim();
                    if (!naam) {
                        document.getElementById('msg').textContent = 'Vul een naam in voor het nieuwe kind!';
                        setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                        return;
                    }
                    // Voeg nieuw kind toe met ouder_id
                    fetch('/api/add_person', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ naam, ouder_id: persoon.id })
                    }).then(r => r.json()).then(newPersoon => {
                        // Koppel direct aan ouder
                        fetch('/api/link_child', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ ouder_id: persoon.id, kind_id: newPersoon.id })
                        }).then(() => {
                            document.getElementById('msg').textContent = 'Nieuw kind toegevoegd!';
                            closeEditModal();
                            fetchTreeAndRender();
                            setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
                        });
                    });
                };
            }
    function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    modal.classList.remove('show');
    setTimeout(()=>{ modal.style.display = 'none'; }, 250);
    }
    document.getElementById('edit-person-form').onsubmit = function(e) {
      e.preventDefault();
      const id = document.getElementById('edit-id').value;
      const naam = document.getElementById('edit-naam').value;
      const geboortedatum = document.getElementById('edit-geboortedatum').value;
      const overlijdensdatum = document.getElementById('edit-overlijdensdatum').value;
      const bijzonderheden = document.getElementById('edit-bijzonderheden').value;
      fetch('/api/update_person', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, naam, geboortedatum, overlijdensdatum, bijzonderheden })
      }).then(r => r.json()).then(res => {
        document.getElementById('msg').textContent = 'Persoon bijgewerkt!';
        closeEditModal();
        fetchTreeAndRender();
        setTimeout(()=>{document.getElementById('msg').textContent='';}, 2000);
      });
    };
    fetchTreeAndRender();
    // Reset weergave knop
    document.getElementById('reset-view').onclick = function() {
        if (network) {
            network.fit({animation: true});
        }
    };
    // Herteken menu en shortcuts na laden
    function fetchTreeAndRender() {
    fetch('/api/tree').then(r => r.json()).then(data => {
            personen = data;
            renderNetwork(data);
            fillSelects(data);
            renderGenMenu();
            renderShortcuts();
            // Herteken shortcuts bij wisselen van generatie
            const genSel = document.getElementById('gen-select');
            if (genSel) {
                genSel.onchange = renderShortcuts;
            }
        });
    }
    </script>
</body>
</html>
"""


# --- Helper functions from txt.py ---
DATE_FORMAT = '%Y-%m-%d'
def parse_date_str(date_str):
    if not date_str:
        return None
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str):
            raise ValueError("Invalid date format")
        return datetime.datetime.strptime(date_str, DATE_FORMAT).date()
    except (ValueError, TypeError):
        return None

def format_date_obj(date_obj):
    return date_obj.isoformat() if date_obj else 'N/A'

# --- Minimal StamboomData for API ---
class StamboomData:
    def __init__(self, json_path):
        self.json_path = json_path
        self.personen = []
        self._laad_data_sync()

    def _laad_data_sync(self):
        self.personen = []
        if not os.path.exists(self.json_path):
            return
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.personen = data.get('personen', [])

stamboom_data = StamboomData("stamboom_data.json")


# Login vereist voor toegang tot de app
@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        msg = ''
        if request.method == 'POST':
            if request.form.get('password') == '160461':
                session['logged_in'] = True
                return redirect(url_for('home'))
            else:
                msg = 'Wachtwoord onjuist!'
        return render_template_string(LOGIN_PAGE, msg=msg)
    return render_template_string(HTML_PAGE)

@app.route('/api/personen')
def api_personen():
    # Reload data each time for demo; in production, cache or reload on change
    stamboom_data._laad_data_sync()
    return jsonify(stamboom_data.personen)

@app.route('/api/add_person', methods=['POST'])
def api_add_person():
    data = request.json
    if not data or not data.get('naam'):
        return {'error': 'Naam is verplicht'}, 400
    # Plaats nieuwe blok onder de ouder (indien opgegeven)
    stamboom_data._laad_data_sync()
    existing = stamboom_data.personen
    spacing_y = 200  # pixels tussen blokken verticaal
    base_x = 0
    ouder_id = data.get('ouder_id')
    y = 0
    if ouder_id:
        ouder = next((p for p in existing if p['id'] == ouder_id), None)
        if ouder:
            y = ouder.get('y', 0) + spacing_y
            base_x = ouder.get('x', 0)
    else:
        y = spacing_y * len(existing)
    new_person = {
        'id': str(uuid.uuid4()),
        'naam': data['naam'],
        'geboortedatum': data.get('geboortedatum'),
        'overlijdensdatum': data.get('overlijdensdatum'),
        'partnerschappen': [],
        'kinderen_ids': [],
        'bijzonderheden': data.get('bijzonderheden'),
        'x': base_x,
        'y': y
    }
    stamboom_data._laad_data_sync();
    stamboom_data.personen.append(new_person)
    # Save to JSON
    _save_stamboom_json(stamboom_data)
    return new_person, 201

@app.route('/api/link_child', methods=['POST'])
def api_link_child():
    data = request.json
    ouder_id = data.get('ouder_id')
    kind_id = data.get('kind_id')
    if not ouder_id or not kind_id:
        return {'error': 'ouder_id en kind_id zijn verplicht'}, 400
    stamboom_data._laad_data_sync()
    ouder = next((p for p in stamboom_data.personen if p['id'] == ouder_id), None)
    kind = next((p for p in stamboom_data.personen if p['id'] == kind_id), None)
    if not ouder:
        return {'error': 'Ouder niet gevonden'}, 404
    if not kind:
        return {'error': 'Kind niet gevonden'}, 404
    if kind_id not in ouder['kinderen_ids']:
        ouder['kinderen_ids'].append(kind_id)
        # Zet positie van kind direct onder ouder
        spacing_y = 200
        kind['x'] = ouder.get('x', 0)
        kind['y'] = ouder.get('y', 0) + spacing_y
        _save_stamboom_json(stamboom_data)
        # Sla ook posities op in stamboom_positions.json
        pos_path = 'stamboom_positions.json'
        positions = {}
        if os.path.exists(pos_path):
            with open(pos_path, 'r', encoding='utf-8') as f:
                positions = json.load(f)
        positions[kind_id] = {'x': kind['x'], 'y': kind['y']}
        with open(pos_path, 'w', encoding='utf-8') as f:
            json.dump(positions, f, ensure_ascii=False, indent=2)
    return {'success': True}

@app.route('/api/unlink_child', methods=['POST'])
def api_unlink_child():
    data = request.json
    ouder_id = data.get('ouder_id')
    kind_id = data.get('kind_id')
    if not ouder_id or not kind_id:
        return {'error': 'ouder_id en kind_id zijn verplicht'}, 400
    stamboom_data._laad_data_sync()
    ouder = next((p for p in stamboom_data.personen if p['id'] == ouder_id), None)
    if not ouder:
        return {'error': 'Ouder niet gevonden'}, 404
    if kind_id in ouder['kinderen_ids']:
        ouder['kinderen_ids'].remove(kind_id);
        _save_stamboom_json(stamboom_data)
    return {'success': True}

@app.route('/api/update_person', methods=['POST'])
def api_update_person():
    data = request.json
    person_id = data.get('id')
    if not person_id:
        return {'error': 'id is verplicht'}, 400
    stamboom_data._laad_data_sync()
    person = next((p for p in stamboom_data.personen if p['id'] == person_id), None)
    if not person:
        return {'error': 'Persoon niet gevonden'}, 404
    # Update fields
    for field in ['naam', 'geboortedatum', 'overlijdensdatum', 'bijzonderheden']:
        if field in data:
            person[field] = data[field]
    _save_stamboom_json(stamboom_data)
    return {'success': True, 'persoon': person}

@app.route('/api/tree')
def api_tree():
    stamboom_data._laad_data_sync()
    # Laad posities uit apart bestand
    pos_path = 'stamboom_positions.json'
    positions = {}
    if os.path.exists(pos_path):
        with open(pos_path, 'r', encoding='utf-8') as f:
            positions = json.load(f)
    # Voeg x/y toe aan personen indien bekend, negeer oude posities
    person_ids = set(p['id'] for p in stamboom_data.personen)
    for p in stamboom_data.personen:
        pos = positions.get(p['id']) if positions else None
        if pos and 'x' in pos and 'y' in pos:
            p['x'] = pos['x']
            p['y'] = pos['y']
    # Optioneel: verwijder oude posities uit positions dict (niet meer gebruikte IDs)
    cleaned_positions = {pid: positions[pid] for pid in person_ids if pid in positions}
    if cleaned_positions != positions:
        pos_path = 'stamboom_positions.json'
        with open(pos_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_positions, f, ensure_ascii=False, indent=2)
    # Alleen als er GEEN x/y, geef een nette spreiding (en overschrijf nooit bestaande x/y)
    spacing = 200
    base_y = 0
    x = 0
    for p in stamboom_data.personen:
        if (p.get('x') is None or p.get('y') is None):
            p['x'] = x
            p['y'] = base_y
            x += spacing
    return jsonify(stamboom_data.personen)

@app.route('/api/autosave', methods=['POST'])
def api_autosave():
    stamboom_data._laad_data_sync()
    _save_stamboom_json(stamboom_data)
    return {'success': True}

# Voeg backend endpoint toe voor zoeken op naam
@app.route('/api/search_person', methods=['GET'])
def api_search_person():
    query = request.args.get('q', '').strip().lower()
    stamboom_data._laad_data_sync()
    if not query:
        return jsonify([])
    results = [p for p in stamboom_data.personen if query in (p.get('naam') or '').lower()]
    return jsonify(results)

@app.route('/api/save_position', methods=['POST'])
def api_save_position():
    data = request.json
    person_id = data.get('id')
    x = data.get('x')
    y = data.get('y')
    if not person_id or x is None or y is None:
        return {'error': 'id, x en y zijn verplicht'}, 400
    stamboom_data._laad_data_sync()
    person = next((p for p in stamboom_data.personen if p['id'] == person_id), None)
    if not person:
        return {'error': 'Persoon niet gevonden'}, 404
    person['x'] = x
    person['y'] = y
    _save_stamboom_json(stamboom_data)
    return {'success': True}

# Helper to save to JSON

def _save_stamboom_json(stamboom_data):
    with open(stamboom_data.json_path, 'w', encoding='utf-8') as f:
        json.dump({'personen': stamboom_data.personen}, f, ensure_ascii=False, indent=2)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')


# Nieuw endpoint om alle posities op te slaan
@app.route('/api/save_positions', methods=['POST'])
def api_save_positions():
    data = request.json
    positions = data.get('positions', {})
    # Sla posities op in apart bestand
    pos_path = 'stamboom_positions.json'
    with open(pos_path, 'w', encoding='utf-8') as f:
        json.dump(positions, f, ensure_ascii=False, indent=2)
    return {'success': True}

if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False)
